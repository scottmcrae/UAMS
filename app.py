import streamlit as st
import pandas as pd
import requests
import pdfplumber
import io
import time
import re
from urllib.parse import urlparse

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UAMS Formulary Search",
    page_icon="💊",
    layout="wide",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #f4f6f9; }
    .header-bar {
        background: linear-gradient(90deg, #1b4f72, #2e86c1);
        color: white;
        padding: 22px 28px;
        border-radius: 10px;
        margin-bottom: 24px;
    }
    .header-bar h1 { margin: 0; font-size: 1.8rem; color: white; }
    .header-bar p  { margin: 4px 0 0; opacity: 0.85; font-size: 0.95rem; }
    .result-card {
        background: white;
        border-left: 5px solid #2e86c1;
        padding: 14px 18px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .result-card.found  { border-left-color: #1e8449; }
    .result-card.error  { border-left-color: #e74c3c; }
    .result-card.skip   { border-left-color: #aaa; }
    .plan-label   { font-size: 1.05rem; font-weight: 700; color: #1a1a1a; }
    .payer-label  { font-size: 0.85rem; color: #555; margin-bottom: 4px; }
    .tag-found  { background:#d5f5e3; color:#1e8449; padding:2px 9px; border-radius:12px; font-size:0.78rem; font-weight:700; }
    .tag-not    { background:#fdecea; color:#c0392b; padding:2px 9px; border-radius:12px; font-size:0.78rem; font-weight:700; }
    .tag-skip   { background:#eee;    color:#777;    padding:2px 9px; border-radius:12px; font-size:0.78rem; }
    .tag-error  { background:#fdecea; color:#c0392b; padding:2px 9px; border-radius:12px; font-size:0.78rem; }
    .url-link   { font-size: 0.78rem; color: #2e86c1; word-break: break-all; }
    .summary-box {
        background: white;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        display: flex;
        gap: 32px;
    }
    .stat { text-align: center; }
    .stat-num  { font-size: 2rem; font-weight: 800; color: #2e86c1; }
    .stat-num.green { color: #1e8449; }
    .stat-label { font-size: 0.78rem; color: #777; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h1>💊 UAMS Formulary Drug Search</h1>
  <p>Search across all payer formulary PDFs — enter a drug name and we'll find every formulary that lists it.</p>
</div>
""", unsafe_allow_html=True)

# ── Load CSV ─────────────────────────────────────────────────────────────────
CSV_FILE = "formulary_links.csv"

@st.cache_data
def load_csv(path):
    df = pd.read_csv(path, header=0)
    # Columns: plan_group(A), payer(B), plan_name(C=col2), url(D=col3)
    df.columns = ["plan_group", "payer", "plan_name", "url"]
    df = df.fillna("")
    df = df[df["url"].str.startswith("http")]   # only rows with real URLs
    df = df.reset_index(drop=True)
    return df

try:
    df = load_csv(CSV_FILE)
except Exception:
    uploaded = st.file_uploader("Upload formulary_links.csv", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded, header=0)
        df.columns = ["plan_group", "payer", "plan_name", "url"]
        df = df.fillna("")
        df = df[df["url"].str.startswith("http")].reset_index(drop=True)
    else:
        st.info("📂 Place `formulary_links.csv` in the same folder as `app.py`, or upload it above.")
        st.stop()

# ── Helpers ───────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def is_pdf_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")

def fetch_and_search(url: str, keyword: str) -> dict:
    """
    Fetch a URL, extract text (PDF or HTML), and search for keyword.
    Returns dict with keys: found (bool), error (str|None), note (str)
    """
    keyword_lower = keyword.strip().lower()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, stream=True)
        if resp.status_code == 404:
            return {"found": False, "error": "404 Not Found", "note": ""}
        if resp.status_code != 200:
            return {"found": False, "error": f"HTTP {resp.status_code}", "note": ""}

        content_type = resp.headers.get("Content-Type", "").lower()
        raw = resp.content

        # ── PDF ──
        if "pdf" in content_type or is_pdf_url(url):
            text = ""
            try:
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
            except Exception as e:
                return {"found": False, "error": f"PDF parse error: {e}", "note": ""}

            found = bool(re.search(r'\b' + re.escape(keyword_lower) + r'\b',
                                   text.lower()))
            return {"found": found, "error": None, "note": "PDF"}

        # ── HTML / web page ──
        else:
            text = resp.text.lower()
            found = keyword_lower in text
            return {"found": found, "error": None, "note": "Web page (non-PDF)"}

    except requests.exceptions.Timeout:
        return {"found": False, "error": "Timeout", "note": ""}
    except Exception as e:
        return {"found": False, "error": str(e)[:80], "note": ""}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Options")

    all_groups = sorted(set(g for g in df["plan_group"].unique() if g))
    group_opts = ["All Plan Groups"] + all_groups
    sel_group  = st.selectbox("Filter by Plan Group", group_opts)

    all_payers = sorted(set(p for p in df["payer"].unique() if p))
    if sel_group != "All Plan Groups":
        all_payers = sorted(set(
            p for p in df[df["plan_group"] == sel_group]["payer"].unique() if p
        ))
    payer_opts = ["All Payers"] + all_payers
    sel_payer  = st.selectbox("Filter by Payer", payer_opts)

    st.divider()
    show_not_found = st.checkbox("Show 'Not Found' results", value=False)
    show_errors    = st.checkbox("Show errors / skipped", value=False)

    st.divider()
    st.caption("📋 Loaded formularies")
    st.metric("Total links", len(df))


# ── Main search UI ────────────────────────────────────────────────────────────
col_search, col_btn = st.columns([5, 1])
with col_search:
    keyword = st.text_input(
        "Drug / keyword to search",
        placeholder="e.g.  metformin   or   ozempic   or   GLP-1",
        label_visibility="collapsed",
    )
with col_btn:
    go = st.button("🔍 Search", use_container_width=True, type="primary")

if not go or not keyword.strip():
    st.markdown("#### 👆 Enter a drug name above and click **Search**")
    with st.expander("📋 View all formulary links loaded"):
        display_df = df[["plan_group","payer","plan_name","url"]].copy()
        display_df.columns = ["Plan Group","Payer","Plan Name","URL"]
        st.dataframe(display_df, use_container_width=True)
    st.stop()

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if sel_group != "All Plan Groups":
    filtered = filtered[filtered["plan_group"] == sel_group]
if sel_payer != "All Payers":
    filtered = filtered[filtered["payer"] == sel_payer]

if filtered.empty:
    st.warning("No formulary links match your filter selection.")
    st.stop()

# ── Run search ────────────────────────────────────────────────────────────────
st.markdown(f"### 🔍 Searching for **\"{keyword.strip()}\"** across {len(filtered)} formularies…")

progress_bar  = st.progress(0)
status_text   = st.empty()
results_area  = st.container()

results = []
total = len(filtered)

for i, (_, row) in enumerate(filtered.iterrows()):
    url       = row["url"]
    payer     = row["payer"] or row["plan_group"]
    plan_name = row["plan_name"]
    display_name = plan_name if plan_name else payer

    status_text.markdown(f"⏳ Checking **{display_name}** ({i+1}/{total})…")
    progress_bar.progress((i + 1) / total)

    result = fetch_and_search(url, keyword.strip())
    results.append({
        "payer":       payer,
        "plan_group":  row["plan_group"],
        "plan_name":   plan_name,
        "url":         url,
        "found":       result["found"],
        "error":       result["error"],
        "note":        result["note"],
    })
    time.sleep(0.15)

progress_bar.empty()
status_text.empty()

# ── Summary stats ─────────────────────────────────────────────────────────────
found_count  = sum(1 for r in results if r["found"])
error_count  = sum(1 for r in results if r["error"])
checked      = sum(1 for r in results if not r["error"])

st.markdown(f"""
<div class="summary-box">
  <div class="stat"><div class="stat-num green">{found_count}</div><div class="stat-label">Formularies Found</div></div>
  <div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Total Searched</div></div>
  <div class="stat"><div class="stat-num">{error_count}</div><div class="stat-label">Errors / Skipped</div></div>
</div>
""", unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────
if found_count == 0:
    st.error(f"❌ **\"{keyword.strip()}\"** was not found in any formulary PDF.")
else:
    st.success(f"✅ **\"{keyword.strip()}\"** found in **{found_count}** formulary/formularies.")

# Sort: found first, then not found, then errors
results_sorted = (
    [r for r in results if r["found"]] +
    [r for r in results if not r["found"] and not r["error"]] +
    [r for r in results if r["error"]]
)

# Download results as CSV
import csv as csv_mod
out_rows = []
for r in results_sorted:
    if r["found"]:
        out_rows.append({
            "plan_group": r["plan_group"],
            "payer":      r["payer"],
            "plan_name":  r["plan_name"],
            "url":        r["url"],
            "result":     "FOUND",
        })

if out_rows:
    out_df = pd.DataFrame(out_rows)
    csv_bytes = out_df.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Download found results as CSV",
        data=csv_bytes,
        file_name=f"formulary_search_{keyword.strip().replace(' ','_')}.csv",
        mime="text/csv",
    )

st.divider()

for r in results_sorted:
    plan_label = r["plan_name"] if r["plan_name"] else (r["payer"] or r["plan_group"])
    payer_line = r["payer"] if r["plan_name"] else ""

    if r["found"]:
        card_class = "result-card found"
        tag = '<span class="tag-found">✅ FOUND</span>'
    elif r["error"]:
        if not show_errors:
            continue
        card_class = "result-card error"
        tag = f'<span class="tag-error">⚠️ {r["error"]}</span>'
    else:
        if not show_not_found:
            continue
        card_class = "result-card"
        tag = '<span class="tag-not">❌ Not found</span>'

    st.markdown(f"""
    <div class="{card_class}">
      <div class="payer-label">{payer_line}</div>
      <div class="plan-label">{plan_label} &nbsp; {tag}</div>
      <div class="url-link"><a href="{r['url']}" target="_blank">{r['url']}</a></div>
    </div>
    """, unsafe_allow_html=True)
