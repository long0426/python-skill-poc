# Change Log

## [2026-03-17]

### factual-synthesis/SKILL.md
- **修改目的**: 根據需求將中文內容翻譯為英文，以支援跨語言使用。
- **修改範圍**: 翻譯了 Description, Critical Rules, Output Sections 以及 Tone 的部分。

## [2026-03-17] (二)
### agent.py
- **修改目的**: 解決財務數據自動進位問題（例如 140.74715 被四捨五入為 140.75）。
- **修改範圍**: 在 `system_prompt` 的 `GOVERNANCE LAYER` 中新增了第 6 條規則 `Data Precision Rule (Critical)`，強制要求保留工具取得的原始小數精度，且優先權高於一般的可讀性要求。

## [2026-03-18]

### factual-synthesis/SKILL.md
- **修改目的**: 集成 `fetcher-mcp` 工具並大幅提升專案的 GitHub 視覺吸引力。
- **修改範圍**:
    - 集成 `Fetcher MCP`：更新安裝與配置說明。
    - **README 視覺化升級**：
        - 產生並嵌入科技感專案 Logo。
        - 加入 GitHub Badges (Python, ADK, LiteLLM)。
        - 使用 Mermaid 繪製 JIT Skill 加載流程圖。
        - 採用現代化排版與 Emoji。
    - **雙語化 (i18n) 工程**：
        - `README.md` 轉為英文版，作為 GitHub 主頁面。
        - 新增 `README.zh-TW.md` 保留繁體中文內容。
        - 修復圖片絕對路徑問題，統一改為相對路徑 `./logo.png`。
        - 加入中英雙語互通連結。

## [2026-03-19]

### README.md / README.zh-TW.md
- **修改目的**: 更新 Mermaid 工作流圖表，以符合 `agent.py` 中對 `Fetcher MCP` 的強制調用邏輯。
- **修改範圍**:
    - 在 `US Stock Research Assistant` 的 Mermaid 圖表中新增 `Scrape full-text news via Fetcher MCP`（或中文版「透過 Fetcher MCP 抓取新聞內文」）步驟。
    - 確保圖表邏輯與 `agent.py` 的 Step 4 完全同步。

## [2026-03-25]

### my_agent/judge_agent.py
- **修改目的**: 重構 `system_prompt` 以嚴格遵守 Governance → Role → Task → Tool 的四層架構，並合併重複的邏輯以提升清晰度與模型遵循度。
- **修改範圍**:
    - 將 `Output Policy` 移至 Governance，作為頂層要求。
    - 將原本兩個重複的 Role 區塊合併為單一區塊。
    - 將 Governance 中的 `Multi-step Checking Logic` 與 TASK 區塊原有的 4 步驟 Audit 工作流進行合併，統整為 6 步驟。
    - 將 `Tool priority order` 由 Governance 移至 Tool 層級。

## [2026-03-26]

### my_agent/pipeline_agent.py & my_agent/agent.py
- **修改目的**: 解決跨輪查詢的 Context Leakage，同時完美保留包含其他文字的 Context。之前使用 UUID 標記注入的方式，因為 ADK 的 History 原生重建機制，會導致標記被洗掉且造成目錄命名異常（混入 UUID 字串）。
- **修改範圍**:
    - `my_agent/agent.py`: 移除 UUID 注入寫法，新增 `_session_user_prompts` BoundedSessionStore。在第一次遇到新的 User Message 時，將**完全精確的使用者原始輸入內容**記錄下來。
    - `my_agent/pipeline_agent.py`: 將跨輪截斷邏輯，改為透過 `exact_prompt = _session_user_prompts.get(inv_id)` 進行**精確字串比對 (`==`)**，不再使用 substring 或 UUID，確保 100% 精準找到每回合的歷史切割點且不影響原始 Context 內容。
