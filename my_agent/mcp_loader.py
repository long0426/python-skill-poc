import json
import os
import logging
from typing import List
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)

def load_mcp_toolsets(config_path: str = "mcp_config.json") -> List[McpToolset]:
    """
    根據給定的 JSON 設定檔載入多個 MCP 伺服器並回傳對應的 McpToolset 列表。
    設計考量解耦與擴充性，後續若有不同通訊協定或更多設定參數也可在此彈性擴充。
    """
    toolsets = []
    if not os.path.exists(config_path):
        logger.warning(f"MCP config file not found: {config_path}")
        return toolsets

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        mcp_servers = config.get("mcpServers", {})
        for name, server_config in mcp_servers.items():
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", None)
            timeout = server_config.get("timeout", 30.0)
            
            if not command:
                logger.warning(f"MCP server '{name}' is missing 'command'. Skipping.")
                continue

            # 將自訂的環境變數與系統環境變數合併，增加彈性
            current_env = None
            if env:
                current_env = os.environ.copy()
                current_env.update(env)
                
            base_params = StdioServerParameters(
                command=command,
                args=args,
                env=current_env
            )
            server_params = StdioConnectionParams(
                server_params=base_params,
                timeout=timeout
            )
            
            # 使用 tool_name_prefix 避免不同 MCP server 中的工具名稱衝突，提高擴充性
            toolsets.append(McpToolset(
                connection_params=server_params,
                tool_name_prefix=f"{name}_"
            ))
            logger.info(f"Loaded MCP server '{name}' with command: {command}")
            
    except Exception as e:
        logger.error(f"Error loading MCP config from {config_path}: {e}")

    return toolsets
