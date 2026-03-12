# =============================================================================
#  CitizenLens  — AI-Powered Policy Comment Intelligence Platform
#  ─────────────────────────────────────────────────────────────────────────────
#  Author      : CitizenLens Team
#  Version     : 2.0.0
#  Built for   : Open Government Hackathon 2025
#  License     : MIT
#
#  ARCHITECTURE
#  ┌─────────────────────────────────────────────────────────────────────────┐
#  │  INPUT LAYER                                                            │
#  │    • Live comment submission form (any citizen can submit)              │
#  │    • CSV file upload (bulk import existing feedback)                    │
#  │    • 50-row self-generated seed dataset (publicly available text)       │
#  │                                                                         │
#  │  NLP PIPELINE                                                           │
#  │    • TextBlob  → polarity score (−1.0 … +1.0)                          │
#  │    • Subjectivity scoring → objective vs subjective filter              │
#  │    • Custom keyword-frequency topic clustering (6 policy domains)       │
#  │    • Confidence scoring → how clearly a theme was detected              │
#  │                                                                         │
#  │  ANALYTICS LAYER                                                        │
#  │    • 5 KPI metrics with delta indicators                                │
#  │    • 5 distinct chart types                                             │
#  │    • Per-theme word clouds (one cloud per policy domain)                │
#  │    • Trend timeline (comments over simulated time periods)              │
#  │    • Subjectivity vs polarity scatter plot                              │
#  │                                                                         │
#  │  OUTPUT LAYER                                                           │
#  │    • Light / Dark theme toggle (full CSS swap)                         │
#  │    • Interactive sidebar filters                                        │
#  │    • Colour-coded data table                                            │
#  │    • CSV export of enriched dataset                                     │
#  │    • Formatted Policy Insight Report (.txt)                             │
#  └─────────────────────────────────────────────────────────────────────────┘
#
#  QUICK START
#    pip install -r requirements.txt
#    python -m textblob.download_corpora   ← once only
#    streamlit run app.py
# =============================================================================

# ── Standard library ──────────────────────────────────────────────────────────
import io
import re
import datetime
import hashlib
import random
import math

# ── Third-party ───────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS

# =============================================================================
#  PAGE CONFIG  ← must be the very first Streamlit call
# =============================================================================
st.set_page_config(
    page_title="CitizenLens | Policy Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
#  THEME STATE
# =============================================================================
if "dark_mode"            not in st.session_state: st.session_state.dark_mode = False
if "submitted_comments"   not in st.session_state: st.session_state.submitted_comments = []
if "upload_processed"     not in st.session_state: st.session_state.upload_processed = False
if "uploaded_rows"        not in st.session_state: st.session_state.uploaded_rows = []
if "active_tab"           not in st.session_state: st.session_state.active_tab = "dashboard"


# =============================================================================
#  COLOUR PALETTE  — every UI colour is defined here, nowhere else
# =============================================================================
def palette(dark: bool) -> dict:
    if dark:
        return dict(
            bg="#0e1621",          sidebar="#090f18",
            card="#162032",        card_border="#1e3050",
            card_hover="#1e2d45",
            hero_a="#090f18",      hero_b="#0a2250",
            text="#dce8ff",        text2="#7a9cc8",       muted="#3d5570",
            accent="#3d8eff",      accent2="#00e5b0",     accent3="#ff6b6b",
            pos="#00d68f",         neg="#ff4d4d",         neu="#5b9bf5",
            pos_bg="#012d1a",      pos_fg="#00d68f",
            neg_bg="#2d0101",      neg_fg="#ff4d4d",
            neu_bg="#011833",      neu_fg="#5b9bf5",
            input_bg="#162032",    input_border="#1e3050",
            chart_bg="#162032",    chart_text="#5b7fa8",  chart_grid="#1e3050",
            wc_bg="#162032",
            rep_bg="#0c1825",      rep_border="#1e3050",
            dl="#3d8eff",          submit="#3d8eff",
            div="#1e3050",         sec="#3d8eff",
            tag_new_bg="#012d1a",  tag_new_fg="#00d68f",
            scatter_c="#3d8eff",   timeline_c="#00e5b0",
            thumb_bg="#1e3050",
        )
    else:
        return dict(
            bg="#f0f5fc",          sidebar="#0d1e38",
            card="#ffffff",        card_border="#d4e3f7",
            card_hover="#f5f9ff",
            hero_a="#0d1e38",      hero_b="#1546a0",
            text="#0d1e38",        text2="#2d4e7a",       muted="#7a95b8",
            accent="#1546a0",      accent2="#00a87a",     accent3="#e03e3e",
            pos="#16a34a",         neg="#dc2626",         neu="#2563eb",
            pos_bg="#dcfce7",      pos_fg="#15803d",
            neg_bg="#fee2e2",      neg_fg="#b91c1c",
            neu_bg="#dbeafe",      neu_fg="#1d4ed8",
            input_bg="#ffffff",    input_border="#c2d6f0",
            chart_bg="#ffffff",    chart_text="#6482a0",  chart_grid="#e4edf8",
            wc_bg="#f5f9ff",
            rep_bg="#eef5ff",      rep_border="#c2d6f0",
            dl="#1546a0",          submit="#1546a0",
            div="#d4e3f7",         sec="#1546a0",
            tag_new_bg="#dcfce7",  tag_new_fg="#15803d",
            scatter_c="#1546a0",   timeline_c="#00a87a",
            thumb_bg="#e4edf8",
        )


C    = palette(st.session_state.dark_mode)
DARK = st.session_state.dark_mode


# =============================================================================
#  INJECT CSS  — every element covered, all text visible in both themes
# =============================================================================
def inject_css(C, dark):
    shadow = "0 8px 32px rgba(0,0,0,0.35)" if dark else "0 4px 20px rgba(13,30,56,0.08)"
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & base ─────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stApp {{ background: {C['bg']} !important; }}

/* ── Universal text visibility ────────────────────────────── */
p, span, div, li, td, th, small, em, strong,
.stMarkdown, .stText, .stCaption, .element-container {{
    color: {C['text']} !important;
}}
h1,h2,h3,h4,h5,h6 {{ color: {C['text']} !important; }}
strong {{ color: {C['text']} !important; font-weight: 700; }}
a {{ color: {C['accent']} !important; }}
code {{
    background: {C['card']} !important;
    color: {C['accent2']} !important;
    border: 1px solid {C['card_border']} !important;
    border-radius: 5px;
    padding: 1px 6px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85em;
}}

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {C['sidebar']} !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}}
section[data-testid="stSidebar"] * {{
    color: #b8cfe8 !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] strong {{
    color: #ffffff !important;
}}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.1) !important;
}}
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stMultiSelect > div > div {{
    background: rgba(255,255,255,0.07) !important;
    border-color: rgba(255,255,255,0.12) !important;
}}
section[data-testid="stSidebar"] label {{
    color: #8aaed4 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}}

/* ── KPI metric cards ─────────────────────────────────────── */
div[data-testid="metric-container"] {{
    background: {C['card']} !important;
    border: 1.5px solid {C['card_border']} !important;
    border-radius: 18px !important;
    padding: 22px 26px !important;
    box-shadow: {shadow} !important;
    transition: transform 0.22s ease, box-shadow 0.22s ease !important;
}}
div[data-testid="metric-container"]:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 36px rgba(0,0,0,{'0.4' if dark else '0.12'}) !important;
}}
div[data-testid="metric-container"] label {{
    color: {C['muted']} !important;
    font-size: 0.68rem !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    color: {C['text']} !important;
    line-height: 1.1 !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] span {{
    color: inherit !important;
}}

/* ── Cards ────────────────────────────────────────────────── */
.cl-card {{
    background: {C['card']};
    border: 1.5px solid {C['card_border']};
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 20px;
    box-shadow: {shadow};
    transition: box-shadow 0.2s;
}}
.cl-card:hover {{
    box-shadow: 0 12px 40px rgba(0,0,0,{'0.35' if dark else '0.1'});
}}
.cl-card h4 {{
    color: {C['text']} !important;
    font-size: 0.92rem !important;
    font-weight: 800 !important;
    margin: 0 0 18px !important;
    letter-spacing: -0.2px !important;
}}

/* ── Hero ─────────────────────────────────────────────────── */
.hero {{
    background: linear-gradient(140deg, {C['hero_a']} 0%, {C['hero_b']} 100%);
    border-radius: 22px;
    padding: 40px 48px;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content: '';
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse at 90% 20%, rgba(61,142,255,0.22) 0%, transparent 55%),
        radial-gradient(ellipse at 10% 80%, rgba(0,229,176,0.12) 0%, transparent 50%);
}}
.hero-inner {{ position: relative; z-index: 1; }}
.hero h1 {{
    color: #ffffff !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    margin: 0 !important;
    letter-spacing: -0.8px !important;
}}
.hero-sub {{
    color: rgba(255,255,255,0.62) !important;
    font-size: 0.92rem !important;
    margin: 8px 0 0 !important;
}}
.hero-badge {{
    display: inline-flex; align-items: center; gap: 7px;
    background: rgba(61,142,255,0.2);
    border: 1px solid rgba(61,142,255,0.4);
    border-radius: 30px;
    padding: 5px 16px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #7ec4ff !important;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 16px;
}}
.hero-stat {{
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 14px;
    padding: 14px 22px;
    text-align: center;
    min-width: 110px;
    backdrop-filter: blur(8px);
}}
.hero-stat-label {{
    color: rgba(255,255,255,0.5) !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    margin-bottom: 4px !important;
}}
.hero-stat-val {{
    color: #ffffff !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    line-height: 1 !important;
}}

