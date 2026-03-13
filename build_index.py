"""
build_index.py
──────────────
Run this script ONCE to download all formulary PDFs and extract their text.
Output: formulary_index.json  (deploy this alongside app.py)

Usage:
    pip install requests pdfplumber
    python build_index.py

Re-run whenever the CSV is updated or formularies change (typically once a year).
"""

import csv
import json
import re
import io
import time
import requests
import pdfplumber
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

CSV_FILE   = "formulary_links.csv"
INDEX_FILE = "formulary_index.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def is_pdf_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")


def fetch_text(url: str) -> tuple[str, str]:
    """
    Download URL and extract text.
    Returns (text, status) where status is 'ok', 'error', or 'skipped'.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 404:
            return "", "404"
        if resp.status_code != 200:
            return "", f"HTTP {resp.status_code}"

        content_type = resp.headers.get("Content-Type", "").lower()

        if "pdf" in content_type or is_pdf_url(url):
            text = ""
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            return text.strip(), "ok"
        else:
            # Web page — strip HTML tags
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text, "ok"

    except requests.exceptions.Timeout:
        return "", "timeout"
    except Exception as e:
        return "", f"error: {str(e)[:80]}"


def main():
    # ── Load CSV ──────────────────────────────────────────────────────────
    if not Path(CSV_FILE).exists():
        print(f"❌  {CSV_FILE} not found. Place it in the same folder.")
        return

    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[3].startswith("http"):
                rows.append({
                    "plan_group": row[0].strip(),
                    "payer":      row[1].strip(),
                    "plan_name":  row[2].strip(),
                    "url":        row[3].strip(),
                })

    print(f"Found {len(rows)} URLs to index.\n")

    # ── Load existing index so we can skip already-indexed URLs ───────────
    existing = {}
    if Path(INDEX_FILE).exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            data = json.load(f)
            existing = {e["url"]: e for e in data.get("entries", [])}
        print(f"Existing index has {len(existing)} entries — skipping those.\n")

    # ── Fetch & index ─────────────────────────────────────────────────────
    entries = []
    ok_count = error_count = skip_count = 0

    for i, row in enumerate(rows, 1):
        url = row["url"]
        label = row["plan_name"] or row["payer"] or row["plan_group"]

        # Re-use existing entry if URL already indexed
        if url in existing:
            entries.append(existing[url])
            skip_count += 1
            print(f"[{i:>3}/{len(rows)}] ⚡ CACHED  {label}")
            continue

        print(f"[{i:>3}/{len(rows)}] ⏳ Fetching  {label[:55]}")
        text, status = fetch_text(url)

        entry = {
            "plan_group": row["plan_group"],
            "payer":      row["payer"],
            "plan_name":  row["plan_name"],
            "url":        url,
            "text":       text,
            "status":     status,
        }
        entries.append(entry)

        if status == "ok":
            words = len(text.split())
            print(f"          ✅ OK  ({words:,} words extracted)")
            ok_count += 1
        else:
            print(f"          ⚠️  {status}")
            error_count += 1

        time.sleep(0.3)   # be polite to servers

    # ── Write index ───────────────────────────────────────────────────────
    index = {
        "built_at": datetime.utcnow().isoformat() + "Z",
        "total":    len(entries),
        "entries":  entries,
    }
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_mb = Path(INDEX_FILE).stat().st_size / 1_048_576
    print(f"\n{'='*55}")
    print(f"✅  Index written to: {INDEX_FILE}  ({size_mb:.1f} MB)")
    print(f"   OK:      {ok_count}")
    print(f"   Errors:  {error_count}")
    print(f"   Skipped: {skip_count} (already indexed)")
    print(f"\nUpload {INDEX_FILE} to your GitHub repo alongside app.py.")
    print("That's it — no more PDF downloads at runtime.")


if __name__ == "__main__":
    main()
