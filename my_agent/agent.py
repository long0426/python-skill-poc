import os
import frontmatter
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from .mcp_loader import load_mcp_toolsets

# 計算專案根目錄與設定檔路徑
base_dir = os.path.dirname(os.path.dirname(__file__))
config_path = os.path.join(base_dir, "mcp_config.json")
mcp_toolsets = load_mcp_toolsets(config_path)

# 動態讀取 Skill.md
skill_path = os.path.join(base_dir, "skills", "stock-data-collector", "SKILL.md")
try:
    with open(skill_path, "r", encoding="utf-8") as f:
        skill_data = frontmatter.load(f)
        agent_name = skill_data.metadata.get("name", "stock-data-collector")
        agent_desc = skill_data.metadata.get("description", "Collects data based on skill.")
        agent_inst = skill_data.content
except Exception as e:
    # 預設行為
    agent_name = "root_agent"
    agent_desc = "A helpful assistant for user questions."
    agent_inst = "You are a helpful assistant."

root_agent = Agent(
    model=LiteLlm(model='azure/gpt-4o'),
    name=agent_name,
    description=agent_desc,
    instruction=agent_inst,
    tools=mcp_toolsets,
)
