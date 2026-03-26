import os
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

from .agent import root_agent, _LOGS_DIR, _session_dirs, _session_call_counts, _session_tickers, _session_user_prompts
from .judge_agent import judge_agent
from .agent_utils import BoundedSessionStore, write_llm_call_log, extract_conclusion

logger = logging.getLogger(__name__)

# 全域暫存每個 session 抽出來的 Conclusion（使用 BoundedSessionStore 防止記憶體洩漏）
_session_conclusions = BoundedSessionStore(maxsize=200)

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

        # 2. 擷取 Evidence-Based Conclusion 內容（使用 extract_conclusion 增加強健性）
        conclusion = extract_conclusion(root_text)
        _session_conclusions[ctx.invocation_id] = conclusion

        # 守衛：確認 root_agent 已完整執行完畢（必須包含 Evidence-Based Conclusion 標記）
        # 若缺少此標記，表示 root_agent 因異常（如 Content Policy Error）提前終止，
        # 此時應停止 pipeline，避免 judge 拿到不完整的結論。
        _CONCLUSION_MARKERS = [
            "## Evidence-Based Conclusion",
            "### Evidence-Based Conclusion",
            "# Evidence-Based Conclusion",
        ]
        root_completed = any(m in root_text for m in _CONCLUSION_MARKERS)
        if not root_completed:
            logger.warning(
                "[Pipeline] root_agent 未產出完整結論，跳過 Judge Agent。"
                f"(root_text 長度: {len(root_text)})"
            )
            yield Event(
                invocation_id=ctx.invocation_id,
                author="System",
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(
                        text=(
                            "\n\n---\n\n"
                            "**[System] 警告：第一階段分析未能完成（可能因 Content Policy 或其他錯誤提前中止），"
                            "Judge Agent 已跳過。請重新輸入 Ticker 再試一次。**\n\n"
                        )
                    )],
                ),
                branch=ctx.branch
            )
            return

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



# 全域暫存每個 session 的 judge 呼叫次數與資料夾（使用 BoundedSessionStore 防止記憶體洩漏）
_judge_call_counts = BoundedSessionStore(maxsize=200)
_judge_session_dirs = BoundedSessionStore(maxsize=200)

def judge_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    inv_id = callback_context.invocation_id

    # --- 截斷跨 ticker 的對話歷史 ---
    # ADK session 的 contents 會跨 invocation 累積所有歷史。
    # --- 截斷跨 ticker 的對話歷史 ---
    # 改用 _session_user_prompts 進行完美的全文字串比對
    # 這樣不會有 substring 誤殺的問題，也不會像 UUID 那樣被 ADK 清除
    exact_prompt = _session_user_prompts.get(inv_id, "")
    if exact_prompt and llm_request.contents:
        cut_idx = 0  # fallback: 不截斷
        for i in range(len(llm_request.contents) - 1, -1, -1):
            content = llm_request.contents[i]
            if getattr(content, "role", "") != "user":
                continue
            match_found = False
            for p in content.parts:
                if hasattr(p, "text") and p.text and str(p.text) == exact_prompt:
                    cut_idx = i
                    match_found = True
                    break
            if match_found:
                break
        if cut_idx > 0:
            llm_request.contents = llm_request.contents[cut_idx:]

    if inv_id not in _judge_session_dirs:
        # 優先從 root_agent 已確認的 ticker 讀取，避免從 contents 猜測造成連續查詢時存錯位置
        safe_ticker = _session_tickers.get(inv_id, "judge_unknown") or "judge_unknown"
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
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
    if call_seq == 1 and llm_request.contents:
        prompt_text = (
            "以下是原本 agent 的產出結論：\n"
            "------------------\n"
            f"[GENERATED_SUMMARY]:\n{conclusion}\n"
            "------------------\n"
            "請根據上述的結論，自動執行 TASK: THE CLOSED-DOMAIN AUDIT。\n"
            "請自行透過 MCP Tool 與現有 Skills 重新擷取資料作為 [SOURCE_ARTICLES] 的驗證基礎，最後依照你的 OUTPUT POLICY 產出嚴格核對的審查報告。"
        )
        last_role = getattr(llm_request.contents[-1], "role", "")
        if last_role != "user":
            # 最後不是 user，正常新增一個 user content
            llm_request.contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])
            )
        else:
            # 最後已是 user（ADK 串接常見情境），直接附加至其 parts 避免連續 user 報錯
            llm_request.contents[-1].parts.append(
                types.Part.from_text(text="\n\n" + prompt_text)
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

    log_file = write_llm_call_log(
        log_dir=current_log_dir,
        seq=call_seq,
        inv_id=callback_context.invocation_id,
        sys_str=sys_str,
        context_str=context_str,
        prefix="judge_call",
    )
    logger.info(f"📝 [Judge LLM 請求] 內容已儲存至 {log_file}")

    return None

judge_agent.before_model_callback = judge_before_model_callback

pipeline_agent = ContinuousPipelineAgent(
    name="pipeline_agent",
    description="自動化執行流程：由 us_stock_research_assistant_agent 分析後，自動觸發 judge_agent 進行嚴格校對。適用於完整的報告與審核作業。",
    sub_agents=[root_agent, judge_agent]
)
