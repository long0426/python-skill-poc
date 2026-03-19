import os
import re
import logging
from datetime import datetime
from google.adk.agents.base_agent import BaseAgent, BaseAgentConfig
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.utils.context_utils import Aclosing
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from .agent import root_agent, _LOGS_DIR, _session_dirs, _session_call_counts
from .judge_agent import judge_agent

logger = logging.getLogger(__name__)

# 全域暫存每個 session 抽出來的 Conclusion
_session_conclusions = {}

class ContinuousPipelineAgentConfig(BaseAgentConfig):
    pass

class ContinuousPipelineAgent(BaseAgent):
    config_type = ContinuousPipelineAgentConfig

    async def _run_async_impl(self, ctx: InvocationContext):
        root = self.sub_agents[0]
        judge = self.sub_agents[1]

        root_text = ""
        # 1. 執行 root_agent，收集輸出的完整內容
        async with Aclosing(root.run_async(ctx)) as agen:
            async for event in agen:
                if event.content and getattr(event.content, "parts", None):
                    for p in event.content.parts:
                        if hasattr(p, "text") and p.text:
                            root_text += p.text
                yield event

        # 2. 擷取 ## Evidence-Based Conclusion 內容
        conclusion = root_text
        match = re.search(r"###?\s*Evidence-Based Conclusion(.*)", root_text, re.IGNORECASE | re.DOTALL)
        if match:
            conclusion = match.group(1).strip()
            
        _session_conclusions[ctx.invocation_id] = conclusion

        # Yield a separator event for the user UI
        yield Event(
            invocation_id=ctx.invocation_id,
            author="System",
            content=types.Content(role="model", parts=[types.Part.from_text(text="\n\n---\n\n**🤖 [System] 第一階段分析完畢，提取結論交由 Judge Agent 進行嚴格檢核...**\n\n")]),
            branch=ctx.branch
        )

        # 3. 連續執行 judge_agent (不會被 SequentialAgent 暫停)
        async with Aclosing(judge.run_async(ctx)) as agen:
            async for event in agen:
                yield event


# 全域暫存每個 session 的 judge 呼叫次數與資料夾
_judge_call_counts = {}
_judge_session_dirs = {}

def judge_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    inv_id = callback_context.invocation_id
    
    if inv_id not in _judge_session_dirs:
        ticker = "judge_unknown"
        if llm_request.contents and getattr(llm_request.contents[0], "parts", None):
            first_part = llm_request.contents[0].parts[0]
            if hasattr(first_part, "text") and first_part.text:
                ticker = str(first_part.text).strip()
                
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_ticker = "".join(c for c in ticker if c.isalnum() or c in ('-', '_'))
        if not safe_ticker: safe_ticker = "judge_unknown"
        
        # 開新的資料夾來存 judge 特有的 logs
        session_dir = os.path.join(_LOGS_DIR, f"{safe_ticker}_{timestamp}_judge")
        os.makedirs(session_dir, exist_ok=True)
        _judge_session_dirs[inv_id] = session_dir
        _judge_call_counts[inv_id] = 0

    _judge_call_counts[inv_id] += 1
    call_seq = _judge_call_counts[inv_id]
    current_log_dir = _judge_session_dirs[inv_id]

    conclusion = _session_conclusions.get(inv_id, "無額外萃取的結論")

    # 判斷是否需要加入觸發 prompt (只有第一次呼叫 judge 時才加入)
    if call_seq == 1 and llm_request.contents and getattr(llm_request.contents[-1], "role", "") != "user":
        llm_request.contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=(
                "以下是原本 agent 的產出結論：\n"
                "------------------\n"
                f"[GENERATED_SUMMARY]:\n{conclusion}\n"
                "------------------\n"
                "請根據上述的結論，自動執行 TASK: THE CLOSED-DOMAIN AUDIT。\n"
                "請自行透過 MCP Tool 與現有 Skills 重新擷取資料作為 [SOURCE_ARTICLES] 的驗證基礎，最後依照你的 OUTPUT POLICY 產出嚴格核對的審查報告。"
            ))])
        )

    # 計算並寫入內容
    context_parts = []
    for part in (llm_request.contents or []):
        for c in getattr(part, "parts", []):
            context_parts.append(str(c))
    context_str = "\n".join(context_parts)
    
    sys_instruction = (
        llm_request.config.system_instruction
        if llm_request.config and llm_request.config.system_instruction else ""
    )
    sys_str = str(sys_instruction)
    
    logger.info(
        f"⚖️ [Judge LLM 請求] 第 {call_seq} 次呼叫 | "
        f"Context 字元數: {len(context_str)} | Sys: {len(sys_str)}"
    )

    log_file = os.path.join(current_log_dir, f"judge_call_{call_seq:03d}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"==== 裁判 AI 第 {call_seq} 次 LLM 呼叫 ====\n")
        f.write(f"invocation_id: {callback_context.invocation_id}\n\n")
        f.write("---- System Prompt ----\n")
        f.write(sys_str)
        f.write("\n\n---- Context (Contents) ----\n")
        f.write(context_str)
        f.write("\n")
        
    return None

judge_agent.before_model_callback = judge_before_model_callback

pipeline_agent = ContinuousPipelineAgent(
    name="pipeline_agent",
    description="自動化執行流程：由 us_stock_research_assistant_agent 分析後，自動觸發 judge_agent 進行嚴格校對。適用於完整的報告與審核作業。",
    sub_agents=[root_agent, judge_agent]
)
