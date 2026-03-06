import os
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from .mcp_loader import load_mcp_toolsets

# 計算 mcp_config.json 的絕對路徑（專案根目錄下）
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_config.json")
mcp_toolsets = load_mcp_toolsets(config_path)

root_agent = Agent(
    model=LiteLlm(model='azure/gpt-4o'),
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='''
    你是一位任職於投資銀行的 「美股研究分析助理」。你的職責是作為資深研究員的第二雙眼睛，利用技術工具採集即時數據，並將其轉化為高純度的情報摘要。你必須表現得極其專業、冷靜且嚴謹。
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
    ''',
    tools=mcp_toolsets,
)
