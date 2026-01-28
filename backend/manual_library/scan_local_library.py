import logging
import os
from typing import Dict, List, Optional, Tuple

import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LibraryScanner")

MANUAL_EXTENSIONS = (".pdf", ".html", ".htm")
META_FILENAMES = ("meta.yaml", "meta.yml", "metadata.yaml", "metadata.yml")


def _list_categories(base_dir: str) -> List[str]:
    categories = []
    for name in os.listdir(base_dir):
        if name.startswith(".") or name == "__pycache__":
            continue
        path = os.path.join(base_dir, name)
        if os.path.isdir(path):
            categories.append(name)
    return categories


def _possible_folder_names(vendor: str, series: str) -> List[str]:
    safe_vendor = vendor.replace(" ", "_").replace("&", "and")
    safe_series = series.replace(" ", "_")
    return [
        f"{safe_vendor}_{safe_series}",
        f"{safe_vendor}_{series}",
        f"{vendor}_{series}".replace(" ", "_"),
    ]


def _parse_vendor_series(folder_name: str) -> Tuple[str, str]:
    if "__" in folder_name:
        vendor_part, series_part = folder_name.split("__", 1)
    else:
        parts = folder_name.split("_")
        if len(parts) == 1:
            vendor_part, series_part = parts[0], "Generic"
        else:
            vendor_part, series_part = "_".join(parts[:-1]), parts[-1]

    vendor = vendor_part.replace("_", " ").strip()
    series = series_part.replace("_", " ").strip()

    vendor = vendor.replace(" and ", " & ")
    series = series.replace(" and ", " & ")

    return vendor, series


def _load_meta(folder_path: str) -> Optional[Dict[str, object]]:
    for filename in META_FILENAMES:
        meta_path = os.path.join(folder_path, filename)
        if os.path.exists(meta_path) and os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load meta file {meta_path}: {e}")
                return None
    return None


def _find_entry_by_folder(entries: List[Dict[str, object]], folder_name: str) -> Optional[Dict[str, object]]:
    for entry in entries:
        vendor = entry.get("vendor", "Unknown")
        series = entry.get("series", "Generic")
        if folder_name in _possible_folder_names(str(vendor), str(series)):
            return entry
    return None


def _find_entry_by_vendor_series(entries: List[Dict[str, object]], vendor: str, series: str) -> Optional[Dict[str, object]]:
    for entry in entries:
        if str(entry.get("vendor", "")).lower() == vendor.lower() and str(entry.get("series", "")).lower() == series.lower():
            return entry
    return None


def _is_manual_file(filename: str) -> bool:
    return filename.lower().endswith(MANUAL_EXTENSIONS)


def _is_registered(entry: Dict[str, object], filename: str) -> bool:
    base_name = os.path.splitext(filename)[0]
    for manual in entry.get("manuals", []):
        m_url = manual.get("url", "")
        if filename in m_url or (m_url and m_url in filename):
            return True
        title = manual.get("title", "")
        if base_name and base_name in str(title):
            return True
    return False


def scan_and_update_catalog(catalog_path="catalog.yaml", library_dir="."):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_catalog_path = os.path.join(base_dir, catalog_path)

    if os.path.exists(full_catalog_path):
        with open(full_catalog_path, "r", encoding="utf-8") as f:
            catalog = yaml.safe_load(f) or {}
    else:
        logger.error(f"Catalog file not found: {full_catalog_path}")
        return

    updated_files = 0
    new_entries = 0
    new_categories = 0

    # 1) 先把文件系统里的类别补进 Catalog
    for category in _list_categories(base_dir):
        if category not in catalog:
            catalog[category] = []
            new_categories += 1

    # 2) 遍历类别目录，自动补齐品牌/系列，并扫描手册文件
    categories_to_scan = [c for c in catalog.keys() if os.path.isdir(os.path.join(base_dir, c))]
    for category in categories_to_scan:
        category_path = os.path.join(base_dir, category)
        series_list = catalog.get(category, [])

        for folder_name in os.listdir(category_path):
            if folder_name.startswith(".") or folder_name == "__pycache__":
                continue
            folder_path = os.path.join(category_path, folder_name)
            if not os.path.isdir(folder_path):
                continue

            entry = _find_entry_by_folder(series_list, folder_name)
            meta = _load_meta(folder_path)

            if not entry:
                vendor, series = _parse_vendor_series(folder_name)
                if meta:
                    vendor = str(meta.get("vendor", vendor))
                    series = str(meta.get("series", series))
                entry = _find_entry_by_vendor_series(series_list, vendor, series)

            if not entry:
                vendor, series = _parse_vendor_series(folder_name)
                if meta:
                    vendor = str(meta.get("vendor", vendor))
                    series = str(meta.get("series", series))
                models = meta.get("models", []) if isinstance(meta, dict) else []
                entry = {
                    "vendor": vendor,
                    "series": series,
                    "models": models if isinstance(models, list) else [],
                    "manuals": []
                }
                series_list.append(entry)
                new_entries += 1

            if meta and isinstance(meta.get("models"), list):
                existing_models = entry.get("models", [])
                if isinstance(existing_models, list):
                    for model in meta["models"]:
                        if model not in existing_models:
                            existing_models.append(model)
                    entry["models"] = existing_models

            for filename in os.listdir(folder_path):
                if filename.startswith(".") or not _is_manual_file(filename):
                    continue
                if _is_registered(entry, filename):
                    continue

                logger.info(f"New manual detected: {filename} for {entry.get('vendor')} {entry.get('series')}")
                new_manual = {
                    "title": os.path.splitext(filename)[0].replace("_", " "),
                    "type": "user_manual_local",
                    "url": filename,
                    "notes": "Automatically detected local file",
                    "is_local": True
                }
                entry.setdefault("manuals", []).append(new_manual)
                updated_files += 1

        catalog[category] = series_list

    if new_categories > 0 or new_entries > 0 or updated_files > 0:
        with open(full_catalog_path, "w", encoding="utf-8") as f:
            yaml.dump(catalog, f, allow_unicode=True, sort_keys=False)
        logger.info(
            "Catalog updated! New categories: %s, new entries: %s, new files: %s",
            new_categories,
            new_entries,
            updated_files
        )
    else:
        logger.info("No new files detected.")


if __name__ == "__main__":
    scan_and_update_catalog()
