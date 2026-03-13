from datetime import datetime, timedelta

def get_current_time() -> str:
    """獲取當前的系統時間。
    
    Returns:
        字串格式的當前時間 (ISO 8601)。
    """
    return datetime.now().astimezone().isoformat()

def calculate_past_time(hours_ago: float) -> str:
    """計算過去特定小時數之前的時間。
    
    Args:
        hours_ago: 要計算的過去幾小時 (例如：72 代表 72 小時前)。
        
    Returns:
        字串格式的歷史時間 (ISO 8601)。
    """
    past_time = datetime.now().astimezone() - timedelta(hours=hours_ago)
    return past_time.isoformat()
