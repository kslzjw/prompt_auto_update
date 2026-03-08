# 🤖 Multi-Agent Answer Optimizer

使用 Playwright 自动控制真实浏览器，在 ChatGPT、Claude、Gemini 之间传递和迭代优化答案。

---

## 工作原理

```
你输入问题
    ↓
Agent A (起草者) 生成初始回答
    ↓
Agent B (批评者) 分析回答，提出改进建议
    ↓
Agent A 根据建议重新优化
    ↓
（重复 N 轮）
    ↓
[可选] Agent C (综合者) 提炼最终版本
    ↓
保存结果到 outputs/ 目录
```

---

## 快速开始

### 第一步：安装依赖

```bash
# 一键安装（Python 依赖 + Chromium 浏览器）
bash install.sh

# 或手动安装：
pip install -r requirements.txt
playwright install chromium
```

### 第二步：配置

打开 `config.py`，修改以下内容：

```python
# 工作流：谁负责起草、谁负责批评、谁负责综合（可选）
WORKFLOW = ["chatgpt", "claude"]   # 例：GPT起草，Claude批评

# 迭代轮数
"rounds": 2,

# Chrome Profile 路径（用来保留你的登录状态）
# macOS:   "/Users/你的名字/Library/Application Support/Google/Chrome"
# Windows: "C:/Users/你的名字/AppData/Local/Google/Chrome/User Data"
# Linux:   "/home/你的名字/.config/google-chrome"
"chrome_profile_path": "...",
```

### 第三步：登录各平台（首次使用）

```bash
# 用你自己的 Chrome Profile 路径启动浏览器
python setup_login.py
```

在弹出的浏览器中手动登录 ChatGPT、Claude、Gemini，然后关闭。登录状态会被保存。

### 第四步：运行

```bash
python main.py
```

输入你的问题，然后等待自动迭代完成。

---

## 配置示例

### 方案 A：GPT 起草，Claude 批评（默认）
```python
WORKFLOW = ["chatgpt", "claude"]
```

### 方案 B：Claude 起草，Gemini 批评，GPT 综合
```python
WORKFLOW = ["claude", "gemini", "chatgpt"]
```

### 方案 C：单模型自我迭代
```python
WORKFLOW = ["chatgpt", "chatgpt"]
```

---

## 输出结果

每次运行在 `outputs/` 目录生成两个文件：

- `result_时间戳.md` — 可读的 Markdown 报告，包含每轮的问题、批评、改进过程
- `result_时间戳.json` — 结构化数据，方便二次处理

---

## 常见问题

**Q: 提示找不到输入框？**  
A: 各平台页面结构可能更新，在 `agents.py` 中对应平台的 `input_selectors` 里添加新的 CSS 选择器。

**Q: 响应提取为空？**  
A: 在 `agents.py` 中对应平台的 `get_response_text` 函数里更新 CSS 选择器。可以在浏览器开发者工具中检查实际的元素结构。

**Q: 如何调试？**  
A: 脚本运行时浏览器窗口是可见的，你可以实时观察每一步操作。

**Q: 可以添加更多平台吗？**  
A: 可以！在 `config.py` 的 `PLATFORMS` 中添加新平台配置，在 `agents.py` 中添加对应的 Agent 类。

---

## 文件结构

```
prompt_auto_update/
├── main.py          # 主程序，工作流调度
├── agents.py        # 各平台 Agent 实现
├── config.py        # 配置（改这里！）
├── setup_login.py   # 首次登录辅助脚本
├── install.sh       # 一键安装脚本
├── requirements.txt # Python 依赖
├── README.md        # English documentation
├── README_CN.md     # 本文件（中文文档）
└── outputs/         # 结果输出目录（自动创建）
```
