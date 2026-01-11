import os
import yaml
import urllib.request
import urllib.error
import logging
from urllib.parse import urlparse

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ManualDownloader")

def load_catalog(path="catalog.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, path)
    if not os.path.exists(full_path):
        logger.error(f"Catalog file not found: {full_path}")
        return {}
    with open(full_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def download_file(url, target_dir, filename_prefix=""):
    if not url.startswith("http"):
        logger.warning(f"Skipping non-HTTP URL: {url}")
        return

    try:
        # 从 URL 推断文件名，或者使用默认名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or filename.endswith("/"):
            filename = "manual.html" if "html" in url else "manual.pdf"
        
        # 加上前缀以防重名
        if filename_prefix:
            filename = f"{filename_prefix}_{filename}"

        # 确保文件名安全
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).strip()
        
        save_path = os.path.join(target_dir, filename)
        
        if os.path.exists(save_path):
            logger.info(f"File already exists: {save_path}")
            return

        logger.info(f"Downloading {url}...")
        
        # 模拟浏览器 User-Agent，防止某些网站拒绝
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response, open(save_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
            logger.info(f"Saved to: {save_path}")

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} for {url}: {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URL Error for {url}: {e.reason}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    catalog = load_catalog()

    if not catalog:
        return

    for category, items in catalog.items():
        logger.info(f"Processing category: {category}")
        for item in items:
            vendor = item.get('vendor', 'Unknown')
            series = item.get('series', 'Generic')
            
            # 创建存放目录: manual_library/<category>/<Vendor>_<Series>
            folder_name = f"{vendor}_{series}".replace(" ", "_").replace("&", "and")
            target_dir = os.path.join(base_dir, category, folder_name)
            
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir)
                except OSError as e:
                    logger.error(f"Failed to create directory {target_dir}: {e}")
                    continue
            
            for manual in item.get('manuals', []):
                url = manual.get('url')
                title = manual.get('title', 'manual')
                if url and "unavailable" not in url:
                    download_file(url, target_dir, filename_prefix=title)
                else:
                    logger.warning(f"Skipping unavailable manual: {title}")

if __name__ == "__main__":
    main()
