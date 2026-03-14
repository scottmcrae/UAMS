"""
build_pa_index.py
─────────────────
Downloads all PA criteria PDFs from column F of formulary_links.csv
and extracts their text into pa_index.json.

Usage:
    pip install requests pdfplumber
    python build_pa_index.py

Re-run whenever PA URLs change or new plans are added.
"""

import csv
import json
import io
import re
import time
import requests
import pdfplumber
from pathlib import Path
from datetime import datetime

CSV_FILE   = "formulary_links.csv"
INDEX_FILE = "pa_index.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_pdf_text(url: str) -> tuple[str, str]:
    """Download a PDF and extract its text. Returns (text, status)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 404:
            return "", "404"
        if resp.status_code != 200:
            return "", f"HTTP {resp.status_code}"

        content_type = resp.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            # Try anyway — some servers return wrong content-type
            pass

        text = ""
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip(), "ok"

    except requests.exceptions.Timeout:
        return "", "timeout"
    except Exception as e:
        return "", f"error: {str(e)[:80]}"


def clean_text(text: str) -> str:
    """
    Clean up extracted PDF text for readability:
    - Normalize multiple blank lines to single blank line
    - Strip trailing whitespace from each line
    - Remove page headers/footers (lines that are just numbers or short repeated strings)
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.rstrip()
        # Skip standalone page numbers
        if re.fullmatch(r'\s*\d{1,3}\s*', stripped):
            continue
        cleaned.append(stripped)

    # Collapse 3+ consecutive blank lines into 2
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned))
    return result.strip()


def main():
    if not Path(CSV_FILE).exists():
        print(f"❌  {CSV_FILE} not found.")
        return

    # Load PA URLs from column F (index 5)
    pa_entries = []
    with open(CSV_FILE, newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) >= 6 and row[5].strip().startswith("http"):
                pa_entries.append({
                    "plan_name": row[3].strip(),
                    "pa_url":    row[5].strip(),
                })

    # Deduplicate by URL (multiple plans may share the same PA PDF)
    seen_urls = {}
    deduped = []
    for e in pa_entries:
        if e["pa_url"] not in seen_urls:
            seen_urls[e["pa_url"]] = e["plan_name"]
            deduped.append(e)

    print(f"Found {len(pa_entries)} PA URLs ({len(deduped)} unique PDFs to fetch)\n")

    # Load existing index to skip already-fetched URLs
    existing = {}
    if Path(INDEX_FILE).exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            data = json.load(f)
            existing = {e["pa_url"]: e for e in data.get("entries", [])}
        print(f"Existing index has {len(existing)} entries — skipping those.\n")

    entries = []
    ok_count = error_count = skip_count = 0

    for i, row in enumerate(deduped, 1):
        url   = row["pa_url"]
        label = row["plan_name"]

        if url in existing:
            entries.append(existing[url])
            skip_count += 1
            print(f"[{i:>3}/{len(deduped)}] ⚡ CACHED  {label}")
            continue

        print(f"[{i:>3}/{len(deduped)}] ⏳ Fetching  {label[:55]}")
        text, status = fetch_pdf_text(url)

        if status == "ok":
            text = clean_text(text)
            words = len(text.split())
            print(f"          ✅ OK  ({words:,} words extracted)")
            ok_count += 1
        else:
            print(f"          ⚠️  {status}")
            error_count += 1

        entries.append({
            "plan_name": label,
            "pa_url":    url,
            "text":      text,
            "status":    status,
        })
        time.sleep(0.3)

    # Build a plan_name → entry lookup (all plans, including those sharing a URL)
    # so every plan name maps to its PA text
    url_to_entry = {e["pa_url"]: e for e in entries}
    all_plan_entries = []
    for row in pa_entries:
        base = url_to_entry.get(row["pa_url"], {})
        all_plan_entries.append({
            "plan_name": row["plan_name"],
            "pa_url":    row["pa_url"],
            "text":      base.get("text", ""),
            "status":    base.get("status", "unknown"),
        })

    index = {
        "built_at": datetime.utcnow().isoformat() + "Z",
        "total":    len(all_plan_entries),
        "entries":  all_plan_entries,
    }
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_mb = Path(INDEX_FILE).stat().st_size / 1_048_576
    print(f"\n{'='*55}")
    print(f"✅  Index written to: {INDEX_FILE}  ({size_mb:.1f} MB)")
    print(f"   OK:      {ok_count}")
    print(f"   Errors:  {error_count}")
    print(f"   Skipped: {skip_count} (already indexed)")
    print(f"\nDeploy {INDEX_FILE} alongside app.py.")


if __name__ == "__main__":
    main()
