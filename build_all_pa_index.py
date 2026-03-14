"""
build_all_pa_index.py
─────────────────────
Builds a complete pa_index.json from ALL sources:

  1. formulary_links.csv  — PA PDFs for Medicare/Medicaid plans (column F)
  2. info.caremark.com    — BCBS AR commercial plans (Playwright scraper)
  3. uhcprovider.com      — UnitedHealthcare Commercial plans (requests scraper)

Output: pa_index.json  (drop-in replacement, ready for app.py)

Usage:
    pip3 install requests beautifulsoup4 pdfplumber playwright
    playwright install chromium
    python3 build_all_pa_index.py

Re-run whenever PDFs change or new plans are added.
Existing cached entries are skipped automatically.
"""

import csv
import io
import json
import re
import ssl
import string
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import pdfplumber
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ── Config ────────────────────────────────────────────────────────────────────

CSV_FILE   = "formulary_links.csv"
INDEX_FILE          = "pa_index.json"          # CSV source (Medicare/Medicaid plans)
CAREMARK_INDEX_FILE = "pa_caremark_index.json"  # Caremark BCBS AR commercial plans
UHC_INDEX_FILE      = "pa_uhc_index.json"       # UHC Commercial

CAREMARK_URL    = "https://info.caremark.com/dig/cd"
CAREMARK_OUTDIR = Path("caremark_pdfs")

UHC_URL    = "https://www.uhcprovider.com/en/prior-auth-advance-notification/prior-auth-specialty-drugs/prior-auth-pharmacy-medical-necessity.html"
UHC_OUTDIR = Path("uhc_commercial_pdfs")

# Plans that pull from caremark
CAREMARK_PLANS = [
    "Arkansas BlueCross BlueShield - Blue Choice",
    "Arkansas BlueCross BlueShield - Essential Complete",
    "Arkansas BlueCross BlueShield - Metallic",
    "Arkansas BlueCross BlueShield - Standard",
    "Arkansas BlueCross BlueShield - BlueAdvantage",
]

UHC_COMMERCIAL_PLAN = "UnitedHealthcare - Commercial"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# SSL bypass for Mac
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


# ── Shared helpers ─────────────────────────────────────────────────────────────

def extract_pdf_text(path_or_bytes):
    """Extract text from a PDF file path or bytes object."""
    text = ""
    try:
        src = pdfplumber.open(path_or_bytes) if isinstance(path_or_bytes, (str, Path)) else pdfplumber.open(io.BytesIO(path_or_bytes))
        with src as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"    PDF read error: {e}")
    return text.strip()


def clean_text(text):
    """Normalize whitespace and remove standalone page numbers."""
    lines = text.split("\n")
    cleaned = [l.rstrip() for l in lines if not re.fullmatch(r'\s*\d{1,3}\s*', l)]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned)).strip()


def download_file(url, dest_path):
    """Download a file via urllib with SSL bypass. Returns True on success."""
    try:
        req = urllib.request.urlopen(url, context=ssl_ctx)
        with open(dest_path, "wb") as f:
            f.write(req.read())
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def safe_filename(label, max_len=80):
    return re.sub(r'[^\w\-]', '_', label)[:max_len] + ".pdf"


# ── Source 1: formulary_links.csv ─────────────────────────────────────────────

