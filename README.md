# UAMS Formulary Drug Search

A Streamlit web app that searches across all payer formulary PDFs for any drug or keyword.

## What it does
- Reads `formulary_links.csv` (Column D = plan name, Column E = URL)
- For each URL, downloads the PDF and extracts its text
- Searches for your keyword and returns only the plans that contain it
- Results are color-coded and downloadable as CSV

## How to deploy (Streamlit Cloud — free, no install for end users)

1. Create a free account at https://streamlit.io
2. Push these files to a GitHub repo:
   - `app.py`
   - `requirements.txt`
   - `formulary_links.csv`
3. In Streamlit Cloud, click **New app** → connect your GitHub repo → select `app.py`
4. Click **Deploy** — you'll get a public URL like `https://yourname-formulary.streamlit.app`
5. Share that URL with anyone — no install needed on their end

## How to run locally (for development)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## CSV format expected
The app reads 4 columns (no strict header names required):
- Column A: plan_group
- Column B: payer  
- Column C: plan_name  ← returned in results
- Column D: url        ← followed and searched

## Notes
- PDFs are downloaded in memory (not saved to disk)
- Non-PDF URLs (web pages) are also searched via text content
- 404 and error URLs are flagged and can be shown/hidden via sidebar toggle
- Results can be downloaded as CSV after each search
