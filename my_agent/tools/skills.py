import os
import sys

# The current script is in my_agent/tools directory
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 將 my_agent 加入 sys.path 確保能找到同層的 skill_manager.py
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from skill_manager import SkillManager

# Initialize the Skill Manager
skill_manager = SkillManager(os.path.join(CURRENT_DIR, "skills"))

def load_skill_protocol(skill_name: str) -> str:
    """Used to retrieve the full instructional content (SOP) of a specific skill.
    
    Args:
        skill_name: The name of the skill to read (e.g. data-harvesting, factual-synthesis).
    """
    return skill_manager.get_skill_content(skill_name)

def discover_skills() -> str:
    """Used to list and search available operational procedures (SOPs) or skills.
    
    Returns:
        A formatted string describing all available skills and what they do.
    """
    return skill_manager.get_available_skills_summary()
