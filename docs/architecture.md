# CitizenLens — Technical Architecture

## System Overview

CitizenLens is a single-file Streamlit application with a four-layer architecture:
Input → NLP Pipeline → Analytics → Output.

## NLP Pipeline Detail

### Sentiment Analysis
- **Library:** TextBlob 0.18+
- **Method:** Pattern-based sentiment analysis using a pre-trained lexicon
- **Output:** `polarity` (float, −1.0 to +1.0) and `subjectivity` (float, 0.0 to 1.0)
- **Thresholds:**
  - polarity > 0.08  → Positive
  - polarity < −0.08 → Negative
  - otherwise        → Neutral
- **Rationale:** 0.08 threshold (rather than 0.0) reduces false positives from
  mildly positive/negative language that is essentially neutral in policy context.

### Topic Clustering
- **Method:** Keyword-frequency scoring against a domain dictionary
- **Domains:** 6 policy areas, 20-25 keywords each (120+ keywords total)
- **Confidence scoring:** `hits / domain_keywords * 100 + 40` (capped at 100%)
  The +40 base prevents zero-confidence for single-keyword matches.
- **Fallback:** "General / Other" when no keywords match

### Subjectivity Analysis
- TextBlob subjectivity is a by-product of the same pattern analysis
- Values near 0.0 = factual/objective language
- Values near 1.0 = opinion/emotional language
- Used in the scatter chart to show the opinion vs fact balance across themes

## Data Flow

```
User Input
    │
    ▼
run_nlp(text)
    ├── TextBlob(text).sentiment.polarity     → float
    ├── TextBlob(text).sentiment.subjectivity → float
    ├── classify polarity → label
    └── detect_theme(text) → (theme, confidence%)
    │
    ▼
st.session_state.submitted_comments  (list of dicts, in-memory only)
    │
    ▼
build_full_df()
    ├── get_base_df()          (cached 50-row seed)
    └── concat with live rows
    │
    ▼
Filter layer (sidebar controls)
    │
    ▼
Charts + Word Clouds + Table + Report
```

## Session State Keys

| Key | Type | Purpose |
|-----|------|---------|
| `dark_mode` | bool | Current theme |
| `submitted_comments` | list[dict] | Live submissions this session |
| `uploaded_rows` | list[dict] | Rows imported from CSV upload |
| `upload_processed` | bool | Guard against double-processing |

## Chart Types

| Chart | Library | Data |
|-------|---------|------|
| Sentiment distribution | Matplotlib bar | Sentiment value_counts |
| Theme distribution | Matplotlib barh | Theme value_counts |
| Polarity histogram | Matplotlib hist | Polarity column |
| Stacked sentiment | Matplotlib bar | groupby Theme+Sentiment |
| Subjectivity scatter | Matplotlib scatter | Polarity vs Subjectivity |
| Sentiment timeline | Matplotlib line/fill | Weekly groupby Date+Sentiment |

## Word Clouds

- One cloud generated per policy theme present in the filtered data
- Custom stopword list removes common English words + policy-neutral filler words
- `collocations=False` prevents repeated phrases from dominating
- Colourmap varies by theme for visual distinctiveness

## Performance Notes

- `@st.cache_data` on `build_seed_df()` ensures the 50-row NLP computation
  only runs once per session, not on every widget interaction.
- All chart functions receive the filtered DataFrame so charts never
  recompute from the full dataset unnecessarily.
- Word clouds are not cached because they depend on the filtered slice
  which changes with user interaction.

## Deployment

- Target: Streamlit Community Cloud (free tier)
- Required files: `app.py`, `requirements.txt`
- No database, no environment variables, no secrets required
- `python -m textblob.download_corpora` runs automatically on Streamlit Cloud
  via the `punkt` and `averaged_perceptron_tagger` NLTK data packages which
  TextBlob downloads on first use if not present.