/* ── Section label ────────────────────────────────────────── */
.section-label {{
    font-size: 0.65rem !important;
    font-weight: 800 !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
    color: {C['sec']} !important;
    margin: 36px 0 16px !important;
    display: flex; align-items: center; gap: 10px;
}}
.section-label::after {{
    content: ''; flex: 1;
    height: 1px; background: {C['div']};
}}

/* ── Submit form ──────────────────────────────────────────── */
.submit-wrap {{
    background: {C['card']};
    border: 2px solid {C['accent']};
    border-radius: 20px;
    padding: 30px 34px;
    margin-bottom: 20px;
    box-shadow: 0 0 0 5px {'rgba(61,142,255,0.08)' if dark else 'rgba(21,70,160,0.06)'};
}}
.submit-wrap h3 {{
    color: {C['text']} !important;
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    margin: 0 0 4px !important;
}}
.submit-desc {{
    color: {C['text2']} !important;
    font-size: 0.875rem !important;
    margin: 0 0 22px !important;
    line-height: 1.6 !important;
}}

/* ── All inputs ───────────────────────────────────────────── */
.stTextArea textarea {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['input_border']} !important;
    border-radius: 12px !important;
    color: {C['text']} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    padding: 12px 16px !important;
    resize: vertical !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.stTextArea textarea::placeholder {{ color: {C['muted']} !important; opacity: 1 !important; }}
.stTextArea textarea:focus {{
    border-color: {C['accent']} !important;
    box-shadow: 0 0 0 4px {'rgba(61,142,255,0.15)' if dark else 'rgba(21,70,160,0.1)'} !important;
    outline: none !important;
}}
.stTextInput input {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['input_border']} !important;
    border-radius: 10px !important;
    color: {C['text']} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stTextInput input::placeholder {{ color: {C['muted']} !important; }}
.stTextInput input:focus {{
    border-color: {C['accent']} !important;
    box-shadow: 0 0 0 3px {'rgba(61,142,255,0.15)' if dark else 'rgba(21,70,160,0.1)'} !important;
    outline: none !important;
}}
.stSelectbox > div > div {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['input_border']} !important;
    border-radius: 10px !important;
    color: {C['text']} !important;
}}
.stMultiSelect > div > div {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['input_border']} !important;
    border-radius: 10px !important;
}}
.stSelectbox label, .stMultiSelect label,
.stTextArea label, .stTextInput label,
.stSlider label, .stRadio label,
.stFileUploader label {{
    color: {C['text']} !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
}}
/* Dropdown menu items */
[data-baseweb="popover"] li, [data-baseweb="menu"] li {{
    background: {C['card']} !important;
    color: {C['text']} !important;
}}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {{
    background: {C['card_border']} !important;
}}
/* Multi-select tags */
[data-baseweb="tag"] {{
    background: {C['neu_bg']} !important;
    color: {C['neu_fg']} !important;
}}

/* ── Buttons ──────────────────────────────────────────────── */
div[data-testid="stForm"] button,
div[data-testid="stForm"] button[kind="primaryFormSubmit"] {{
    background: linear-gradient(135deg, {C['submit']}, {C['accent2']}) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 13px 28px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    letter-spacing: 0.2px !important;
    cursor: pointer !important;
    transition: opacity 0.2s, transform 0.15s !important;
}}
div[data-testid="stForm"] button:hover {{
    opacity: 0.88 !important; transform: translateY(-1px) !important;
}}
.stDownloadButton > button {{
    background: {C['dl']} !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    width: 100% !important;
    transition: opacity 0.2s, transform 0.15s !important;
    letter-spacing: 0.2px !important;
}}
.stDownloadButton > button:hover {{
    opacity: 0.85 !important; transform: translateY(-1px) !important;
}}
.stButton > button {{
    background: {C['card']} !important;
    color: {C['accent3']} !important;
    border: 1.5px solid {C['accent3']} !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: {C['accent3']} !important;
    color: white !important;
}}

/* ── File uploader ────────────────────────────────────────── */
[data-testid="stFileUploader"] {{
    background: {C['card']} !important;
    border: 2px dashed {C['card_border']} !important;
    border-radius: 14px !important;
    padding: 10px !important;
}}
[data-testid="stFileUploader"] * {{
    color: {C['text2']} !important;
}}

