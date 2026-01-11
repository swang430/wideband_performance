import sys
import os
from pypdf import PdfReader

def extract_manual_info(pdf_path, keywords):
    """
    从 PDF 中提取包含特定关键词的页面文本。
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return

    print(f"--- 正在分析手册: {os.path.basename(pdf_path)} ---")
    print(f"--- 搜索关键词: {', '.join(keywords)} ---")
    
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        print(f"总页数: {total_pages}")

        found_sections = 0
        
        # 遍历每一页
        for i in range(total_pages):
            page = reader.pages[i]
            text = page.extract_text()
            
            if not text:
                continue
                
            # 检查是否有关键词
            matches = [k for k in keywords if k.lower() in text.lower()]
            
            if matches:
                found_sections += 1
                print(f"\n[第 {i+1} 页] (匹配到: {', '.join(matches)})\n")
                print("-" * 40)
                # 打印出文本（截断以防过长，但保留关键行）
                for line in text.split('\n'):
                    if any(k.lower() in line.lower() for k in keywords):
                        print(f" > {line.strip()}")
                print("-" * 40)
                
            # 为了防止输出过大，如果匹配到太多页，就停止
            if found_sections > 15:
                print("\n... 匹配内容较多，已停止。请查阅上述结果。")
                break
                
    except Exception as e:
        print(f"读取 PDF 出错: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_pdf_info.py <pdf_path> [keyword1] [keyword2]...")
        sys.exit(1)
        
    path = sys.argv[1]
    # 预设默认关键词
    default_keywords = ["SCPI", "Remote", "LOAD", "COMMAND", "SIM", "SCENARIO"]
    
    if len(sys.argv) > 2:
        target_keywords = sys.argv[2:]
    else:
        target_keywords = default_keywords
        
    extract_manual_info(path, target_keywords)
