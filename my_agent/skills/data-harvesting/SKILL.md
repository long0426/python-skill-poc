---
name: data-harvesting
description: Collects current and historical stock prices, as well as recent company news, formatting the output into a specific JSON structure.
metadata:
  version: "1.0"
allowed-tools: financial-datasets:*
---

Collect financial data and company news.

Steps:

1 Retrieve current system time using get_current_time tool.
2 Retrieve historical stock prices
3 Retrieve current stock info (including current stock price)
4 Retrieve recent company news
5 Classify news into categories

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
