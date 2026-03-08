"""
配置文件 - 修改这里来定制你的工作流
"""
import os

# ============================================================
# 平台配置
# ============================================================
PLATFORMS = {
    "chatgpt": {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
    },
    "claude": {
        "name": "Claude",
        "url": "https://claude.ai/new",
    },
    "gemini": {
        "name": "Gemini",
        "url": "https://gemini.google.com/app",
    },
}

# ============================================================
# 工作流配置（按顺序列出 agent 角色）
#
# 规则：
#   WORKFLOW[0] = 起草者（生成初始回答 + 每轮优化）
#   WORKFLOW[1] = 批评者（评价回答，提出改进建议）
#   WORKFLOW[2] = 综合者（可选，最终汇总）
#
# 示例方案：
#   ["chatgpt", "claude"]             → GPT起草，Claude批评
#   ["claude", "gemini", "chatgpt"]   → Claude起草，Gemini批评，GPT综合
#   ["chatgpt", "chatgpt"]            → 单模型自我批评迭代
# ============================================================
WORKFLOW = ["chatgpt", "claude"]   # ← 改这里来切换模型组合

# ============================================================
# 运行设置
# ============================================================
SETTINGS = {
    # 迭代优化轮数（每轮 = 1次批评 + 1次改进）
    "rounds": 2,

    # 结果保存目录
    "output_dir": "./output",

    # Chrome 用户数据目录（保留你的登录状态）
    # Windows 默认路径示例：
    #   "C:/Users/你的用户名/AppData/Local/Google/Chrome/User Data"
    # macOS 默认路径示例：
    #   "/Users/你的用户名/Library/Application Support/Google/Chrome"
    # Linux 默认路径示例：
    #   "/home/你的用户名/.config/google-chrome"
    "chrome_profile_path": os.path.expanduser("~") + "/chrome_profile_for_playwright",

    # 每次发送消息后等待响应的最长时间（秒）
    "response_timeout": 120,

    # 响应稳定检测间隔（秒）- 用于判断AI是否还在生成中
    "stability_check_interval": 3,

    # 响应稳定需要连续多少次检测无变化才算完成
    "stability_threshold": 3,
}
