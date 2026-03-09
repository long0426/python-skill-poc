---
name: stock-data-collector
description: Collects current and historical stock prices, as well as recent company news, formatting the output into a specific JSON structure.
metadata:
  version: "1.0"
allowed-tools: yahoo-finance-mcp:*
---

Collect financial data and company news.

Steps:

1 Retrieve historical stock prices from yfinance
2 Retrieve current stock info (including current stock price) from yfinance
3 Retrieve recent company news
4 Classify news into categories

Output Requirement:
You MUST output ONLY valid JSON. Do NOT wrap the JSON in markdown code blocks (e.g., ```json). Do NOT add any conversational text before or after the JSON.

Output Format:
{
"market_data":{
    "current_price": 0.0,
    "historical_prices": []
},
"news":[]
}
