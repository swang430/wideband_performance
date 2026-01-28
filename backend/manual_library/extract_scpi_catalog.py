import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path


SCPI_ANCHOR_RE = re.compile(
    r'<a[^>]*class="scpi_searchable"[^>]*data-index="([^"]+)"[^>]*>\s*<code>(.*?)</code>',
    re.IGNORECASE | re.DOTALL,
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_scpi_commands(html_text: str):
    items = []
    for data_index, code in SCPI_ANCHOR_RE.findall(html_text):
        index = _normalize_text(unescape(data_index))
        command = _normalize_text(unescape(code))
        if not command:
            continue
        placeholders = sorted({p.strip() for p in re.findall(r"<([^>]+)>", command) if p.strip()})
        items.append(
            {
                "index": index,
                "command": command,
                "query": "?" in command,
                "placeholders": placeholders,
            }
        )

    seen = set()
    unique_items = []
    for item in items:
        key = item["command"]
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)

    unique_items.sort(key=lambda entry: entry["command"])
    return unique_items


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_manual = (
        base_dir
        / "manual_library"
        / "integrated_tester"
        / "Keysight_UXM"
        / "5G_NR_Test_Application_SCPI_Reference.html"
    )
    default_output = base_dir / "scpi_catalog" / "keysight_uxm.json"

    parser = argparse.ArgumentParser(description="Extract SCPI commands from a manual HTML.")
    parser.add_argument("--manual", type=Path, default=default_manual, help="Path to SCPI manual HTML.")
    parser.add_argument("--output", type=Path, default=default_output, help="Output JSON path.")
    parser.add_argument("--catalog-id", default="keysight_uxm", help="Catalog ID to embed in JSON.")
    args = parser.parse_args()

    html_text = args.manual.read_text(encoding="utf-8", errors="ignore")
    commands = extract_scpi_commands(html_text)

    try:
        source_value = str(args.manual.relative_to(base_dir))
    except ValueError:
        source_value = str(args.manual)

    payload = {
        "catalog_id": args.catalog_id,
        "source": source_value,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command_count": len(commands),
        "commands": commands,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    print(f"Extracted {len(commands)} commands -> {args.output}")


if __name__ == "__main__":
    main()
