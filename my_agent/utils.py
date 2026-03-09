import json
import logging
from typing import Any, Dict, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class DataLoader:
    """
    資料載入的基礎類別，保持解耦與未來擴充其他格式的彈性。
    """
    
    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        讀取 JSON 檔案內容並回傳字典格式。
        
        Args:
            file_path: JSON 檔案的路徑 (字串或 Path 物件)
            
        Returns:
            Dict[str, Any]: 解析後的 JSON 資料
            
        Raises:
            FileNotFoundError: 如果檔案不存在
            json.JSONDecodeError: 如果檔案內容不是有效的 JSON 格式
        """
        path = Path(file_path)
        if not path.exists():
            error_msg = f"檔案不存在: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"成功讀取 JSON 檔案: {path}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析錯誤 ({path}): {e}")
            raise

def read_data_json(file_path: Union[str, Path, None] = "data.json") -> Dict[str, Any]:
    """
    專門用來讀取特定 JSON 檔案內容的輔助函數。
    預設會讀取工作目錄下的 data.json
    
    Args:
        file_path: JSON 檔案路徑，如果不提供則預設讀取 "data.json"
        
    Returns:
        JSON 解析後的字典資料
    """
    if file_path is None:
        file_path = "data.json"
    return DataLoader.read_json(file_path)
