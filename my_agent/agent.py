import json
import logging
import os
from datetime import datetime
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
import importlib.util
import inspect
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

logger = logging.getLogger(__name__)

# 紀錄 session 對應的目錄與呼叫次數
_session_dirs = {}
_session_call_counts = {}

# logs 目錄（與 agent.py 同層）
_LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)

# Official ADK before_model_callback to log prompt length
def log_prompt_length(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    inv_id = callback_context.invocation_id
    
    # --- 取消對話歷史記憶 ---
    # 如果最新的請求是來自使用者的文字（非 tool response），我們只保留從該訊息開始的序列
    if llm_request.contents:
        last_user_idx = 0
        for i in range(len(llm_request.contents) - 1, -1, -1):
            content = llm_request.contents[i]
            # 判斷是否為使用者的文字輸入 (非 function_response)
            has_text = any(hasattr(p, "text") and p.text for p in content.parts)
            has_func_resp = any(hasattr(p, "function_response") and p.function_response for p in content.parts)
            
            # 若是使用者單純的文字訊息（我們假設這代表一個新的 Ticker 輸入）
            # 並且不是工具的返回結果
            if getattr(content, "role", "") == "user" and has_text and not has_func_resp:
                last_user_idx = i
                break
        
        # 只保留從最後一個 User 訊息開始的內容，清空先前的歷史
        llm_request.contents = llm_request.contents[last_user_idx:]

    if inv_id not in _session_dirs:
        ticker = "unknown"
        if llm_request.contents and llm_request.contents[0].parts:
            first_part = llm_request.contents[0].parts[0]
            if hasattr(first_part, "text") and first_part.text:
                ticker = str(first_part.text).strip()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_ticker = "".join(c for c in ticker if c.isalnum() or c in ('-', '_'))
        if not safe_ticker:
            safe_ticker = "unknown"
            
        session_dir = os.path.join(_LOGS_DIR, f"{safe_ticker}_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        _session_dirs[inv_id] = session_dir
        _session_call_counts[inv_id] = 0

    _session_call_counts[inv_id] += 1
    call_seq = _session_call_counts[inv_id]
    current_log_dir = _session_dirs[inv_id]

    # --- 計算字元數 ---
    context_parts = []
    for part in (llm_request.contents or []):
        for c in (part.parts or []):
            context_parts.append(str(c))
    context_str = "\n".join(context_parts)
    total_chars = len(context_str)

    sys_instruction = (
        llm_request.config.system_instruction
        if llm_request.config and llm_request.config.system_instruction
        else ""
    )
    sys_str = str(sys_instruction)
    sys_chars = len(sys_str)

    logger.info(
        f"🚀 [LLM 請求] 第 {call_seq} 次呼叫 | "
        f"Context 字元數: {total_chars} | System Prompt 字元數: {sys_chars} | "
        f"合計: {total_chars + sys_chars}"
    )

    # --- 將完整內容寫入子目錄下的 call_{N}.txt ---
    log_file = os.path.join(current_log_dir, f"call_{call_seq:03d}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"==== 第 {call_seq} 次 LLM 呼叫 ====\n")
        f.write(f"invocation_id: {callback_context.invocation_id}\n\n")
        f.write("---- System Prompt ----\n")
        f.write(sys_str)
        f.write("\n\n---- Context (Contents) ----\n")
        f.write(context_str)
        f.write("\n")
    logger.info(f"📝 [LLM 請求] 內容已儲存至 {log_file}")

    return None  # None means: proceed with the actual LLM call

# The current script is in my_agent directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

system_prompt = """
================================================
GOVERNANCE LAYER
================================================

You must follow the strict execution hierarchy:

Governance → Role → Task → Tool

Higher layers constrain lower layers.
Lower layers must never violate higher-layer rules.

Core Governance Rules:

1. Zero Hallucination Rule
Only use information retrieved from tools. If required information is unavailable, explicitly state: "Insufficient data available."

2. Source Attribution
All financial data and news references must clearly cite their source.

3. Neutral Research Standard
Your language must remain objective, analytical, and professional. Avoid emotional or subjective wording.

4. Just-in-Time (JIT) Skill Loading
All operational procedures are stored in Skills. You MUST follow a "Load-then-Execute" cycle for EACH phase of the task. 

• Step 1 — Skill Discovery: Use the appropriate tool to discover available skill summaries.
• Step 2 — Phase-Specific Loading: Based on the task requirements, load EXACTLY ONE corresponding skill immediately before execution. 
• PROHIBITION: Do NOT pre-load skills for future steps. You must complete the current tool execution phase before loading the skill required for the subsequent phase.

Tool priority order:
1. Skill-based tools
2. MCP tools
3. Function calls

5. Output Policy (User-Facing)
Final responses MUST follow these rules:
• Output must be written in Markdown.
• Do NOT output JSON code blocks to the user.
• Maintain readability suitable for professional investment research.
• Cite the source of financial data and news clearly.

Required sections:
### Base Market Data
### Recent News Summary
### Evidence-Based Conclusion


================================================
ROLE
================================================

You are an Equity Research Assistant working at an investment bank. Your responsibility is to act as the second pair of eyes for senior research analysts.

Your duties include:
• Retrieving real-time financial data.
• Collecting recent company-related news.
• Transforming raw information into high-purity intelligence summaries.

Your behavior must always be: professional, calm, analytical, precise, and evidence-based.


================================================
TASK
================================================

Primary Task: US Equity Intelligence Brief

When the user provides a stock ticker symbol (e.g., "AAPL", "NVDA", "TSLA"), execute the following workflow strictly:

Step 1 — Input Recognition
Confirm the input represents a valid stock ticker symbol and identify the target company.

Step 2 — Strategic Discovery
Use the skill discovery tool to identify all available skills. 
Identify which skills are functionally appropriate for:
1. Data collection/retrieval.
2. Data synthesis/analysis.
(Constraint: ONLY identify the skill identifiers. Do NOT read their content at this step.)

Step 3 — Information Acquisition Phase
1. **Load:** Use the reading tool to retrieve the content of the skill identified for "data collection" in Step 2.
2. **Execute:** Follow the SOP within that loaded skill to retrieve all required market data, analyst ratings, and news (last 72 hours).
3. **Verify:** Confirm all necessary data points are present before proceeding.

Step 4 — Analytical Synthesis Phase
1. **Load:** Use the reading tool to retrieve the content of the skill identified for "synthesis/analysis" in Step 2.
2. **Execute:** Perform the analytical procedures defined in this specific skill using ONLY the data collected in Step 3.

Step 5 — Present Intelligence Brief
Deliver the final intelligence report to the user according to the Output Policy defined in the Governance Layer.


================================================
TOOL LAYER
================================================

Tools provide access to external capabilities and operational procedures.

1. Skill Discovery Tool: Used to list and search available operational procedures (SOPs).
2. Skill Reading Tool: Used to retrieve the full instructional content of a specific skill.
3. Data Retrieval Tools: Access to real-time market data and news feeds.
4. Analytical Tools: Any additional tools required for data processing as defined within loaded skills.

All tool executions must be transparently handled but formatted for the user according to the Output Policy.

"""

print(f"[系統啟動] 完成！(目前 System Prompt 字元數: {len(system_prompt)})")


# Construct MCP tools from config mapping
config_path = os.path.join(CURRENT_DIR, "mcp_config.json")
mcp_tools = []
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    for server_name, server_details in config.get("mcpServers", {}).items():
        cmd = server_details.get("command")
        args = server_details.get("args", [])
        if cmd:
            toolset = McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=cmd,
                        args=args
                    ),
                    timeout=120.0
                ),
            )
            mcp_tools.append(toolset)
            print(f"[系統啟動] 掛載 MCP Server: {server_name}")

def load_local_tools() -> list:
    """自動載入 tools 目錄下的所有 function 工具"""
    tools = []
    tools_dir = os.path.join(CURRENT_DIR, "tools")
    if not os.path.exists(tools_dir):
        return tools
        
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            file_path = os.path.join(tools_dir, filename)
            
            try:
                # 從檔案動態載入模組
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 掃描並過濾 function
                    for name, obj in inspect.getmembers(module, inspect.isfunction):
                        # 排除私有函式，並確保是從該檔案載入的
                        if not name.startswith('_') and obj.__module__ == module_name:
                            tools.append(obj)
                            print(f"[系統啟動] 掛載 Local Tool: {name} (from {filename})")
            except Exception as e:
                print(f"[系統啟動] 警告：無法載入 Tool 檔案 {filename} ({e})")
                
    return tools

local_tools = load_local_tools()

root_agent = Agent(
    name="us_stock_research_assistant_agent",
    description="投資銀行「美股研究分析助理」，使用 MCP 取得盤面與新聞去資料，並可以依據按需加載的 SOP 產生純粹的分析報告。",
    model=LiteLlm(model='azure/gpt-4o'),
    instruction=system_prompt,
    tools=local_tools + mcp_tools,
    before_model_callback=log_prompt_length,
)
