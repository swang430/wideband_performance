import yaml
import os
import argparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualLibrary:
    def __init__(self, catalog_path="catalog.yaml"):
        self.catalog_path = os.path.join(os.path.dirname(__file__), catalog_path)
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        if not os.path.exists(self.catalog_path):
            logger.error(f"Catalog file not found: {self.catalog_path}")
            return {}
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def list_manuals(self, instrument_type=None):
        """列出所有或特定类型仪表的可用手册"""
        for cat_type, entries in self.catalog.items():
            if instrument_type and cat_type != instrument_type:
                continue
            print(f"--- {cat_type.upper().replace('_', ' ')} ---")
            for entry in entries:
                print(f"  Vendor: {entry['vendor']} ({entry['series']})")
                print(f"  Models: {', '.join(entry['models'])}")
                for manual in entry['manuals']:
                    print(f"    - [{manual['type']}] {manual['title']}")
                    print(f"      URL: {manual['url']}")
                print("")

    def find_manual(self, model_name):
        """查找特定型号的手册"""
        found = False
        print(f"Searching manuals for model: {model_name}...")
        for cat_type, entries in self.catalog.items():
            for entry in entries:
                if any(model_name in m for m in entry['models']):
                    print(f"Found in {cat_type} ({entry['vendor']} {entry['series']}):")
                    for manual in entry['manuals']:
                        print(f"  - {manual['title']} ({manual['url']})")
                    found = True
        if not found:
            print("No manuals found for this model.")

    def download_manual(self, manual_title):
        """模拟下载手册"""
        logger.info(f"Simulating download for: {manual_title}")
        # 在实际实现中，这里会使用 requests.get(url)
        logger.info("Download complete (simulated).")

def main():
    parser = argparse.ArgumentParser(description="Manual Library Manager")
    parser.add_argument("--list", action="store_true", help="List all manuals")
    parser.add_argument("--find", type=str, help="Find manuals by model name")
    parser.add_argument("--type", type=str, help="Filter list by instrument type")
    
    args = parser.parse_args()
    
    lib = ManualLibrary()
    
    if args.find:
        lib.find_manual(args.find)
    elif args.list:
        lib.list_manuals(args.type)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
