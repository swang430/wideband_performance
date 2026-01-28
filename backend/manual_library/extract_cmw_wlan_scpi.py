import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from pypdf import PdfReader


REMOTE_COMMAND_RE = re.compile(r"remote command", re.IGNORECASE)
SCPI_LINE_RE = re.compile(r"^[A-Za-z]+:", re.IGNORECASE)


def _normalize_line(line: str) -> str:
    line = unescape(line)
    line = re.sub(r"\s+", " ", line).strip()
    if not line:
        return line
    # Remove trailing notes like "(CSP)"
    line = re.sub(r"\s*\([^)]*\)\s*$", "", line).strip()
    # Trim "etc." suffixes
    line = re.sub(r"\s+etc\.?$", "", line, flags=re.IGNORECASE).strip()
    line = re.sub(r"\s*\.\.\.$", "", line).strip()
    line = line.rstrip(",;.")
    return line


def _extract_scpi_commands(pdf_path: Path):
    reader = PdfReader(str(pdf_path))
    commands = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if not text:
            continue
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            if not REMOTE_COMMAND_RE.search(line):
                continue
            for follow in lines[idx + 1: idx + 12]:
                if REMOTE_COMMAND_RE.search(follow):
                    break
                if "WLAN" not in follow.upper():
                    continue
                if ":" not in follow or not SCPI_LINE_RE.match(follow):
                    continue
                if follow.strip().lower().startswith("access:"):
                    continue
                command = _normalize_line(follow)
                if not command or command.endswith(":"):
                    continue
                commands.append(command)

    unique = sorted(set(commands))
    result = []
    for cmd in unique:
        placeholders = sorted({p.strip() for p in re.findall(r"<([^>]+)>", cmd) if p.strip()})
        result.append(
            {
                "index": cmd.lower(),
                "command": cmd,
                "query": "?" in cmd,
                "placeholders": placeholders,
            }
        )
    return result


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_manual = (
        base_dir
        / "manual_library"
        / "integrated_tester"
        / "Rohde_and_Schwarz_CMW"
        / "CMW_WLAN_UserManual_V4-0-20_en_35 (2).pdf"
    )
    default_output = base_dir / "scpi_catalog" / "rohde_schwarz_cmw_wlan.json"

    parser = argparse.ArgumentParser(description="Extract WLAN SCPI commands from CMW WLAN User Manual.")
    parser.add_argument("--manual", type=Path, default=default_manual, help="Path to CMW WLAN manual PDF.")
    parser.add_argument("--output", type=Path, default=default_output, help="Output JSON path.")
    parser.add_argument("--catalog-id", default="rohde_schwarz_cmw_wlan", help="Catalog ID to embed.")
    args = parser.parse_args()

    commands = _extract_scpi_commands(args.manual)
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
    print(f"Extracted {len(commands)} WLAN SCPI commands -> {args.output}")


if __name__ == "__main__":
    main()
