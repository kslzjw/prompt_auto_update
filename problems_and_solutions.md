# 项目开发问题与解决方案汇总

本文档整理了在 `prompt_auto_update` 开发过程中遇到的核心业务/技术问题及其对应的解决方法。

---

## 1. 自动化工具特征被识别 (Bot Detection)
### 问题描述
ChatGPT、Claude 等平台拥有极高的反爬/反自动化检测机制。最初使用 Playwright 默认的 Chromium 浏览器时，页面常由于 “检测到自动化工具” 而被拒绝访问，或者无法正常登录 Google 账号。

### 解决方案
- **切换至正式版 Chrome**：在浏览器启动参数中指定 `channel="chrome"`，使用系统安装的正式版 Google Chrome。
- **引入 Stealth 插件**：集成 `playwright-stealth` 库，抹除自动化指纹。
- **绕过自动化控制参数**：在启动时禁用了 `AutomationControlled` 特征，并忽略了 Playwright 默认的 `--enable-automation` 参数。

### 代码实现概要
```python
# main.py 启动配置
context = await p.chromium.launch_persistent_context(
    user_data_dir=SETTINGS["chrome_profile_path"],
    channel="chrome",  # 使用正式版 Chrome
    headless=False,
    args=[
        "--start-maximized", 
        "--disable-blink-features=AutomationControlled" # 禁用自动化控制特征
    ],
    ignore_default_args=["--enable-automation"], # 忽略默认自动化参数
    no_viewport=True,
)

# 应用 Stealth 抹除指纹
from playwright_stealth import Stealth
await Stealth().apply_stealth_async(page)
```

---

## 2. 人机校验 (Cloudflare) 拦截
### 问题描述
即便隐藏了浏览器特征，在访问 ChatGPT 或 Claude 时仍会频繁触发 Cloudflare 的 “验证你是人类” (Verify you are human) 的 Checkbox。脚本由于运行速度过快，在验证框出现时会因为找不到输入框而直接报 Timeout 错误。

### 解决方案
- **显式等待机制**：在 `agents.py` 中为 ChatGPT 和 Claude 增加了专门的 “防御等待期”。
- **动态监测**：脚本在导航到页面后，会检测是否存在验证码或加载中状态，给予用户最长 30 秒的窗口进行手动点击校验。

### 代码实现概要
```python
# agents.py 中的防御性等待
try:
    # 等待关键输入元素出现，作为验证通过的标志
    await page.wait_for_selector(
        "input#prompt-textarea, [contenteditable='true']", 
        state="visible", 
        timeout=30000 # 最长等待 30 秒供人工点击或系统自动通过
    )
except Exception:
    print("⚠️ 验证超时，尝试继续执行...")

# 状态稳定检测逻辑
async def wait_for_stable_response(self, get_text_fn):
    # 通过对比前后两次获取的文本是否一致，判断 AI 是否回复完毕
    while elapsed < timeout:
        current_text = await get_text_fn()
        if current_text == last_text:
            stable_count += 1
            if stable_count >= threshold: return current_text
        else:
            stable_count = 0
```

---

## 3. 动态 React/ProseMirror 输入框注入失败
### 问题描述
ChatGPT 和 Claude 的前端 UI 经常更新。最初使用 JavaScript 的 `document.execCommand('insertText')` 或直接修改 `innerHTML`/`value` 的方式向输入框注入文本。由于现代前端框架（React）的 State 绑定机制，这种直接修改 DOM 的方式无法触发页面逻辑，导致内容看起来填进去了，但点击发送按钮时内容消失或报错。

### 解决方案
- **原生 API 填充**：弃用不稳定的 JS 注入，改用 Playwright 原生的 `input_box.fill(text)` 方法。
- **事件模拟**：该方法会完整触发 React 或富文本框架（如 ProseMirror）所需的 input、focus 等事件。

### 代码实现概要
```python
# agents.py 使用 fill 确保触发 React State 更新
input_box = page.locator("#prompt-textarea").first
await input_box.fill(text) # 原生 fill 模拟真实输入事件
```

---

## 4. 多轮对话中的上下文丢失
### 问题描述
最初的逻辑中，每一轮 “起草” 或 “评价” 都会调用 `page.goto()` 重新打开一个新的对话窗口。这导致原本属于同一个工作流的优化过程在网页端看起来支离破碎，AI 无法利用同一会话中的上文语境。

### 解决方案
- **会话持久化状态**：在 `BaseAgent` 类中增加了 `has_active_chat` 状态位。
- **按需导航**：只有在 Agent 第一次接收任务时才会执行 `goto`（开启新对话），后续所有迭代消息直接在同一个 Page 页面寻找输入框并发送。

### 代码实现概要
```python
# agents.py 按需导航逻辑
if not self.has_active_chat:
    await page.goto("https://chatgpt.com")
    self.has_active_chat = True # 标记当前页面已有活跃对话

# 后续直接定位输入框发送，不再重新 goto
await input_box.fill(text)
```

---

## 5. 浏览器 Profile 锁定与冲突
### 问题描述
由于程序使用了持久化的 `chrome_profile_path` 来保存登录状态，当用户的系统中已经有一个正在运行的 Chrome 实例（或者上次非正常退出导致的残留进程）占用了该 Profile 时，Playwright 启动会报 `TargetClosedError`。

### 解决方案
- **环境诊断引导**：在文档中明确了启动失败的常见原因。
- **手动清理指令**：提供 `pkill -f "Google Chrome"` 等指令建议。

### 代码实现概要
```bash
# 遇到 Profile 被占用时，强制关闭残留的 Chrome 进程
pkill -f "Google Chrome"

# 或者在代码启动前检查目录锁定文件（本项目目前推荐手动清理）
```

---

## 6. 工作流闭环与结果持久化
### 问题描述
生成的优化结果原本只显示在终端，不便后续查阅。且 browser 在任务完成后会立刻自动关闭，导致用户无法手动干预或保存尚未提取的状态。

### 解决方案
- **自动保存 Markdown**：逻辑中增加了 `save_results` 函数，将结果自动保存至 `./output` 目录。
- **持续对话模式**：将 `main.py` 的执行逻辑改为 `while True` 循环。

### 代码实现概要
```python
# main.py 持续循环
while True:
    question = input("\n📝 请输入你的问题：\n> ")
    if question.lower() in ["exit", "quit"]: break
    results = await run_workflow(question, agents)
    save_results(question, results) # 自动持久化到本地 Markdown

# save_results 实现概要
def save_results(question, results):
    filename = f"./output/result_{timestamp}.md"
    with open(filename, "w") as f:
        f.write(f"# Question: {question}\n\n")
        # 遍历 results 写入内容...
```