/* ── Dataframe ────────────────────────────────────────────── */
.stDataFrame {{ border-radius: 14px !important; overflow: hidden !important; }}
.stDataFrame thead th {{
    background: {'#1a2d45' if dark else '#eaf1fc'} !important;
    color: {C['text']} !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}
.stDataFrame tbody td {{
    color: {C['text']} !important;
    background: {C['card']} !important;
    font-size: 0.875rem !important;
}}
.stDataFrame tbody tr:nth-child(even) td {{
    background: {'#162032' if dark else '#f7f9fd'} !important;
}}

/* ── Alerts ───────────────────────────────────────────────── */
div[data-testid="stAlert"] {{ border-radius: 14px !important; }}
div[data-testid="stAlert"] p {{ color: inherit !important; }}

/* ── Expander ─────────────────────────────────────────────── */
details {{
    background: {C['card']} !important;
    border: 1.5px solid {C['card_border']} !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    margin-bottom: 10px !important;
}}
details summary {{
    color: {C['text']} !important;
    font-weight: 700 !important;
    padding: 16px 22px !important;
    background: {C['card']} !important;
    cursor: pointer !important;
    transition: background 0.18s !important;
    font-size: 0.92rem !important;
}}
details summary:hover {{ background: {C['card_hover']} !important; }}
details[open] > summary {{
    border-bottom: 1px solid {C['card_border']} !important;
}}

/* ── Tabs ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: {C['card']} !important;
    border-bottom: 2px solid {C['card_border']} !important;
    gap: 4px !important;
    padding: 0 8px !important;
    border-radius: 14px 14px 0 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {C['muted']} !important;
    font-weight: 600 !important;
    padding: 12px 18px !important;
    border-radius: 10px 10px 0 0 !important;
    transition: all 0.18s !important;
}}
.stTabs [aria-selected="true"] {{
    color: {C['accent']} !important;
    font-weight: 800 !important;
    background: {C['bg']} !important;
    border-bottom: 2px solid {C['accent']} !important;
}}
.stTabs [data-testid="stTabsContent"] {{
    background: {C['card']} !important;
    border: 1.5px solid {C['card_border']} !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
    padding: 20px !important;
}}

/* ── Toggle ───────────────────────────────────────────────── */
.stCheckbox label, [data-testid="stToggle"] label {{
    color: #b8cfe8 !important;
    font-weight: 700 !important;
}}

/* ── Progress / slider ────────────────────────────────────── */
.stSlider [data-testid="stSlider"] {{
    color: {C['accent']} !important;
}}

/* ── Semantic UI components ───────────────────────────────── */
.tag-pos {{
    background: {C['pos_bg']}; color: {C['pos_fg']};
    padding: 3px 13px; border-radius: 30px;
    font-size: 0.75rem; font-weight: 700; display: inline-block;
}}
.tag-neg {{
    background: {C['neg_bg']}; color: {C['neg_fg']};
    padding: 3px 13px; border-radius: 30px;
    font-size: 0.75rem; font-weight: 700; display: inline-block;
}}
.tag-neu {{
    background: {C['neu_bg']}; color: {C['neu_fg']};
    padding: 3px 13px; border-radius: 30px;
    font-size: 0.75rem; font-weight: 700; display: inline-block;
}}
.tag-new {{
    background: {C['tag_new_bg']}; color: {C['tag_new_fg']};
    padding: 2px 9px; border-radius: 20px;
    font-size: 0.65rem; font-weight: 800; display: inline-block;
    text-transform: uppercase; letter-spacing: 0.5px;
    vertical-align: middle; margin-left: 6px;
}}

/* ── Latest card ──────────────────────────────────────────── */
.latest-card {{
    background: {C['card']};
    border: 1.5px solid {C['card_border']};
    border-left: 4px solid {C['accent']};
    border-radius: 14px;
    padding: 16px 22px;
    margin-bottom: 14px;
}}
.latest-meta {{ color: {C['muted']}; font-size: 0.78rem; margin-top: 8px; }}
.latest-quote {{ color: {C['text']}; font-size: 0.93rem; line-height: 1.55;
                  margin: 6px 0; font-style: italic; }}

/* ── Report box ───────────────────────────────────────────── */
.report-box {{
    background: {C['rep_bg']};
    border: 1.5px solid {C['rep_border']};
    border-radius: 14px;
    padding: 22px 26px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: {C['text']} !important;
    white-space: pre-wrap;
    max-height: 380px;
    overflow-y: auto;
    line-height: 1.75;
}}

/* ── Confidence bar ───────────────────────────────────────── */
.conf-bar-wrap {{
    width: 100%; height: 6px;
    background: {C['card_border']}; border-radius: 3px; overflow: hidden;
}}
.conf-bar-fill {{
    height: 100%; border-radius: 3px;
    background: linear-gradient(90deg, {C['accent']}, {C['accent2']});
}}

/* ── Stat strip ───────────────────────────────────────────── */
.stat-strip {{
    display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px;
}}
.stat-pill {{
    background: {C['card']};
    border: 1.5px solid {C['card_border']};
    border-radius: 30px;
    padding: 8px 18px;
    font-size: 0.82rem;
    font-weight: 700;
    color: {C['text2']};
    white-space: nowrap;
}}

/* ── Divider / section break ──────────────────────────────── */
hr {{ border-color: {C['div']} !important; opacity: 0.7 !important; }}
.stCaption, caption, small {{ color: {C['muted']} !important; }}

/* ── Hide Streamlit chrome ────────────────────────────────── */
#MainMenu, footer, header {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


inject_css(C, DARK)


# =============================================================================
#  SELF-GENERATED SEED DATASET
#  50 original, handcrafted comments spanning 6 policy domains.
#  All text is original — not scraped, copied, or sourced from restricted data.
#  Dates are simulated across a 6-month window for trend charts.
# =============================================================================
_BASE_DATE = datetime.date(2025, 1, 1)

SEED_DATA = [
    # ── Economy & Tax ─────────────────────────────────────────────────────────
    ("The revised business grant scheme genuinely helped us survive the slow season.", "Economy & Tax", 15),
    ("Another property tax hike with zero improvement in local services is inexcusable.", "Economy & Tax", 8),
    ("Corporate incentives for the new tech park will create high-paying jobs. Strong policy.", "Economy & Tax", 22),
    ("Hiking sales tax on essentials during a cost-of-living crisis shows total disregard for families.", "Economy & Tax", 5),
    ("The economic regeneration zone has brought three new employers to our district this year.", "Economy & Tax", 40),
    ("The council's budget transparency portal is excellent — every citizen should use it.", "Economy & Tax", 55),
    ("Hidden fees in the new business licensing process are driving small traders away.", "Economy & Tax", 70),
    ("Reducing stamp duty for first-time buyers is exactly the kind of targeted relief we needed.", "Economy & Tax", 90),

    # ── Infrastructure & Transport ────────────────────────────────────────────
    ("The segregated cycle highway on the waterfront is world-class — our city finally gets it.", "Infrastructure", 12),
    ("Unrepaired sinkholes on the industrial estate have damaged two delivery vehicles this month.", "Infrastructure", 18),
    ("The new intercity rail link will transform commuting and reduce congestion enormously.", "Infrastructure", 28),
    ("Bus routes cut by 40% since last year — rural communities are completely isolated now.", "Infrastructure", 35),
    ("EV charging stations in every council car park by year-end is an ambitious but achievable target.", "Infrastructure", 50),
    ("The harbour bridge closure with zero alternative route was catastrophically mismanaged.", "Infrastructure", 60),
    ("Pavement tactile paving upgrades across the city centre have improved accessibility significantly.", "Infrastructure", 75),
    ("Flood drainage on the south ring road is completely inadequate — it floods every winter.", "Infrastructure", 85),
    ("Smart traffic signals at the five busiest junctions have cut rush-hour delays by 18%.", "Infrastructure", 100),
    ("The long-promised footbridge connecting the station to the business park is still not built.", "Infrastructure", 110),

    # ── Housing & Planning ────────────────────────────────────────────────────
    ("The community land trust pilot in Westgate is the most progressive housing policy in years.", "Housing", 20),
    ("Retrospective planning approval for the illegal riverside development sets a terrible precedent.", "Housing", 30),
    ("Purpose-built student accommodation near the university is relieving pressure on family housing.", "Housing", 45),
    ("Permitted development rights abuse is converting quality office space into substandard flats.", "Housing", 58),
    ("The rent-to-buy scheme gave my family a realistic pathway to ownership after seven years of renting.", "Housing", 72),
    ("Green-belt encroachment for luxury estates while social housing waiting lists grow is unforgivable.", "Housing", 82),
    ("Retrofit grants for Victorian terraces will reduce emissions and fuel poverty simultaneously.", "Housing", 95),
    ("The planning portal redesign is a genuine improvement — applications take half the time now.", "Housing", 115),
    ("Mixed-tenure social housing developments foster much healthier communities than segregated estates.", "Housing", 130),

    # ── Environment & Green Spaces ────────────────────────────────────────────
    ("The river rewilding project has restored otter and kingfisher populations. Remarkable work.", "Environment & Parks", 10),
    ("Industrial effluent discharge near the estuary has not been properly investigated despite reports.", "Environment & Parks", 25),
    ("Community allotment expansion programme has a two-year waiting list — scale it up urgently.", "Environment & Parks", 38),
    ("The new air quality monitoring network finally gives us real-time data to hold polluters accountable.", "Environment & Parks", 52),
    ("Replacing grass verges with wildflower meadows is beautiful, cheap, and brilliant for biodiversity.", "Environment & Parks", 65),
    ("Single-use plastic ban in council-run venues should extend to all licensed premises immediately.", "Environment & Parks", 78),
    ("The waste-to-energy plant proposal near primary schools is deeply alarming and must be refused.", "Environment & Parks", 92),
    ("Urban tree canopy target of 25% by 2030 is ambitious and the right direction for climate resilience.", "Environment & Parks", 105),
    ("Contaminated land remediation at the old gasworks site is long overdue — residents deserve answers.", "Environment & Parks", 120),

    # ── Public Safety & Justice ───────────────────────────────────────────────
    ("Neighbourhood watch digital integration with the council portal has visibly reduced burglaries.", "Public Safety", 14),
    ("Knife crime intervention programmes for at-risk youth deserve far more sustained investment.", "Public Safety", 32),
    ("Ambulance response times in rural postcodes remain dangerously above the national target.", "Public Safety", 47),
    ("The new community safety hub brings police, social services, and housing under one roof. Excellent.", "Public Safety", 63),
    ("CCTV expansion without a clear data governance policy is surveillance creep, not public safety.", "Public Safety", 80),
    ("The fire station closure in Millbrook leaves 15,000 residents with unacceptably slow coverage.", "Public Safety", 96),

    # ── Education & Community Services ───────────────────────────────────────
    ("Early years literacy programme results show a 22% improvement in school readiness. Keep investing.", "Education & Services", 17),
    ("Adult education centre cuts mean workers cannot access the retraining they need after redundancy.", "Education & Services", 33),
    ("Free school meals extension to all primary pupils is a straightforward public health intervention.", "Education & Services", 48),
    ("The new community hub model co-locating library, health, and job-centre services is inspired.", "Education & Services", 67),
    ("Special educational needs funding shortfall is forcing schools to exclude children who need support.", "Education & Services", 84),
    ("Digital inclusion tablets for care home residents bridging the connectivity gap — wonderful scheme.", "Education & Services", 102),
    ("Closing the only youth centre in Northfield will push teenagers onto streets. Short-sighted saving.", "Education & Services", 118),
    ("Graduate retention grants for healthcare professionals have reduced vacancy rates by a third.", "Education & Services", 135),
]


@st.cache_data
def build_seed_df() -> pd.DataFrame:
    rows = []
    for comment, theme, day_offset in SEED_DATA:
        blob = TextBlob(comment)
        polarity    = round(blob.sentiment.polarity, 4)
        subjectivity = round(blob.sentiment.subjectivity, 4)
        sentiment   = ("Positive" if polarity > 0.08 else
                       "Negative" if polarity < -0.08 else "Neutral")
        # Keyword confidence: how many theme keywords matched
        kws = TOPIC_KEYWORDS.get(theme, [])
        hits = sum(1 for kw in kws if kw.lower() in comment.lower())
        confidence  = min(round(hits / max(len(kws), 1) * 100 + 40, 0), 100)
        date_val    = _BASE_DATE + datetime.timedelta(days=day_offset)
        rows.append({
            "Comment":       comment,
            "Theme":         theme,
            "Sentiment":     sentiment,
            "Polarity":      polarity,
            "Subjectivity":  subjectivity,
            "Confidence %":  int(confidence),
            "Source":        "Seed Dataset",
            "Date":          date_val.strftime("%Y-%m-%d"),
            "Submitted At":  "—",
        })
    return pd.DataFrame(rows)


# =============================================================================
#  TOPIC KEYWORD DICTIONARY
# =============================================================================
TOPIC_KEYWORDS = {
    "Economy & Tax":        ["tax","economic","business","grant","sales","relief","jobs",
                              "development","zone","corporate","investment","budget","revenue",
                              "finance","fiscal","trade","employer","incentive","commerce",
                              "wage","income","spend","procurement","levy","tariff"],
    "Infrastructure":       ["road","bike","lane","pothole","bus","transit","bridge",
                              "construction","pedestrian","electric","fleet","traffic",
                              "highway","pavement","transport","rail","tram","station",
                              "port","freight","cycle","signal","junction","drainage"],
    "Housing":              ["housing","affordable","zoning","rent","condo","rental","homes",
                              "land trust","social housing","luxury","apartment","mortgage",
                              "shelter","property","planning","development","estate","permit",
                              "tenure","retrofit","flat","landlord","tenant","vacancy"],
    "Environment & Parks":  ["recycling","park","tree","pollution","solar","environment",
                              "river","green","corridor","native","climate","emission","waste",
                              "garden","biodiversity","habitat","meadow","allotment","canopy",
                              "wildflower","rewilding","effluent","contamination","air quality"],
    "Public Safety":        ["police","safety","crime","emergency","response","dispatch",
                              "mentor","youth","street","patrol","fire","ambulance","security",
                              "cctv","surveillance","knife","burglary","antisocial","violence",
                              "justice","prosecution","warden","neighbourhood"],
    "Education & Services": ["school","library","education","student","class","arts",
                              "curriculum","workshop","digital","literacy","after-school",
                              "teacher","college","learning","childcare","nursery","special",
                              "inclusion","retraining","skills","adult","graduate","sen",
                              "health","social care","community hub","youth centre"],
}


def detect_theme(text: str) -> tuple[str, int]:
    """Return (theme_name, confidence_pct)."""
    text_lower = text.lower()
    scores = {}
    for theme, keywords in TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits:
            scores[theme] = hits
    if not scores:
        return "General / Other", 30
    best = max(scores, key=scores.get)
    conf = min(int(scores[best] / len(TOPIC_KEYWORDS[best]) * 100 + 40), 100)
    return best, conf


def run_nlp(text: str) -> dict:
    """Full NLP pass on a single comment string."""
    blob        = TextBlob(str(text))
    polarity    = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)
    sentiment   = ("Positive" if polarity > 0.08 else
                   "Negative" if polarity < -0.08 else "Neutral")
    theme, conf = detect_theme(text)
    return dict(
        Sentiment    = sentiment,
        Polarity     = polarity,
        Subjectivity = subjectivity,
        Theme        = theme,
        confidence   = conf,
    )


