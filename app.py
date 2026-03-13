import streamlit as st
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UAMS Formulary Search",
    page_icon="💊",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

    :root {
        --ink:       #0f1923;
        --slate:     #1e3448;
        --teal:      #0d7a6e;
        --teal-mid:  #0fa898;
        --teal-lt:   #d4f0ec;
        --amber:     #e8913a;
        --amber-lt:  #fdf0e3;
        --rose:      #c94f4f;
        --rose-lt:   #fbeaea;
        --surface:   #ffffff;
        --bg:        #f0f4f7;
        --border:    #dde4eb;
        --muted:     #6b7e8f;
    }

    * { font-family: 'DM Sans', sans-serif; }

    [data-testid="stAppViewContainer"] {
        background: var(--bg);
        background-image: radial-gradient(circle at 80% 10%, rgba(13,122,110,0.06) 0%, transparent 55%),
                          radial-gradient(circle at 10% 90%, rgba(30,52,72,0.05) 0%, transparent 50%);
    }

    /* ── Header ── */
    .header-bar {
        background: var(--slate);
        background-image: linear-gradient(135deg, #0f1923 0%, #1e3448 50%, #0d4a60 100%);
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

    /* ── Result cards ── */
    .result-card {
        background: var(--surface);
        border-left: 4px solid var(--border);
        padding: 14px 20px;
        margin: 7px 0;
        border-radius: 0 10px 10px 0;
        box-shadow: 0 1px 3px rgba(15,25,35,0.06), 0 4px 12px rgba(15,25,35,0.04);
        transition: box-shadow 0.2s ease;
    }
    .result-card:hover { box-shadow: 0 2px 8px rgba(15,25,35,0.1), 0 6px 20px rgba(15,25,35,0.06); }
    .result-card.found { border-left-color: var(--teal); }
    .result-card.error { border-left-color: var(--rose); }

    .plan-label  { font-size: 1rem; font-weight: 600; color: var(--ink); letter-spacing: -0.01em; }
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
        background: var(--teal) !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        transition: background 0.2s ease !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background: var(--teal-mid) !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h1>💊 Formulary Drug Search</h1>
  <p>Search across insurance formularies instantly — results include direct links to source documents.</p>
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

        # 1. Explicit "Tier N" anywhere in snippet
        t = re.search(r'\btier\s*[:\-]?\s*([1-9])\b', snippet, re.IGNORECASE)
        if t:
            return f"Tier {t.group(1)}"

        # 2. AR Benefits pattern: "DRUG ... - 2 DRUGCLASS" (digit after dash before ALL CAPS class)
        ar_match = re.search(r'\s-\s([1-6])\s+[A-Z]{3}', after.split('\n')[0])
        if ar_match:
            return f"Tier {ar_match.group(1)}"

        # 3. Digit before PA/QL/ST flags on same line: "OZEMPIC ... 2 PA, QL"
        flag_match = re.search(r'\b([1-6])\s+(?:PA|QL|ST)\b', after.split('\n')[0], re.IGNORECASE)
        if flag_match:
            return f"Tier {flag_match.group(1)}"

        # 3. Standalone digit (1-6) on the same line after the drug name
        #    e.g. "metformin tabs 500mg   1   PA QL"
        same_line = re.search(r'[^\S\n]{2,}([1-6])\b', after.split('\n')[0])
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

    return None

# ── Tricare status extractor ──────────────────────────────────────────────────
TRICARE_URL_STATUS = {
    "non-formulary": "Non-Formulary",
    "tier4":         "Not Covered",
}

def tricare_status_from_url(url):
    """Derive Tricare coverage status from which list the URL points to."""
    url_lower = url.lower()
    for fragment, label in TRICARE_URL_STATUS.items():
        if fragment in url_lower:
            return label
    return "Covered"

# ── Aetna code extractor ─────────────────────────────────────────────────────
AETNA_CODE_LEGEND = {
    "CE":   "Copay Exception",
    "PB":   "Preferred Brand",
    "PBSP": "Preferred Brand Specialty",
    "PG":   "Preferred Generic",
    "N8":   "Drug Specific Coverage",
    "SPC":  "Select Plan Coverage",
}

def extract_aetna_code(text, keyword):
    """Find Aetna coverage code on the line immediately after the keyword match."""
    pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
    for m in pattern.finditer(text):
        after_lines = text[m.end():m.end()+200].split('\n')
        for line in after_lines[1:4]:
            stripped = line.strip()
            if stripped in AETNA_CODE_LEGEND:
                return AETNA_CODE_LEGEND[stripped]
    return None

with st.form("search_form"):
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        keyword = st.text_input("Drug / keyword", placeholder="e.g.  metformin", label_visibility="collapsed")
    with col_btn:
        go = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

st.markdown(f"""
<div style="display:flex;gap:10px;margin-top:8px;">
  <a href="https://www.goodrx.com/" target="_blank" style="background:#e8913a;color:white;padding:7px 16px;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">💊 GoodRx</a>
  <a href="https://www.openevidence.com" target="_blank" style="background:#0d7a6e;color:white;padding:7px 16px;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">🔬 OpenEvidence</a>
</div>
""", unsafe_allow_html=True)

if go and keyword.strip():
    # ── Run search ────────────────────────────────────────────────────────────
    results       = search_entries(entries, keyword, "All Plan Groups", "All Payers")
    found_results = sorted([r for r in results if r["found"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
    missed        = sorted([r for r in results if not r["found"] and not r["search_error"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
    errors        = [r for r in results if r["search_error"]]

    if found_results:
        st.success(f'✅ **"{keyword.strip()}"** found in **{len(found_results)}** formulary/formularies.')
    else:
        st.error(f'❌ **"{keyword.strip()}"** was not found in any formulary.')

    st.divider()
    st.markdown("**After selecting a PDF, hit Ctrl+F**")

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
            tier_html = '<span style="font-size:0.85rem;color:var(--muted);margin-left:8px;">Covered</span>'
        else:
            is_aetna = "aetna" in plan_label.lower()
            if is_aetna and r.get("found") and r.get("text"):
                code = extract_aetna_code(r.get("text",""), keyword)
                tier_html = f'<span style="font-size:0.85rem;color:var(--muted);margin-left:8px;">{code}</span>' if code else ""
            else:
                tier = extract_tier(r.get("text") or "", keyword) if r.get("found") and r.get("text") else None
                if tier:
                    tier_html = f'<span style="font-size:0.85rem;color:var(--muted);margin-left:8px;">{tier}</span>'
                else:
                    tier_html = ""

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
        st.markdown(f"""
    <div class="{card_class}">
      <div class="plan-label">{plan_link} &nbsp; {tag}{tier_html}</div>
    </div>""", unsafe_allow_html=True)

# ── View all formularies ──────────────────────────────────────────────────────
if not (go and keyword.strip()):
    st.markdown("<div style='height:40vh'></div>", unsafe_allow_html=True)
with st.expander("📋 View all formularies"):
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
