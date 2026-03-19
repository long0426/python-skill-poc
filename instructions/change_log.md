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
