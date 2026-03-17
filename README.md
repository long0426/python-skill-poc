# python-skill-poc

這是一個關於 **Just-in-Time (JIT) Skill Loading (按需加載技能)** 的技術驗證 (POC) 專案。其核心概念是：根據任務需求，動態地將特定領域的標準作業程序 (SOP) 與工具注入到 AI Agent 中，而非在啟動時就塞入所有內容。

本專案基於 [Google ADK](https://google.github.io/adk-docs/) 開發，並使用 `LiteLLM` 來確保模型切換的靈活性。

---

## 背景與動機

傳統的 AI Agent 通常在啟動時就負載了所有知識與指令，這會導致兩個主要問題：

1. **上下文爆量 (Context Overflow)**：將無關的 SOP 塞進 Context Window 會浪費 Token，並降低模型的檢索準確度（容易失憶）。
2. **行為污染 (Behavioral Contamination)**：例如一個負責「程式碼審查」的 Agent，如果同時啟動了「財務分析」技能，可能會在審查程式時意外套用了財務規則。

本專案展示了一個更乾淨的模式：**Agent 只在需要時，才加載對應的技能，執行完後即釋放。**

Skill格式參考了 [agentskills.io](https://agentskills.io/specification) 的規範 —— 每個Skill都是一個 `SKILL.md` 檔案，包含 YAML Frontmatter 格式的標記資料 (Metadata) 以及 Markdown 格式的 SOP 內容。

---

## 範例展示：美股研究助理

專案內包含了一個具體的實作範例：**美股情報簡報助理 (US Stock Intelligence Brief Assistant)**。

當使用者提供股票代號（例如：`AAPL`, `NVDA`）時，Agent 會嚴格執行以下工作流：

```
1. 技能發現 (Skill Discovery)：僅列出可用技能摘要，不讀取詳細內容。
2. 加載「data-harvesting」技能 → 執行資料採集 SOP（獲取股價、新聞）。
3. 加載「factual-synthesis」技能 → 對採集到的資料執行分析 SOP。
4. 產出結構化的 Markdown 投資建議報告。
```

Agent 永遠不會同時加載這兩個技能，而是遵循嚴格的 **「載入 → 執行 → 繼續下一步」** 的循環。

---

## 專案架構

```
python-skill-poc/
├── main.py                         # 程式進入點 (僅印出啟動資訊)
├── pyproject.toml                  # 使用 uv 管理的依賴套件
└── my_agent/
    ├── agent.py                    # ADK Agent 定義、MCP 工具組、回調函式
    ├── skill_manager.py            # 掃描 skills/ 目錄，解析 SKILL.md 的標記資料
    ├── mcp_config.json             # MCP Server 設定 (例如：Yahoo Finance)
    ├── mcp_config_dataset.json     # 備用的 MCP 設定範例
    ├── skills/
    │   ├── data-harvesting/
    │   │   └── SKILL.md            # SOP：以結構化 JSON 獲取市場數據與新聞
    │   └── factual-synthesis/
    │       └── SKILL.md            # SOP：將資料合成投資級別的情報分析
    └── tools/
        ├── skills.py               # 提供 discover_skills() 與 load_skill_protocol() 工具
        └── time.py                 # 提供 get_current_time() 與 calculate_past_time() 工具
```

### 核心元件說明

| 元件 | 職責 |
|---|---|
| `SkillManager` | 在啟動時掃描 `skills/` 目錄，僅讀取元數據（延遲加載）。 |
| `discover_skills()` | 暴露給 Agent 的工具 —— 回傳所有可用Skill的摘要。 |
| `load_skill_protocol()` | 暴露給 Agent 的工具 —— 讀取並回傳特定Skill的完整 SOP 內容。 |
| `log_prompt_length` | 基於 `before_model_callback` —— 紀錄 Prompt 長度，並將每次 LLM 呼叫存檔至 `logs/`。 |
| MCP Toolset | 依據 `mcp_config.json` 連接外部 MCP Server（如 Yahoo Finance）。 |

---

## 技能 (Skills) 目錄運作機制

每個Skill都是 `my_agent/skills/` 下的一個子目錄，其中包含一個 `SKILL.md` 檔案：

```markdown
---
name: data-harvesting
description: 收集當前與歷史股價，以及最新的公司新聞。
metadata:
  version: "1.0"
---

步驟：
1. 使用 get_current_time 工具獲取當前系統時間。
2. 獲取歷史股價...
...
```

- **Frontmatter**：啟動時解析，用於輕量級的Skill發現 (Discovery)。
- **Body**：按需加載，只有當 Agent 明確請求讀取該Skill內容時才會載入。

---

## System Prompt 設計

Agent 運行於一個四層治理架構下：

```
治理層 (Governance) → 角色層 (Role) → 任務層 (Task) → 工具層 (Tool)
```

- **治理層**：強制執行「零幻覺」、「來源標註」以及「JIT Skill加載」規則。
- **角色層**：投資銀行的股票研究助理。
- **任務層**：定義了美股情報簡報的 5 個嚴格執行步驟。
- **工具層**：包含Skill管理工具、MCP 工具以及本地 Python 函式。

---

## 準備工作

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) 套件管理工具
- 已設定環境變數的 Azure OpenAI (或相容) API 金鑰

---

## 安裝步驟

**1. 複製儲存庫**

```bash
git clone https://github.com/long0426/python-skill-poc.git
cd python-skill-poc
```

**2. 使用 `uv` 安裝依賴**

```bash
uv sync
```

**3. 設定環境變數**

在 `my_agent/` 目錄下建立 `.env` 檔案，填入模型憑證：

```env
# Azure OpenAI 範例
AZURE_API_KEY=你的金鑰
AZURE_API_BASE=https://你的資源名稱.openai.azure.com/
AZURE_API_VERSION=2024-02-01
```

**4. 設定 MCP Server (選配)**

本專案建議使用 [Yahoo Finance MCP](https://github.com/Alex2Yang97/yahoo-finance-mcp) 作為市場數據來源。

**4.1 本地安裝 MCP Server**

請在與本專案併列的目錄下執行以下指令：

```bash
# 1. 複製儲存庫
git clone https://github.com/Alex2Yang97/yahoo-finance-mcp.git
cd yahoo-finance-mcp

# 2. 建立並啟動虛擬環境項，安裝依賴
uv venv
source .venv/bin/activate  # Windows 使用: .venv\Scripts\activate
uv pip install -e .
```

**4.2 配置 my_agent**

編輯 `my_agent/mcp_config.json` 以指向你的本地 MCP server。請確保將 `/絕對路徑/到/` 替換為你實際存放該專案的絕對路徑：

```json
{
    "mcpServers": {
        "yfinance": {
            "command": "uv",
            "args": ["--directory", "/絕對路徑/到/yahoo-finance-mcp", "run", "server.py"]
        }
    }
}
```


---

## 執行 Agent

使用 ADK web UI 啟動 Agent：

```bash
uv run adk web .
```

接著開啟瀏覽器並前往 `http://localhost:8000/dev-ui/?app=my_agent`，輸入股票代號開始對話：

```
AAPL
NVDA
TSLA
```

---

## 如何新增技能

1. 在 `my_agent/skills/` 下建立新目錄，例如 `my_agent/skills/risk-assessment/`。
2. 新增 `SKILL.md` 檔案，並填入 YAML Frontmatter：

```markdown
---
name: risk-assessment
description: 評估特定股票的下行風險因素與波動率。
---

這裡填入你的 SOP 內容...
```

3. 重啟 Agent —— `SkillManager` 會在啟動時自動發現新技能，無需修改任何程式碼。

---

## 紀錄 (Logging)

每次 LLM 呼叫都會自動記錄在 `my_agent/logs/` 中。每個 Session 會建立一個帶時間戳的子目錄：

```
my_agent/logs/
└── AAPL_20260313101500/
    ├── call_001.txt    # 第一次呼叫的 System Prompt + Context
    ├── call_002.txt    # 第二次呼叫的內容
    └── ...
```

這對於除錯 Prompt 內容、驗證技能注入邏輯以及審計 Token 消耗非常有用。

---

## 技術堆疊

| 套件 | 用途 |
|---|---|
| `google-adk[gradio]` | Agent 框架與網頁 UI |
| `litellm` | 統一的 LLM API (支援 Azure, OpenAI, Anthropic 等) |
| `python-frontmatter` | 解析 SKILL.md 的 YAML 元數據 |
| `pyyaml` | YAML 支援 |
| `gradio` | 網頁前端介面 |

---

## 授權

MIT
