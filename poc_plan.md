# 專案：Python 開放技能動態加載 POC (Proof of Concept)

## 1. 專案背景與目標
基於 Openclaw 對於 Skills 的管理與注入模式（讀取目錄、解析 Frontmatter Metadata + Markdown 內容），建立一個以 Python 為基礎的 POC 專案，結合套件名稱為 `google-adk` (版本為 1.21.0)，來展示模型如何「按需加載 (On-demand loading)」額外的技能與工具。

## 2. 核心技術選型
- **開發語言**: Python 3.13
- **套件管理工具**: 使用 `uv` 來管理專案依賴。
- **AI 代理框架**: `google-adk` v1.21.0
- **設定檔與文本解析**: `PyYAML`、`python-frontmatter`
- **架構風格**: 模仿 Openclaw 的 `SKILL.md` 讀取機制與 System Prompt 動態組合。

## 3. POC 場景設計：按需加載 (On-demand Loading)
**Skill 與 MCP (Model Context Protocol) 最大的差異在哪？**
MCP 主要是「提供模型可以呼叫的 Callable Tools（函式）」，而 Openclaw 實作的 Skill 則是「**Prompt Context/SOP + Tools** 的綜合體」。
許多任務光靠工具是不夠的，還需要把「專家知識、分析流程或是公司內部 SOP」等厚重的背景設定塞進 System Prompt 裡。
如果啟動時就把所有專家的 SOP 塞給 Agent，會造成:
1. Context Window（上下文）爆量，花費大量 Token 且容易失憶。
2. 模型行為發散，例如在寫程式時，突然套用了客服的退費條款。

因此「按需加載」的場景會體現：**啟動時只給輕量說明；依意圖動態載入完整的 Prompt 指引（MD 檔）與相關 Tool。**

