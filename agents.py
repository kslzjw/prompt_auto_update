"""
各平台的 Agent 实现
每个 Agent 负责：打开页面、发送消息、等待并提取回答
"""

import asyncio
from playwright.async_api import Page
from config import SETTINGS, PLATFORMS


def get_agent(platform_id: str, page: Page):
    """工厂函数：根据平台ID返回对应的Agent实例"""
    agents = {
        "chatgpt": ChatGPTAgent,
        "claude": ClaudeAgent,
        "gemini": GeminiAgent,
    }
    cls = agents.get(platform_id)
    if not cls:
        raise ValueError(f"不支持的平台：{platform_id}")
    return cls(page, platform_id)

class BaseAgent:
    def __init__(self, page: Page, platform_id: str):
        self.page = page
        self.platform_id = platform_id
        self.config = PLATFORMS[platform_id]
        self.has_active_chat = False

    async def open(self):
        """打开平台页面"""
        await self.page.goto(self.config["url"], wait_until="domcontentloaded")
        await asyncio.sleep(3)
        print(f"   ✅ {self.config['name']} 页面已加载")

    async def send_and_get(self, text: str) -> str:
        """发送消息并等待完整回答（子类实现）"""
        raise NotImplementedError

    async def wait_for_stable_response(self, get_text_fn, timeout: int = None) -> str:
        """
        等待响应文本稳定（停止变化）来判断生成完成
        """
        timeout = timeout or SETTINGS["response_timeout"]
        interval = SETTINGS["stability_check_interval"]
        threshold = SETTINGS["stability_threshold"]

        stable_count = 0
        last_text = ""
        elapsed = 0

        print(f"   ⏳ 等待响应...", end="", flush=True)

        while elapsed < timeout:
            await asyncio.sleep(interval)
            elapsed += interval

            try:
                current_text = await get_text_fn()
            except Exception:
                current_text = ""

            if current_text and current_text == last_text:
                stable_count += 1
                print(".", end="", flush=True)
                if stable_count >= threshold:
                    print(f" 完成！({elapsed}秒)")
                    return current_text
            else:
                stable_count = 0
                last_text = current_text
                print("~", end="", flush=True)

        print(f" 超时！返回当前内容")
        return last_text


class ChatGPTAgent(BaseAgent):
    async def send_and_get(self, text: str) -> str:
        page = self.page

        # 仅在没有活跃聊天时导航到新对话并等待 Cloudflare（避免上下文污染）
        if not self.has_active_chat:
            await page.goto("https://chatgpt.com", wait_until="domcontentloaded")
            
            # 增加防作弊检测等待：如果此时出现了 Cloudflare 或真人验证，等待用户手动点击通过（最长等待 30 秒）
            print("   🔍 正在检查是否有 ChatGPT 验证/Cloudflare，如出现请手动点击...")
            try:
                # 判断是否有经典的验证元素（例如 Turnstile, challenge form）
                await page.wait_for_selector(
                    "input#prompt-textarea, textarea[data-id='root'], textarea[placeholder], [contenteditable='true']", 
                    state="visible", 
                    timeout=30000
                )
                print("   ✅ ChatGPT 验证通过，对话界面已加载！")
                self.has_active_chat = True
            except Exception:
                print("   ⚠️ ChatGPT 聊天界面加载超时，可能还在验证页面或受到其他拦截。直接尝试继续...")
            
            await asyncio.sleep(2)

        # 定位输入框（多个 selector 备用）
        input_selectors = [
            "#prompt-textarea",
            "textarea[data-id='root']",
            "textarea[placeholder]",
            "[contenteditable='true']",
        ]

        input_box = None
        for sel in input_selectors:
            try:
                # 寻找输入框并等待其可交互
                input_box = page.locator(sel).first
                await input_box.wait_for(state="visible", timeout=3000)
                break
            except Exception:
                continue

        if not input_box:
            raise RuntimeError("ChatGPT: 找不到输入框 (可能是验证未通过或者UI变更)")

        # 聚焦并输入文本（对于复杂的富文本框，使用原生的 fill/type 最稳定）
        await input_box.click()
        await asyncio.sleep(0.5)

        # 清空现有内容并输入
        await input_box.fill(text)
        await asyncio.sleep(0.5)

        # 点击发送按钮
        send_selectors = [
            "button[data-testid='send-button']",
            "button[aria-label='Send message']",
            "button[aria-label*='Send']",
            "button svg[data-icon='arrow-up']",
        ]
        sent = False
        for sel in send_selectors:
            try:
                btn = page.locator(sel).first
                await btn.wait_for(state="visible", timeout=3000)
                await btn.click()
                sent = True
                break
            except Exception:
                continue

        if not sent:
            # 备用：按 Enter 发送
            await input_box.press("Enter")

        await asyncio.sleep(2)

        # 等待并提取回答
        async def get_response_text():
            try:
                # 获取最后一条助手消息
                responses = await page.locator(
                    "[data-message-author-role='assistant'] .markdown, "
                    "[data-message-author-role='assistant'] .prose, "
                    "article.w-full .markdown"
                ).all_text_contents()
                return responses[-1] if responses else ""
            except Exception:
                return ""

        return await self.wait_for_stable_response(get_response_text)


