"""
首次使用辅助脚本：用来在 Playwright 管理的浏览器中手动登录各平台
运行后会打开浏览器，你手动登录 ChatGPT、Claude、Gemini 后关闭即可
登录状态会保存在 chrome_profile_path 指定的目录中
"""

import asyncio
from playwright.async_api import async_playwright
from config import SETTINGS, PLATFORMS


async def main():
    print("\n" + "="*50)
    print("  🔐 首次登录设置")
    print("="*50)
    print(f"\n浏览器 Profile 将保存到：")
    print(f"  {SETTINGS['chrome_profile_path']}\n")
    print("浏览器打开后，请手动登录以下平台：")
    for pid, p in PLATFORMS.items():
        print(f"  - {p['name']}: {p['url']}")
    print("\n全部登录完成后，关闭浏览器窗口即可。\n")

    input("按 Enter 键启动浏览器...")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SETTINGS["chrome_profile_path"],
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )

        # 打开各平台页面
        for pid, platform in PLATFORMS.items():
            page = await context.new_page()
            await page.goto(platform["url"])
            print(f"✅ 已打开 {platform['name']}")

        print("\n请在浏览器中完成登录，完成后关闭浏览器窗口。")
        print("（或按 Enter 键关闭）")
        input()

        await context.close()
        print("\n✅ 登录状态已保存！现在可以运行 python main.py")


if __name__ == "__main__":
    asyncio.run(main())