Agent Skills的spec請參考[Specification](https://agentskills.io/specification)

### 3.1 下載三個真實的開源/現成 Skills 進行測試
為了完全不用自己寫，POC 將直接使用活躍於 GitHub 上的開源 AI Agent 技能庫 (`skillcreatorai/Ai-Agent-Skills`)。這些現成的技能都已經寫好了嚴謹的 YAML Metadata 與 Markdown 提示詞 SOP，我們只需「**直接下載它們的 `SKILL.md` 檔案**」即可讓 Agent 套用：

1. **`python-development` (Python 開發專家)**
   - **來源連結**: [skillcreatorai/python-development](https://github.com/skillcreatorai/Ai-Agent-Skills/tree/main/skills/python-development)
   - **特色**: 下載這個現成的 `SKILL.md` 後，模型會自動具備 Python 3.12+、Django、FastAPI 以及 Type Hints 等開發 SOP 的深層認知。
   - **下載網址**: `https://raw.githubusercontent.com/skillcreatorai/Ai-Agent-Skills/main/skills/python-development/SKILL.md`

2. **`code-review` (程式碼審查專家)**
   - **來源連結**: [skillcreatorai/code-review](https://github.com/skillcreatorai/Ai-Agent-Skills/tree/main/skills/code-review)
   - **特色**: 下載這個技能後，模型會嚴格遵守安全性、效能與邏輯檢查，並依據現成寫好的評估表格格式回覆。
   - **下載網址**: `https://raw.githubusercontent.com/skillcreatorai/Ai-Agent-Skills/main/skills/code-review/SKILL.md`

3. **`code-refactoring` (程式碼重構專家)**
   - **來源連結**: [skillcreatorai/code-refactoring](https://github.com/skillcreatorai/Ai-Agent-Skills/tree/main/skills/code-refactoring)
   - **特色**: 注入重構 SOP，包含遵守 SOLID 原則與設計模式，讓模型從普通助理變成重構大師。
   - **下載網址**: `https://raw.githubusercontent.com/skillcreatorai/Ai-Agent-Skills/main/skills/code-refactoring/SKILL.md`

## 4. 預期 Terminal Demo 互動流程
透過執行 `python main.py`，終端機會展示出明顯的系統動態加載特性：

```text
[系統啟動] 正在掃描 skills/ 目錄...
[Skill Manager] 發現 3 個可用技能 (僅讀取 Metadata)：
  - python-development
  - code-review
  - code-refactoring
[系統啟動] 完成！(目前 System Prompt: 50 字元 - "你是一個有用的 AI 助理")
```

### 📌 情境一：無關閒聊（不觸發技能）
- **User 輸入**: 「你好，請幫我寫一封請假信。」
- **後台印出**: `[Agent] 注入的技能：無` (系統 Prompt 無變化)
- **Model 回覆**: (正常的信件內容，未受到工程師 SOP 規則干擾)

### 📌 情境二：觸發 Python 開發技能
- **User 輸入**: 「我想寫一個登入的 API，請給我範例。」
- **後台印出**: `[Skill Manager] 動態讀取 => skills/python-development/SKILL.md`
- **Model 回覆**: (模型瞬間取得開發 SOP，主動產出包含 FastAPI、async 與 Type Hints 的完整目錄與程式碼結構)

### 📌 情境三：觸發 Code Review 技能
- **User 輸入**: 「幫我看這段程式碼：`def get_data(d): return d['name']`」
- **後台印出**: `[Skill Manager] 動態讀取 => skills/code-review/SKILL.md`
- **Model 回覆**: (嚴格依照技能設定檔規定的「安全性、效能、可讀性」Markdown 表格格式產出審查報告)

### 📌 情境四：觸發 Code Refactoring 技能
- **User 輸入**: 「這段程式碼太亂了，幫我整理乾淨（附上一段 IF-ELSE 程式碼）」
- **後台印出**: `[Skill Manager] 動態讀取 => skills/code-refactoring/SKILL.md`
- **Model 回覆**: (不僅僅是縮減程式碼，而是依照注入的 SOLID 原則，提出採用 Strategy Pattern 或 Enum 的高階重構建議)

## 5. 目錄結構規劃
```text
python-skill-poc/
├── main.py                     # 程式進入點與測試腳本
├── agent_runner.py             # 封裝 Google ADK Agent 的啟動與 Prompt 組合
├── skill_manager.py            # 負責掃描、解析與加載 SKILL.md
├── pyproject.toml              # 使用 uv 管理的套件與設定檔
└── skills/
    ├── python-development/
    │   └── SKILL.md            # 直接由網路下載的現成官方技能檔
    ├── code-review/
    │   └── SKILL.md            # 直接由網路下載的現成官方技能檔
    └── code-refactoring/
        └── SKILL.md            # 直接由網路下載的現成官方技能檔
```

## 6. 專案建置與執行流程步驟

- **步驟 1：環境準備**
  - 使用 `uv` 初始化專案並建立 Python 3.13 虛擬環境 (`uv init`)。
  - 使用 `uv add` 安裝 `google-adk==1.21.0` 以及其他依賴套件 (`uv add pyyaml python-frontmatter`)。

- **步驟 2：建立目錄並下載真正的開源技能**
  - 建立 `skills/` 與底下三個對應子庫 `python-development`, `code-review`, `code-refactoring`。
  - 直接使用 `curl` 抓取 `Ai-Agent-Skills` 存放庫中現成的 `SKILL.md` 存入到我們的專案中，**不用寫任何程式與設定檔**。

- **步驟 3：實作 `skill_manager.py` (自動加載器)**
  - 撰寫掃描 `skills/` 目錄的邏輯 (`os.walk` 或 `pathlib`)。
  - 透過 `python-frontmatter` 解析 [.md](file:///Users/long0426/Documents/project/AI/openclaw/VISION.md)，將 Metadata 取出建檔。

- **步驟 4：實作按需加載邏輯與 Orchestrator**
  - 簡單的路由邏輯：透過關鍵字或是輕量 LLM 判斷使用者的輸入需要配對到哪個 Metadata 的 Skill。
  - 一旦決定需要的 Skill，動態載入對應的 Markdown 文本與 Python Callable Functions。

- **步驟 5：整合 Google ADK 進行測試 (`main.py`)**
  - 啟動 Router 判斷意圖。
  - 依據意圖向 ADK Agent 注入被選上的 Skill 的 System Prompt 與 Tools。
  - 針對 3 個不同的問題進行提問，於 Terminal 輸出，印出「觸發了哪些 Skill」、「Model 是否成功調用 Tool」並給出最終回答。