class ClaudeAgent(BaseAgent):
    async def send_and_get(self, text: str) -> str:
        page = self.page

        # 仅在没有活跃聊天时导航到新对话
        if not self.has_active_chat:
            await page.goto("https://claude.ai/new", wait_until="domcontentloaded")
            
            # 增加防作弊检测等待：如果此时出现了 Cloudflare 或真人验证，等待用户手动点击通过（最长等待 30 秒）
            print("   🔍 正在检查是否有 Claude 验证/Cloudflare，如出现请手动点击...")
            try:
                await page.wait_for_selector(
                    "div[contenteditable='true'].ProseMirror, div[contenteditable='true'], fieldset div[contenteditable='true']", 
                    state="visible", 
                    timeout=30000
                )
                print("   ✅ Claude 验证通过，对话界面已加载！")
                self.has_active_chat = True
            except Exception:
                print("   ⚠️ Claude 聊天界面加载超时，可能还在验证页面或受到其他拦截。直接尝试继续...")

            await asyncio.sleep(2)

        # 定位输入框
        input_selectors = [
            "div[contenteditable='true'].ProseMirror",
            "div[contenteditable='true']",
            "fieldset div[contenteditable='true']",
        ]

        input_box = None
        for sel in input_selectors:
            try:
                input_box = page.locator(sel).first
                await input_box.wait_for(state="visible", timeout=3000)
                break
            except Exception:
                continue

        if not input_box:
            raise RuntimeError("Claude: 找不到输入框 (可能是验证未通过或者UI变更)")

        await input_box.click()
        await asyncio.sleep(0.5)

        # 使用 Playwright 自身的 fill 进行输入，对 React 最稳定
        await input_box.fill(text)
        await asyncio.sleep(0.5)

        # 点击发送
        send_selectors = [
            "button[aria-label='Send Message']",
            "button[aria-label*='Send']",
            "button[type='submit']",
        ]
        sent = False
        for sel in send_selectors:
            try:
                btn = page.locator(sel).first
                await btn.wait_for(state="visible", timeout=3000)
                await btn.click()
                sent = True
                break
            except Exception:
                continue

        if not sent:
            await input_box.press("Enter")

        await asyncio.sleep(2)

        # 等待并提取回答
        async def get_response_text():
            try:
                responses = await page.locator(
                    ".font-claude-message, "
                    "[data-is-streaming='false'] .prose, "
                    ".prose.max-w-none"
                ).all_text_contents()
                return responses[-1] if responses else ""
            except Exception:
                return ""

        return await self.wait_for_stable_response(get_response_text)


class GeminiAgent(BaseAgent):
    async def send_and_get(self, text: str) -> str:
        page = self.page

        # 仅在没有活跃聊天时导航到新对话
        if not self.has_active_chat:
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            self.has_active_chat = True

        # 定位输入框
        input_selectors = [
            "rich-textarea div[contenteditable='true']",
            "div.input-area-container div[contenteditable='true']",
            "div[contenteditable='true']",
            "textarea.input-box",
        ]

        input_box = None
        for sel in input_selectors:
            try:
                input_box = page.locator(sel).first
                await input_box.wait_for(state="visible", timeout=5000)
                break
            except Exception:
                continue

        if not input_box:
            raise RuntimeError("Gemini: 找不到输入框")

        await input_box.click()
        await asyncio.sleep(0.5)

        # 注入文本
        await input_box.fill(text)
        await asyncio.sleep(0.5)

        # 发送
        send_selectors = [
            "button.send-button",
            "button[aria-label='Send message']",
            "button[aria-label*='Send']",
            "mat-icon[data-mat-icon-name='send']",
        ]
        sent = False
        for sel in send_selectors:
            try:
                btn = page.locator(sel).first
                await btn.wait_for(state="visible", timeout=3000)
                await btn.click()
                sent = True
                break
            except Exception:
                continue

        if not sent:
            await input_box.press("Enter")

        await asyncio.sleep(2)

        # 等待并提取回答
        async def get_response_text():
            try:
                responses = await page.locator(
                    "message-content .markdown, "
                    ".response-container-content .markdown, "
                    "model-response .markdown"
                ).all_text_contents()
                return responses[-1] if responses else ""
            except Exception:
                return ""

        return await self.wait_for_stable_response(get_response_text)
