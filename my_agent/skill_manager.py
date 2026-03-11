import os
import frontmatter

class SkillManager:
    """Manages the discovery and reading of skills from the filesystem."""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skills_metadata = {}
        self._scan_skills()

    def _scan_skills(self):
        """Scans the skills directory and loads metadata for each skill."""
        if not os.path.exists(self.skills_dir):
            print(f"[Skill Manager] Directory {self.skills_dir} not found.")
            return

        print(f"[系統啟動] 正在掃描 {self.skills_dir}/ 目錄...")
        count = 0
        for entry in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, entry)
            if os.path.isdir(skill_path):
                md_file = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(md_file):
                    try:
                        with open(md_file, "r", encoding="utf-8") as f:
                            post = frontmatter.load(f)
                            name = post.metadata.get("name", entry)
                            description = post.metadata.get("description", "No description provided.")
                            self.skills_metadata[name] = {
                                "dir": entry,
                                "description": description,
                                "path": md_file
                            }
                            count += 1
                    except Exception as e:
                        print(f"[Skill Manager] Failed to load metadata for {entry}: {e}")
        
        print(f"[Skill Manager] 發現 {count} 個可用技能 (僅讀取 Metadata)：")
        for skill_name in self.skills_metadata.keys():
            print(f"  - {skill_name}")

    def get_available_skills_summary(self) -> str:
        """Returns a formatted string of available skills and their descriptions."""
        if not self.skills_metadata:
            return "No skills available."
        
        summary = "Available Skills (can be loaded via read_skill):\n"
        for name, info in self.skills_metadata.items():
            summary += f"- {name}: {info['description']}\n"
        return summary

    def get_skill_content(self, skill_name: str) -> str:
        """Reads and returns the full content of a SKILL.md file."""
        if skill_name not in self.skills_metadata:
            return f"Error: Skill '{skill_name}' not found."
        
        md_file = self.skills_metadata[skill_name]["path"]
        print(f"[Skill Manager] 動態讀取 => {md_file}")
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading skill file: {e}"
