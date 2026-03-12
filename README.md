# 🏛️ CitizenLens — AI-Powered Policy Comment Intelligence Platform

> **Open Government Hackathon 2025** &nbsp;|&nbsp; Team Entry &nbsp;|&nbsp; v2.0.0

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![TextBlob](https://img.shields.io/badge/NLP-TextBlob-green.svg)](https://textblob.readthedocs.io)

---

## 🎯 Problem Statement

Governments receive thousands of citizen comments on policies every week.  
Less than 3% of these are ever read by a policymaker (Open Government Partnership, 2023).  
The rest sit unread — wasting public trust and policy insight.

**CitizenLens solves this.**

---

## 💡 Solution

CitizenLens is a real-time web platform that:

1. **Accepts live citizen comments** via a public submission form
2. **Runs an NLP pipeline** — scoring sentiment, subjectivity, and clustering by policy topic
3. **Visualises everything** — 6 chart types, per-theme word clouds, trend timeline
4. **Exports a structured Policy Insight Report** — ready for policymakers in one click

---

## 🧠 NLP Pipeline Architecture

```
INPUT
  ├── Live comment form (any citizen)
  ├── CSV bulk upload (existing feedback)
  └── 50-row self-generated seed dataset

      ↓

PROCESSING
  ├── TextBlob polarity score  (−1.0 → +1.0)
  ├── TextBlob subjectivity score  (0.0 → 1.0)
  ├── Sentiment label  (Positive / Neutral / Negative)
  ├── Keyword-frequency topic clustering  (6 policy domains)
  └── Confidence score  (% of domain keywords matched)

      ↓

OUTPUT
  ├── 5 KPI metrics  (live, filter-reactive)
  ├── 6 chart types  (sentiment, themes, polarity histogram,
  │                   stacked breakdown, scatter, timeline)
  ├── Per-theme word clouds  (one per policy domain)
  ├── Interactive filters  (theme, sentiment, polarity, subjectivity)
  ├── Colour-coded data table
  ├── CSV export  (enriched dataset)
  └── Policy Insight Report  (.txt, formatted for policymakers)
```

---

## 🚀 Features

| Feature | Description |
|---|---|
| ✍️ **Live comment submission** | Citizens type and submit feedback — instantly analyzed |
| 📂 **CSV bulk upload** | Import any existing feedback CSV with a `comment` column |
| 🎭 **Sentiment analysis** | TextBlob polarity + subjectivity scoring |
| 🗂️ **Topic clustering** | 6 policy domains via keyword-frequency pipeline |
| 📊 **6 chart types** | Sentiment bar, theme bar, polarity histogram, stacked breakdown, scatter, timeline |
| ☁️ **Per-theme word clouds** | One cloud per policy domain, distinct colour palette |
| 🔬 **Subjectivity scatter** | Polarity vs subjectivity — shows opinion vs fact balance |
| 📅 **Trend timeline** | Weekly sentiment trend over submission dates |
| 🌙 **Light / Dark theme** | Full CSS theme swap — all text visible in both modes |
| 💾 **CSV export** | Enriched dataset with all NLP scores |
| 📄 **Policy Insight Report** | Formatted .txt report with recommendations |
| 📱 **Responsive layout** | Works on desktop, tablet, and mobile |

---

## 📊 Dataset

The seed dataset is **50 original, hand-authored comments** covering six policy domains.

All text was written specifically for this project — **not scraped, copied, or sourced from any restricted or government-only dataset**. This satisfies the hackathon requirement:

> *"Teams must use only publicly available or self-generated datasets."*

The dataset is in `data/seed_comments.csv`.

### Policy Domains Covered

| Domain | Comments | Focus Areas |
|---|---|---|
| Economy & Tax | 8 | Business grants, tax relief, economic zones |
| Infrastructure | 10 | Roads, cycling, public transit, bridges |
| Housing & Planning | 9 | Affordable housing, zoning, planning |
| Environment & Parks | 9 | Green spaces, pollution, climate |
| Public Safety | 6 | Policing, emergency services, crime |
| Education & Services | 8 | Schools, libraries, community services |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| UI Framework | [Streamlit](https://streamlit.io) | Web dashboard, reactive state |
| NLP Engine | [TextBlob](https://textblob.readthedocs.io) | Sentiment + subjectivity scoring |
| Data Pipeline | [Pandas](https://pandas.pydata.org) | DataFrame processing |
| Visualisation | [Matplotlib](https://matplotlib.org) | 6 chart types |
| Word Clouds | [WordCloud](https://github.com/amueller/word_cloud) | Per-theme frequency clouds |
| Hosting | [Streamlit Community Cloud](https://share.streamlit.io) | Free, zero-config deploy |
| Version Control | [GitHub](https://github.com) | Code + CI |

---

## ⚡ Quick Start

### Option A — Streamlit Cloud (Recommended, no setup)

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
3. Click **New app** → select your fork → main file: `app.py`
4. Click **Deploy** — live in ~2 minutes

### Option B — Run locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/citizenlens-app.git
cd citizenlens-app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download NLP data (run once)
python -m textblob.download_corpora

# 4. Launch
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📁 Repository Structure

```
citizenlens-app/
│
├── app.py                  ← Main application (single file)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── LICENSE                 ← MIT License
│
├── data/
│   └── seed_comments.csv   ← 50-row self-generated seed dataset
│
└── docs/
    └── architecture.md     ← Technical architecture notes
```

---

## 🏆 Hackathon Evaluation Criteria

| Criterion | How CitizenLens addresses it |
|---|---|
| **Functionality** | Live comment submission → NLP → 6 charts → export. All features working end-to-end |
| **Innovation** | Subjectivity scatter, confidence scoring, per-theme word clouds, trend timeline |
| **Feasibility** | Deployed live on Streamlit Cloud. Zero cost. Zero infrastructure. 2-file deploy |
| **GitHub Repo Quality** | Structured folders, MIT license, documented architecture, seed dataset, this README |

---

## 🎥 Demo

**Live App:** `https://YOUR_USERNAME-citizenlens-app-app-xxxxx.streamlit.app`  
**Pitch Video:** *(2-minute walkthrough — link here)*  
**GitHub Repo:** `https://github.com/YOUR_USERNAME/citizenlens-app`

---

## ⚖️ Ethics & Data

- **No personal data stored** — comments exist in browser session state only
- **No external API calls** — NLP runs entirely locally
- **Open source dataset** — 50 self-generated seed comments, zero restricted data
- **Human-in-the-loop** — CitizenLens informs policymakers; all decisions remain human
- **MIT License** — fully open for government use and extension

---

## 👥 Team

Built for the Open Government Hackathon 2025.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*CitizenLens — making public voices count, automatically.*
