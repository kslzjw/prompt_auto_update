"""
Multi-Agent Answer Optimizer
使用 Playwright 自动在 ChatGPT / Claude / Gemini 之间传递、批评、优化答案
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext
from config import PLATFORMS, WORKFLOW, SETTINGS
from agents import get_agent


async def main():
    print("\n" + "="*60)
    print("  🤖 Multi-Agent Answer Optimizer")
    print("="*60)

    # 获取用户输入
    question = input("\n📝 请输入你的问题：\n> ").strip()
    if not question:
        print("问题不能为空，退出。")
        return

    print(f"\n⚙️  工作流：{' → '.join(WORKFLOW)}")
    print(f"🔄 迭代轮数：{SETTINGS['rounds']}")
    print(f"📁 结果保存至：{SETTINGS['output_dir']}\n")

    # 启动浏览器（使用已有的用户 Profile，保留登录状态）
    async with async_playwright() as p:
        print("🌐 启动浏览器中（使用你已有的 Chrome 登录状态）...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SETTINGS["chrome_profile_path"],
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )

        # 初始化所有用到的 agent 页面
        agents = {}
        for platform_id in set(WORKFLOW):
            if platform_id not in PLATFORMS:
                print(f"❌ 未知平台：{platform_id}，跳过")
                continue
            print(f"   打开 {PLATFORMS[platform_id]['name']} ...")
            page = await context.new_page()
            agent = get_agent(platform_id, page)
            await agent.open()
            agents[platform_id] = agent
            await asyncio.sleep(2)

        print("\n✅ 所有页面已打开，开始优化流程...\n")
        await asyncio.sleep(2)

        # 执行工作流
        results = await run_workflow(question, agents)

        # 保存结果
        save_results(question, results)

        print("\n✅ 完成！按 Enter 键关闭浏览器...")
        input()
        await context.close()


async def run_workflow(question: str, agents: dict) -> list:
    """
    执行多轮优化工作流
    WORKFLOW 定义了每一步使用哪个 agent
    """
    rounds = SETTINGS["rounds"]
    results = []

    # 第一步：初始回答（由 WORKFLOW[0] 生成）
    drafter_id = WORKFLOW[0]
    drafter = agents[drafter_id]

    print(f"{'='*50}")
    print(f"📤 第一步：{PLATFORMS[drafter_id]['name']} 生成初始回答")
    print(f"{'='*50}")

    initial_answer = await drafter.send_and_get(question)
    print(f"\n💬 初始回答（前200字）：\n{initial_answer[:200]}...\n")

    results.append({
        "round": 0,
        "step": "initial",
        "agent": drafter_id,
        "role": "drafter",
        "input": question,
        "output": initial_answer,
    })

    current_answer = initial_answer

    # 多轮迭代优化
    for round_num in range(1, rounds + 1):
        print(f"\n{'='*50}")
        print(f"🔄 第 {round_num} 轮优化")
        print(f"{'='*50}")

        # 步骤1：批评者评价当前答案
        critic_id = WORKFLOW[1] if len(WORKFLOW) > 1 else WORKFLOW[0]
        critic = agents[critic_id]
        critic_prompt = build_critic_prompt(question, current_answer)

        print(f"\n🔍 [{PLATFORMS[critic_id]['name']}] 正在分析和批评...")
        critique = await critic.send_and_get(critic_prompt)
        print(f"📋 批评意见（前200字）：\n{critique[:200]}...\n")

        results.append({
            "round": round_num,
            "step": "critique",
            "agent": critic_id,
            "role": "critic",
            "input": critic_prompt,
            "output": critique,
        })

        # 步骤2：起草者根据批评优化答案
        drafter_id = WORKFLOW[0]
        drafter = agents[drafter_id]
        improve_prompt = build_improve_prompt(question, current_answer, critique)

        print(f"\n✏️  [{PLATFORMS[drafter_id]['name']}] 正在根据批评优化答案...")
        improved_answer = await drafter.send_and_get(improve_prompt)
        print(f"📝 优化后答案（前200字）：\n{improved_answer[:200]}...\n")

        results.append({
            "round": round_num,
            "step": "improvement",
            "agent": drafter_id,
            "role": "drafter",
            "input": improve_prompt,
            "output": improved_answer,
        })

        current_answer = improved_answer

    # 可选：最终综合（如果 WORKFLOW 有第三个 agent）
    if len(WORKFLOW) >= 3:
        synthesizer_id = WORKFLOW[2]
        synthesizer = agents[synthesizer_id]
        synth_prompt = build_synthesis_prompt(question, current_answer, results)

        print(f"\n🎯 [{PLATFORMS[synthesizer_id]['name']}] 正在综合最终答案...")
        final_answer = await synthesizer.send_and_get(synth_prompt)

        results.append({
            "round": rounds,
            "step": "synthesis",
            "agent": synthesizer_id,
            "role": "synthesizer",
            "input": synth_prompt,
            "output": final_answer,
        })
        current_answer = final_answer

    print(f"\n{'='*50}")
    print(f"🏁 最终答案：")
    print(f"{'='*50}")
    print(current_answer)

    return results


def build_critic_prompt(question: str, answer: str) -> str:
    return f"""请以严格但建设性的批评者身份，评价以下这个问题的回答。

【原始问题】
{question}

【当前回答】
{answer}

请从以下角度提供具体的改进建议：
1. 内容准确性和完整性
2. 逻辑结构和清晰度
3. 是否真正解决了问题核心
4. 表达方式和实用性

请给出具体、可操作的改进点，而不是泛泛的评价。"""


def build_improve_prompt(question: str, answer: str, critique: str) -> str:
    return f"""请根据以下批评意见，重新改进这个问题的回答。

【原始问题】
{question}

【当前回答】
{answer}

【改进建议】
{critique}

请综合以上批评，提供一个更完整、更准确、更有帮助的改进版本回答。直接给出改进后的完整回答。"""


def build_synthesis_prompt(question: str, best_answer: str, results: list) -> str:
    return f"""你是最终综合者。请基于多轮迭代优化后的最佳答案，提供一个最终、精炼的版本。

【原始问题】
{question}

【经过多轮优化的最佳答案】
{best_answer}

请提供一个结构清晰、简洁有力的最终版本回答。"""


def save_results(question: str, results: list):
    output_dir = Path(SETTINGS["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"result_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Multi-Agent 优化结果\n\n")
        f.write(f"**时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**问题**：{question}\n\n")
        f.write("---\n\n")

        for r in results:
            emoji = {"initial": "📤", "critique": "🔍", "improvement": "✏️", "synthesis": "🎯"}.get(r["step"], "💬")
            f.write(f"## {emoji} Round {r['round']} - {r['step'].upper()} [{r['agent']}]\n\n")
            f.write(f"**角色**：{r['role']}\n\n")
            f.write(f"**输出**：\n\n{r['output']}\n\n")
            f.write("---\n\n")

        # 最终答案
        final = results[-1]["output"]
        f.write(f"## ✅ 最终答案\n\n{final}\n")

    # 同时保存 JSON
    json_file = output_dir / f"result_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({"question": question, "results": results}, f, ensure_ascii=False, indent=2)

    print(f"\n💾 结果已保存：\n   {filename}\n   {json_file}")


if __name__ == "__main__":
    asyncio.run(main())
