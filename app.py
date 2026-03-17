import streamlit as st
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Prior Authorization Search",
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
<script>
(function() {
    function attachCloseDetails() {
        var btn = document.querySelector('[data-testid="stFormSubmitButton"] button');
        if (btn && !btn._detailsListenerAttached) {
            btn._detailsListenerAttached = true;
            btn.addEventListener('click', function() {
                document.querySelectorAll('details[open]').forEach(function(d) {
                    d.removeAttribute('open');
                });
            });
        }
        if (!btn) setTimeout(attachCloseDetails, 300);
    }
    attachCloseDetails();
})();
</script>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h1>Prior Authorization Search</h1>
  <p>Searches (brand) drug coverage, tiers, and PA criteria across multiple health plans.</p>
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

# ── Load PA URLs from CSV ─────────────────────────────────────────────────────
import csv as _csv

def _normalize_plan(name):
    """Normalize plan name for lookup — treats hyphens and multiple spaces as single space."""
    return re.sub(r'\s*-\s*|\s{2,}', ' ', name).strip().lower()

_pa_lookup = {}
_pa_csv = Path("formulary_links.csv")
if _pa_csv.exists():
    with open(_pa_csv, newline="", encoding="utf-8-sig", errors="replace") as _f:
        for _row in _csv.reader(_f):
            if len(_row) >= 6 and _row[5].strip().startswith("http"):
                _pa_lookup[_row[3].strip()] = _row[5].strip()

# ── Load PA criteria text index ───────────────────────────────────────────────
PA_INDEX_FILE          = "pa_index.json"
PA_CAREMARK_INDEX_FILE = "pa_caremark_index.json"
PA_UHC_INDEX_FILE      = "pa_uhc_index.json"

_pa_text_lookup  = {}   # normalized plan_name -> single text (CSV/Medicare plans)
_pa_entry_lookup = {}   # normalized plan_name -> list of {drug_label, text, url} (caremark/UHC)

def _load_pa_index(filepath, multi_entry=False):
    if not Path(filepath).exists():
        return
    with open(filepath, encoding="utf-8") as _f:
        _data = json.load(_f)
    _texts = _data.get("texts", {})  # url -> text (deduplicated format)
    for _e in _data.get("entries", []):
        _url  = _e.get("url","") or _e.get("pa_url","")
        _text = _e.get("text","") or _texts.get(_url,"")
        if not _text:
            continue
        _nkey = _normalize_plan(_e["plan_name"])
        if multi_entry:
            if _nkey not in _pa_entry_lookup:
                _pa_entry_lookup[_nkey] = []
            _pa_entry_lookup[_nkey].append({
                "drug_label": _e.get("drug_label",""),
                "text":       _text,
                "url":        _url,
            })
        else:
            _pa_text_lookup[_nkey] = _text

_load_pa_index(PA_INDEX_FILE,          multi_entry=False)
_load_pa_index(PA_CAREMARK_INDEX_FILE, multi_entry=True)
_load_pa_index(PA_UHC_INDEX_FILE,      multi_entry=True)

# ── Load Aetna CPB data into _pa_entry_lookup ─────────────────────────────────
AETNA_CPB_FILE = "aetna_cpb_full.json"
AETNA_CPB_PLANS = [
    "Aetna - Advanced Control Choice",
    "Aetna - Basic Control",
    "Aetna - High Value",
    "Aetna - Standard",
    "Aetna - Standard Control Plan",
]
if Path(AETNA_CPB_FILE).exists():
    with open(AETNA_CPB_FILE, encoding="utf-8") as _af:
        _aetna_data = json.load(_af)
    _aetna_entries = [e for e in _aetna_data.get("entries", []) if e.get("full_text") and e.get("status") == "ok"]
    for _aplan in AETNA_CPB_PLANS:
        _nkey = _normalize_plan(_aplan)
        if _nkey not in _pa_entry_lookup:
            _pa_entry_lookup[_nkey] = []
        for _ae in _aetna_entries:
            _pa_entry_lookup[_nkey].append({
                "drug_label": _ae.get("title", ""),
                "text":       _ae.get("full_text", ""),
                "url":        _ae.get("url", ""),
            })
    for _aplan in AETNA_CPB_PLANS:
        if _aplan not in _pa_lookup:
            _pa_lookup[_aplan] = "https://www.aetna.com/health-care-professionals/clinical-policy-bulletins/pharmacy-clinical-policy-bulletins.html"

try:
    built_nice = datetime.fromisoformat(built_at.replace("Z","")).strftime("%B %d, %Y")
except Exception:
    built_nice = built_at

# ── Build plan word vocabulary from CSV column D ──────────────────────────────
_plan_words = set()
if _pa_csv.exists():
    with open(_pa_csv, newline="", encoding="utf-8-sig", errors="replace") as _pwf:
        for _prow in _csv.reader(_pwf):
            if len(_prow) >= 4 and _prow[3].strip():
                for _pw in re.split(r'[\s\-\(\),/]+', _prow[3].strip().lower()):
                    if _pw and len(_pw) > 1:
                        _plan_words.add(_pw)