def build_csv_entries(existing_by_url):
    """Fetch PA PDFs from column F of formulary_links.csv."""
    if not Path(CSV_FILE).exists():
        print(f"⚠️  {CSV_FILE} not found — skipping CSV source.\n")
        return []

    pa_rows = []
    with open(CSV_FILE, newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) >= 6 and row[5].strip().startswith("http"):
                pa_rows.append({"plan_name": row[3].strip(), "pa_url": row[5].strip()})

    seen_urls = {}
    deduped = []
    for r in pa_rows:
        if r["pa_url"] not in seen_urls:
            seen_urls[r["pa_url"]] = r["plan_name"]
            deduped.append(r)

    print(f"[CSV] {len(pa_rows)} PA URLs ({len(deduped)} unique PDFs)\n")

    url_to_entry = {}
    ok = errors = skipped = 0

    for i, row in enumerate(deduped, 1):
        url = row["pa_url"]
        label = row["plan_name"]

        if url in existing_by_url:
            cached = dict(existing_by_url[url])
            cached["source"] = "csv"  # ensure source tag survives re-runs
            url_to_entry[url] = cached
            skipped += 1
            print(f"  [{i:>3}/{len(deduped)}] ⚡ cached  {label[:60]}")
            continue

        print(f"  [{i:>3}/{len(deduped)}] ⏳ fetching {label[:55]}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}")
            text = clean_text(extract_pdf_text(resp.content))
            status = "ok"
            print(f"           ✅ {len(text.split()):,} words")
            ok += 1
        except Exception as e:
            text, status = "", f"error: {str(e)[:80]}"
            print(f"           ⚠️  {status}")
            errors += 1

        url_to_entry[url] = {"plan_name": label, "pa_url": url, "text": text, "status": status}
        time.sleep(0.3)

    # Expand back to all plans (multiple plans may share a URL)
    entries = []
    for row in pa_rows:
        base = url_to_entry.get(row["pa_url"], {})
        entries.append({
            "plan_name": row["plan_name"],
            "pa_url":    row["pa_url"],
            "text":      base.get("text", ""),
            "status":    base.get("status", "unknown"),
            "source":    "csv",
        })

    print(f"\n[CSV] Done — {ok} fetched, {errors} errors, {skipped} cached\n")
    return entries


# ── Source 2: Caremark (Playwright) ───────────────────────────────────────────

