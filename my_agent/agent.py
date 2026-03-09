import logging
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from my_agent.utils import read_data_json

logger = logging.getLogger(__name__)
root_agent = Agent(
    model=LiteLlm(model='azure/gpt-4o'),
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='''
    You are an Equity Research Assistant working in an investment bank.
    Rules:

    1 Use only harvested data
    2 Neutral tone
    3 Provide sources

    Output sections:

    1 Base Market Data
    2 Recent News Summary
    3 Evidence Based Conclusion
    ''',
    tools=[read_data_json],
)