def parse_query(raw_query):
    """
    Split up to 4 words into plan filter words and drug keyword.
    Words found in plan names (column D) are plan words; others are drug words.
    Consecutive plan words stay SEPARATE (each filters independently with OR logic).
    Consecutive drug words are merged into one search term.
    """
    words = raw_query.strip().lower().split()
    if not words:
        return [], ""
    tags = ['P' if w in _plan_words else 'D' for w in words]
    plan_parts, drug_parts = [], []
    i = 0
    while i < len(words):
        if tags[i] == 'P':
            # Each plan word stays separate
            plan_parts.append(words[i])
        else:
            group = [words[i]]
            while i + 1 < len(words) and tags[i + 1] == 'D':
                i += 1
                group.append(words[i])
            drug_parts.append(' '.join(group))
        i += 1
    return plan_parts, ' '.join(drug_parts)

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
    If multiple different tiers are found (e.g. metformin has Tier 1 and Tier 2 entries),
    returns None to avoid displaying a misleading tier.
    """
    kw = keyword.strip()
    pattern = re.compile(re.escape(kw), re.IGNORECASE)
    found_tiers = set()

    def _get_tier_from_match(after):
        line0 = after.split('\n')[0]
        first_lines = '\n'.join(after.split('\n')[:2])

        t = re.search(r'\btier\s*[:\-]?\s*([1-9])\b', after, re.IGNORECASE)
        if t:
            return f"Tier {t.group(1)}"

        ar_match = re.search(r'\s-\s([1-6])\s+[A-Z]{3}', line0)
        if ar_match:
            return f"Tier {ar_match.group(1)}"

        # QL-RDX and dollar-tier legitimately span 2 lines
        ql_rdx = re.search(r'QL-RDX\s+([1-6])\b', first_lines, re.IGNORECASE)
        if ql_rdx:
            return f"Tier {ql_rdx.group(1)}"

        dollar_tier = re.search(r'\$\d+\s*\(([1-6])\)', first_lines)
        if dollar_tier:
            return f"Tier {dollar_tier.group(1)}"

        # All remaining patterns: same line only to avoid adjacent drug bleed
        mo_tier = re.search(r'\bMO\s+([1-6])\b', line0)
        if mo_tier:
            return f"Tier {mo_tier.group(1)}"

        # flag_match: check line0 first, then line1 only if it looks like a continuation
        # (not a new drug — new drugs start with a capitalized word at beginning of line)
        after_lines = after.split('\n')
        line1 = after_lines[1] if len(after_lines) > 1 else ''
        # New drug entries start with a proper word (3+ chars), not dosage continuations like "MG (" or "ML)"
        is_new_entry = line1 and re.match(r'^[A-Za-z]{3,}(?:\s|$)', line1.strip()) and \
                       not re.match(r'^(?:MG|ML|MCG|MEQ|GM|IU|Units?)\b', line1.strip(), re.IGNORECASE)
        is_continuation = line1 and not is_new_entry
        search_scope = '\n'.join([line0, line1]) if is_continuation else line0

        # Tier digit must be preceded by whitespace (not part of a dosage like "5-1.5" or "500mg")
        flag_match = re.search(r'(?<![0-9\-\.])(?:^|(?<=\s))([1-6])\s+(?:PA|QL|ST|MO)\b', search_scope, re.IGNORECASE)
        if flag_match:
            return f"Tier {flag_match.group(1)}"

        # Cigna/BCBS-style: tier digit preceded by space, followed by * or NDS: "200mg/ml 5 NDS" or "10-325 2 *"
        # WellCare-style: tier digit followed by ^ caret: "400 MG 5^ PA"
        restriction_match = re.search(r'(?<=\s)([1-6])(?:\s+(?:\*|NDS)|\^)', search_scope)
        if restriction_match:
            return f"Tier {restriction_match.group(1)}"

        same_line = re.search(r'[^\S\n]{2,}([1-6])(?:\s*$|\s+(?:PA|QL|ST|MO)\b)', search_scope, re.IGNORECASE)
        if same_line and not re.search(r'[0-9\-\.]' + same_line.group(1), search_scope):
            return f"Tier {same_line.group(1)}"

        lines = [l.strip() for l in after.split('\n') if l.strip()]
        if lines and re.fullmatch(r'[1-6]', lines[0]):
            return f"Tier {lines[0]}"

        same_line_text = after.split('\n')[0]
        label = re.search(
            r'\b(preferred specialty|non.preferred specialty|specialty|'
            r'preferred brand|non.preferred brand|preferred|non.preferred|generic)\b',
            same_line_text, re.IGNORECASE
        )
        if label:
            mapping = {
                'generic': 'Tier 1',
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

    for m in pattern.finditer(text):
        # Skip index/TOC lines: any line containing dots followed by a page number
        line_start = text.rfind('\n', 0, m.start()) + 1
        line_end = text.find('\n', m.end())
        full_line = text[line_start: line_end if line_end > 0 else m.end()+100]
        if re.search(r'\.{2,}\s*\d+', full_line):
            continue

        after = text[m.end() : m.end() + 300]
        tier = _get_tier_from_match(after)
        if tier:
            found_tiers.add(tier)

    if len(found_tiers) == 1:
        return found_tiers.pop()
    return None  # No tier found, or conflicting tiers

# ── Tricare status extractor ──────────────────────────────────────────────────
TRICARE_URL_STATUS = {
    "non-formulary": "Non-Formulary",
    "tier4":         "Not Covered",
}

def extract_pa(text, keyword):
    """Return True only if ALL valid keyword matches have PA on the same line or continuation line."""
    pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
    valid_matches = []
    for m in pattern.finditer(text):
        line_start = text.rfind('\n', 0, m.start()) + 1
        line_end = text.find('\n', m.end())
        full_line = text[line_start: line_end if line_end > 0 else m.end()+100]
        if re.search(r'\.{2,}\s*\d+', full_line):
            continue
        valid_matches.append(m)
    if not valid_matches:
        return False
    def _pa_scope(m):
        after_lines = text[m.end():m.end()+300].split('\n')
        line0 = after_lines[0]
        line1 = after_lines[1] if len(after_lines) > 1 else ''
        is_new_entry = line1 and re.match(r'^[A-Za-z]{3,}(?:\s|$)', line1.strip()) and \
                       not re.match(r'^(?:MG|ML|MCG|MEQ|GM|IU|Units?)\b', line1.strip(), re.IGNORECASE)
        return '\n'.join([line0, line1]) if (line1 and not is_new_entry) else line0
    pa_count = sum(1 for m in valid_matches if re.search(r'\bPA\b', _pa_scope(m)))
    return pa_count == len(valid_matches)


def extract_st(text, keyword):
    """Return True only if ALL valid keyword matches have ST on the same line or continuation line."""
    pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
    valid_matches = []
    for m in pattern.finditer(text):
        line_start = text.rfind('\n', 0, m.start()) + 1
        line_end = text.find('\n', m.end())
        full_line = text[line_start: line_end if line_end > 0 else m.end()+100]
        if re.search(r'\.{2,}\s*\d+', full_line):
            continue
        valid_matches.append(m)
    if not valid_matches:
        return False
    def _st_scope(m):
        after_lines = text[m.end():m.end()+300].split('\n')
        line0 = after_lines[0]
        line1 = after_lines[1] if len(after_lines) > 1 else ''
        is_new_entry = line1 and re.match(r'^[A-Za-z]{3,}(?:\s|$)', line1.strip()) and \
                       not re.match(r'^(?:MG|ML|MCG|MEQ|GM|IU|Units?)\b', line1.strip(), re.IGNORECASE)
        return '\n'.join([line0, line1]) if (line1 and not is_new_entry) else line0
    st_count = sum(1 for m in valid_matches if re.search(r'\bST\b|step therapy', _st_scope(m), re.IGNORECASE))
    return st_count == len(valid_matches)


def tricare_status_from_url(url):
    """Derive Tricare coverage status from which list the URL points to."""
    url_lower = url.lower()
    for fragment, label in TRICARE_URL_STATUS.items():
        if fragment in url_lower:
            return label
    return "Covered"

# ── Free-text PA formatter ────────────────────────────────────────────────────
def format_freetext_html(text):
    """Convert free-form PA criteria text to indented HTML based on outline hierarchy."""
    import html as _html
    # Strip caremark boilerplate footer
    text = re.sub(
        r'©\s*\d{4}\s*CVS Caremark.*',
        '', text, flags=re.IGNORECASE | re.DOTALL
    ).strip()
    # Strip embedded .docx filename lines (e.g. "Wegovy PA with Limit 4774-C P08-2025 v3.docx")
    text = re.sub(r'\n[^\n]*\.docx\b[^\n]*', '', text, flags=re.IGNORECASE).strip()
    # Strip UHC copyright lines (appear mid-text in UHC PDFs — strip line only, not everything after)
    text = re.sub(r'\n©\s*\d{4}\s*UnitedHealthcare[^\n]*', '', text, flags=re.IGNORECASE)
    # Strip References section and everything below (with or without number prefix e.g. "4. References:")
    text = re.sub(
        r'\n\d*\.?\s*References:?\s*\n.*',
        '', text, flags=re.IGNORECASE | re.DOTALL
    ).strip()
    # Strip Change Control section and everything below
    text = re.sub(
        r'\nChange Control\n.*',
        '', text, flags=re.IGNORECASE | re.DOTALL
    ).strip()
    # Fix footnote letters concatenated onto "Criteria" by PDF extractor
    # e.g. "Criteriaa" -> "Criteriaª", "Criteriab" -> "Criteriaᵇ", "Coverage Criteriaa, b" -> "Coverage Criteriaª,ᵇ"
    _sup_map = {'a': 'ª', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ'}
    def _fix_criteria_fn(m):
        base = m.group(1)
        letters = re.findall(r'[a-e]', m.group(2))
        return base + ','.join(_sup_map.get(l, l) for l in letters)
    text = re.sub(
        r'((?:Coverage )?Criteria)((?:[,\s]*[a-e])+)(?=[^a-z]|$)',
        _fix_criteria_fn, text
    )
    # Rejoin mid-sentence line breaks in Background section and add sentence spacing
    def _reflow_background(m):
        block = m.group(0)
        header_end = block.index('\n') + 1
        header = block[:header_end]
        body = block[header_end:]
        # Rejoin lines that don't end with sentence-ending punctuation
        joined = re.sub(r'(?<![.!?])\n(?=[a-zA-Z(])', ' ', body)
        # Split into individual sentences and render each as a bullet
        sentences = re.split(r'(?<=\.)\s+(?=[A-Z])', joined.strip())
        bullet_lines = [f'\u25cf\u0020{s.strip()}' for s in sentences if s.strip()]
        return header + '\n'.join(bullet_lines)
    text = re.sub(
        r'\d+\.\s*Background:.*?(?=\n\d+\.\s*\w|\Z)',
        _reflow_background, text, flags=re.IGNORECASE | re.DOTALL
    )
    lines = text.split('\n')
    parts = []
    _last_bullet_indent = 0
    _last_was_bullet = False

    for line in lines:
        raw = line.rstrip()
        s = raw.strip()
        if not s:
            parts.append('<div style="height:4px;"></div>')
            _last_was_bullet = False
            continue
        esc = _html.escape(s)
        leading = len(raw) - len(raw.lstrip(' '))

        if re.match(r'^\d+\.\s.{2,}:', s):
            parts.append(f'<div style="margin:10px 0 2px 0;font-weight:700;color:#1e3448;border-bottom:1px solid #dde4eb;padding-bottom:2px;">{esc}</div>')
            _last_was_bullet = False
        elif re.match(r'^[A-Z]\.\s', s):
            _last_bullet_indent = 16
            parts.append(f'<div style="margin:6px 0 2px {_last_bullet_indent}px;font-weight:600;color:#1e3448;">{esc}</div>')
            _last_was_bullet = True
        elif re.match(r'^Criteria for \w', s, re.IGNORECASE):
            parts.append(f'<div style="margin:8px 0 2px 8px;font-weight:600;color:#1e3448;">{esc}</div>')
            _last_was_bullet = False
        elif re.match(r'^\d+\.\s', s):
            _last_bullet_indent = 32
            parts.append(f'<div style="margin:4px 0 1px {_last_bullet_indent}px;font-weight:600;">{esc}</div>')
            _last_was_bullet = True
        elif re.match(r'^[a-z]\.\s', s) and not re.match(r'^(are|and|or|the|of|to|in|is|for)\b', s):
            _last_bullet_indent = 48
            parts.append(f'<div style="margin:3px 0 1px {_last_bullet_indent}px;">{esc}</div>')
            _last_was_bullet = True
        elif re.match(r'^\d\)\s', s):                          # 1) 2) 3) — sub-items under a. b.
            _last_bullet_indent = 64
            parts.append(f'<div style="margin:2px 0 1px {_last_bullet_indent}px;">{esc}</div>')
            _last_was_bullet = True
        elif re.match(r'^\(\d+\)\s', s):
            _last_bullet_indent = 64
            parts.append(f'<div style="margin:2px 0 1px {_last_bullet_indent}px;">{esc}</div>')
            _last_was_bullet = True
        elif re.match(r'^\([a-z]\)\s', s):
            _last_bullet_indent = 80
            parts.append(f'<div style="margin:2px 0 1px {_last_bullet_indent}px;">{esc}</div>')
            _last_was_bullet = True
        elif re.match(r'^[a-z] [A-Z]', s):                     # footnote line e.g. "a State mandates..." "b Bydureon..."
            parts.append(f'<div style="margin:4px 0 1px 0;font-size:0.78rem;">{esc}</div>')
            _last_was_bullet = False
        elif re.match(r'^● ', s):                              # background sentence bullet
            rest = _html.escape(s[2:].strip())
            _last_bullet_indent = 14
            parts.append(f'<div style="display:flex;margin:4px 0 1px 0;"><span style="flex-shrink:0;width:14px;padding-top:1px;">•</span><span>{rest}</span></div>')
            _last_was_bullet = False
        elif re.match(r'^•\s', s):
            indent = 40 + min(leading, 12) * 4
            rest = _html.escape(s[2:].strip())
            _last_bullet_indent = indent
            parts.append(f'<div style="display:flex;margin:2px 0 1px {_last_bullet_indent}px;"><span style="flex-shrink:0;width:14px;">•</span><span>{rest}</span></div>')
            _last_was_bullet = True
        elif re.match(r'^◦\s', s):
            rest = _html.escape(s[2:].strip())
            _last_bullet_indent = 48
            parts.append(f'<div style="display:flex;margin:2px 0 1px {_last_bullet_indent}px;"><span style="flex-shrink:0;width:14px;">◦</span><span>{rest}</span></div>')
            _last_was_bullet = True
        elif re.match(r'^\uf0a7', s) or re.match(r'^\u25aa', s):
            rest = _html.escape(s[1:].strip())
            _last_bullet_indent = 48
            parts.append(f'<div style="display:flex;margin:2px 0 1px {_last_bullet_indent}px;"><span style="flex-shrink:0;width:14px;">◦</span><span>{rest}</span></div>')
            _last_was_bullet = True
        elif s in ('-AND-', '-OR-', 'AND', 'OR'):
            parts.append(f'<div style="margin:3px 0 3px 48px;color:#856404;font-weight:500;">{esc}</div>')
            _last_was_bullet = False
        elif re.match(r'^(Coverage Criteria|COVERAGE CRITERIA|Continuation of Therapy|References|Background)', s, re.IGNORECASE):
            parts.append(f'<div style="margin:8px 0 2px 0;font-weight:600;color:#1e3448;">{esc}</div>')
            _last_was_bullet = False
        elif re.match(r'^(Authorization of|Authorization will|Authorization may)', s, re.IGNORECASE):
            parts.append(f'<div style="margin:4px 0 2px 16px;font-style:italic;color:#555;">{esc}</div>')
            _last_was_bullet = False
        elif re.match(r'^©|^Reference number|Caremark\.', s):
            parts.append(f'<div style="margin:2px 0;color:#aaa;font-size:0.72rem;">{esc}</div>')
            _last_was_bullet = False
        elif leading >= 4:
            indent = 24 + min(leading, 16) * 3
            parts.append(f'<div style="margin:1px 0 1px {indent}px;">{esc}</div>')
            _last_was_bullet = False
        elif _last_was_bullet:                                  # continuation of previous bullet
            parts.append(f'<div style="margin:0 0 1px {_last_bullet_indent + 14}px;">{esc}</div>')
        else:
            parts.append(f'<div style="margin:2px 0 1px 0;">{esc}</div>')
            _last_was_bullet = False
    return ''.join(parts)





# ── Aetna CPB PA criteria formatter ──────────────────────────────────────────
import re
import html as _html

def format_aetna_cpb_html(text, drug_term=""):
    # Trim References section and Aetna copyright boilerplate
    text = re.sub(r'\nReferences\s*\n.*', '', text, flags=re.IGNORECASE|re.DOTALL).strip()
    text = re.sub(r'\nThe above policy is based on the following references.*', '', text, flags=re.IGNORECASE|re.DOTALL).strip()
    text = re.sub(r'\nBackground\s*\n.*', '', text, flags=re.IGNORECASE|re.DOTALL).strip()
    text = re.sub(r'\n?Copyright Aetna.*', '', text, flags=re.IGNORECASE|re.DOTALL).strip()

    # Fix broken superscript lines e.g. "1.73m\n2\n)"
    text = re.sub(r'(\w)\n(\d+)\n(\))', r'\1\2\3', text)

    lines = [l.rstrip() for l in text.split('\n')]

    OPENER = re.compile(
        r'(?:ALL|ONE|BOTH|any)\s+of\s+the\s+following|'
        r'following\s+criteria\s+(?:is|are)\s+met|'
        r'when\s+(?:ALL|ONE|BOTH|the)\s+of\s+the\s+following|'
        r'criteria\s+(?:is|are)\s+met\s*:',
        re.IGNORECASE
    )
    ACTION_REQ = re.compile(r'\[ACTION REQUIRED[^\]]*\]', re.IGNORECASE)
    CONNECTOR = re.compile(r'^(?:AND|OR|-AND-|-OR-)$', re.IGNORECASE)
    INDENT_PX = [0, 18, 36, 54, 72, 90]

    def indent(d):
        return INDENT_PX[min(d, len(INDENT_PX)-1)]

    def badge(s):
        return ACTION_REQ.sub(
            lambda m: '<span style="background:#fef3e2;color:#b45309;font-size:0.7rem;'
                      'padding:1px 6px;border-radius:10px;margin-left:4px;font-weight:600;">'
                      'Action Required</span>',
            s
        )

    def hilight(s):
        if not drug_term:
            return s
        return re.sub(
            r'(?i)(' + re.escape(drug_term) + r')',
            r'<strong style="color:#1e3448;">\1</strong>',
            s
        )

    depth = 0
    result = []

    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            result.append('<div style="height:3px;"></div>')
            continue

        esc = _html.escape(s)
        esc = badge(esc)
        esc = hilight(esc)

        # Drug name line just before FDA-approved Indications — render as sub-header, don't bullet
        if (len(s) < 40 and re.match(r'^[A-Z]', s) and not s.startswith('The ')
                and not s.startswith('If ') and ':' not in s
                and not CONNECTOR.match(s)
                and not re.search(r'criteria|authorization|patient|request|dose|therapy|diagnosis|type|heart|kidney|obesity', s, re.IGNORECASE)):
            # Peek ahead — if next non-empty line is "FDA-approved Indications", this is a drug name
            _j = i + 1
            while _j < len(lines) and not lines[_j].strip():
                _j += 1
            _nxt_s = lines[_j].strip() if _j < len(lines) else ''
            if re.match(r'^FDA-approved Indications', _nxt_s, re.IGNORECASE):
                result.append(
                    '<div style="margin:10px 0 1px 0;font-weight:700;font-size:0.82rem;color:#1e3448;">'
                    + esc + '</div>'
                )
                depth = 1
                continue

        # FDA-approved Indications header — plain, no color, no caps, no bullet
        if re.match(r'^FDA-approved Indications$', s, re.IGNORECASE):
            result.append(
                '<div style="margin:4px 0 2px 0;font-weight:600;font-size:0.8rem;color:#2a3a4a;">'
                + esc + '</div>'
            )
            depth = 1
            continue

        # "DrugName is indicated:" — plain, no bullet
        if re.match(r'^\w.*\bis indicated\b', s, re.IGNORECASE) and s.rstrip().endswith(':'):
            result.append(
                '<div style="margin:2px 0 2px 0;font-size:0.8rem;color:#2a3a4a;">'
                + esc + '</div>'
            )
            depth = 2
            continue

        # Compendial Uses header — bold label, WITH bullet
        if re.match(r'^Compendial Uses$', s, re.IGNORECASE):
            bullet_span = '<span style="color:#9aafc4;margin-right:5px;">●</span>'
            result.append(
                '<div style="margin:6px 0 2px 0;font-weight:600;font-size:0.8rem;color:#2a3a4a;">'
                + bullet_span + esc + '</div>'
            )
            depth = 2
            continue

        # Section title
        if s == 'Coverage Criteria':
            depth = 0
            result.append(
                '<div style="margin:10px 0 4px 0;font-weight:700;font-size:0.85rem;'
                'color:#1e3448;border-bottom:1px solid #dde4eb;padding-bottom:3px;">'
                + esc + '</div>'
            )
            continue

        # Diagnosis / condition sub-header
        if (len(s) < 65 and not s.startswith('The ') and not s.startswith('If ')
                and not s[0].islower() and ':' not in s
                and not CONNECTOR.match(s)
                and re.match(r'^[A-Z]', s)
                and not re.search(r'criteria|authorization|patient|request|dose|therapy|diagnosis', s, re.IGNORECASE)):
            depth = 1
            result.append(
                '<div style="margin:8px 0 2px 0;font-weight:600;font-size:0.82rem;'
                'color:#416CA6;">' + esc + '</div>'
            )
            continue

        # Connector (AND/OR)
        if CONNECTOR.match(s):
            result.append(
                '<div style="margin:2px 0 2px ' + str(indent(depth)) + 'px;'
                'color:#856404;font-weight:600;font-size:0.75rem;">' + esc + '</div>'
            )
            continue

        # Authorization intro line
        if re.match(r'^Authorization\s+may\s+be\s+granted', s, re.IGNORECASE):
            depth = 1
            is_opener = bool(s.rstrip().endswith(':') and OPENER.search(s))
            result.append(
                '<div style="margin:5px 0 2px 0;font-style:italic;color:#555;font-size:0.8rem;">'
                + esc + '</div>'
            )
            if is_opener:
                depth += 1
            continue

        # Bullet items
        is_opener = bool(s.rstrip().endswith(':') and OPENER.search(s))

        bullets = ['●', '◦', '▸', '–', '·']
        colors  = ['#1e3448', '#2a3a4a', '#3a4a5a', '#4a5a6a', '#5a6a7a']
        weights = ['500', '400', '400', '400', '400']

        d = depth
        b = bullets[min(d, len(bullets)-1)]
        c = colors[min(d, len(colors)-1)]
        w = weights[min(d, len(weights)-1)]
        bullet_span = '<span style="color:#9aafc4;margin-right:5px;">' + b + '</span>'

        result.append(
            '<div style="margin:2px 0 1px ' + str(indent(d)) + 'px;color:' + c + ';'
            'font-weight:' + w + ';font-size:0.8rem;line-height:1.55;">'
            + bullet_span + esc + '</div>'
        )

        if is_opener:
            depth += 1

        # Look ahead — if next non-empty line looks like a new section, reset depth
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines):
            nxt = lines[j].strip()
            if (len(nxt) < 65 and not nxt.startswith('The ') and not nxt.startswith('If ')
                    and re.match(r'^[A-Z]', nxt)
                    and not re.search(r'criteria|patient|request|dose', nxt, re.IGNORECASE)
                    and ':' not in nxt):
                depth = 1

    return ''.join(result)

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
    """Find Aetna coverage code. Returns None if conflicting codes found across matches."""
    pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
    found_codes = set()
    for m in pattern.finditer(text):
        after = text[m.end():m.end()+200]
        for line in after.split('\n')[0:4]:
            stripped = line.strip()
            end_code = re.search(r'\b(' + '|'.join(AETNA_CODE_LEGEND.keys()) + r')\s*$', stripped)
            if end_code:
                found_codes.add(AETNA_CODE_LEGEND[end_code.group(1)])
                break
            if stripped in AETNA_CODE_LEGEND:
                found_codes.add(AETNA_CODE_LEGEND[stripped])
                break
    if len(found_codes) == 1:
        return found_codes.pop()
    return None


with st.form("search_form"):
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        keyword = st.text_input("Drug / keyword", placeholder="type the brand & plan  (tier results unreliable with generics)", label_visibility="collapsed", key="search_input")
    with col_btn:
        go = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

_kw = keyword.strip() if keyword.strip() else ""

# Buttons below, aligned under the search bar (5/6 of width matches the [5,1] column ratio)
_btn_col, _spacer = st.columns([5, 1])
with _btn_col:
    st.markdown(f"""
