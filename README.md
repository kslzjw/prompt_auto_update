# 🤖 Multi-Agent Answer Optimizer

Automatically orchestrate iterative answer refinement across ChatGPT, Claude, and Gemini using Playwright for real browser automation.

---

## How It Works

```
You enter a question
    ↓
Agent A (Drafter) generates an initial answer
    ↓
Agent B (Critic) analyzes the answer and suggests improvements
    ↓
Agent A refines based on feedback
    ↓
(Repeat for N rounds)
    ↓
[Optional] Agent C (Synthesizer) distills the final version
    ↓
Results saved to outputs/
```

---

## Quick Start

### Step 1: Install Dependencies

```bash
# One-click install (Python packages + Chromium browser)
bash install.sh

# Or manually:
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Configure

Edit `config.py`:

```python
# Workflow: who drafts, who critiques, who synthesizes (optional)
WORKFLOW = ["chatgpt", "claude"]   # e.g. GPT drafts, Claude critiques

# Number of iteration rounds
"rounds": 2,

# Chrome Profile path (to persist your login sessions)
# macOS:   "/Users/yourname/Library/Application Support/Google/Chrome"
# Windows: "C:/Users/yourname/AppData/Local/Google/Chrome/User Data"
# Linux:   "/home/yourname/.config/google-chrome"
"chrome_profile_path": "...",
```

### Step 3: Login to Platforms (First Time Only)

```bash
python setup_login.py
```

A browser window will open. Manually log in to ChatGPT, Claude, and Gemini, then close the window. Your login sessions will be saved.

### Step 4: Run

```bash
python main.py
```

Enter your question and wait for the automated iteration to complete.

---

## Workflow Examples

### Option A: GPT drafts, Claude critiques (default)
```python
WORKFLOW = ["chatgpt", "claude"]
```

### Option B: Claude drafts, Gemini critiques, GPT synthesizes
```python
WORKFLOW = ["claude", "gemini", "chatgpt"]
```

### Option C: Single-model self-iteration
```python
WORKFLOW = ["chatgpt", "chatgpt"]
```

---

## Output

Each run generates two files in the `outputs/` directory:

- `result_<timestamp>.md` — Human-readable Markdown report with the full question, critique, and improvement history
- `result_<timestamp>.json` — Structured data for programmatic processing

---

## FAQ

**Q: Can't find the input box?**  
A: Platform UIs may change. Add updated CSS selectors to the corresponding platform's `input_selectors` in `agents.py`.

**Q: Response extraction is empty?**  
A: Update the CSS selectors in the `get_response_text` function for the corresponding platform in `agents.py`. Use browser DevTools to inspect the actual DOM structure.

**Q: How to debug?**  
A: The browser runs in headed mode — you can watch every step in real time.

**Q: Can I add more platforms?**  
A: Yes! Add a new platform config in `config.py` under `PLATFORMS`, and create a corresponding Agent class in `agents.py`.

---

## Project Structure

```
prompt_auto_update/
├── main.py          # Main program — workflow orchestration
├── agents.py        # Platform Agent implementations
├── config.py        # Configuration (edit this!)
├── setup_login.py   # First-time login helper script
├── install.sh       # One-click dependency installer
├── requirements.txt # Python dependencies
├── README.md        # This file (English)
├── README_CN.md     # 中文文档
└── outputs/         # Results output directory (auto-created)
```

---

## License

MIT
