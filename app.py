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
    [data-testid="stAppViewContainer"] { background: #f4f6f9; }
    .header-bar {
        background: linear-gradient(90deg, #1b4f72, #2e86c1);
        color: white; padding: 22px 28px;
        border-radius: 10px; margin-bottom: 24px;
    }
    .header-bar h1 { margin: 0; font-size: 1.8rem; color: white; }
    .header-bar p  { margin: 4px 0 0; opacity: 0.85; font-size: 0.95rem; }
    .result-card {
        background: white; border-left: 5px solid #2e86c1;
        padding: 14px 18px; margin: 8px 0;
        border-radius: 0 8px 8px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .result-card.found { border-left-color: #1e8449; }
    .result-card.error { border-left-color: #e74c3c; }
    .plan-label  { font-size: 1.05rem; font-weight: 700; color: #1a1a1a; }
    .payer-label { font-size: 0.85rem; color: #555; margin-bottom: 4px; }
    .tag-found { background:#d5f5e3; color:#1e8449; padding:2px 9px; border-radius:12px; font-size:0.78rem; font-weight:700; }
    .tag-not   { background:#fdecea; color:#c0392b; padding:2px 9px; border-radius:12px; font-size:0.78rem; font-weight:700; }
    .tag-error { background:#fff3cd; color:#856404; padding:2px 9px; border-radius:12px; font-size:0.78rem; }
    .url-link  { font-size: 0.78rem; color: #2e86c1; word-break: break-all; }
    .summary-box { display:flex; gap:32px; background:white; border-radius:10px; padding:18px 22px; margin-bottom:20px; box-shadow:0 1px 4px rgba(0,0,0,0.07); }
    .stat { text-align:center; }
    .stat-num { font-size:2rem; font-weight:800; color:#2e86c1; }
    .stat-num.green { color:#1e8449; }
    .stat-label { font-size:0.78rem; color:#777; }
    .index-info { font-size:0.75rem; color:#aaa; margin-top:6px; }
    [data-testid="stExpander"] summary p { color: #001f5b !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h1>💊 Formulary Drug Search</h1>
  <p>Search most insurance formularies, results will be displayed with links.</p>
</div>
""", unsafe_allow_html=True)

# ── Load index ────────────────────────────────────────────────────────────────
INDEX_FILE = "formulary_index.json"

@st.cache_data
def load_index(path):
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

index     = load_index(INDEX_FILE)
entries   = index["entries"]
built_at  = index.get("built_at", "unknown")

try:
    built_nice = datetime.fromisoformat(built_at.replace("Z","")).strftime("%B %d, %Y")
except Exception:
    built_nice = built_at

# ── Search function ───────────────────────────────────────────────────────────
def search_entries(entries, keyword, group_filter, payer_filter):
    pattern = re.compile(r'\b' + re.escape(keyword.strip().lower()) + r'\b')
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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Options")


    st.divider()

    st.divider()
    ok_count = sum(1 for e in entries if e.get("status") == "ok")
    st.caption("🗄️ Search Index")
    st.metric("Formularies indexed", ok_count)
    st.markdown(f'<div class="index-info">Built: {built_nice}</div>', unsafe_allow_html=True)
    st.caption("⚡ All searches run locally — no network calls.")

# ── Search UI ─────────────────────────────────────────────────────────────────
with st.form("search_form"):
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        keyword = st.text_input("Drug / keyword", placeholder="e.g.  metformin   or   ozempic   or   GLP-1", label_visibility="collapsed")
    with col_btn:
        go = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

if not go or not keyword.strip():
    with st.expander("📋 View all indexed formularies"):
        st.dataframe(pd.DataFrame([{
            "Plan": e.get("plan_name",""),
            "URL":  e.get("url",""),
        } for e in entries]), use_container_width=True)
    st.stop()

# ── Run search ────────────────────────────────────────────────────────────────
results       = search_entries(entries, keyword, "All Plan Groups", "All Payers")
found_results = sorted([r for r in results if r["found"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
missed        = sorted([r for r in results if not r["found"] and not r["search_error"]], key=lambda r: (r.get("plan_name") or r.get("payer") or r.get("plan_group","")).lower())
errors        = [r for r in results if r["search_error"]]

st.markdown(f"""
<div class="summary-box">
  <div class="stat"><div class="stat-num green">{len(found_results)}</div><div class="stat-label">Found In</div></div>
  <div class="stat"><div class="stat-num">{len(results)}</div><div class="stat-label">Searched</div></div>
  <div class="stat"><div class="stat-num">{len(errors)}</div><div class="stat-label">Errors</div></div>
</div>
""", unsafe_allow_html=True)

if found_results:
    st.success(f'✅ **"{keyword.strip()}"** found in **{len(found_results)}** formulary/formularies.')
else:
    st.error(f'❌ **"{keyword.strip()}"** was not found in any formulary.')

st.divider()

for r in (found_results + [] + []):
    plan_label = r.get("plan_name") or r.get("payer") or r.get("plan_group","")
    payer_line = r.get("payer","") if r.get("plan_name") else ""
    if r["found"]:
        card_class, tag = "result-card found", '<span class="tag-found">✅ FOUND</span>'
    elif r.get("search_error"):
        card_class, tag = "result-card error", f'<span class="tag-error">⚠️ {r["search_error"]}</span>'
    else:
        card_class, tag = "result-card", '<span class="tag-not">❌ Not found</span>'
    st.markdown(f"""
    <div class="{card_class}">
      <div class="payer-label">{payer_line}</div>
      <div class="plan-label">{plan_label} &nbsp; {tag}</div>
      <div class="url-link"><a href="{r.get('url','')}" target="_blank">{r.get('url','')}</a></div>
    </div>""", unsafe_allow_html=True)