# =============================================================================
#  FULL DATAFRAME BUILDER
# =============================================================================
def build_full_df() -> pd.DataFrame:
    base = build_seed_df().copy()
    extra_rows = (st.session_state.submitted_comments +
                  st.session_state.uploaded_rows)
    if extra_rows:
        extra = pd.DataFrame(extra_rows)
        return pd.concat([extra, base], ignore_index=True)
    return base


# =============================================================================
#  CHART FACTORY  — 5 distinct chart types
# =============================================================================
SCOL = {"Positive": "#00d68f", "Neutral": "#5b9bf5", "Negative": "#ff4d4d"}
TPAL = ["#3d8eff","#00e5b0","#f5a623","#b06bff","#ff7c5c","#00d4ff","#a3e635"]


def _style(fig, ax, C):
    fig.patch.set_facecolor(C["chart_bg"])
    ax.set_facecolor(C["chart_bg"])
    ax.spines[["top","right"]].set_visible(False)
    ax.spines["left"].set_color(C["chart_grid"])
    ax.spines["bottom"].set_color(C["chart_grid"])
    ax.tick_params(colors=C["chart_text"], labelsize=9.5)
    ax.yaxis.grid(True, color=C["chart_grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()


# ── 1. Sentiment bar chart ────────────────────────────────────────────────────
def chart_sentiment(df, C):
    counts = df["Sentiment"].value_counts().reindex(
        ["Positive","Neutral","Negative"], fill_value=0)
    fig, ax = plt.subplots(figsize=(5, 3.6))
    colors = [SCOL[s] for s in counts.index]
    bars = ax.bar(counts.index, counts.values, color=colors,
                  edgecolor=C["chart_bg"], linewidth=2.5, width=0.48, zorder=3)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x()+bar.get_width()/2, h+0.2,
                str(int(h)), ha="center", va="bottom",
                fontsize=13, fontweight="bold", color=C["text"])
    ax.set_ylabel("Comments", fontsize=10, color=C["chart_text"])
    ax.set_ylim(0, max(counts.max(),1)+3)
    ax.tick_params(axis="x", colors=C["text"], labelsize=11)
    _style(fig, ax, C)
    return fig


# ── 2. Horizontal theme bar ───────────────────────────────────────────────────
def chart_themes(df, C):
    counts = df["Theme"].value_counts()
    colors = TPAL[:len(counts)]
    fig, ax = plt.subplots(figsize=(5, 3.8))
    bars = ax.barh(counts.index, counts.values, color=colors,
                   edgecolor=C["chart_bg"], linewidth=1.5, height=0.52, zorder=3)
    for bar in bars:
        w = bar.get_width()
        ax.text(w+0.15, bar.get_y()+bar.get_height()/2,
                str(int(w)), va="center",
                fontsize=11, fontweight="bold", color=C["text"])
    ax.set_xlabel("Comments", fontsize=10, color=C["chart_text"])
    ax.set_xlim(0, max(counts.max(),1)+2.5)
    ax.invert_yaxis()
    ax.tick_params(axis="y", colors=C["text"])
    ax.xaxis.grid(True, color=C["chart_grid"], linewidth=0.6, zorder=0)
    ax.yaxis.grid(False)
    fig.patch.set_facecolor(C["chart_bg"])
    ax.set_facecolor(C["chart_bg"])
    ax.spines[["top","right","left"]].set_visible(False)
    ax.spines["bottom"].set_color(C["chart_grid"])
    plt.tight_layout()
    return fig


# ── 3. Polarity histogram ─────────────────────────────────────────────────────
def chart_polarity(df, C):
    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.hist(df["Polarity"], bins=16, color=C["accent"],
            edgecolor=C["chart_bg"], linewidth=1, zorder=3, alpha=0.85)
    ax.axvline(0, color=C["muted"], linestyle="--", linewidth=1.5)
    mean_v = df["Polarity"].mean()
    ax.axvline(mean_v, color="#f5a623", linestyle="-", linewidth=2,
               label=f"Mean {mean_v:+.2f}")
    ax.set_xlabel("Polarity Score  (−1 neg → +1 pos)", fontsize=10, color=C["chart_text"])
    ax.set_ylabel("Frequency", fontsize=10, color=C["chart_text"])
    legend = ax.legend(fontsize=9, framealpha=0.4, facecolor=C["chart_bg"])
    for t in legend.get_texts(): t.set_color(C["text"])
    _style(fig, ax, C)
    return fig


# ── 4. Stacked sentiment-by-theme ────────────────────────────────────────────
def chart_stacked(df, C):
    pivot = df.groupby(["Theme","Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive","Neutral","Negative"]:
        if col not in pivot.columns: pivot[col] = 0
    pivot = pivot[["Positive","Neutral","Negative"]]
    fig, ax = plt.subplots(figsize=(5, 3.8))
    bot = pd.Series([0]*len(pivot), index=pivot.index)
    for s, color in SCOL.items():
        ax.bar(pivot.index, pivot[s], bottom=bot, color=color,
               label=s, edgecolor=C["chart_bg"], linewidth=0.8)
        bot += pivot[s]
    ax.set_ylabel("Comments", fontsize=10, color=C["chart_text"])
    ax.tick_params(axis="x", rotation=26, labelsize=8.5, colors=C["text"])
    ax.tick_params(axis="y", colors=C["text"])
    legend = ax.legend(fontsize=9, loc="upper right", framealpha=0.4,
                       facecolor=C["chart_bg"])
    for t in legend.get_texts(): t.set_color(C["text"])
    _style(fig, ax, C)
    return fig


# ── 5. Subjectivity vs Polarity scatter ───────────────────────────────────────
def chart_scatter(df, C):
    fig, ax = plt.subplots(figsize=(5, 3.6))
    for sentiment, color in SCOL.items():
        sub_df = df[df["Sentiment"]==sentiment]
        ax.scatter(sub_df["Polarity"], sub_df["Subjectivity"],
                   c=color, label=sentiment, alpha=0.72,
                   s=55, edgecolors=C["chart_bg"], linewidths=1, zorder=3)
    ax.axvline(0, color=C["muted"], linestyle="--", linewidth=1, alpha=0.6)
    ax.axhline(0.5, color=C["muted"], linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("Polarity Score", fontsize=10, color=C["chart_text"])
    ax.set_ylabel("Subjectivity Score", fontsize=10, color=C["chart_text"])
    ax.text(-0.95, 0.97, "Negative\nSubjective", fontsize=7.5,
            color=C["muted"], va="top")
    ax.text(0.55, 0.97, "Positive\nSubjective", fontsize=7.5,
            color=C["muted"], va="top")
    ax.text(-0.95, 0.03, "Negative\nObjective", fontsize=7.5,
            color=C["muted"], va="bottom")
    ax.text(0.55, 0.03, "Positive\nObjective", fontsize=7.5,
            color=C["muted"], va="bottom")
    legend = ax.legend(fontsize=9, framealpha=0.4, facecolor=C["chart_bg"])
    for t in legend.get_texts(): t.set_color(C["text"])
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-0.05, 1.05)
    _style(fig, ax, C)
    return fig


# ── 6. Timeline (simulated trend) ────────────────────────────────────────────
def chart_timeline(df, C):
    if "Date" not in df.columns or df["Date"].isna().all():
        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.text(0.5, 0.5, "No date data available",
                ha="center", va="center", color=C["muted"])
        ax.axis("off")
        fig.patch.set_facecolor(C["chart_bg"])
        return fig

    df2 = df.copy()
    df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce")
    df2 = df2.dropna(subset=["Date"])
    if df2.empty:
        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.text(0.5, 0.5, "No date data available",
                ha="center", va="center", color=C["muted"])
        ax.axis("off")
        fig.patch.set_facecolor(C["chart_bg"])
        return fig

    df2["Week"] = df2["Date"].dt.to_period("W").dt.start_time
    weekly = df2.groupby(["Week","Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive","Neutral","Negative"]:
        if col not in weekly.columns: weekly[col] = 0

    fig, ax = plt.subplots(figsize=(10, 2.8))
    for s, color in SCOL.items():
        ax.fill_between(weekly.index, weekly[s],
                        alpha=0.2, color=color)
        ax.plot(weekly.index, weekly[s], color=color,
                linewidth=2, label=s, marker="o", markersize=4)
    ax.set_ylabel("Count", fontsize=9, color=C["chart_text"])
    ax.tick_params(axis="x", rotation=25, labelsize=8, colors=C["text"])
    ax.tick_params(axis="y", colors=C["text"])
    legend = ax.legend(fontsize=9, framealpha=0.4, facecolor=C["chart_bg"],
                       loc="upper left")
    for t in legend.get_texts(): t.set_color(C["text"])
    _style(fig, ax, C)
    return fig


# ── Per-theme word cloud ──────────────────────────────────────────────────────
EXTRA_STOP = {
    "will","city","new","one","also","get","make","need","use","say",
    "go","come","want","people","think","know","good","much","really",
    "well","way","time","year","many","still","even","back","us","our",
    "more","very","been","have","this","that","with","from","they","their",
    "were","are","has","had","not","but","for","and","the","its","into",
}

THEME_CMAPS = {
    "Economy & Tax":        "YlOrBr",
    "Infrastructure":       "Blues",
    "Housing":              "Purples",
    "Environment & Parks":  "Greens",
    "Public Safety":        "Oranges",
    "Education & Services": "PuBuGn",
    "General / Other":      "Greys",
}


def make_wordcloud(text_series: pd.Series, colormap: str, C: dict):
    combined = " ".join(text_series.astype(str).tolist()).strip()
    fig, ax = plt.subplots(figsize=(6, 2.8))
    fig.patch.set_facecolor(C["wc_bg"])
    ax.set_facecolor(C["wc_bg"])

    if len(combined.split()) < 5:
        ax.text(0.5, 0.5, "Add more comments to generate a word cloud",
                ha="center", va="center", fontsize=11, color=C["muted"])
        ax.axis("off")
        return fig

    stopwords = STOPWORDS.union(EXTRA_STOP)
    try:
        wc = WordCloud(
            width=820, height=300,
            background_color=C["wc_bg"],
            colormap=colormap,
            max_words=60,
            collocations=False,
            prefer_horizontal=0.78,
            stopwords=stopwords,
            min_font_size=10,
            contour_width=0,
        ).generate(combined)
        ax.imshow(wc, interpolation="bilinear")
    except Exception:
        ax.text(0.5, 0.5, "Word cloud unavailable",
                ha="center", va="center", color=C["muted"])
    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig


# =============================================================================
#  POLICY INSIGHT REPORT
# =============================================================================
def generate_report(df: pd.DataFrame) -> str:
    n = len(df)
    if n == 0: return "No data to report."
    pos = (df["Sentiment"]=="Positive").sum()
    neg = (df["Sentiment"]=="Negative").sum()
    neu = (df["Sentiment"]=="Neutral").sum()
    avg = df["Polarity"].mean()
    now = datetime.datetime.now().strftime("%d %B %Y  %H:%M")
    live = len(df[df["Source"] != "Seed Dataset"])

    L = []
    L += [
        "╔══════════════════════════════════════════════════════════════╗",
        "║        C I T I Z E N L E N S   —   P O L I C Y             ║",
        "║              I N S I G H T   R E P O R T                    ║",
        "╚══════════════════════════════════════════════════════════════╝",
        f"\n  Generated  : {now}",
        f"  Comments   : {n} analyzed  ({live} live, {n-live} from seed dataset)",
        f"  Filters    : see dashboard sidebar\n",
    ]
    L += [
        "── OVERALL SENTIMENT ──────────────────────────────────────────",
        f"  ✅ Positive   : {pos:>4}  ({round(pos/n*100) if n else 0}%)",
        f"  ➖ Neutral    : {neu:>4}  ({round(neu/n*100) if n else 0}%)",
        f"  ❌ Negative   : {neg:>4}  ({round(neg/n*100) if n else 0}%)",
        f"  📊 Avg Polarity : {avg:+.4f}",
        f"  📐 Avg Subjectivity : {df['Subjectivity'].mean():.4f}\n",
    ]
    L.append("── PER-THEME BREAKDOWN ────────────────────────────────────────")
    stats = df.groupby("Theme").agg(
        Count=("Sentiment","count"),
        Pos  =("Sentiment", lambda x:(x=="Positive").sum()),
        Neg  =("Sentiment", lambda x:(x=="Negative").sum()),
        Neu  =("Sentiment", lambda x:(x=="Neutral").sum()),
        Pol  =("Polarity","mean"),
        Subj =("Subjectivity","mean"),
    ).sort_values("Count", ascending=False)

    for theme, r in stats.iterrows():
        mood = ("🟢" if r["Pol"] > 0.06 else
                "🔴" if r["Pol"] < -0.06 else "🟡")
        L += [
            f"\n  {mood}  {theme}",
            f"     Comments : {int(r['Count'])}  |  "
            f"✅ {int(r['Pos'])} pos  ➖ {int(r['Neu'])} neu  ❌ {int(r['Neg'])} neg",
            f"     Avg Polarity : {r['Pol']:+.4f}   "
            f"Avg Subjectivity : {r['Subj']:.4f}",
        ]

    L.append("\n\n── TOP 3 MOST POSITIVE COMMENTS ───────────────────────────────")
    for i,(_, r) in enumerate(df[df["Sentiment"]=="Positive"]
                               .nlargest(3,"Polarity").iterrows(), 1):
        L += [f"\n  {i}.  [{r['Polarity']:+.4f}]  {r['Theme']}",
              f'       "{r["Comment"]}"']

    L.append("\n\n── TOP 3 MOST NEGATIVE COMMENTS ───────────────────────────────")
    for i,(_, r) in enumerate(df[df["Sentiment"]=="Negative"]
                               .nsmallest(3,"Polarity").iterrows(), 1):
        L += [f"\n  {i}.  [{r['Polarity']:+.4f}]  {r['Theme']}",
              f'       "{r["Comment"]}"']

    L.append("\n\n── POLICY RECOMMENDATIONS ─────────────────────────────────────")
    L.append("  Themes ranked by negative comment count (highest = most urgent):\n")
    neg_themes = (df[df["Sentiment"]=="Negative"]
                  .groupby("Theme").size()
                  .sort_values(ascending=False))
    for i, (theme, cnt) in enumerate(neg_themes.items(), 1):
        bar = "█" * min(cnt, 20)
        L.append(f"  {i}. ⚠️  {theme:35s}  {bar}  ({cnt})")

    pos_themes = (df[df["Sentiment"]=="Positive"]
                  .groupby("Theme").size()
                  .sort_values(ascending=False))
    L.append("\n  Themes with strongest positive sentiment (best practices):\n")
    for i, (theme, cnt) in enumerate(pos_themes.items(), 1):
        bar = "█" * min(cnt, 20)
        L.append(f"  {i}. ✅  {theme:35s}  {bar}  ({cnt})")

    L += [
        "\n\n╔══════════════════════════════════════════════════════════════╗",
        "║  CitizenLens  |  Open Government Hackathon 2025  |  v2.0   ║",
        "║  Built with Streamlit · TextBlob · WordCloud · Matplotlib  ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ]
    return "\n".join(L)


# =============================================================================
#  MAIN DASHBOARD
# =============================================================================
def main():

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        new_dark = st.toggle(
            "🌙 Dark Mode" if not DARK else "☀️ Light Mode",
            value=DARK,
            key="theme_toggle",
        )
        if new_dark != DARK:
            st.session_state.dark_mode = new_dark
            st.rerun()

        st.divider()
        st.markdown("### 🔍 Filters")
        df_all = build_full_df()

        all_themes = sorted(df_all["Theme"].unique().tolist())
        sel_themes = st.multiselect("Policy Theme", all_themes, default=all_themes)
        sel_sents  = st.multiselect("Sentiment",
                                    ["Positive","Neutral","Negative"],
                                    default=["Positive","Neutral","Negative"])
        p_min = float(df_all["Polarity"].min())
        p_max = float(df_all["Polarity"].max())
        pol_r = st.slider("Polarity Range", p_min, p_max, (p_min, p_max), 0.01)
        subj_r = st.slider("Subjectivity Range", 0.0, 1.0, (0.0, 1.0), 0.05)

        st.divider()
        src_filter = st.radio("Data source",
                              ["All","Live & uploaded only","Seed data only"])

        st.divider()
        live_n = len(st.session_state.submitted_comments)
        up_n   = len(st.session_state.uploaded_rows)
        st.markdown(f"**📬 Live submissions:** `{live_n}`")
        st.markdown(f"**📂 CSV rows imported:** `{up_n}`")
        if live_n + up_n > 0:
            if st.button("🗑️  Clear all live data", use_container_width=True):
                st.session_state.submitted_comments = []
                st.session_state.uploaded_rows = []
                st.rerun()

        st.divider()
        st.markdown("""
**How CitizenLens works**
1. Citizens submit a comment  
2. TextBlob NLP scores sentiment  
3. Keyword clustering finds the theme  
4. Every chart updates instantly  
5. Download the Policy Report  
""")

    # ── FILTER ────────────────────────────────────────────────────────────────
    df = build_full_df()
    if src_filter == "Live & uploaded only":
        df = df[df["Source"] != "Seed Dataset"]
    elif src_filter == "Seed data only":
        df = df[df["Source"] == "Seed Dataset"]

    filtered = df[
        df["Theme"].isin(sel_themes) &
        df["Sentiment"].isin(sel_sents) &
        df["Polarity"].between(pol_r[0], pol_r[1]) &
        df["Subjectivity"].between(subj_r[0], subj_r[1])
    ]

    total     = len(filtered)
    pos_count = (filtered["Sentiment"]=="Positive").sum()
    neg_count = (filtered["Sentiment"]=="Negative").sum()
    neu_count = (filtered["Sentiment"]=="Neutral").sum()
    avg_pol   = filtered["Polarity"].mean() if total else 0.0
    avg_subj  = filtered["Subjectivity"].mean() if total else 0.0

    # ── HERO ──────────────────────────────────────────────────────────────────
    mode_label = "🌙 Dark" if DARK else "☀️ Light"
    st.markdown(f"""
<div class="hero">
 <div class="hero-inner">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;
              flex-wrap:wrap;gap:20px;">
   <div>
    <div class="hero-badge">🏆 Open Government Hackathon 2025</div>
    <h1>🏛️ CitizenLens</h1>
    <p class="hero-sub">
     AI-powered policy comment intelligence platform &nbsp;·&nbsp;
     Sentiment · Topic Clustering · Visual Reports · {mode_label} Mode
    </p>
   </div>
   <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <div class="hero-stat">
     <div class="hero-stat-label">Total</div>
     <div class="hero-stat-val">{len(df)}</div>
    </div>
    <div class="hero-stat">
     <div class="hero-stat-label">Themes</div>
     <div class="hero-stat-val">{df['Theme'].nunique()}</div>
    </div>
    <div class="hero-stat">
     <div class="hero-stat-label">Live</div>
     <div class="hero-stat-val">{live_n + up_n}</div>
    </div>
   </div>
  </div>
 </div>
</div>
""", unsafe_allow_html=True)

    # =========================================================================
    #  TABBED LAYOUT  — Submit | Dashboard | Upload | About
    # =========================================================================
    tab_submit, tab_dash, tab_upload, tab_about = st.tabs([
        "✍️  Submit Comment",
        "📊  Dashboard",
        "📂  Bulk Upload",
        "ℹ️  About",
    ])

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 1 — SUBMIT COMMENT
    # ─────────────────────────────────────────────────────────────────────────
    with tab_submit:
        st.markdown('<p class="section-label">✍️ Share Your View on City Policies</p>',
                    unsafe_allow_html=True)
        st.markdown(f"""
<div class="submit-wrap">
 <h3>💬 What do you think about local government policies?</h3>
 <p class="submit-desc">
  Write your comment below — in your own words, about any policy area.
  CitizenLens will instantly analyze your comment for sentiment, measure
  subjectivity, detect the policy topic, and add it to the live dashboard.
  Your feedback helps shape better policy decisions.
 </p>
</div>
""", unsafe_allow_html=True)

        with st.form("comment_form", clear_on_submit=True):
            col_a, col_b = st.columns([3,1])
            with col_a:
                user_text = st.text_area(
                    "Your comment *",
                    placeholder=(
                        "Write your genuine feedback here — e.g.:\n"
                        "\"The new cycle lanes on the high street have transformed "
                        "my morning commute. More people are cycling and the air "
                        "quality has noticeably improved. Keep investing in this.\""
                    ),
                    height=130,
                )
            with col_b:
                policy_hint = st.selectbox(
                    "Policy area (optional)",
                    ["Auto-detect 🤖"] + list(TOPIC_KEYWORDS.keys()) + ["General / Other"],
                    help="Let the AI detect it, or choose manually.",
                )
                name_in = st.text_input("Your name (optional)", placeholder="Anonymous")
                location_in = st.text_input("Location (optional)", placeholder="e.g. District 4")

            do_submit = st.form_submit_button(
                "🔍  Analyze & Submit My Comment",
                use_container_width=True,
            )

            if do_submit:
                txt = user_text.strip()
                if len(txt) < 10:
                    st.error("⚠️  Please write at least 10 characters.")
                else:
                    nlp = run_nlp(txt)
                    if "Auto-detect" not in policy_hint:
                        nlp["Theme"] = policy_hint
                        nlp["confidence"] = 99
                    name = name_in.strip() or "Anonymous"
                    loc  = location_in.strip() or "—"
                    st.session_state.submitted_comments.insert(0, {
                        "Comment":      txt,
                        "Theme":        nlp["Theme"],
                        "Sentiment":    nlp["Sentiment"],
                        "Polarity":     nlp["Polarity"],
                        "Subjectivity": nlp["Subjectivity"],
                        "Confidence %": nlp["confidence"],
                        "Source":       f"Live — {name}",
                        "Date":         datetime.date.today().strftime("%Y-%m-%d"),
                        "Submitted At": datetime.datetime.now().strftime("%H:%M:%S"),
                    })
                    emoji = "✅" if nlp["Sentiment"]=="Positive" else \
                            ("❌" if nlp["Sentiment"]=="Negative" else "➖")
                    mood  = ("This comment expresses satisfaction." if nlp["Polarity"] > 0.3 else
                             "This comment expresses serious concern." if nlp["Polarity"] < -0.3 else
                             "This comment has mixed or measured sentiment.")
                    st.success(
                        f"{emoji}  **Comment analyzed!**  \n"
                        f"Sentiment: **{nlp['Sentiment']}** &nbsp; "
                        f"Polarity: `{nlp['Polarity']:+.4f}` &nbsp; "
                        f"Subjectivity: `{nlp['Subjectivity']:.4f}`  \n"
                        f"Theme: **{nlp['Theme']}** &nbsp; "
                        f"Confidence: `{nlp['confidence']}%`  \n"
                        f"*{mood}*"
                    )
                    st.rerun()

        # Show recent live submissions
        if st.session_state.submitted_comments:
            st.markdown('<p class="section-label">📬 Recent Submissions</p>',
                        unsafe_allow_html=True)
            for entry in st.session_state.submitted_comments[:5]:
                tag = ("tag-pos" if entry["Sentiment"]=="Positive" else
                       ("tag-neg" if entry["Sentiment"]=="Negative" else "tag-neu"))
                st.markdown(f"""
<div class="latest-card">
 <span class="latest-meta">
  {entry.get('Source','—')} &nbsp;·&nbsp; {entry['Theme']}
  &nbsp;·&nbsp; {entry.get('Submitted At','—')}
 </span>
 <span class="{tag}">{entry['Sentiment']}</span>
 <span class="tag-new">NEW</span>
 <p class="latest-quote">"{entry['Comment']}"</p>
 <div class="conf-bar-wrap" style="margin-top:8px;">
  <div class="conf-bar-fill" style="width:{entry.get('Confidence %',50)}%;"></div>
 </div>
 <span class="latest-meta">
  Polarity {entry['Polarity']:+.4f} &nbsp;·&nbsp;
  Subjectivity {entry['Subjectivity']:.4f} &nbsp;·&nbsp;
  Topic confidence {entry.get('Confidence %','?')}%
 </span>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("💡  No live submissions yet — be the first to submit above!")

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 2 — DASHBOARD
    # ─────────────────────────────────────────────────────────────────────────
    with tab_dash:

        # KPIs
        st.markdown('<p class="section-label">📊 Overview Metrics</p>',
                    unsafe_allow_html=True)
        k1,k2,k3,k4,k5,k6 = st.columns(6)
        k1.metric("💬 Total",       total)
        k2.metric("✅ Positive",    pos_count,
                  delta=f"{round(pos_count/total*100) if total else 0}%")
        k3.metric("➖ Neutral",     neu_count,
                  delta=f"{round(neu_count/total*100) if total else 0}%",
                  delta_color="off")
        k4.metric("❌ Negative",    neg_count,
                  delta=f"{round(neg_count/total*100) if total else 0}%",
                  delta_color="inverse")
        k5.metric("📈 Avg Polarity",  f"{avg_pol:+.3f}")
        k6.metric("🔬 Avg Subjectivity", f"{avg_subj:.3f}")

        if total == 0:
            st.warning("⚠️  No comments match your current filters.")
            return

        # Charts row 1
        st.markdown('<p class="section-label">📈 Sentiment & Theme Analysis</p>',
                    unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="cl-card"><h4>🎭 Sentiment Distribution</h4>',
                        unsafe_allow_html=True)
            st.pyplot(chart_sentiment(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="cl-card"><h4>🗂️ Comments by Policy Theme</h4>',
                        unsafe_allow_html=True)
            st.pyplot(chart_themes(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)

        # Charts row 2
        cc, cd = st.columns(2)
        with cc:
            st.markdown('<div class="cl-card"><h4>📉 Polarity Score Distribution</h4>',
                        unsafe_allow_html=True)
            st.pyplot(chart_polarity(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)
        with cd:
            st.markdown('<div class="cl-card"><h4>🧩 Sentiment by Theme (Stacked)</h4>',
                        unsafe_allow_html=True)
            st.pyplot(chart_stacked(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)

        # Charts row 3 — full width scatter + timeline
        st.markdown('<div class="cl-card"><h4>🔬 Subjectivity vs Polarity Scatter</h4>',
                    unsafe_allow_html=True)
        st.pyplot(chart_scatter(filtered, C))
        st.caption("Each dot is one comment. Horizontal axis = sentiment direction. "
                   "Vertical axis = how opinion-based vs fact-based the comment is.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="cl-card"><h4>📅 Sentiment Trend Over Time</h4>',
                    unsafe_allow_html=True)
        st.pyplot(chart_timeline(filtered, C))
        st.caption("Weekly aggregated sentiment based on submission date.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Per-theme word clouds
        st.markdown('<p class="section-label">☁️ Word Clouds by Policy Theme</p>',
                    unsafe_allow_html=True)
        st.caption("Word size = frequency within each theme's comments. "
                   "Each theme has a distinct colour palette.")

        themes_present = sorted(filtered["Theme"].unique().tolist())
        if themes_present:
            for i in range(0, len(themes_present), 2):
                wc1, wc2 = st.columns(2)
                for j, col in enumerate([wc1, wc2]):
                    idx = i + j
                    if idx < len(themes_present):
                        tname    = themes_present[idx]
                        tcomms   = filtered[filtered["Theme"]==tname]["Comment"]
                        cmap     = THEME_CMAPS.get(tname, "viridis")
                        t_pos    = (filtered[filtered["Theme"]==tname]["Sentiment"]=="Positive").sum()
                        t_neg    = (filtered[filtered["Theme"]==tname]["Sentiment"]=="Negative").sum()
                        t_neu    = (filtered[filtered["Theme"]==tname]["Sentiment"]=="Neutral").sum()
                        t_avg    = filtered[filtered["Theme"]==tname]["Polarity"].mean()
                        with col:
                            st.markdown(
                                f'<div class="cl-card"><h4>☁️ {tname}</h4>',
                                unsafe_allow_html=True)
                            st.caption(
                                f"{len(tcomms)} comments · "
                                f"✅ {t_pos} · ➖ {t_neu} · ❌ {t_neg} · "
                                f"avg polarity {t_avg:+.3f}"
                            )
                            st.pyplot(make_wordcloud(tcomms, cmap, C))
                            st.markdown('</div>', unsafe_allow_html=True)

        # Theme deep dive
        st.markdown('<p class="section-label">🔬 Theme Deep Dive</p>',
                    unsafe_allow_html=True)
        with st.expander("Expand — read every comment by theme", expanded=False):
            if themes_present:
                ttabs = st.tabs(themes_present)
                for ttab, tname in zip(ttabs, themes_present):
                    with ttab:
                        tdf  = filtered[filtered["Theme"]==tname].copy()
                        tavg = tdf["Polarity"].mean()
                        mood = ("🟢 Mostly Positive" if tavg > 0.06 else
                                "🔴 Mostly Negative" if tavg < -0.06 else "🟡 Mixed")
                        st.markdown(
                            f"**{len(tdf)} comments** &nbsp;·&nbsp; {mood} "
                            f"&nbsp;·&nbsp; Avg polarity: **{tavg:+.4f}**"
                        )
                        st.dataframe(
                            tdf[["Comment","Sentiment","Polarity","Subjectivity",
                                 "Confidence %","Source","Date"]]
                            .reset_index(drop=True),
                            use_container_width=True,
                        )

        # Data table
        st.markdown('<p class="section-label">📋 All Comments</p>',
                    unsafe_allow_html=True)
        st.caption(f"Showing **{total}** of **{len(df)}** comments · "
                   "Sentiment column is colour-coded")

        def colour_sentiment(val):
            m = {
                "Positive": f"background-color:{C['pos_bg']};color:{C['pos_fg']};font-weight:700;",
                "Negative": f"background-color:{C['neg_bg']};color:{C['neg_fg']};font-weight:700;",
                "Neutral":  f"background-color:{C['neu_bg']};color:{C['neu_fg']};font-weight:700;",
            }
            return m.get(val, "")

        styled_df = (filtered
                     .reset_index(drop=True)
                     .style.applymap(colour_sentiment, subset=["Sentiment"]))
        st.dataframe(styled_df, use_container_width=True, height=380)

        # Export
        st.markdown('<p class="section-label">💾 Export</p>',
                    unsafe_allow_html=True)
        ex1, ex2 = st.columns(2)
        with ex1:
            st.markdown('<div class="cl-card"><h4>📊 Enriched Dataset — CSV</h4>',
                        unsafe_allow_html=True)
            st.markdown(
                f"<p style='color:{C['text2']};font-size:0.875rem;margin-bottom:16px;'>"
                f"All {total} filtered comments with Sentiment, Polarity, Subjectivity, "
                f"Theme, and Confidence scores — ready for Excel, Sheets, or further analysis.</p>",
                unsafe_allow_html=True)
            buf = io.StringIO()
            filtered.to_csv(buf, index=False)
            st.download_button(
                "⬇️  Download CSV",
                buf.getvalue().encode("utf-8"),
                f"citizenlens_{datetime.date.today()}.csv",
                "text/csv",
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with ex2:
            st.markdown('<div class="cl-card"><h4>📄 Policy Insight Report — TXT</h4>',
                        unsafe_allow_html=True)
            st.markdown(
                f"<p style='color:{C['text2']};font-size:0.875rem;margin-bottom:16px;'>"
                f"Formatted executive report: sentiment summary, per-theme breakdown, "
                f"top/worst comments, and ranked policy recommendations.</p>",
                unsafe_allow_html=True)
            report = generate_report(filtered)
            st.download_button(
                "📄  Download Policy Report",
                report.encode("utf-8"),
                f"citizenlens_report_{datetime.date.today()}.txt",
                "text/plain",
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("👀 Preview Policy Report", expanded=False):
            st.markdown(
                f'<div class="report-box">{generate_report(filtered)}</div>',
                unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 3 — BULK CSV UPLOAD
    # ─────────────────────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown('<p class="section-label">📂 Bulk Upload Existing Feedback</p>',
                    unsafe_allow_html=True)
        st.markdown(f"""
<div class="cl-card">
 <h4>📤 Upload a CSV file of citizen comments</h4>
 <p style="color:{C['text2']};font-size:0.875rem;margin-bottom:0;">
  Upload any CSV that contains a column named <code>comment</code> or <code>Comment</code>.
  CitizenLens will run the full NLP pipeline on every row automatically.
  Optional columns: <code>source</code>, <code>date</code>, <code>name</code>.
 </p>
</div>
""", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="Must have a 'comment' or 'Comment' column.",
        )
        if uploaded:
            try:
                raw = pd.read_csv(uploaded)
                # Normalize column name
                col_map = {c.lower(): c for c in raw.columns}
                if "comment" not in col_map:
                    st.error("❌  CSV must have a 'comment' column.")
                else:
                    comment_col = col_map["comment"]
                    with st.spinner(f"Analyzing {len(raw)} comments…"):
                        new_rows = []
                        for _, row in raw.iterrows():
                            txt = str(row[comment_col]).strip()
                            if len(txt) < 3:
                                continue
                            nlp = run_nlp(txt)
                            new_rows.append({
                                "Comment":      txt,
                                "Theme":        nlp["Theme"],
                                "Sentiment":    nlp["Sentiment"],
                                "Polarity":     nlp["Polarity"],
                                "Subjectivity": nlp["Subjectivity"],
                                "Confidence %": nlp["confidence"],
                                "Source":       str(row.get("source", row.get("Source","CSV Upload"))),
                                "Date":         str(row.get("date",  row.get("Date", datetime.date.today()))),
                                "Submitted At": datetime.datetime.now().strftime("%H:%M:%S"),
                            })
                        st.session_state.uploaded_rows = (
                            st.session_state.uploaded_rows + new_rows
                        )
                    st.success(
                        f"✅  **{len(new_rows)} comments imported and analyzed!**  "
                        f"Switch to the Dashboard tab to see the results."
                    )
                    # Preview
                    preview_df = pd.DataFrame(new_rows)
                    st.dataframe(
                        preview_df[["Comment","Sentiment","Polarity","Theme"]]
                        .head(10),
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"❌  Could not process file: {e}")

        st.markdown(f"""
<div class="cl-card" style="margin-top:20px;">
 <h4>📋 CSV Format Example</h4>
 <p style="color:{C['text2']};font-size:0.875rem;">
  Your CSV should look like this (only the <code>comment</code> column is required):
 </p>
</div>
""", unsafe_allow_html=True)
        example = pd.DataFrame({
            "comment": [
                "The new park renovation has completely transformed our neighbourhood.",
                "Bus routes to rural areas are still inadequate despite promises.",
                "Affordable housing targets are not being met — we need accountability.",
            ],
            "source":  ["Resident Survey", "Public Forum", "Email Submission"],
            "date":    ["2025-03-01", "2025-03-15", "2025-04-01"],
        })
        st.dataframe(example, use_container_width=True)
        buf2 = io.StringIO()
        example.to_csv(buf2, index=False)
        st.download_button(
            "⬇️  Download Example CSV Template",
            buf2.getvalue().encode("utf-8"),
            "citizenlens_template.csv",
            "text/csv",
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 4 — ABOUT
    # ─────────────────────────────────────────────────────────────────────────
    with tab_about:
        st.markdown('<p class="section-label">ℹ️ About CitizenLens</p>',
                    unsafe_allow_html=True)
        st.markdown(f"""
<div class="cl-card">
 <h4>🏛️ What is CitizenLens?</h4>
 <p style="color:{C['text2']};line-height:1.75;font-size:0.9rem;">
  CitizenLens is an open-source AI platform that makes citizen feedback useful
  for policymakers at scale. Instead of thousands of comments sitting unread in
  inboxes, CitizenLens runs every comment through a natural language processing
  pipeline — scoring sentiment, measuring subjectivity, and clustering by policy
  topic — then visualises the results in a real-time dashboard.
 </p>
</div>

<div class="cl-card">
 <h4>🧠 NLP Pipeline</h4>
 <p style="color:{C['text2']};line-height:1.75;font-size:0.9rem;">
  <strong>Step 1 — Sentiment Scoring:</strong> TextBlob calculates a
  polarity score from −1.0 (strongly negative) to +1.0 (strongly positive)
  and a subjectivity score from 0.0 (purely factual) to 1.0 (purely opinion).
  Comments above +0.08 are Positive; below −0.08 are Negative; the rest are Neutral.<br><br>
  <strong>Step 2 — Topic Clustering:</strong> A custom keyword-frequency dictionary
  maps each comment to one of six policy domains. The number of keyword hits
  relative to total domain keywords produces a Confidence % score.<br><br>
  <strong>Step 3 — Visualisation:</strong> Six chart types + per-theme word clouds
  update live as filters change. The Policy Report aggregates everything into a
  structured executive summary ready for decision-makers.
 </p>
</div>

<div class="cl-card">
 <h4>📊 Dataset</h4>
 <p style="color:{C['text2']};line-height:1.75;font-size:0.9rem;">
  The seed dataset is 50 original, hand-authored comments covering six policy
  domains. All text was written specifically for this project — it is not
  scraped, copied, or sourced from any restricted or government-only dataset.
  It satisfies the hackathon rule: <em>"Teams must use only publicly available
  or self-generated datasets."</em>
 </p>
</div>

<div class="cl-card">
 <h4>🛠️ Tech Stack</h4>
 <div class="stat-strip">
  <div class="stat-pill">🔴 Streamlit — UI Framework</div>
  <div class="stat-pill">🧠 TextBlob — NLP / Sentiment</div>
  <div class="stat-pill">🐼 Pandas — Data Pipeline</div>
  <div class="stat-pill">☁️ WordCloud — Topic Clouds</div>
  <div class="stat-pill">📈 Matplotlib — Charts</div>
  <div class="stat-pill">🐙 GitHub — Version Control</div>
  <div class="stat-pill">🚀 Streamlit Cloud — Hosting</div>
 </div>
</div>

<div class="cl-card">
 <h4>⚖️ License & Ethics</h4>
 <p style="color:{C['text2']};line-height:1.75;font-size:0.9rem;">
  CitizenLens is MIT licensed. No personal data is stored beyond the session.
  Submitted comments are held in browser session state only — they are not
  written to disk or transmitted to any external server.
  The NLP engine is used solely to inform policymakers — it does not make
  autonomous decisions and all outputs should be reviewed by a human.
 </p>
</div>
""", unsafe_allow_html=True)

    # Footer
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{C['muted']};font-size:11px;'>"
        "CitizenLens v2.0 &nbsp;·&nbsp; "
        "Streamlit · TextBlob · WordCloud · Matplotlib &nbsp;·&nbsp; "
        "Open Government Hackathon 2025 &nbsp;·&nbsp; MIT License &nbsp;·&nbsp; "
        f"{'🌙 Dark' if DARK else '☀️ Light'} Mode"
        "</p>",
        unsafe_allow_html=True,
    )


# =============================================================================
if __name__ == "__main__":
    main()
