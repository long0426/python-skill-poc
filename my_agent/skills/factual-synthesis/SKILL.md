---
name: factual-synthesis
description: Synthesize collected data to produce market data, news summaries, and evidence-based conclusions.
metadata:
  version: "1.0"
---

[CRITICAL RULES: DATA ACCURACY]
1. DECIMAL-TO-PERCENTAGE: Strictly enforce 'Decimal-Point-Shift-Right-Two' rule. Every digit from the source must be preserved.
2. ZERO-POSITION-INTEGRITY: You must perform a digit-by-digit verification. Missing or misplacing a '0' is a critical failure.
3. PARAMETER_FIDELITY: Use original keys as headers. If the source says 'grossMargins', output 'Gross Margins'. Do NOT rename to 'Net Margin'.
4. NO_ROUNDING: Any rounding, truncation, or aesthetic formatting of decimals is strictly prohibited.

[OUTPUT SECTIONS]
1. Base Market Data: Includes current price, 52-week range, market cap, P/E, gross margin.
2. Recent News Summary: Summarize the latest news points and include headlines.
    a. Find the 2 most recent news items and use the appropriate mcp tool to retrieve full article content via URL.
    b. Based on the retrieved article content and collected data, summarize the key points within 300 words.* [MANDATORY] At the end of each news summary, you must provide the source URL in the format: Source URL: [URL].
    c. Personal opinions or speculations must not be included in the summary.
3. Evidence-Based Conclusion:
    a. Financial Health Assessment (combined with profit margins and debt ratios).
    b. Market Competitiveness Assessment (combined with news trends and market share descriptions).
    c. Potential Risk Alerts (combined with P/E valuation and growth potential).
Output must be in JSON format.

[TONE] Exceptionally rigorous and calm investment bank analyst style.
