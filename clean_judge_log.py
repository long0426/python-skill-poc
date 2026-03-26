import os
import re

def clean_judge_logs_recursively():
    # 1. 取得此 Python 執行檔所在的目錄 (絕對路徑鎖定)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 設定進入點：./my_agent/logs
    root_log_dir = os.path.join(base_dir, 'my_agent', 'logs')
    
    # 定義要移除的 Metadata 雜訊
    noise_patterns = [
        "media_resolution=None", "code_execution_result=None",
        "executable_code=None", "file_data=None",
        "function_call=None", "function_response=None",
        "inline_data=None", "thought=None",
        "thought_signature=None", "video_metadata=None"
    ]

    if not os.path.exists(root_log_dir):
        print(f"❌ 找不到根目錄：{root_log_dir}")
        return

    print(f"🔍 開始掃描目錄：{root_log_dir}")

    # 3. 遍歷目錄，尋找以 'judge' 結尾的資料夾
    found_files = 0
    for subdir in os.listdir(root_log_dir):
        subdir_path = os.path.join(root_log_dir, subdir)
        
        # 判斷是否為資料夾且名稱以 judge 結尾
        if os.path.isdir(subdir_path) and subdir.lower().endswith('judge'):
            target_file = os.path.join(subdir_path, 'judge_call_001.txt')
            
            if os.path.exists(target_file):
                print(f"📄 處理中：{target_file}")
                process_file(target_file, subdir_path, noise_patterns)
                found_files += 1

    if found_files == 0:
        print("⚠️ 未找到符合條件的 judge 資料夾或 judge_call_001.txt 檔案。")
    else:
        print(f"✨ 任務完成，共處理 {found_files} 個檔案。")

def process_file(file_path, output_dir, noise_patterns):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 清理內容，保留主體文章
    for pattern in noise_patterns:
        content = content.replace(pattern, "")

    # 移除 text=' 標記與修復轉義字元
    content = re.sub(r"text=['\"]", "", content)
    content = content.replace('\\n', '\n')
    content = content.replace("\\'", "'").replace('\\"', '"')
    content = content.replace('\\', '')

    # 修飾排版
    content = re.sub(r"['\"](?=\n|$)", "", content)
    content = re.sub(r' +', ' ', content)

    # 存檔至同一個子資料夾
    output_path = os.path.join(output_dir, 'cleaned_report.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f"✅ 已輸出至：{output_path}")

if __name__ == "__main__":
    clean_judge_logs_recursively()