"""
agent_utils.py
==============
跨 Agent 共用的工具模組。

包含：
- BoundedSessionStore：有上限的 Session 字典，防止記憶體洩漏
- write_llm_call_log：統一的 LLM 呼叫日誌寫入
- extract_conclusion：彈性擷取報告中的結論段落
"""
from __future__ import annotations

import os
from collections import OrderedDict


# ---------------------------------------------------------------------------
# BoundedSessionStore
# ---------------------------------------------------------------------------

class BoundedSessionStore:
    """有上限的 Session 字典，超過 maxsize 時自動淘汰最舊的項目。

    行為與 dict 相同，額外保證 len(store) <= maxsize。
    使用 OrderedDict 實作 LRU 淘汰策略。
    """

    def __init__(self, maxsize: int = 200) -> None:
        if maxsize < 1:
            raise ValueError("maxsize 必須大於等於 1")
        self._maxsize = maxsize
        self._store: OrderedDict = OrderedDict()

    # --- dict-like 介面 ---

    def __setitem__(self, key: str, value) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)  # 淘汰最舊的項目

    def __getitem__(self, key: str):
        return self._store[key]

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def get(self, key: str, default=None):
        return self._store.get(key, default)

    def keys(self):
        return self._store.keys()

    def __repr__(self) -> str:  # pragma: no cover
        return f"BoundedSessionStore(maxsize={self._maxsize}, len={len(self._store)})"


# ---------------------------------------------------------------------------
# write_llm_call_log
# ---------------------------------------------------------------------------

def write_llm_call_log(
    log_dir: str,
    seq: int,
    inv_id: str,
    sys_str: str,
    context_str: str,
    prefix: str = "call",
) -> str:
    """統一的 LLM 呼叫日誌寫入。

    Args:
        log_dir:      日誌目錄的絕對路徑（需已建立）。
        seq:          本次呼叫序號（從 1 開始）。
        inv_id:       invocation_id。
        sys_str:      System Prompt 字串。
        context_str:  Context（contents）字串。
        prefix:       檔名前綴，預設 "call"（例如 call_001.txt）。

    Returns:
        寫入的檔案路徑。
    """
    log_file = os.path.join(log_dir, f"{prefix}_{seq:03d}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"==== 第 {seq} 次 LLM 呼叫 ====\n")
        f.write(f"invocation_id: {inv_id}\n\n")
        f.write("---- System Prompt ----\n")
        f.write(sys_str)
        f.write("\n\n---- Context (Contents) ----\n")
        f.write(context_str)
        f.write("\n")
    return log_file


# ---------------------------------------------------------------------------
# extract_conclusion
# ---------------------------------------------------------------------------

_DEFAULT_MARKERS = [
    "## Evidence-Based Conclusion",
    "### Evidence-Based Conclusion",
    "# Evidence-Based Conclusion",
]


def extract_conclusion(text: str, markers: list[str] | None = None) -> str:
    """從報告文本中擷取結論段落。

    依序嘗試 markers 清單中的每個標記字串，找到第一個出現的位置後
    回傳其後的所有內容（strip 處理）。若全部找不到，回傳完整原始文本。

    Args:
        text:    要解析的原始文字。
        markers: 要嘗試的標記清單，預設為常見的 Markdown 標題格式。

    Returns:
        擷取到的結論段落，或完整原始文字（fallback）。
    """
    if markers is None:
        markers = _DEFAULT_MARKERS

    best_pos: int | None = None
    best_marker_len: int = 0

    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            if best_pos is None or idx < best_pos:
                best_pos = idx
                best_marker_len = len(marker)

    if best_pos is not None:
        return text[best_pos + best_marker_len:].strip()

    # Fallback：找不到任何標記，回傳完整文本
    return text.strip()
