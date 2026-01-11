import os
import yaml
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LibraryScanner")

def scan_and_update_catalog(catalog_path="catalog.yaml", library_dir="."):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_catalog_path = os.path.join(base_dir, catalog_path)
    
    # 1. 加载现有 Catalog
    if os.path.exists(full_catalog_path):
        with open(full_catalog_path, 'r', encoding='utf-8') as f:
            catalog = yaml.safe_load(f) or {}
    else:
        logger.error(f"Catalog file not found: {full_catalog_path}")
        return

    # 2. 遍历 Catalog (正向匹配)
    updated_count = 0
    
    for category, series_list in catalog.items():
        category_path = os.path.join(base_dir, category)
        if not os.path.exists(category_path):
            continue

        for entry in series_list:
            vendor = entry.get('vendor', 'Unknown')
            series = entry.get('series', 'Generic')
            
            # 构建预期的文件夹名称
            # 规则: 空格 -> 下划线, & -> and
            safe_vendor = vendor.replace(" ", "_").replace("&", "and")
            safe_series = series.replace(" ", "_")
            
            # 尝试几种可能的命名组合，以提高兼容性
            possible_names = [
                f"{safe_vendor}_{safe_series}",
                f"{safe_vendor}_{series}", # Series 可能没转义
                f"{vendor}_{series}".replace(" ", "_") # 最原始拼接
            ]
            
            target_series_path = None
            for name in possible_names:
                path = os.path.join(category_path, name)
                if os.path.exists(path) and os.path.isdir(path):
                    target_series_path = path
                    break
            
            if not target_series_path:
                # logger.debug(f"Folder not found for {vendor} {series}")
                continue

            # 找到了对应的文件夹，开始扫描文件
            existing_urls = [m.get('url', '') for m in entry.get('manuals', [])]
            existing_titles = [m.get('title', '') for m in entry.get('manuals', [])]

            for filename in os.listdir(target_series_path):
                if filename.startswith(".") or not (filename.endswith(".pdf") or filename.endswith(".html") or filename.endswith(".htm")):
                    continue
                
                # 检查是否已注册
                is_registered = False
                for manual in entry.get('manuals', []):
                    # 宽松匹配: 只要 URL 包含文件名，或者文件名包含在 URL 中
                    m_url = manual.get('url', '')
                    if filename in m_url or (m_url and m_url in filename):
                        is_registered = True
                        break
                    
                    # 标题匹配
                    if os.path.splitext(filename)[0] in manual.get('title', ''):
                        is_registered = True
                        break
                
                if not is_registered:
                    logger.info(f"New manual detected: {filename} for {vendor} {series}")
                    new_manual = {
                        'title': os.path.splitext(filename)[0].replace("_", " "),
                        'type': 'user_manual_local',
                        'url': filename, 
                        'notes': 'Automatically detected local file',
                        'is_local': True # 显式标记
                    }
                    entry['manuals'].append(new_manual)
                    updated_count += 1


    # 3. 如果有更新，回写 Catalog
    if updated_count > 0:
        with open(full_catalog_path, 'w', encoding='utf-8') as f:
            yaml.dump(catalog, f, allow_unicode=True, sort_keys=False)
        logger.info(f"Catalog updated! Added {updated_count} new files.")
    else:
        logger.info("No new files detected.")

if __name__ == "__main__":
    scan_and_update_catalog()
