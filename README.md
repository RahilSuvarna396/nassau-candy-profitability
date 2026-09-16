# Nassau Candy — Product Line Profitability & Margin Performance Dashboard

An interactive Streamlit dashboard for the Nassau Candy Distributor profitability analysis.

## Contents
- `app.py` — the dashboard application
- `nassau_candy_cleaned.csv` — the cleaned dataset used by the app
- `requirements.txt` — Python dependencies

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## What's inside

- **Product Profitability Overview** — profit leaderboard, profit contribution share, full product detail table with margin-colored heatmap.
- **Division Performance Dashboard** — revenue vs. profit contribution by division, average margin by division, margin distribution (box plot), and a factory/sourcing view.
- **Cost vs Margin Diagnostics** — cost-ratio-vs-sales scatter, automated margin-risk flags (below-average margin + above-average cost ratio), and a repricing-priority chart.
- **Profit Concentration (Pareto) Analysis** — product-level Pareto chart with an 80% cumulative-profit marker, and geographic (state-level) revenue concentration for comparison.

## Interactive controls (sidebar)
- Order date range selector
- Division filter (multi-select)
- Minimum gross-margin threshold slider (filters out low-margin products)
- Product name search

## Deploying

To share this as a live link, deploy the folder to [Streamlit Community Cloud](https://share.streamlit.io) (point it at `app.py`), or run it on any host that supports Python + Streamlit.
