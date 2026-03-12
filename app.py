# =============================================================================
# 🏛️  CitizenLens — AI-Powered Citizen Comment Analyzer
#     Complete Hackathon Solution | Streamlit + TextBlob + WordCloud
# =============================================================================
#
#  ┌─────────────────────────────────────────────────────────────────────┐
#  │  QUICK START (3 steps)                                              │
#  │                                                                     │
#  │  1. pip install -r requirements.txt                                 │
#  │  2. python -m textblob.download_corpora   ← run ONCE               │
#  │  3. streamlit run app.py                                            │
#  │                                                                     │
#  │  Then open → http://localhost:8501 in your browser                  │
#  └─────────────────────────────────────────────────────────────────────┘
#
# =============================================================================

# ── STANDARD LIBRARY ─────────────────────────────────────────────────────────
import io          # In-memory file handling (for CSV export)

# ── THIRD-PARTY LIBRARIES ────────────────────────────────────────────────────
import streamlit as st            # Web framework — the entire UI lives here
import pandas as pd               # Spreadsheet-like data manipulation
import matplotlib.pyplot as plt   # Drawing charts and plots
import matplotlib.patches as mpatches  # Legend patches for charts
from textblob import TextBlob     # Sentiment analysis (NLP)
from wordcloud import WordCloud   # Word cloud image generation