<div style="display:flex;gap:10px;margin-top:2px;">
  <a href="https://www.goodrx.com/" target="_blank" style="background:#C89647;color:white;padding:7px 16px;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">💊 GoodRx</a>
  <a href="https://www.openevidence.com" target="_blank" style="background:#734702;color:white;padding:7px 16px;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">🔬 OpenEvidence</a>
</div>
""", unsafe_allow_html=True)

_results_placeholder = st.empty()

if go and keyword.strip():
    with _results_placeholder.container():
        # ── Parse input: split into plan filter words + drug keyword ──────────────
        plan_words_filter, drug_term = parse_query(keyword.strip())

        # Fallback: if no drug term, treat entire input as drug search
        if not drug_term and plan_words_filter:
            drug_term        = keyword.strip()
            plan_words_filter = []

        # ── Run search ────────────────────────────────────────────────────────────
        results = search_entries(entries, drug_term, "All Plan Groups", "All Payers")

        # Apply plan filter — plan name must contain ALL filter words (each independently)
        if plan_words_filter:
            results = [r for r in results if all(
                w in (r.get("plan_name","") or "").lower()
                for w in plan_words_filter
            )]

        plan_filter = ' '.join(plan_words_filter)  # for display only

        keyword = drug_term  # use drug term for tier extraction below

        found_results = sorted([r for r in results if r["found"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
        missed        = sorted([r for r in results if not r["found"] and not r["search_error"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
        errors        = [r for r in results if r["search_error"]]

        filter_note = f' in plans matching <strong>{plan_filter}</strong>' if plan_filter else ''
        if found_results:
            st.markdown(f'<div style="background:#eaf2d7;border:1px solid #478000;border-radius:6px;padding:10px 16px;color:#478000;font-weight:600;margin-top:20px;">"{drug_term}" found in <strong>{len(found_results)}</strong> formulary/formularies{filter_note}.</div>', unsafe_allow_html=True)
        else:
            st.error(f'❌ **"{drug_term}"** was not found in any formulary{(" matching " + plan_filter) if plan_filter else ""}.')

        st.divider()
        st.markdown('<p style="color:#416CA6;font-weight:600;">After selecting a PDF, hit Ctrl+F</p>', unsafe_allow_html=True)

        _cards_list = []  # list of (sort_key, card_html)
        _tricare_shown = False
        _seen_plans = set()
        for r in (found_results + [] + []):
            plan_label = r.get("plan_name") or r.get("payer") or r.get("plan_group","")
            is_tricare = "tricare" in plan_label.lower()

            # Deduplicate by normalized plan name (handles hyphen vs space variants)
            _plan_key = re.sub(r'\s*-\s*|\s{2,}', ' ', plan_label).strip().lower()
            if _plan_key in _seen_plans:
                continue
            _seen_plans.add(_plan_key)

            # Tricare: only show Covered results, skip all others, and only show once
            if is_tricare:
                if not r.get("found"):
                    continue
                status_label = tricare_status_from_url(r.get("url",""))
                if status_label != "Covered":
                    continue
                if _tricare_shown:
                    continue
                _tricare_shown = True
                tier_html = '<span style="font-size:0.75rem;background:#e8eaed;color:#444;padding:2px 8px;border-radius:20px;margin-left:8px;font-weight:500;">Covered</span>'
                pa_html = ""
                st_html = ""
            else:
                is_aetna = "aetna" in plan_label.lower() and "medicare" in plan_label.lower()
                if is_aetna and r.get("found") and r.get("text"):
                    code = extract_aetna_code(r.get("text",""), keyword)
                    if not code:
                        code = extract_tier(r.get("text",""), keyword)
                    tier_html = '<span style="font-size:0.75rem;background:#e8eaed;color:#444;padding:2px 8px;border-radius:20px;margin-left:8px;font-weight:500;">' + code + '</span>' if code else ""
                else:
                    tier = extract_tier(r.get("text") or "", keyword) if r.get("found") and r.get("text") else None
                    tier_html = '<span style="font-size:0.75rem;background:#e8eaed;color:#444;padding:2px 8px;border-radius:20px;margin-left:8px;font-weight:500;">' + tier + '</span>' if tier else ""
                # PA and ST badges
                has_pa = extract_pa(r.get("text") or "", keyword) if r.get("found") and r.get("text") else False
                has_st = extract_st(r.get("text") or "", keyword) if r.get("found") and r.get("text") else False
                pa_criteria_url  = _pa_lookup.get(plan_label, "")
                pa_criteria_text = _pa_text_lookup.get(_normalize_plan(plan_label), "")
                _plan_norm        = _normalize_plan(plan_label)
                _multi_entries    = _pa_entry_lookup.get(_plan_norm, [])

                # ── Multi-entry plans (caremark/UHC commercial): free-form display ──
                if _multi_entries:
                    # Find best matching entry for this drug
                    best_entry = None
                    best_score = 0
                    _criteria_terms = re.compile(
                        r'coverage criteria|authorization|indications?|required medical|'
                        r'exclusion criteria|step therapy|prior auth',
                        re.IGNORECASE
                    )
                    for _entry in _multi_entries:
                        _haystack = (_entry["drug_label"] + " " + _entry["text"]).lower()
                        if drug_term.lower() not in _haystack:
                            continue
                        # Score: label match = +2, criteria content = +3, content length = +1
                        _label_match   = drug_term.lower() in _entry["drug_label"].lower()
                        _has_criteria  = bool(_criteria_terms.search(_entry["text"]))
                        _header_match  = drug_term.lower() in _entry["text"][:300].lower()
                        # Penalize if drug only appears as incidental example e.g. "(e.g., methylphenidate)"
                        _egonly = bool(re.search(r'\(e\.g\.[^)]*' + re.escape(drug_term), _entry["text"][:500], re.IGNORECASE)) and not _label_match
                        _score = (_label_match * 2) + (_has_criteria * 3) + (len(_entry["text"]) > 2000) + (_header_match * 4) - (_egonly * 10)
                        if _score > best_score:
                            best_score = _score
                            best_entry = _entry

                    if best_entry:
                        _text = best_entry["text"]
                        _is_aetna_cpb = _normalize_plan(plan_label) in [_normalize_plan(p) for p in AETNA_CPB_PLANS]

                        # Check for multi-match ambiguity upfront — show link only, skip all rendering
                        _ind_m_pre = re.search(r'(?:^|\n)Indications\s*\nFDA-approved Indications', _text, re.IGNORECASE)
                        if _ind_m_pre:
                            _after_pre = _text[_ind_m_pre.end():]
                            _pre_count = len(re.findall(r'(?:^|\n)[^\n]*' + re.escape(drug_term) + r'[^\n]*\n', _after_pre, re.IGNORECASE))
                            if _pre_count > 1:
                                _entry_url = best_entry.get("url","") or pa_criteria_url
                                pa_criteria_link = f'<a href="{_entry_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>' if _entry_url else ""
                                best_entry = None  # prevent all further processing

                    if best_entry:
                        _text = best_entry["text"]
                        _is_aetna_cpb = _normalize_plan(plan_label) in [_normalize_plan(p) for p in AETNA_CPB_PLANS]
                        _skip_snippet = False
                        _start, _end = 0, 0

                        # For Aetna CPB: start at drug's FDA-approved Indications if found,
                        # otherwise fall back to Coverage Criteria
                        if _is_aetna_cpb:
                            # Count how many times drug term appears near an FDA-approved Indications header
                            _fda_sections = list(re.finditer(
                                r'(?:^|\n)[^\n]*\nFDA-approved Indications',
                                _text, re.IGNORECASE
                            ))
                            # Find sections that contain the drug term in the line just before FDA-approved
                            _drug_fda_matches = [m for m in _fda_sections
                                if re.search(re.escape(drug_term), m.group(), re.IGNORECASE)]
                            # If multiple drug-specific FDA sections, too ambiguous — show link only
                            if len(_drug_fda_matches) > 1:
                                pa_criteria_link = f'<a href="{pa_criteria_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>' if pa_criteria_url else ""
                                _skip_snippet = True
                            else:
                                _fda_m = _drug_fda_matches[0] if _drug_fda_matches else None
                                _cov_m = re.search(r'(?:^|\n)Coverage Criteria', _text, re.IGNORECASE)
                                _ind_header_m = re.search(r'(?:^|\n)Indications\s*\nFDA-approved Indications', _text, re.IGNORECASE)
                                # If Indications section exists and drug appears multiple times as a header, link only
                                if _ind_header_m:
                                    _after = _text[_ind_header_m.end():]
                                    _drug_count = len(re.findall(
                                        r'(?:^|\n)[^\n]*' + re.escape(drug_term) + r'[^\n]*(?:\n|$)',
                                        _after, re.IGNORECASE
                                    ))
                                    if _drug_count > 1:
                                        _entry_url = best_entry.get("url","") or pa_criteria_url
                                        pa_criteria_link = f'<a href="{_entry_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>' if _entry_url else ""
                                        _skip_snippet = True
                                    else:
                                        _start = _ind_header_m.start()
                                        _end = min(len(_text), (_cov_m.start() + 4000) if _cov_m else (_start + 6000))
                                elif _fda_m:
                                    _start = _fda_m.start()
                                    _cov_end = min(len(_text), (_cov_m.start() + 4000) if _cov_m else (_start + 5000))
                                    _next_drug = re.search(
                                        r'\n[A-Z][a-zA-Z\xae\-\s]{2,40}\nFDA-approved Indications',
                                        _text[_fda_m.end():], re.IGNORECASE
                                    )
                                    if _next_drug:
                                        _end = _fda_m.end() + _next_drug.start()
                                        if _cov_m and _cov_m.start() > _end:
                                            _end = _cov_end
                                    else:
                                        _end = _cov_end
                                elif _cov_m:
                                    _start = _cov_m.start()
                                    _end = min(len(_text), _start + 4000)
                                else:
                                    _start, _end = 0, 4000
                        else:
                            # Priority 1: "Indications\nFDA-approved Indications" section header
                            _ind_m = re.search(r'(?:^|\n)Indications\s*\nFDA-approved Indications', _text, re.IGNORECASE)
                            # Fallback: bare "Indications" line
                            _ind_bare_m = re.search(r'(?:^|\n)Indications\b', _text, re.IGNORECASE) if not _ind_m else None
                            # Priority 2: find "Coverage Criteria" section
                            _cov_m = re.search(r'(?:^|\n)(?:\d+\.\s*)?Coverage Criteria', _text, re.IGNORECASE)

                            # If Indications section has multiple drug entries for the search term, too ambiguous — link only
                            if _ind_m:
                                _after_ind = _text[_ind_m.end():]
                                _multi_fda = list(re.finditer(
                                    r'(?:^|\n)[^\n]*' + re.escape(drug_term) + r'[^\n]*\n',
                                    _after_ind, re.IGNORECASE
                                ))
                                if len(_multi_fda) > 1:
                                    _entry_url = best_entry.get("url","") or pa_criteria_url
                                    pa_criteria_link = f'<a href="{_entry_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>' if _entry_url else ""
                                    _skip_snippet = True

                            # Priority 2: find drug's own section header: "DrugName\n" or "DrugName FDA-approved"
                            _section_start = None
                            for _pat in [
                                r'(?:^|\n)(' + re.escape(drug_term) + r'\s*\nFDA)',
                                r'(?:^|\n)(' + re.escape(drug_term) + r'\s*\n)',
                                r'(?:^|\n)(' + re.escape(drug_term) + r'\s+FDA)',
                            ]:
                                _sm = re.search(_pat, _text, re.IGNORECASE)
                                if _sm:
                                    _section_start = _sm.start()
                                    break

                            _bg_m = re.search(r"(?:^|\n)(?:\d+\.\s*)?Background\s*:?\s*\n", _text, re.IGNORECASE)
                            _cov_m2 = re.search(r"(?:^|\n)(?:\d+\.\s*)?Coverage Criteria", _text, re.IGNORECASE) or _cov_m
                            _cont_m = re.search(r'(?:^|\n)(?:Continuation of Therapy|Criteria for continuation)\b', _text, re.IGNORECASE)
                            if not _skip_snippet:
                                _effective_ind = _ind_m or _ind_bare_m
                                if _effective_ind:
                                    _start = _effective_ind.start()
                                    _end = _cont_m.start() if (_cont_m and _cont_m.start() > _effective_ind.start()) else min(len(_text), _start + 6000)
                                elif _cov_m2:
                                    _start = _bg_m.start() if (_bg_m and _bg_m.start() < _cov_m2.start()) else _cov_m2.start()
                                    _end = _cont_m.start() if (_cont_m and _cont_m.start() > _start) else min(len(_text), _cov_m2.start() + 6000)
                                elif _section_start is not None:
                                    _start = _section_start
                                    _after_header = _text[_section_start:]
                                    _skip = re.search(r'\n.*?\n', _after_header)
                                    _search_from = _section_start + (_skip.end() if _skip else 50)
                                    _next = re.search(r'\n[A-Z][a-zA-Z\-® ]{2,}\n(?:FDA-approved|Compendial|Limitations)', _text[_search_from:])
                                    _end = _search_from + _next.start() if _next else min(len(_text), _section_start + 6000)
                                    if _cont_m and _cont_m.start() > _start:
                                        _end = min(_end, _cont_m.start())
                                else:
                                    _m = re.search(re.escape(drug_term), _text, re.IGNORECASE)
                                    if _m:
                                        _start = max(0, _m.start() - 100)
                                        _end = _cont_m.start() if (_cont_m and _cont_m.start() > _start) else min(len(_text), _m.start() + 6000)
                                    else:
                                        _start, _end = 0, 3000

                        if not _skip_snippet:
                            _snippet = _text[_start:_end].strip()
                            # Remove leading drug name line if it's just the drug term repeated
                            _snippet = re.sub(r'^' + re.escape(drug_term) + r'\s*\n', '', _snippet, flags=re.IGNORECASE).strip()
                            # Fix known typos in source PDFs
                            _snippet = re.sub(r'Coverage Criteria+a+', 'Coverage Criteria', _snippet)

                            _snippet_html = format_aetna_cpb_html(_snippet, drug_term) if _is_aetna_cpb else format_freetext_html(_snippet)
                            _entry_url = best_entry.get("url","") or pa_criteria_url
                            _pdf_link = f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #f0e0c0;"><a href="{_entry_url}" target="_blank" style="color:#416CA6;font-size:0.75rem;">View full PDF ↗</a></div>' if _entry_url else ""
                            _inner = f'<div style="font-size:0.8rem;line-height:1.6;color:#2a3a4a;">{_snippet_html}</div>{_pdf_link}'
                            pa_criteria_link = (
                                f'<details style="display:block;margin-top:4px;width:100%;">'
                                f'<summary style="display:inline;font-size:0.75rem;color:#856404;font-weight:500;cursor:pointer;text-decoration:none;">PA Criteria ▾</summary>'
                                f'<div style="margin-top:8px;padding:14px 16px;background:#fffbf0;border-left:3px solid #e8913a;border-radius:0 6px 6px 0;max-height:600px;overflow-y:auto;box-sizing:border-box;">'
                                f'{_inner}'
                                f'</div></details>'
                            )
                    else:
                        pa_criteria_link = f'<a href="{pa_criteria_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>' if pa_criteria_url else ""

                elif pa_criteria_url:
                    if pa_criteria_text:
                        # Check for multi-match ambiguity — show link only
                        _ind_m_pre2 = re.search(r'(?:^|\n)Indications\s*\nFDA-approved Indications', pa_criteria_text, re.IGNORECASE)
                        if _ind_m_pre2:
                            _after_pre2 = pa_criteria_text[_ind_m_pre2.end():]
                            _pre_count2 = len(re.findall(r'(?:^|\n)[^\n]*' + re.escape(drug_term) + r'[^\n]*\n', _after_pre2, re.IGNORECASE))
                            if _pre_count2 > 1:
                                pa_criteria_link = f'<a href="{pa_criteria_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>'
                                pa_criteria_text = ""  # skip all further rendering

                    elif pa_criteria_text:
                        def _find_section(text, term):
                            # EBRx: "DrugName (BrandName)\nEBRx PA Criteria" — AR Benefits format
                            ebrx = re.search(
                                r'(?:^|\n).*?' + re.escape(term) + r'.*?\nEBRx PA Criteria',
                                text, re.IGNORECASE
                            )
                            if ebrx:
                                start = ebrx.start()
                                # End at next drug entry (line with "EBRx PA Criteria" again)
                                nxt = re.search(r'\n.+?\nEBRx PA Criteria', text[ebrx.end():], re.IGNORECASE)
                                end = ebrx.end() + nxt.start() if nxt else min(len(text), ebrx.end()+3000)
                                # Stop before Criteria for continuation or Continuation of Therapy
                                cont = re.search(r'\n(?:Criteria for continuation|Continuation of Therapy)\b', text[start:end], re.IGNORECASE)
                                if cont:
                                    end = start + cont.start()
                                return text[start:end], 'ebrx'
                            # BCBS: "Prior Authorization Group DRUGNAME"
                            pa = re.search(r'Prior Authorization Group\s+' + re.escape(term) + r'\b', text, re.IGNORECASE)
                            if pa:
                                nxt = re.search(r'\nPrior Authorization Group\s+', text[pa.end():], re.IGNORECASE)
                                end = pa.end() + nxt.start() if nxt else min(len(text), pa.end()+2000)
                                return text[pa.start():end], 'bcbs'
                            # Humana: "DRUGNAME - FORM (e.g. OZEMPIC - PEN INJECTOR)"
                            dh = re.search(r'(?:^|\n)' + re.escape(term) + r'\s*[-–]\s*[A-Z]', text, re.IGNORECASE|re.MULTILINE)
                            if dh:
                                nxt = re.search(r'\n[A-Z][A-Z\s]+\s*[-–]\s*[A-Z]', text[dh.end():])
                                end = dh.end() + nxt.start() if nxt else min(len(text), dh.end()+2000)
                                return text[dh.start():end], 'humana'
                            # Cigna/UHC: Products Affected bullet list
                            # Only match if drug term appears as a product name (on its own line or in a header)
                            # not just as an incidental mention mid-sentence
                            kw = re.search(r'(?:^|\n)[^\n]*\b' + re.escape(term) + r'\b[^\n]*(?:\n|$)', text, re.IGNORECASE)
                            if kw:
                                caps = list(re.finditer(r'(?:^|\n)([A-Z][A-Z0-9\s\-/,\(\)]{5,})(?:\n|$)', text[:kw.start()], re.MULTILINE))
                                start = caps[-1].start() if caps else max(0, kw.start()-200)
                                nxt = re.search(r'\nPrior Authorization Group\s+[A-Z]|(?:\n[A-Z][A-Z0-9\s\-/,\(\)]{5,}\n)', text[kw.end():])
                                end = kw.end() + nxt.start() if nxt else min(len(text), kw.end()+3000)
                                # Reject if the match is just an incidental mention (term appears in parentheses as an example)
                                _match_line = kw.group().strip()
                                if re.search(r'\(e\.g\.|e\.g\.,|for example', _match_line, re.IGNORECASE):
                                    return None, 'unknown'
                                return text[start:end], 'cigna_uhc'
                            return None, 'unknown'

                        def _cv(v):
                            v = re.sub(r'^[\s\-–:\n]+', '', v).strip()
                            return re.sub(r'\s+', ' ', v).strip()

                        def _empty(v):
                            return not v or v.lower() in ('', '-', 'n/a', 'no', 'none', 'diagnosis')

                        NEXT_LABELS = r'(?:^|\n)(?:Exclusion|Required\s+Medical|Age\s+Restrict|Prescriber|Coverage|Other\s+Criteria|Off[\s\-]?Label|Part\s+B|Prerequisite|Indications|Prior\s+Authorization)\b'

                        section, fmt = _find_section(pa_criteria_text, drug_term)
                        if section is None or fmt == 'unknown':
                            pa_criteria_link = ""
                        if section is not None and fmt != 'unknown':
                            result_rows = []
                            if fmt == 'bcbs':
                                _next_lbl = r'(?=\n(?:Off-label Uses|Exclusion Criteria|Required Medical Information|Age Restrictions|Prescriber Restrictions|Coverage Duration|Other Criteria|Part\s+B|Prior Authorization Group)|$)'
                                for pat, label in [
                                    (r'Exclusion Criteria\s+(.+?)' + _next_lbl, 'Exclusion Criteria'),
                                    (r'Required Medical Information\s+(.+?)' + _next_lbl, 'Required Medical Info'),
                                    (r'Age Restrictions\s+(.+?)' + _next_lbl, 'Age Restrictions'),
                                    (r'Prescriber Restrictions\s+(.+?)' + _next_lbl, 'Prescriber Restrictions'),
                                    (r'Coverage Duration\s+(.+?)' + _next_lbl, 'Coverage Duration'),
                                    (r'Other Criteria\s+(.+?)' + _next_lbl, 'Other Criteria'),
                                    (r'Off-label Uses\s+(.+?)' + _next_lbl, 'Off-Label Uses'),
                                    (r'Part\s+B\s+(.+?)' + _next_lbl, 'Part B Prerequisite'),
                                ]:
                                    m = re.search(pat, section, re.IGNORECASE | re.DOTALL)
                                    val = _cv(m.group(1)) if m else ''
                                    result_rows.append((label, val))

                            elif fmt == 'humana':
                                excl = re.search(r'(?:^|\n)Exclusion\s+(.+?)\nCriteria\b', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Exclusion Criteria', _cv(excl.group(1)) if excl else ''))

                                req = re.search(r'(?:^|\n)Required\s+(.+?)\nMedical\s*(.*?)\nInformation\b', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Required Medical Info', _cv(req.group(1) + ' ' + req.group(2)) if req else ''))

                                # "Age Restriction\n" (no value) or "Age Restrictions\n[val]\n"
                                age = re.search(r'(?:^|\n)Age\s+Restrictions?\n(.+?)\n(?:Prescriber|Coverage|Other|Part)', section, re.IGNORECASE|re.DOTALL)
                                age_val = _cv(age.group(1)) if age else ''
                                result_rows.append(('Age Restrictions', '' if age_val.lower().startswith('prescriber') else age_val))

                                # "Prescriber [val]\nRestriction" (split) or "Prescriber Restriction\n[val]"
                                pres = re.search(r'(?:^|\n)Prescriber\s+(.+?)\nRestrictions?\b', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Prescriber Restrictions', _cv(pres.group(1)) if pres else ''))

                                # "Coverage [val]\nDuration" (split)
                                cov = re.search(r'(?:^|\n)Coverage\s+(.+?)\nDuration\b', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Coverage Duration', _cv(cov.group(1)) if cov else ''))

                                other = re.search(r'(?:^|\n)Other\s+Criteria\s*\n(.+?)\n(?:Part|Prerequisite|Off|Prior|\Z)', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Other Criteria', _cv(other.group(1)) if other else ''))

                                off = re.search(r'(?:^|\n)Off[\s\-]?Label\s+Uses?\n(.+?)\n(?:Exclusion|Required|Age|Prescriber|Coverage|Other|Part|Prior)', section, re.IGNORECASE|re.DOTALL)
                                off_val = _cv(off.group(1)) if off else ''
                                _bad = ('exclusion','required','age','prescriber','coverage','other','part')
                                result_rows.append(('Off-Label Uses', '' if any(off_val.lower().startswith(l) for l in _bad) else off_val))

                                # "Part B [val]\nPrerequisite"
                                partb = re.search(r'(?:^|\n)Part\s+B\s+(.+?)\n(?:Prerequisite|Prior|\Z)', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Part B Prerequisite', _cv(partb.group(1)) if partb else ''))

                            else:  # cigna_uhc
                                excl_split = re.search(r'(?:^|\n)Exclusion\s+(.+?)\nCriteria\b', section, re.IGNORECASE|re.DOTALL)
                                excl_val = ''
                                if excl_split and _cv(excl_split.group(1)).lower() not in ('criteria', ''):
                                    # Also grab any continuation lines after \nCriteria until next label
                                    _after_crit = section[excl_split.end():]
                                    _next_label = re.search(r'(?:^|\n)(?:Required|Age|Prescriber|Coverage|Other|Off[\s\-]?Label|Part\s+B|Prior\s+Auth|Indications)', _after_crit, re.IGNORECASE)
                                    _cont = _after_crit[:_next_label.start()] if _next_label else ''
                                    excl_val = _cv(excl_split.group(1) + ' ' + _cont)
                                result_rows.append(('Exclusion Criteria', excl_val))

                                req_cigna  = re.search(r'(?:^|\n)Required\s+Medical\s+(Diagnosis)\nInformation\b', section, re.IGNORECASE)
                                req_split  = re.search(r'(?:^|\n)Required\s+(.+?)\nMedical\s*(.*?)\nInformation\b', section, re.IGNORECASE|re.DOTALL)
                                req_inline = re.search(r'(?:^|\n)Required\s+Medical\s+(?:Information|Diagnosis)\s+(.+?)(?=\n(?:Age|Prescriber|Coverage|Other|Off|Part|Prior)|\Z)', section, re.IGNORECASE|re.DOTALL)
                                req_val = ''
                                if req_cigna:
                                    req_val = 'Diagnosis'
                                elif req_split and _cv(req_split.group(1)).lower() not in ('medical','information',''):
                                    # Capture everything from after the header until the next label
                                    _after_info = section[req_split.end():]
                                    _next_label = re.search(r'(?:^|\n)(?:Age|Prescriber|Coverage|Other|Off[\s\-]?Label|Part\s+B|Prior\s+Auth)', _after_info, re.IGNORECASE)
                                    _continuation = _after_info[:_next_label.start()] if _next_label else _after_info[:1000]
                                    req_val = _cv(req_split.group(1) + ' ' + req_split.group(2) + ' ' + _continuation)
                                elif req_inline:
                                    req_val = _cv(req_inline.group(1))
                                result_rows.append(('Required Medical Info', req_val))

                                age = re.search(r'(?:^|\n)Age\s+Restrictions?\s+(.+?)(?=\n(?:Prescriber|Coverage|Other|Part|Off)|\Z)', section, re.IGNORECASE|re.DOTALL)
                                age_val = _cv(age.group(1)) if age else ''
                                result_rows.append(('Age Restrictions', '' if age_val.lower().startswith('prescriber') else age_val))

                                pres = re.search(r'(?:^|\n)Prescriber\s+(.+?)\nRestrictions?\b', section, re.IGNORECASE|re.DOTALL)
                                pres2 = re.search(r'(?:^|\n)Prescriber\s+Restrictions?\s+(.+?)(?=\n(?:Coverage|Other|Part|Off)|\Z)', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Prescriber Restrictions', _cv(pres.group(1)) if pres else (_cv(pres2.group(1)) if pres2 else '')))

                                cov = re.search(r'(?:^|\n)Coverage\s+Duration\s+(.+?)(?=\n(?:Other|Part|Off|Prior)|\Z)', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Coverage Duration', _cv(cov.group(1)) if cov else ''))

                                other = re.search(r'(?:^|\n)Other\s+Criteria\s+(.+?)(?=\n(?:Indications|Off|Part|Prior)|\Z)', section, re.IGNORECASE|re.DOTALL)
                                other_val = _cv(other.group(1)) if other else ''
                                result_rows.append(('Other Criteria', '' if other_val.lower().startswith('indications') else other_val))

                                off = re.search(r'(?:^|\n)Off[\s\-]?Label\s+Uses?\n(.+?)(?=\n(?:Exclusion|Required|Age|Prescriber|Coverage|Other|Part|Prior)|\Z)', section, re.IGNORECASE|re.DOTALL)
                                off_val = _cv(off.group(1)) if off else ''
                                _bad = ('exclusion','required','age','prescriber','coverage','other','part b','prerequisite')
                                result_rows.append(('Off-Label Uses', '' if any(off_val.lower().startswith(l) for l in _bad) else off_val))

                                partb = re.search(r'(?:^|\n)Part\s+B\s+(.+?)(?=\n(?:Prerequisite|Prior|\Z))', section, re.IGNORECASE|re.DOTALL)
                                result_rows.append(('Part B Prerequisite', _cv(partb.group(1)) if partb else ''))

                            # Always display all 8 rows, no filtering
                            if fmt == 'ebrx':
                                # EBRx format: free-form narrative, display as-is
                                _freeform = section.strip()
                                _freeform_html = format_freetext_html(_freeform)
                                snippet_html = (
                                    f'<div style="font-size:0.8rem;line-height:1.6;color:#2a3a4a;">{_freeform_html}</div>'
                                    f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #f0e0c0;">'
                                    f'<a href="{pa_criteria_url}" target="_blank" style="color:#416CA6;font-size:0.75rem;">View full PDF ↗</a></div>'
                                )
                            else:
                                ALL_CATEGORIES = [
                                    'Exclusion Criteria',
                                    'Required Medical Info',
                                    'Age Restrictions',
                                    'Prescriber Restrictions',
                                    'Coverage Duration',
                                    'Other Criteria',
                                    'Off-Label Uses',
                                    'Part B Prerequisite',
                                ]
                                result_dict = {}
                                for lbl, val in result_rows:
                                    if lbl not in result_dict or (not result_dict[lbl] and val):
                                        result_dict[lbl] = val
                                display_rows = [(lbl, result_dict.get(lbl, '')) for lbl in ALL_CATEGORIES]

                                rows_html = "".join(
                                    f'<tr>'
                                    f'<td style="padding:5px 10px 5px 0;font-weight:600;color:#734702;vertical-align:top;white-space:nowrap;font-size:0.78rem;border-bottom:1px solid #f5e8d0;">{lbl}</td>'
                                    f'<td style="padding:5px 0 5px 10px;color:#2a3a4a;font-size:0.8rem;line-height:1.6;border-bottom:1px solid #f5e8d0;">{val.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</td>'
                                    f'</tr>'
                                    for lbl, val in display_rows
                                )
                                snippet_html = (
                                    f'<table style="width:100%;border-collapse:collapse;">{rows_html}</table>'
                                    f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #f0e0c0;">'
                                    f'<a href="{pa_criteria_url}" target="_blank" style="color:#416CA6;font-size:0.75rem;">View full PDF ↗</a></div>'
                                )

                            pa_criteria_link = (
                                f'<details style="display:block;margin-top:4px;width:100%;">'
                                f'<summary style="display:inline;font-size:0.75rem;color:#856404;font-weight:500;cursor:pointer;text-decoration:none;">PA Criteria ▾</summary>'
                                f'<div style="margin-top:8px;padding:14px 16px;background:#fffbf0;border-left:3px solid #e8913a;border-radius:0 6px 6px 0;max-height:600px;overflow-y:auto;box-sizing:border-box;">'
                                f'{snippet_html}'
                                f'</div></details>'
                            )
                        else:
                            pa_criteria_link = (
                                f'<a href="{pa_criteria_url}" target="_blank" style="font-size:0.88rem;color:#856404;font-weight:600;text-decoration:none;margin-left:15px;">PA Criteria ↗</a>'
                        )
                else:
                    pa_criteria_link = ""

                pa_html = '<span style="font-size:0.75rem;background:#FFF3CD;color:#856404;padding:2px 8px;border-radius:20px;margin-left:6px;font-weight:500;">PA</span>' if has_pa else ""
                st_html = '<span style="font-size:0.75rem;background:#eaf2d7;color:#478000;padding:2px 8px;border-radius:20px;margin-left:6px;font-weight:500;">ST</span>' if has_st else ""

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
            plan_link_no_underline = ('<a href="' + url + '" target="_blank" style="color:var(--ink);text-decoration:none;">' + plan_label + '</a>') if url else plan_label

            _cards_list.append((plan_label.lower(), (
                '<div class="' + card_class + '">'
                '<div class="plan-label" style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">'
                + plan_link_no_underline + ' &nbsp; ' + tag + tier_html + pa_html + st_html
                + ('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + pa_criteria_link if pa_criteria_link else '')
                + '</div>'
                '</div>'
            )))

        # ── PA-only results: plans with PA criteria but not in formulary ──────────
        # Build into a dict keyed by plan name so we can sort everything together
        _pa_only_cards = {}  # plan_name -> card_html
        _pa_only_style = 'color:#856404;font-weight:600;font-size:0.88rem;'
        for _pa_plan_key, _pa_entries in _pa_entry_lookup.items():
            if _pa_plan_key in _seen_plans:
                continue
            # Apply plan word filter — skip PA-only cards that don't match
            if plan_words_filter and not all(
                w in _pa_plan_key for w in plan_words_filter
            ):
                continue
            _best = None
            _best_score = 0
            _criteria_terms = re.compile(r'coverage criteria|authorization|indications?|required medical|exclusion criteria|step therapy|prior auth', re.IGNORECASE)
            for _pe in _pa_entries:
                _hay = (_pe["drug_label"] + " " + _pe["text"]).lower()
                if drug_term.lower() not in _hay:
                    continue
                _score = (drug_term.lower() in _pe["drug_label"].lower()) * 2 + bool(_criteria_terms.search(_pe["text"])) * 3 + (drug_term.lower() in _pe["text"][:300].lower()) * 4
                if _score > _best_score:
                    _best_score = _score
                    _best = _pe
            if not _best:
                continue
            _text = _best["text"]
            _cov_m = re.search(r'(?:^|\n)(?:\d+\.\s*)?Coverage Criteria', _text, re.IGNORECASE)
            _section_start = None
            for _pat in [
                r'(?:^|\n)(' + re.escape(drug_term) + r'\s*\nFDA)',
                r'(?:^|\n)(' + re.escape(drug_term) + r'\s*\n)',
                r'(?:^|\n)(' + re.escape(drug_term) + r'\s+FDA)',
            ]:
                _sm = re.search(_pat, _text, re.IGNORECASE)
                if _sm:
                    _section_start = _sm.start()
                    break
            if _cov_m:
                _section_start = _cov_m.start()
                _end = min(len(_text), _section_start + 3000)
            elif _section_start is not None:
                _ah = _text[_section_start:]
                _sk = re.search(r'\n.*?\n', _ah)
                _sf = _section_start + (_sk.end() if _sk else 50)
                _nx = re.search(r'\n[A-Z][a-zA-Z\-® ]{2,}\n(?:FDA-approved|Compendial|Limitations)', _text[_sf:])
                _end = _sf + _nx.start() if _nx else min(len(_text), _section_start + 3000)
            else:
                _km = re.search(re.escape(drug_term), _text, re.IGNORECASE)
                _section_start = max(0, _km.start() - 100) if _km else 0
                _end = min(len(_text), _section_start + 3000)
            _snip = _text[_section_start:_end].strip()
            _snip = re.sub(r'^' + re.escape(drug_term) + r'\s*\n', '', _snip, flags=re.IGNORECASE).strip()
            _snip_html = format_freetext_html(_snip)
            _eu = _best.get("url","")
            _pdf_link = f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #f0e0c0;"><a href="{_eu}" target="_blank" style="color:#416CA6;font-size:0.75rem;">View full PDF ↗</a></div>' if _eu else ""
            _pa_link = (
                f'<details style="display:block;margin-top:4px;width:100%;">'
                f'<summary style="display:inline;font-size:0.75rem;color:#856404;font-weight:500;cursor:pointer;text-decoration:none;">PA Criteria ▾</summary>'
                f'<div style="margin-top:8px;padding:14px 16px;background:#fffbf0;border-left:3px solid #e8913a;border-radius:0 6px 6px 0;max-height:600px;overflow-y:auto;box-sizing:border-box;">'
                f'<div style="font-size:0.8rem;line-height:1.6;color:#2a3a4a;">{_snip_html}</div>{_pdf_link}'
                f'</div></details>'
            )
            _display_name = next(
                (k for k in _pa_lookup.keys() if _normalize_plan(k) == _pa_plan_key),
                _pa_plan_key.replace('-', ' ').title()
            )
            _pa_only_cards[_display_name.lower()] = (
                '<div class="result-card found">'
                f'<div class="plan-label" style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">'
                f'<span style="{_pa_only_style}">{_display_name}</span>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{_pa_link}</div>'
                '</div>'
            )

        # Add PA-only cards and sort everything together
        for _k, _c in _pa_only_cards.items():
            _cards_list.append((_k, _c))
        _cards_list.sort(key=lambda x: x[0])
        cards_html = ''.join(c for _, c in _cards_list)

        st.markdown(f'<div class="results-container">{cards_html}</div>', unsafe_allow_html=True)

# ── Formularies ──────────────────────────────────────────────────────
if not (go and keyword.strip()):
    st.markdown("<div style='height:40vh'></div>", unsafe_allow_html=True)
with st.expander("Useful Links"):
    _useful_links = []
    _ul_csv = Path("formulary_links.csv")
    if _ul_csv.exists():
        import csv as _csv3
        with open(_ul_csv, newline="", encoding="utf-8-sig", errors="replace") as _ulf:
            for _ulrow in _csv3.reader(_ulf):
                if len(_ulrow) >= 12 and _ulrow[10].strip() and _ulrow[11].strip().startswith("http") and _ulrow[10].strip().lower() != "links":
                    _useful_links.append({"label": _ulrow[10].strip(), "url": _ulrow[11].strip()})
    if _useful_links:
        ul_rows_html = "".join(
            f'<tr><td style="padding:7px 14px;border-bottom:1px solid #edf1f5;">'
            f'<a href="{lnk["url"]}" target="_blank" style="color:#416CA6;font-weight:500;text-decoration:none;border-bottom:1px solid #416CA6;">{lnk["label"]}</a>'
            f'</td></tr>'
            for lnk in _useful_links
        )
        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;font-size:0.9rem;background:white;color:#0f1923;">'
            f'<tbody>{ul_rows_html}</tbody></table>',
            unsafe_allow_html=True
        )

with st.expander("Drug Tiers Explained"):
    st.components.v1.html("""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"><style>*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}body{background:transparent;font-family:'DM Sans',sans-serif;padding:8px 0;}.card{width:100%;background:#ffffff;border:1px solid #e4dfd8;border-radius:24px;overflow:hidden;box-shadow:0 4px 32px rgba(0,0,0,0.08);position:relative;}.tiers{padding:16px 28px 24px;display:flex;flex-direction:column;gap:10px;}.tier{display:grid;grid-template-columns:64px 1fr auto;align-items:start;border-radius:12px;overflow:hidden;border:1px solid transparent;}.tier-num{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px 0;font-family:'DM Serif Display',serif;font-size:26px;line-height:1;gap:3px;}.tier-word{font-family:'DM Sans',sans-serif;font-size:8px;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;opacity:0.6;}.tier-body{padding:10px 16px;border-left:1px solid rgba(0,0,0,0.06);}.tier-label{font-size:13px;font-weight:500;margin-bottom:3px;letter-spacing:0.01em;}.tier-desc{font-size:12px;font-weight:300;line-height:1.55;margin-bottom:5px;}.tier-example{font-size:10.5px;font-style:italic;opacity:0.5;}.tier-cost{padding:10px 14px 10px 0;display:flex;align-items:flex-start;justify-content:flex-end;}.cost-pill{font-size:11px;font-weight:500;padding:4px 10px;border-radius:20px;white-space:nowrap;letter-spacing:0.02em;}.t1{background:#f0f7e8;border-color:#d4eab8;}.t1 .tier-num{background:#e4f2d0;color:#3B6D11;}.t1 .tier-label{color:#27500A;}.t1 .tier-desc{color:#557a30;}.t1 .cost-pill{background:#d4eab8;color:#3B6D11;}.t2{background:#edf4fc;border-color:#c5ddf5;}.t2 .tier-num{background:#daeaf8;color:#185FA5;}.t2 .tier-label{color:#0c447c;}.t2 .tier-desc{color:#3a6e9e;}.t2 .cost-pill{background:#c5ddf5;color:#185FA5;}.t3{background:#fdf6e8;border-color:#f5e0a8;}.t3 .tier-num{background:#faefd0;color:#854F0B;}.t3 .tier-label{color:#633806;}.t3 .tier-desc{color:#9a6820;}.t3 .cost-pill{background:#f5e0a8;color:#854F0B;}.t4{background:#fdf0eb;border-color:#f5cebb;}.t4 .tier-num{background:#fae2d5;color:#993C1D;}.t4 .tier-label{color:#712B13;}.t4 .tier-desc{color:#a35030;}.t4 .cost-pill{background:#f5cebb;color:#993C1D;}.t5{background:#fdf0f0;border-color:#f5c0c0;}.t5 .tier-num{background:#fad8d8;color:#A32D2D;}.t5 .tier-label{color:#791F1F;}.t5 .tier-desc{color:#a84040;}.t5 .cost-pill{background:#f5c0c0;color:#A32D2D;}.corner-tag{position:absolute;bottom:14px;right:24px;font-size:9px;letter-spacing:0.15em;text-transform:uppercase;color:#d8d2ca;font-weight:500;}@media(max-width:520px){.tiers{padding:10px 12px 18px;gap:7px;}.tier{grid-template-columns:44px 1fr auto;}.tier-num{font-size:18px;padding:10px 0;}.tier-body{padding:8px 10px;}.tier-label{font-size:11px;}.tier-desc{font-size:10px;}.tier-example{font-size:9px;}.cost-pill{font-size:9px;padding:3px 7px;}.tier-cost{padding:8px 6px 8px 0;}}</style></head><body><div class="card"><div class="tiers"><div class="tier t1"><div class="tier-num">1<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Generic drugs</div><div class="tier-desc">Same active ingredient as the brand name.</div><div class="tier-example">metformin · lisinopril · amoxicillin</div></div><div class="tier-cost"><span class="cost-pill">$0 – $15</span></div></div><div class="tier t2"><div class="tier-num">2<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Preferred brand-name</div><div class="tier-desc">Insurer has negotiated a deal with drug company. Still a decent copay.</div><div class="tier-example">Lipitor · Zoloft · Synthroid</div></div><div class="tier-cost"><span class="cost-pill">$30 – $60</span></div></div><div class="tier t3"><div class="tier-num">3<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Non-preferred brand-name</div><div class="tier-desc">Insurer has not negotiated a deal with drug company.</div><div class="tier-example">Newer name-brands</div></div><div class="tier-cost"><span class="cost-pill">$60 – $100+</span></div></div><div class="tier t4"><div class="tier-num">4<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Specialty drugs</div><div class="tier-desc">Complex conditions. Often 20–30% coinsurance instead of a flat copay.</div><div class="tier-example">Humira · Enbrel · MS &amp; cancer drugs</div></div><div class="tier-cost"><span class="cost-pill">20–30% cost</span></div></div><div class="tier t5"><div class="tier-num">5<span class="tier-word">Tier</span></div><div class="tier-body"><div class="tier-label">Very high-cost specialty</div><div class="tier-desc">Highest cost-sharing. May require step therapy.</div><div class="tier-example">Gene therapies · biologic infusions</div></div><div class="tier-cost"><span class="cost-pill">Highest</span></div></div></div><div class="corner-tag">Health Plan Reference</div></div><script>function resize(){var h=document.body.scrollHeight;window.parent.postMessage({type:'streamlit:setFrameHeight',height:h},'*');}window.addEventListener('load',resize);window.addEventListener('resize',resize);</script></body></html>""", height=560, scrolling=False)
