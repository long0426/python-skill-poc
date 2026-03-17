# Change Log

## [2026-03-17]

### factual-synthesis/SKILL.md
- **修改目的**: 根據需求將中文內容翻譯為英文，以支援跨語言使用。
- **修改範圍**: 翻譯了 Description, Critical Rules, Output Sections 以及 Tone 的部分。

## [2026-03-17] (二)
### agent.py
- **修改目的**: 解決財務數據自動進位問題（例如 140.74715 被四捨五入為 140.75）。
- **修改範圍**: 在 `system_prompt` 的 `GOVERNANCE LAYER` 中新增了第 6 條規則 `Data Precision Rule (Critical)`，強制要求保留工具取得的原始小數精度，且優先權高於一般的可讀性要求。