def build_caremark_entries(existing_by_url):
    """Scrape caremark.com letter-by-letter and download PDFs."""
    CAREMARK_OUTDIR.mkdir(exist_ok=True)
    entries = []
    seen_urls = set(existing_by_url.keys())

    print(f"[Caremark] Opening {CAREMARK_URL} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(CAREMARK_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        for letter in string.ascii_uppercase:
            print(f"  Letter: {letter}")
            try:
                btn = page.locator(f'button[data-id="gloss__desk__{letter}"]')
                if btn.count() == 0:
                    btn = page.locator("button", has_text=re.compile(f"^{letter}$"))
                if btn.count() == 0:
                    continue
                btn.first.click()
                time.sleep(1.5)
            except Exception as e:
                print(f"    Click failed: {e}")
                continue

            links = page.locator('a[href$=".pdf"], a[href*=".pdf"]').all()
            new_links = 0
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    label = link.inner_text().strip()
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    if href.startswith("/"):
                        href = "https://info.caremark.com" + href

                    # Reuse cached entry if URL already indexed
                    if href in existing_by_url:
                        base = existing_by_url[href]
                        for plan in CAREMARK_PLANS:
                            entries.append({**base, "plan_name": plan, "drug_label": label, "source": "caremark"})
                        continue

                    pdf_path = CAREMARK_OUTDIR / safe_filename(label)
                    if not pdf_path.exists():
                        download_file(href, pdf_path)

                    text = clean_text(extract_pdf_text(pdf_path)) if pdf_path.exists() else ""
                    status = "ok" if text else "no_text"

                    for plan in CAREMARK_PLANS:
                        entries.append({
                            "plan_name":  plan,
                            "drug_label": label,
                            "url":        href,
                            "text":       text,
                            "status":     status,
                            "source":     "caremark",
                        })
                    new_links += 1
                except Exception as e:
                    print(f"    Link error: {e}")

            if new_links:
                print(f"    +{new_links} new PDFs")

        browser.close()

    print(f"\n[Caremark] Done — {len(entries)} entries ({len(entries) // len(CAREMARK_PLANS)} unique PDFs × {len(CAREMARK_PLANS)} plans)\n")
    return entries


# ── Source 3: UHC Commercial (requests) ───────────────────────────────────────

def build_uhc_entries(existing_by_url):
    """Scrape UHC provider page and download PDFs."""
    UHC_OUTDIR.mkdir(exist_ok=True)
    entries = []

    print(f"[UHC Commercial] Fetching {UHC_URL} ...")
    resp = requests.get(UHC_URL, verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" not in href.lower():
            continue
        if not href.startswith("http"):
            href = "https://www.uhcprovider.com" + href
        if href in seen:
            continue
        seen.add(href)
        links.append((a.get_text(strip=True), href))

    print(f"  Found {len(links)} PDF links")
    new_count = cached_count = 0

    for label, href in links:
        if href in existing_by_url:
            base = existing_by_url[href]
            entries.append({**base, "plan_name": UHC_COMMERCIAL_PLAN, "drug_label": label, "source": "uhc_commercial"})
            cached_count += 1
            continue

        pdf_path = UHC_OUTDIR / safe_filename(label)
        if not pdf_path.exists():
            download_file(href, pdf_path)

        text = clean_text(extract_pdf_text(pdf_path)) if pdf_path.exists() else ""
        entries.append({
            "plan_name":  UHC_COMMERCIAL_PLAN,
            "drug_label": label,
            "url":        href,
            "text":       text,
            "status":     "ok" if text else "no_text",
            "source":     "uhc_commercial",
        })
        new_count += 1

    print(f"  {new_count} new, {cached_count} cached")
    print(f"\n[UHC Commercial] Done — {len(entries)} entries\n")
    return entries


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    # Load existing entries from all 3 index files for caching
    existing_by_url = {}
    for fname in (INDEX_FILE, CAREMARK_INDEX_FILE, UHC_INDEX_FILE):
        if Path(fname).exists():
            with open(fname, encoding="utf-8") as f:
                old = json.load(f)
                for e in old.get("entries", []):
                    url = e.get("pa_url") or e.get("url", "")
                    if url and e.get("text"):
                        existing_by_url[url] = e
    print(f"Loaded {len(existing_by_url)} cached entries from existing index files\n")

    print("=" * 60)
    print("SOURCE 1: formulary_links.csv  →  pa_index.json")
    print("=" * 60)
    csv_entries = build_csv_entries(existing_by_url)

    print("=" * 60)
    print("SOURCE 2: Caremark  →  pa_caremark_index.json")
    print("=" * 60)
    caremark_entries = build_caremark_entries(existing_by_url)

    print("=" * 60)
    print("SOURCE 3: UHC Commercial  →  pa_uhc_index.json")
    print("=" * 60)
    uhc_entries = build_uhc_entries(existing_by_url)

    def write_index(path, entries):
        # Always deduplicate text by URL — stores text once regardless of how many plans reference it
        texts = {}
        slim_entries = []
        for e in entries:
            url = e.get("url","") or e.get("pa_url","")
            if url and e.get("text") and url not in texts:
                texts[url] = e["text"]
            slim = {k: v for k, v in e.items() if k != "text"}
            slim_entries.append(slim)
        data = {
            "built_at": datetime.utcnow().isoformat() + "Z",
            "total":    len(slim_entries),
            "texts":    texts,        # url -> text lookup (deduped)
            "entries":  slim_entries, # metadata only, no text
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        size_mb = Path(path).stat().st_size / 1_048_576
        print(f"  ✅  {path}  ({size_mb:.1f} MB, {len(slim_entries):,} entries, {len(texts):,} unique texts)")

    print("=" * 60)
    print("Writing index files...")
    write_index(INDEX_FILE,          csv_entries)
    write_index(CAREMARK_INDEX_FILE, caremark_entries)
    write_index(UHC_INDEX_FILE,      uhc_entries)
    print("\nDeploy all 3 files alongside app.py and restart Streamlit.")
    print("=" * 60)


if __name__ == "__main__":
    main()