with st.expander("Formularies"):
    _vaf_plans = []
    _vaf_seen_tricare = False
    if _pa_csv.exists():
        with open(_pa_csv, newline="", encoding="utf-8-sig", errors="replace") as _vf:
            for _vrow in _csv.reader(_vf):
                if len(_vrow) >= 5 and _vrow[4].strip().startswith("http"):
                    _vname = _vrow[3].strip()
                    _vurl  = _vrow[4].strip()
                    if "tricare" in _vname.lower():
                        if _vaf_seen_tricare:
                            continue
                        _vaf_seen_tricare = True
                        _vurl = "https://www.express-scripts.com/frontend/open-enrollment/tricare/fst/#/"
                    _vaf_plans.append({"plan_name": _vname, "url": _vurl})
    _vaf_display = sorted(_vaf_plans, key=lambda x: x["plan_name"].lower()) if _vaf_plans else sorted(entries, key=lambda e: e.get("plan_name","").lower())
    rows_html = "".join(
        f'<tr><td style="padding:7px 14px;border-bottom:1px solid #edf1f5;color:#0f1923;">{p.get("plan_name","")}</td>'
        f'<td style="padding:7px 14px;border-bottom:1px solid #edf1f5;"><a href="{p.get("url","")}" target="_blank" style="color:#0d7a6e;">{p.get("url","")}</a></td></tr>'
        for p in _vaf_display
    )
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:0.85rem;background:white;color:#0f1923;">'
        f'<thead><tr>'
        f'<th style="padding:10px 14px;text-align:left;border-bottom:2px solid #dde4eb;color:#1e3448;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">Plan</th>'
        f'<th style="padding:10px 14px;text-align:left;border-bottom:2px solid #dde4eb;color:#1e3448;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">URL</th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True
    )

with st.expander("Prior Authorizations"):
    _pa_plans = sorted(
        [{"plan_name": k, "pa_url": v} for k, v in _pa_lookup.items()],
        key=lambda x: x["plan_name"].lower()
    )
    pa_rows_html = "".join(
        f'<tr><td style="padding:7px 14px;border-bottom:1px solid #edf1f5;color:#0f1923;">{p["plan_name"]}</td>'
        f'<td style="padding:7px 14px;border-bottom:1px solid #edf1f5;"><a href="{p["pa_url"]}" target="_blank" style="color:#0d7a6e;">{p["pa_url"]}</a></td></tr>'
        for p in _pa_plans
    )
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:0.85rem;background:white;color:#0f1923;">'
        f'<thead><tr>'
        f'<th style="padding:10px 14px;text-align:left;border-bottom:2px solid #dde4eb;color:#1e3448;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">Plan</th>'
        f'<th style="padding:10px 14px;text-align:left;border-bottom:2px solid #dde4eb;color:#1e3448;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">PA URL</th></tr></thead>'
        f'<tbody>{pa_rows_html}</tbody></table>',
        unsafe_allow_html=True
    )
