import streamlit as st
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arkansas Formulary Search",
    page_icon="💊",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

    :root {
        --ink:       #1a2633;
        --slate:     #416CA6;
        --teal:      #416CA6;
        --teal-mid:  #548DBF;
        --teal-lt:   #ddeaf5;
        --amber:     #F29B30;
        --amber-lt:  #fef3e2;
        --rose:      #BF6D65;
        --rose-lt:   #f9eaea;
        --surface:   #ffffff;
        --bg:        #ACBFD6;
        --border:    #dde4eb;

    /* ── Search input border ── */
    [data-testid="stTextInput"] input {
        border: 1.5px solid #9aafc4 !important;
        border-radius: 8px !important;
        background: white !important;
        color: #132F40 !important;
        -webkit-text-fill-color: #132F40 !important;
        caret-color: #132F40 !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #132F40 !important;
        -webkit-text-fill-color: #132F40 !important;
        opacity: 0.6 !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #416CA6 !important;
        box-shadow: 0 0 0 2px rgba(65,108,166,0.15) !important;
        background: white !important;
        color: #132F40 !important;
        -webkit-text-fill-color: #132F40 !important;
    }
    [data-testid="stTextInput"] input:-webkit-autofill,
    [data-testid="stTextInput"] input:-webkit-autofill:focus {
        -webkit-box-shadow: 0 0 0 1000px white inset !important;
        -webkit-text-fill-color: #132F40 !important;
    }
        --muted:     #6b7e8f;
    }

    /* ── Hide Streamlit top bar ── */
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    #MainMenu { display: none !important; }
    header { display: none !important; }

    * { font-family: 'DM Sans', sans-serif; }

    [data-testid="stAppViewContainer"] {
        background: var(--bg);
        background-image: radial-gradient(circle at 80% 10%, rgba(13,122,110,0.06) 0%, transparent 55%),
                          radial-gradient(circle at 10% 90%, rgba(30,52,72,0.05) 0%, transparent 50%);
    }

    /* ── Header ── */
    .header-bar {
        background: #0E2233;
        background-image: linear-gradient(135deg, #091620 0%, #0E2233 50%, #162e44 100%);
        color: white;
        padding: 28px 32px;
        border-radius: 14px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .header-bar::before {
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(13,168,152,0.25) 0%, transparent 70%);
        pointer-events: none;
    }
    .header-bar::after {
        content: '';
        position: absolute;
        bottom: -20px; left: 30%;
        width: 120px; height: 120px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(232,145,58,0.15) 0%, transparent 70%);
        pointer-events: none;
    }
    .header-bar h1 {
        margin: 0;
        font-family: 'DM Serif Display', serif;
        font-size: 2rem;
        color: white;
        letter-spacing: -0.02em;
    }
    .header-bar p {
        margin: 6px 0 0;
        opacity: 0.72;
        font-size: 0.92rem;
        font-weight: 300;
        letter-spacing: 0.01em;
    }

    /* ── Results container ── */
    .results-container {
        background: white;
        border-radius: 10px;
        padding: 4px 16px;
        margin-top: 8px;
        box-shadow: 0 1px 4px rgba(15,25,35,0.08);
    }

    /* ── Result cards ── */
    .result-card {
        background: transparent;
        border-left: none;
        border-bottom: 1px solid var(--border);
        padding: 6px 4px;
        margin: 0;
        border-radius: 0;
        box-shadow: none;
        transition: none;
    }
    .result-card:hover { box-shadow: none; }
    .result-card.found { border-left: none; }
    .result-card.error { border-left: none; }

    .plan-label  { font-size: 0.88rem; font-weight: 600; color: var(--ink); letter-spacing: -0.01em; }
    .payer-label { font-size: 0.83rem; color: var(--muted); margin-bottom: 5px; }

    /* ── Tags ── */
    .tag-found {
        background: var(--teal-lt); color: var(--teal);
        padding: 2px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.02em;
    }
    .tag-not {
        background: var(--rose-lt); color: var(--rose);
        padding: 2px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 700;
    }
    .tag-error {
        background: var(--amber-lt); color: var(--amber);
        padding: 2px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }

    .url-link { font-size: 0.77rem; color: var(--teal-mid); word-break: break-all; }

    /* ── Summary box ── */
    .summary-box {
        display: flex;
        gap: 0;
        background: var(--surface);
        border-radius: 12px;
        padding: 0;
        margin-bottom: 22px;
        box-shadow: 0 1px 3px rgba(15,25,35,0.06), 0 4px 12px rgba(15,25,35,0.04);
        overflow: hidden;
        border: 1px solid var(--border);
    }
    .stat {
        text-align: center;
        flex: 1;
        padding: 20px 16px;
        border-right: 1px solid var(--border);
    }
    .stat:last-child { border-right: none; }
    .stat-num { font-size: 2.1rem; font-weight: 800; color: var(--slate); line-height: 1; }
    .stat-num.green { color: var(--teal); }
    .stat-label { font-size: 0.72rem; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; }

    .index-info { font-size: 0.73rem; color: #b0bcc8; margin-top: 6px; }

    /* ── Expander ── */
    [data-testid="stExpander"] summary p { color: var(--slate) !important; font-weight: 600; }
    [data-testid="stExpander"] summary:hover { background-color: transparent !important; }
    [data-testid="stExpander"] summary { list-style: none; }

    /* ── Streamlit button overrides ── */
    [data-testid="stFormSubmitButton"] button {
        background: #023E73 !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        transition: background 0.2s ease !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background: #0a5299 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h1>Arkansas Formulary Drug Search</h1>
  <p>Search across insurance formularies instantly — results are clickable links to source documents.</p>
</div>
""", unsafe_allow_html=True)

# ── Load index ────────────────────────────────────────────────────────────────
INDEX_FILE = "formulary_index.json"

@st.cache_data(ttl=0)
def load_index(path, _mtime):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

if not Path(INDEX_FILE).exists():
    st.error("⚠️ **formulary_index.json not found.**")
    st.markdown("""
    Build the index first by running on your computer:
    ```bash
    pip install requests pdfplumber
    python build_index.py
    ```
    Then upload `formulary_index.json` to your GitHub repo alongside `app.py`.
    """)
    st.stop()

index     = load_index(INDEX_FILE, Path(INDEX_FILE).stat().st_mtime)
entries   = index["entries"]
built_at  = index.get("built_at", "unknown")

try:
    built_nice = datetime.fromisoformat(built_at.replace("Z","")).strftime("%B %d, %Y")
except Exception:
    built_nice = built_at

# ── Search function ───────────────────────────────────────────────────────────
def search_entries(entries, keyword, group_filter, payer_filter):
    pattern = re.compile(re.escape(keyword.strip().lower()))
    results = []
    for e in entries:
        if group_filter != "All Plan Groups" and e.get("plan_group","") != group_filter:
            continue
        if payer_filter != "All Payers" and e.get("payer","") != payer_filter:
            continue
        status = e.get("status","ok")
        text   = e.get("text","")
        if status != "ok" or not text:
            results.append({**e, "found": False, "search_error": status or "no text"})
        else:
            results.append({**e, "found": bool(pattern.search(text.lower())), "search_error": None})
    return results


# ── Tier extractor ───────────────────────────────────────────────────────────
def extract_tier(text, keyword):
    """
    Extract tier from formulary text near the keyword.
    Handles multiple real-world formats:
      - "Tier 2", "tier: 3", "TIER 4"
      - Standalone digit on same line: "metformin ... 1"
      - Column-style: digit within ~200 chars after drug name
      - "Preferred / Non-Preferred / Specialty" labels
    """
    kw = keyword.strip()
    pattern = re.compile(re.escape(kw), re.IGNORECASE)

    for m in pattern.finditer(text):
        # Wide window: 60 chars before, 300 chars after
        before  = text[max(0, m.start() - 60) : m.start()]
        after   = text[m.end() : m.end() + 300]
        snippet = before + after

        # 1. Explicit "Tier N" in after only (not before, to avoid picking up tier from preceding drug)
        t = re.search(r'\btier\s*[:\-]?\s*([1-9])\b', after, re.IGNORECASE)
        if t:
            return f"Tier {t.group(1)}"

        # Search first 4 lines to handle multi-line drug names
        # (e.g. Ozempic description wraps 3 lines before the tier digit appears)
        first_lines = '\n'.join(after.split('\n')[:4])

        # 2. AR Benefits pattern: "DRUG ... - 2 DRUGCLASS" (digit after dash before ALL CAPS class)
        ar_match = re.search(r'\s-\s([1-6])\s+[A-Z]{3}', after.split('\n')[0])
        if ar_match:
            return f"Tier {ar_match.group(1)}"

        # 2c. AR Benefits QL-RDX pattern: "OZEMPIC INJ (...) QL-RDX 2 ANTIDIABETICS"
        ql_rdx = re.search(r'QL-RDX\s+([1-6])\b', first_lines, re.IGNORECASE)
        if ql_rdx:
            return f"Tier {ql_rdx.group(1)}"

        # 2b. Dollar-amount tier format: "$0 (1)" or "$10 (2)" — WellCare Dual plans
        dollar_tier = re.search(r'\$\d+\s*\(([1-6])\)', first_lines)
        if dollar_tier:
            return f"Tier {dollar_tier.group(1)}"

        # 3. Digit before PA/QL/ST/MO flags across first 4 lines: "OZEMPIC 3 QL PA MO"
        flag_match = re.search(r'\b([1-6])\s+(?:PA|QL|ST|MO)\b', first_lines, re.IGNORECASE)
        if flag_match:
            return f"Tier {flag_match.group(1)}"

        # 3. Standalone digit (1-6) within first 4 lines after the drug name
        #    e.g. "metformin tabs 500mg   1   PA QL"
        same_line = re.search(r'[^\S\n]{2,}([1-6])\b', first_lines)
        if same_line:
            return f"Tier {same_line.group(1)}"

        # 3. Digit on the very next non-blank line (column-layout PDFs)
        lines = [l.strip() for l in after.split('\n') if l.strip()]
        if lines and re.fullmatch(r'[1-6]', lines[0]):
            return f"Tier {lines[0]}"

        # 4. Named tier labels — same line after keyword only (avoids multi-column bleed)
        same_line_text = after.split('\n')[0]
        label = re.search(
            r'\b(preferred specialty|non.preferred specialty|specialty|'
            r'preferred brand|non.preferred brand|preferred|non.preferred|generic)\b',
            same_line_text, re.IGNORECASE
        )
        if label:
            mapping = {
                'generic': 'Generic (Tier 1)',
                'preferred brand': 'Preferred Brand',
                'non-preferred brand': 'Non-Preferred Brand',
                'non preferred brand': 'Non-Preferred Brand',
                'preferred specialty': 'Preferred Specialty',
                'non-preferred specialty': 'Non-Preferred Specialty',
                'non preferred specialty': 'Non-Preferred Specialty',
                'specialty': 'Specialty',
                'preferred': 'Preferred',
                'non-preferred': 'Non-Preferred',
                'non preferred': 'Non-Preferred',
            }
            key = label.group(1).lower().replace('\u2011', '-')
            return mapping.get(key, label.group(1).title())

        # No tier found in this match — try the next occurrence
        continue

    return None

# ── Tricare status extractor ──────────────────────────────────────────────────
TRICARE_URL_STATUS = {
    "non-formulary": "Non-Formulary",
    "tier4":         "Not Covered",
}

def extract_pa(text, keyword):
    """Return True if PA (Prior Authorization) is required near the keyword match."""
    pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
    for m in pattern.finditer(text):
        after = text[m.end() : m.end() + 300]
        first_lines = '\n'.join(after.split('\n')[:4])
        if re.search(r'\bPA\b', first_lines):
            return True
    return False


def tricare_status_from_url(url):
    """Derive Tricare coverage status from which list the URL points to."""
    url_lower = url.lower()
    for fragment, label in TRICARE_URL_STATUS.items():
        if fragment in url_lower:
            return label
    return "Covered"

# ── Aetna code extractor ─────────────────────────────────────────────────────
AETNA_CODE_LEGEND = {
    "G":    "Tier 1",
    "NF":   "Tier 3",
    "NPB":  "Non-Preferred Brand",
    "CE":   "Copay Exception",
    "PB":   "Tier 2",
    "PBSP": "Preferred Brand Specialty",
    "PG":   "Preferred Generic",
    "N8":   "Drug Specific Coverage",
    "SPC":  "Select Plan Coverage",
}

def extract_aetna_code(text, keyword):
    """Find Aetna coverage code on the same line or immediately after the keyword match."""
    pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
    for m in pattern.finditer(text):
        after = text[m.end():m.end()+200]
        all_lines = after.split('\n')
        # Check same line first, then next 3 lines
        for line in all_lines[0:4]:
            # Look for a standalone code at end of line or on its own
            stripped = line.strip()
            # Code at end of same line: "metformin hcl oral tablet 1000 mg G"
            end_code = re.search(r'\b(' + '|'.join(AETNA_CODE_LEGEND.keys()) + r')\s*$', stripped)
            if end_code:
                return AETNA_CODE_LEGEND[end_code.group(1)]
            # Code alone on a line
            if stripped in AETNA_CODE_LEGEND:
                return AETNA_CODE_LEGEND[stripped]
    return None

with st.form("search_form"):
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        keyword = st.text_input("Drug / keyword", placeholder="e.g. Wegovy - (tier results unreliable with generics)", label_visibility="collapsed")
    with col_btn:
        go = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

_kw = keyword.strip() if keyword.strip() else ""
st.markdown(f"""
<div style="display:flex;gap:10px;margin-top:8px;">
  <a href="https://www.goodrx.com/" target="_blank" style="background:#C89647;color:white;padding:7px 16px;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">💊 GoodRx</a>
  <a href="https://www.openevidence.com" target="_blank" style="background:#734702;color:white;padding:7px 16px;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">🔬 OpenEvidence</a>
</div>
""", unsafe_allow_html=True)

if go and keyword.strip():
    # ── Run search ────────────────────────────────────────────────────────────
    results       = search_entries(entries, keyword, "All Plan Groups", "All Payers")
    found_results = sorted([r for r in results if r["found"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
    missed        = sorted([r for r in results if not r["found"] and not r["search_error"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
    errors        = [r for r in results if r["search_error"]]

    if found_results:
        st.markdown(f'<div style="background:#eaf2d7;border:1px solid #478000;border-radius:6px;padding:10px 16px;color:#478000;font-weight:600;margin-top:20px;">"{keyword.strip()}" found in <strong>{len(found_results)}</strong> formulary/formularies.</div>', unsafe_allow_html=True)
    else:
        st.error(f'❌ **"{keyword.strip()}"** was not found in any formulary.')

    st.divider()
    st.markdown('<p style="color:#416CA6;font-weight:600;">After selecting a PDF, hit Ctrl+F</p>', unsafe_allow_html=True)

    cards_html = ""
    for r in (found_results + [] + []):
        plan_label = r.get("plan_name") or r.get("payer") or r.get("plan_group","")
        is_tricare = "tricare" in plan_label.lower()

        # Tricare: only show Covered results, skip all others
        if is_tricare:
            if not r.get("found"):
                continue
            status_label = tricare_status_from_url(r.get("url",""))
            if status_label != "Covered":
                continue
            tier_html = '<span style="font-size:0.75rem;background:#e8eaed;color:#444;padding:2px 8px;border-radius:20px;margin-left:8px;font-weight:500;">Covered</span>'
            pa_html = ""
            is_aetna = "aetna" in plan_label.lower()
            if is_aetna and r.get("found") and r.get("text"):
                code = extract_aetna_code(r.get("text",""), keyword)
                if not code:
                    code = extract_tier(r.get("text",""), keyword)
                tier_html = f'<span style="font-size:0.75rem;background:#e8eaed;color:#444;padding:2px 8px;border-radius:20px;margin-left:8px;font-weight:500;">{code}</span>' if code else ""
            else:
                tier = extract_tier(r.get("text") or "", keyword) if r.get("found") and r.get("text") else None
                tier_html = f'<span style="font-size:0.75rem;background:#e8eaed;color:#444;padding:2px 8px;border-radius:20px;margin-left:8px;font-weight:500;">{tier}</span>' if tier else ""
            # PA badge
            has_pa = extract_pa(r.get("text") or "", keyword) if r.get("found") and r.get("text") else False
            pa_html = '<span style="font-size:0.75rem;background:#FFF3CD;color:#856404;padding:2px 8px;border-radius:20px;margin-left:6px;font-weight:500;">PA</span>' if has_pa else ""

        # URL: Tricare uses per-entry URL (each list has its own), others use overrides
        if is_tricare:
            url = r.get("url","")
        else:
            URL_OVERRIDES = {
                "GOV - BCBS Federal Employee Program (FEP) - Blue Basic": "https://www.caremark.com/portal/asset/z6500_drug_list807.pdf",
            }
            url = next((v for k, v in URL_OVERRIDES.items() if k.lower() in plan_label.lower()), r.get("url",""))

        if r["found"]:
            card_class, tag = "result-card found", ''
        elif r.get("search_error"):
            card_class, tag = "result-card error", f'<span class="tag-error">⚠️ {r["search_error"]}</span>'
        else:
            card_class, tag = "result-card", '<span class="tag-not">❌ Not found</span>'
        plan_link = f'<a href="{url}" target="_blank" style="color:var(--ink);text-decoration:none;border-bottom:1.5px solid var(--teal);padding-bottom:1px;">{plan_label}</a>' if url else plan_label
        cards_html += f"""
    <div class="{card_class}">
      <div class="plan-label">{plan_link} &nbsp; {tag}{tier_html}{pa_html}</div>
    </div>"""

    st.markdown(f'<div class="results-container">{cards_html}</div>', unsafe_allow_html=True)

# ── View all formularies ──────────────────────────────────────────────────────
if not (go and keyword.strip()):
    st.markdown("<div style='height:40vh'></div>", unsafe_allow_html=True)
with st.expander("Drug Tiers Explained"):
    st.components.v1.html("""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"><style>*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}body{background:transparent;font-family:'DM Sans',sans-serif;padding:8px 0;}.card{width:100%;background:#ffffff;border:1px solid #e4dfd8;border-radius:24px;overflow:hidden;box-shadow:0 4px 32px rgba(0,0,0,0.08);position:relative;}.tiers{padding:16px 28px 24px;display:flex;flex-direction:column;gap:10px;}.tier{display:grid;grid-template-columns:64px 1fr auto;align-items:start;border-radius:12px;overflow:hidden;border:1px solid transparent;}.tier-num{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px 0;font-family:'DM Serif Display',serif;font-size:26px;line-height:1;gap:3px;}.tier-word{font-family:'DM Sans',sans-serif;font-size:8px;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;opacity:0.6;}.tier-body{padding:10px 16px;border-left:1px solid rgba(0,0,0,0.06);}.tier-label{font-size:13px;font-weight:500;margin-bottom:3px;letter-spacing:0.01em;}.tier-desc{font-size:12px;font-weight:300;line-height:1.55;margin-bottom:5px;}.tier-example{font-size:10.5px;font-style:italic;opacity:0.5;}.tier-cost{padding:10px 14px 10px 0;display:flex;align-items:flex-start;justify-content:flex-end;}.cost-pill{font-size:11px;font-weight:500;padding:4px 10px;border-radius:20px;white-space:nowrap;letter-spacing:0.02em;}.t1{background:#f0f7e8;border-color:#d4eab8;}.t1 .tier-num{background:#e4f2d0;color:#3B6D11;}.t1 .tier-label{color:#27500A;}.t1 .tier-desc{color:#557a30;}.t1 .cost-pill{background:#d4eab8;color:#3B6D11;}.t2{background:#edf4fc;border-color:#c5ddf5;}.t2 .tier-num{background:#daeaf8;color:#185FA5;}.t2 .tier-label{color:#0c447c;}.t2 .tier-desc{color:#3a6e9e;}.t2 .cost-pill{background:#c5ddf5;color:#185FA5;}.t3{background:#fdf6e8;border-color:#f5e0a8;}.t3 .tier-num{background:#faefd0;color:#854F0B;}.t3 .tier-label{color:#633806;}.t3 .tier-desc{color:#9a6820;}.t3 .cost-pill{background:#f5e0a8;color:#854F0B;}.t4{background:#fdf0eb;border-color:#f5cebb;}.t4 .tier-num{background:#fae2d5;color:#993C1D;}.t4 .tier-label{color:#712B13;}.t4 .tier-desc{color:#a35030;}.t4 .cost-pill{background:#f5cebb;color:#993C1D;}.t5{background:#fdf0f0;border-color:#f5c0c0;}.t5 .tier-num{background:#fad8d8;color:#A32D2D;}.t5 .tier-label{color:#791F1F;}.t5 .tier-desc{color:#a84040;}.t5 .cost-pill{background:#f5c0c0;color:#A32D2D;}.corner-tag{position:absolute;bottom:14px;right:24px;font-size:9px;letter-spacing:0.15em;text-transform:uppercase;color:#d8d2ca;font-weight:500;}@media(max-width:520px){.tiers{padding:10px 12px 18px;gap:7px;}.tier{grid-template-columns:44px 1fr auto;}.tier-num{font-size:18px;padding:10px 0;}.tier-body{padding:8px 10px;}.tier-label{font-size:11px;}.tier-desc{font-size:10px;}.tier-example{font-size:9px;}.cost-pill{font-size:9px;padding:3px 7px;}.tier-cost{padding:8px 6px 8px 0;}}</style></head><body><div class="card"><div class="tiers"><div class="tier t1"><div class="tier-num">1<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Generic drugs</div><div class="tier-desc">Same active ingredient as the brand name.</div><div class="tier-example">metformin · lisinopril · amoxicillin</div></div><div class="tier-cost"><span class="cost-pill">$0 – $15</span></div></div><div class="tier t2"><div class="tier-num">2<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Preferred brand-name</div><div class="tier-desc">Insurer has negotiated a deal with drug company. Still a decent copay.</div><div class="tier-example">Lipitor · Zoloft · Synthroid</div></div><div class="tier-cost"><span class="cost-pill">$30 – $60</span></div></div><div class="tier t3"><div class="tier-num">3<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Non-preferred brand-name</div><div class="tier-desc">Insurer has not negotiated a deal with drug company.</div><div class="tier-example">Newer name-brands</div></div><div class="tier-cost"><span class="cost-pill">$60 – $100+</span></div></div><div class="tier t4"><div class="tier-num">4<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Specialty drugs</div><div class="tier-desc">Complex conditions. Often 20–30% coinsurance instead of a flat copay.</div><div class="tier-example">Humira · Enbrel · MS &amp; cancer drugs</div></div><div class="tier-cost"><span class="cost-pill">20–30% cost</span></div></div><div class="tier t5"><div class="tier-num">5<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Very high-cost specialty</div><div class="tier-desc">Highest cost-sharing. May require step therapy.</div><div class="tier-example">Gene therapies · biologic infusions</div></div><div class="tier-cost"><span class="cost-pill">Highest</span></div></div></div><div class="corner-tag">Health Plan Reference</div></div><script>function resize(){var h=document.body.scrollHeight;window.parent.postMessage({type:'streamlit:setFrameHeight',height:h},'*');}window.addEventListener('load',resize);window.addEventListener('resize',resize);</script></body></html>""", height=560, scrolling=False)
with st.expander("View all formularies"):
    rows_html = "".join(
        f'<tr><td style="padding:7px 14px;border-bottom:1px solid #edf1f5;color:#0f1923;">{e.get("plan_name","")}</td>'
        f'<td style="padding:7px 14px;border-bottom:1px solid #edf1f5;"><a href="{e.get("url","")}" target="_blank" style="color:#0d7a6e;">{e.get("url","")}</a></td></tr>'
        for e in sorted(entries, key=lambda e: e.get("plan_name","").lower())
    )
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:0.85rem;background:white;color:#0f1923;">'
        f'<thead><tr>'
        f'<th style="padding:10px 14px;text-align:left;border-bottom:2px solid #dde4eb;color:#1e3448;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">Plan</th>'
        f'<th style="padding:10px 14px;text-align:left;border-bottom:2px solid #dde4eb;color:#1e3448;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">URL</th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True
    )