# =============================================================================
# ⚡  PAGE CONFIG  ← Must be the VERY FIRST Streamlit call in the file
# =============================================================================
st.set_page_config(
    page_title="CitizenLens | Policy Comment Analyzer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 🎨  GLOBAL STYLES  — Copy/edit this block to change colors and fonts
# =============================================================================
st.markdown("""
<style>
/* ── Google Font ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ── Base ────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp {
    background: #eef1f6;
}

/* ── Hero banner ─────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #0d1f3c 0%, #1a3a6b 60%, #1e5ca8 100%);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "🏛️";
    position: absolute;
    right: 40px; top: 50%;
    transform: translateY(-50%);
    font-size: 72px;
    opacity: 0.15;
}
.hero h1 { color: #ffffff; margin: 0; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.5px; }
.hero p  { color: #90b8e8; margin: 8px 0 0; font-size: 1rem; }

/* ── KPI metric cards ────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: white;
    border-radius: 14px;
    padding: 22px 24px;
    border: 1px solid #dde2ec;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: transform 0.2s;
}
div[data-testid="metric-container"]:hover { transform: translateY(-2px); }
div[data-testid="metric-container"] label { color: #5a6882 !important; font-size: 0.8rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 2.4rem !important; font-weight: 700 !important; color: #0d1f3c !important; }

/* ── Chart card wrapper ──────────────────────────────────── */
.card {
    background: white;
    border-radius: 14px;
    padding: 24px;
    border: 1px solid #dde2ec;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
.card h4 { margin: 0 0 18px; color: #0d1f3c; font-size: 1rem; font-weight: 600; }

/* ── Section label ───────────────────────────────────────── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #8a9aba;
    margin: 32px 0 14px;
}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0d1f3c;
}
section[data-testid="stSidebar"] * { color: #ccdaef; }
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: white !important; }
section[data-testid="stSidebar"] .stMultiSelect > label,
section[data-testid="stSidebar"] .stSelectbox > label { color: #8aaed4 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Download button ─────────────────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1a3a6b, #1e5ca8);
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-weight: 600;
    font-size: 0.95rem;
    width: 100%;
    transition: opacity 0.2s;
}
.stDownloadButton > button:hover { opacity: 0.88; }

/* ── Dataframe ───────────────────────────────────────────── */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* ── Hide Streamlit branding ─────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 📦  SECTION 1 — MOCK DATA
#     In production: replace generate_mock_data() with a database call,
#     form submission API, or CSV upload.
# =============================================================================

@st.cache_data   # ← Caches the result so it doesn't regenerate on every click
def generate_mock_data() -> pd.DataFrame:
    """
    Creates 30 realistic citizen comments spanning 6 policy areas.
    Each comment is a plain string — just like someone would type
    into a government feedback form.
    """
    comments = [
        # ── Economy & Tax ─────────────────────────────────
        "The new small business grant program has been a genuine lifesaver for local entrepreneurs.",
        "Property taxes keep rising while city services deteriorate. This is completely unacceptable.",
        "I appreciate the council's commitment to reducing the corporate tax burden this year.",
        "Raising the sales tax again will crush working families who are already stretched thin.",
        "The new economic development zone is bringing real jobs and investment to our area.",

        # ── Infrastructure & Transport ────────────────────
        "The new protected bike lanes downtown are fantastic — more people are cycling than ever!",
        "The potholes on Main Street are a complete disgrace. My car was seriously damaged last week.",
        "Public transit desperately needs investment. Buses are always late and dangerously overcrowded.",
        "The pedestrian bridge renovation in Riverside Park looks beautiful and was well worth the cost.",
        "Road construction on 5th Avenue has dragged on for two years with absolutely no end in sight.",
        "The new electric bus fleet is a massive improvement — quiet, clean, and on time.",

        # ── Housing & Development ─────────────────────────
        "Affordable housing policy is moving in the right direction, but implementation is far too slow.",
        "The new zoning laws will completely destroy the character of our beloved historic neighborhood.",
        "Finally the city is investing in social housing — families need stable homes to thrive.",
        "Luxury condos keep replacing affordable rentals. Where are working people supposed to live?",
        "The community land trust initiative is an innovative and overdue solution to the housing crisis.",

        # ── Environment & Parks ───────────────────────────
        "The new recycling system is confusing and the bins overflow every single week. Total failure.",
        "Planting 10,000 native trees is the best environmental policy this city has seen in decades.",
        "The park renovation project has completely revitalized our neighborhood — families love it.",
        "Industrial pollution near the river remains totally unaddressed despite years of complaints.",
        "The solar panel initiative for public buildings will save millions in taxpayer money long-term.",
        "Green corridors connecting our parks are a wonderful idea — please expand the program.",

        # ── Public Safety ─────────────────────────────────
        "Community policing programs have made our street feel noticeably safer this past year.",
        "Emergency response times have improved dramatically — the new dispatch system is working.",
        "The youth mentorship program is genuinely keeping kids engaged and off the streets.",

        # ── Education & Services ─────────────────────────
        "School funding cuts are devastating — my child's class now has 40 students. Unacceptable.",
        "The library closure is a tremendous blow. It was a vital resource for seniors and children.",
        "After-school programs have been a lifeline for working parents in our community.",
        "The new digital literacy workshops at community centers are excellent and well-attended.",
        "Cutting the arts curriculum was a terrible mistake that will harm children for years.",
    ]

    return pd.DataFrame({"comment": comments})


# =============================================================================
# 🤖  SECTION 2 — SENTIMENT ANALYSIS
#     TextBlob reads the text and gives it a polarity score:
#       +1.0 = very positive    0.0 = neutral    -1.0 = very negative
#     We convert this number into a human-readable label.
# =============================================================================

def analyze_sentiment(text: str) -> tuple[str, float]:
    """
    Runs TextBlob on a single comment string.
    Returns a (label, score) tuple.

    Thresholds (you can tune these):
      score >  0.08  →  Positive
      score < -0.08  →  Negative
      otherwise      →  Neutral
    """
    score = TextBlob(text).sentiment.polarity

    if score > 0.08:
        label = "Positive"
    elif score < -0.08:
        label = "Negative"
    else:
        label = "Neutral"

    return label, round(score, 4)


# =============================================================================
# 🗂️  SECTION 3 — THEME / TOPIC DETECTION
#     No ML needed! We simply check whether any keyword from a predefined
#     dictionary appears in the comment. Fast, transparent, and easy to extend.
#     ── To add a new topic ──────────────────────────────────────────────────
#       1. Add a new key (topic name) to TOPIC_KEYWORDS below
#       2. Add a list of relevant trigger words
#     ────────────────────────────────────────────────────────────────────────
# =============================================================================

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Economy & Tax":         ["tax", "economic", "business", "grant", "sales",
                               "relief", "jobs", "development", "zone", "corporate", "investment"],
    "Infrastructure":        ["road", "bike", "lane", "pothole", "bus", "transit",
                               "bridge", "construction", "pedestrian", "electric", "fleet"],
    "Housing":               ["housing", "affordable", "zoning", "rent", "condo",
                               "rental", "homes", "land trust", "social housing", "luxury"],
    "Environment & Parks":   ["recycling", "park", "tree", "pollution", "solar",
                               "environment", "river", "green", "corridor", "native"],
    "Public Safety":         ["police", "safety", "crime", "emergency", "response",
                               "dispatch", "mentor", "youth", "street"],
    "Education & Services":  ["school", "library", "education", "student", "class",
                               "arts", "curriculum", "workshop", "digital", "literacy", "after-school"],
}

def detect_theme(text: str) -> str:
    """
    Scans a comment for keyword matches and returns the best-fit theme.
    Falls back to 'General / Other' if no keywords match.
    """
    text_lower = text.lower()
    for theme, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return theme
    return "General / Other"


# =============================================================================
# ⚙️  SECTION 4 — DATA PIPELINE
#     Ties Sections 1–3 together: load → analyze → return enriched DataFrame.
# =============================================================================

@st.cache_data
def process_data() -> pd.DataFrame:
    """
    Full pipeline:
      generate_mock_data()   → raw comments
      analyze_sentiment()    → adds Sentiment + Polarity Score columns
      detect_theme()         → adds Theme column

    Returns the final enriched DataFrame ready for the dashboard.
    """
    df = generate_mock_data()

    # Apply sentiment — returns two values, so we use pd.Series
    df[["Sentiment", "Polarity Score"]] = df["comment"].apply(
        lambda t: pd.Series(analyze_sentiment(t))
    )

    # Apply theme detection
    df["Theme"] = df["comment"].apply(detect_theme)

    # Rename for display friendliness
    df.rename(columns={"comment": "Citizen Comment"}, inplace=True)

    return df


# =============================================================================
# ☁️  SECTION 5 — WORD CLOUD HELPER
#     Generates a matplotlib Figure containing a word cloud image.
#     Pass a Series of comment strings and a matplotlib colormap name.
# =============================================================================

def make_wordcloud(text_series: pd.Series, colormap: str, title: str):
    """
    Generates a word cloud figure from a Series of text strings.
    Returns a matplotlib Figure you can pass directly to st.pyplot().
    """
    combined = " ".join(text_series.tolist()).strip()

    fig, ax = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor("white")

    if not combined:
        ax.text(0.5, 0.5, "No comments in this category",
                ha="center", va="center", fontsize=13, color="#aaa")
        ax.axis("off")
        return fig

    wc = WordCloud(
        width=900, height=380,
        background_color="white",
        colormap=colormap,
        max_words=60,
        collocations=False,       # Avoid repeated pairs
        prefer_horizontal=0.85,   # Mostly horizontal text
        min_font_size=11,
    ).generate(combined)

    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig


# =============================================================================
# 📊  SECTION 6 — CHART HELPERS
# =============================================================================

# Color palette for consistent look across all charts
SENTIMENT_COLORS = {
    "Positive": "#22c55e",   # Green
    "Neutral":  "#3b82f6",   # Blue
    "Negative": "#ef4444",   # Red
}

THEME_COLORS = [
    "#1e5ca8", "#0ea5e9", "#14b8a6",
    "#8b5cf6", "#f59e0b", "#64748b", "#ec4899",
]


def chart_sentiment(df: pd.DataFrame):
    """Bar chart — how many comments are Positive / Neutral / Negative."""
    counts = df["Sentiment"].value_counts().reindex(["Positive", "Neutral", "Negative"], fill_value=0)
    colors = [SENTIMENT_COLORS[s] for s in counts.index]

    fig, ax = plt.subplots(figsize=(5, 3.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fafbfd")

    bars = ax.bar(counts.index, counts.values, color=colors,
                  edgecolor="white", linewidth=2, width=0.55, zorder=3)

    # Value labels above each bar
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15,
                str(int(h)), ha="center", va="bottom",
                fontsize=13, fontweight="bold", color="#1e293b")

    ax.set_ylabel("Comments", fontsize=10, color="#64748b")
    ax.tick_params(colors="#64748b", labelsize=11)
    ax.set_ylim(0, counts.max() + 2.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def chart_themes(df: pd.DataFrame):
    """Horizontal bar chart — comment count per policy theme."""
    counts = df["Theme"].value_counts()
    colors = THEME_COLORS[:len(counts)]

    fig, ax = plt.subplots(figsize=(5, 3.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fafbfd")

    bars = ax.barh(counts.index, counts.values,
                   color=colors, edgecolor="white", linewidth=1.5,
                   height=0.6, zorder=3)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.08, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", fontsize=11,
                fontweight="bold", color="#1e293b")

    ax.set_xlabel("Comments", fontsize=10, color="#64748b")
    ax.tick_params(colors="#64748b", labelsize=10)
    ax.set_xlim(0, counts.max() + 1.8)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.xaxis.grid(True, color="#e2e8f0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.invert_yaxis()   # Highest bar at top
    plt.tight_layout()
    return fig


def chart_polarity_histogram(df: pd.DataFrame):
    """Histogram — distribution of raw polarity scores (-1 to +1)."""
    fig, ax = plt.subplots(figsize=(5, 3.4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fafbfd")

    ax.hist(df["Polarity Score"], bins=14, color="#1e5ca8",
            edgecolor="white", linewidth=1.2, zorder=3)
    ax.axvline(0, color="#94a3b8", linestyle="--", linewidth=1.5, label="Neutral line")
    ax.axvline(df["Polarity Score"].mean(), color="#f59e0b",
               linestyle="-", linewidth=2, label=f"Mean ({df['Polarity Score'].mean():.2f})")

    ax.set_xlabel("Polarity Score  (negative ← | → positive)", fontsize=10, color="#64748b")
    ax.set_ylabel("Frequency", fontsize=10, color="#64748b")
    ax.tick_params(colors="#64748b", labelsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=9, framealpha=0.5)
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def chart_stacked_theme_sentiment(df: pd.DataFrame):
    """Stacked bar chart — sentiment breakdown per theme."""
    pivot = df.groupby(["Theme", "Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive", "Neutral", "Negative"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[["Positive", "Neutral", "Negative"]]

    fig, ax = plt.subplots(figsize=(5, 3.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fafbfd")

    bottom = pd.Series([0] * len(pivot), index=pivot.index)
    for sentiment, color in SENTIMENT_COLORS.items():
        ax.bar(pivot.index, pivot[sentiment], bottom=bottom,
               color=color, label=sentiment, edgecolor="white", linewidth=0.8)
        bottom += pivot[sentiment]

    ax.set_ylabel("Comments", fontsize=10, color="#64748b")
    ax.tick_params(axis="x", rotation=30, labelsize=9, colors="#64748b")
    ax.tick_params(axis="y", labelsize=10, colors="#64748b")
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.6)
    plt.tight_layout()
    return fig


# =============================================================================
# 🖥️  SECTION 7 — MAIN DASHBOARD
# =============================================================================

def main():
    # ── Load & process data ───────────────────────────────────────────────────
    df = process_data()

    # ── HERO HEADER ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero">
        <h1>CitizenLens</h1>
        <p>AI-powered citizen comment analyzer for policymakers &nbsp;·&nbsp;
           Sentiment · Themes · Visual Reports</p>
    </div>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🔍 Filters")
        st.markdown("Narrow the analysis using the options below.")
        st.divider()

        # Theme filter
        all_themes = sorted(df["Theme"].unique().tolist())
        selected_themes = st.multiselect(
            "Policy Theme",
            options=all_themes,
            default=all_themes,
            help="Select the policy areas you want to analyze.",
        )

        st.divider()

        # Sentiment filter
        all_sentiments = ["Positive", "Neutral", "Negative"]
        selected_sentiments = st.multiselect(
            "Sentiment",
            options=all_sentiments,
            default=all_sentiments,
            help="Filter comments by sentiment category.",
        )

        st.divider()

        # Polarity slider
        min_pol, max_pol = float(df["Polarity Score"].min()), float(df["Polarity Score"].max())
        pol_range = st.slider(
            "Polarity Score Range",
            min_value=min_pol, max_value=max_pol,
            value=(min_pol, max_pol), step=0.01,
            help="Slide to focus on strongly positive or negative comments.",
        )

        st.divider()
        st.markdown("""
        #### 📌 How it works
        - **Sentiment** — TextBlob NLP polarity score  
        - **Themes** — Keyword matching rules  
        - **No database** — runs entirely in memory  
        """)

    # ── APPLY FILTERS ─────────────────────────────────────────────────────────
    filtered = df[
        df["Theme"].isin(selected_themes) &
        df["Sentiment"].isin(selected_sentiments) &
        df["Polarity Score"].between(pol_range[0], pol_range[1])
    ]

    total     = len(filtered)
    pos_count = (filtered["Sentiment"] == "Positive").sum()
    neg_count = (filtered["Sentiment"] == "Negative").sum()
    neu_count = (filtered["Sentiment"] == "Neutral").sum()
    avg_pol   = filtered["Polarity Score"].mean() if total else 0

    # ── KPI METRICS ───────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">📊 Overview Metrics</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💬 Total Comments",   total)
    c2.metric("✅ Positive",          pos_count,
              delta=f"{round(pos_count/total*100) if total else 0}%")
    c3.metric("➖ Neutral",            neu_count,
              delta=f"{round(neu_count/total*100) if total else 0}%", delta_color="off")
    c4.metric("❌ Negative",           neg_count,
              delta=f"{round(neg_count/total*100) if total else 0}%", delta_color="inverse")
    c5.metric("📈 Avg Polarity",      f"{avg_pol:.3f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CHARTS ROW 1 — Sentiment + Theme ──────────────────────────────────────
    st.markdown('<p class="section-label">📈 Sentiment & Theme Breakdown</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="card"><h4>🎭 Sentiment Distribution</h4>', unsafe_allow_html=True)
        st.pyplot(chart_sentiment(filtered))
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card"><h4>🗂️ Comments per Policy Theme</h4>', unsafe_allow_html=True)
        st.pyplot(chart_themes(filtered))
        st.markdown('</div>', unsafe_allow_html=True)

    # ── CHARTS ROW 2 — Polarity histogram + Stacked ───────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<div class="card"><h4>📉 Polarity Score Distribution</h4>', unsafe_allow_html=True)
        st.pyplot(chart_polarity_histogram(filtered))
        st.markdown('</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="card"><h4>🧩 Sentiment by Theme (Stacked)</h4>', unsafe_allow_html=True)
        st.pyplot(chart_stacked_theme_sentiment(filtered))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── WORD CLOUDS ───────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">☁️ Word Clouds</p>', unsafe_allow_html=True)
    wc_col1, wc_col2 = st.columns(2)

    pos_comments = filtered[filtered["Sentiment"] == "Positive"]["Citizen Comment"]
    neg_comments = filtered[filtered["Sentiment"] == "Negative"]["Citizen Comment"]

    with wc_col1:
        st.markdown('<div class="card"><h4>✅ Positive Comment Keywords</h4>', unsafe_allow_html=True)
        st.pyplot(make_wordcloud(pos_comments, "YlGn", "Positive"))
        st.caption(f"Based on {len(pos_comments)} positive comment(s)")
        st.markdown('</div>', unsafe_allow_html=True)

    with wc_col2:
        st.markdown('<div class="card"><h4>❌ Negative Comment Keywords</h4>', unsafe_allow_html=True)
        st.pyplot(make_wordcloud(neg_comments, "OrRd", "Negative"))
        st.caption(f"Based on {len(neg_comments)} negative comment(s)")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── THEME DEEP DIVE — expandable per-theme analysis ────────────────────
    st.markdown('<p class="section-label">🔬 Theme Deep Dive</p>', unsafe_allow_html=True)
    with st.expander("Click to explore sentiment within each policy theme", expanded=False):
        if total == 0:
            st.info("No comments match your current filters.")
        else:
            theme_tabs = st.tabs(sorted(filtered["Theme"].unique().tolist()))
            for tab, theme_name in zip(theme_tabs, sorted(filtered["Theme"].unique().tolist())):
                with tab:
                    theme_df = filtered[filtered["Theme"] == theme_name]
                    t_pos = (theme_df["Sentiment"] == "Positive").sum()
                    t_neg = (theme_df["Sentiment"] == "Negative").sum()
                    t_neu = (theme_df["Sentiment"] == "Neutral").sum()
                    st.markdown(
                        f"**{len(theme_df)} comments** · "
                        f"✅ {t_pos} positive · "
                        f"➖ {t_neu} neutral · "
                        f"❌ {t_neg} negative · "
                        f"Avg polarity: **{theme_df['Polarity Score'].mean():.3f}**"
                    )
                    st.dataframe(
                        theme_df[["Citizen Comment", "Sentiment", "Polarity Score"]].reset_index(drop=True),
                        use_container_width=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── RAW DATA TABLE ────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">📋 Raw Data Table</p>', unsafe_allow_html=True)
    st.caption(f"Showing **{total}** of **{len(df)}** total comments based on active filters.")

    # Colour-code the Sentiment column using pandas Styler
    def colour_sentiment(val):
        colours = {
            "Positive": "background-color:#dcfce7; color:#166534;",
            "Negative": "background-color:#fee2e2; color:#991b1b;",
            "Neutral":  "background-color:#dbeafe; color:#1e3a8a;",
        }
        return colours.get(val, "")

    display_df = filtered.reset_index(drop=True)
    styled = display_df.style.applymap(colour_sentiment, subset=["Sentiment"])
    st.dataframe(styled, use_container_width=True, height=380)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── EXPORT SECTION ────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">💾 Export</p>', unsafe_allow_html=True)

    exp_col1, exp_col2 = st.columns([2, 1])

    with exp_col1:
        # Build CSV in memory — no temp file needed
        buf = io.StringIO()
        filtered.to_csv(buf, index=False)
        st.download_button(
            label="⬇️  Download Filtered Data as CSV",
            data=buf.getvalue().encode("utf-8"),
            file_name="citizenlens_report.csv",
            mime="text/csv",
        )

    with exp_col2:
        st.info(f"📄 **{total} rows** will be exported", icon="ℹ️")

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#94a3b8;font-size:12px;'>"
        "CitizenLens &nbsp;·&nbsp; Built with Streamlit, TextBlob & WordCloud &nbsp;·&nbsp; Hackathon 2025"
        "</p>",
        unsafe_allow_html=True,
    )


# =============================================================================
# 🚀  RUN
# =============================================================================
if __name__ == "__main__":
    main()
