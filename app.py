# =============================================================================
#  CitizenLens — AI-Powered Policy Comment Intelligence Platform
#  Version     : 3.0.0
#  Hackathon   : Open Government Hackathon 2025
#  License     : MIT
#
#  ARCHITECTURE NOTES v3.0
#  ───────────────────────
#  • Theme toggle uses st.checkbox() inside the sidebar — Streamlit handles
#    its own rerun for widget changes, which PRESERVES sidebar open/closed
#    state. Never call st.rerun() for theme changes.
#  • TOPIC_KEYWORDS defined at module level before any function that uses it.
#  • pandas .style.map() used (not deprecated .applymap()).
#  • Every matplotlib figure is closed via plt.close(fig) after st.pyplot().
#  • matplotlib.use("Agg") set before any plt import side-effects.
# =============================================================================

import io
import datetime
import matplotlib
matplotlib.use("Agg")                          # must be before pyplot import

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG — must be the VERY FIRST Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CitizenLens | Policy Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "dark_mode":          False,
    "submitted_comments": [],
    "uploaded_rows":      [],
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC KEYWORD DICTIONARY
#  Must be defined at module level (before build_seed_df) so the
#  @st.cache_data function can reference it on first cached call.
# ─────────────────────────────────────────────────────────────────────────────
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Economy & Tax": [
        "tax","economic","business","grant","sales","relief","jobs","development",
        "zone","corporate","investment","budget","revenue","finance","fiscal","trade",
        "employer","incentive","commerce","wage","income","spend","procurement",
        "levy","tariff","stamp duty","business rates",
    ],
    "Infrastructure": [
        "road","bike","lane","pothole","bus","transit","bridge","construction",
        "pedestrian","electric","fleet","traffic","highway","pavement","transport",
        "rail","tram","station","port","freight","cycle","signal","junction",
        "drainage","footbridge","sinkhole",
    ],
    "Housing": [
        "housing","affordable","zoning","rent","condo","rental","homes","land trust",
        "social housing","luxury","apartment","mortgage","shelter","property",
        "planning","development","estate","permit","tenure","retrofit","flat",
        "landlord","tenant","vacancy","green belt",
    ],
    "Environment & Parks": [
        "recycling","park","tree","pollution","solar","environment","river","green",
        "corridor","native","climate","emission","waste","garden","biodiversity",
        "habitat","meadow","allotment","canopy","wildflower","rewilding","effluent",
        "contamination","air quality","plastic",
    ],
    "Public Safety": [
        "police","safety","crime","emergency","response","dispatch","mentor","youth",
        "street","patrol","fire","ambulance","security","cctv","surveillance","knife",
        "burglary","antisocial","violence","justice","prosecution","warden",
        "neighbourhood","fire station",
    ],
    "Education & Services": [
        "school","library","education","student","class","arts","curriculum",
        "workshop","digital","literacy","after-school","teacher","college",
        "learning","childcare","nursery","special","inclusion","retraining","skills",
        "adult","graduate","sen","health","social care","community hub","youth centre",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTES
# ─────────────────────────────────────────────────────────────────────────────
def _palette(dark: bool) -> dict:
    if dark:
        return {
            # Page & structure
            "bg":           "#0b1220",
            "sidebar_bg":   "#080e1a",
            "card_bg":      "#111e30",
            "card_border":  "#1a3050",
            "card_hover":   "#162540",
            # Hero gradient stops
            "hero_a":       "#060d1a",
            "hero_b":       "#0a2060",
            # Text hierarchy
            "text":         "#d8e8ff",
            "text2":        "#7a9cc5",
            "muted":        "#3d5878",
            # Accent colours
            "accent":       "#4a90ff",
            "accent2":      "#00e0a0",
            "accent3":      "#ff5f5f",
            # Sentiment colours
            "pos":          "#00cc88",
            "neg":          "#ff4444",
            "neu":          "#4a90ff",
            "pos_bg":       "#002a18",
            "pos_fg":       "#00cc88",
            "neg_bg":       "#2a0000",
            "neg_fg":       "#ff4444",
            "neu_bg":       "#001830",
            "neu_fg":       "#4a90ff",
            # Inputs
            "input_bg":     "#111e30",
            "input_border": "#1a3050",
            # Charts
            "chart_bg":     "#111e30",
            "chart_text":   "#7a9cc5",
            "chart_grid":   "#1a3050",
            "wc_bg":        "#111e30",
            # Report
            "rep_bg":       "#080e1a",
            "rep_border":   "#1a3050",
            # Misc
            "div":          "#1a3050",
            "sec_label":    "#4a90ff",
            "tag_new_bg":   "#002a18",
            "tag_new_fg":   "#00cc88",
            "btn_bg":       "#111e30",
        }
    return {
        "bg":           "#f4f7fc",
        "sidebar_bg":   "#0c1c36",
        "card_bg":      "#ffffff",
        "card_border":  "#dce8f5",
        "card_hover":   "#f0f6ff",
        "hero_a":       "#0c1c36",
        "hero_b":       "#1548a8",
        "text":         "#0c1c36",
        "text2":        "#2c4c7a",
        "muted":        "#7a9ab8",
        "accent":       "#1548a8",
        "accent2":      "#009c70",
        "accent3":      "#d83a3a",
        "pos":          "#158040",
        "neg":          "#cc2222",
        "neu":          "#2255cc",
        "pos_bg":       "#d6f5e3",
        "pos_fg":       "#126030",
        "neg_bg":       "#fde0e0",
        "neg_fg":       "#aa1818",
        "neu_bg":       "#dbeafe",
        "neu_fg":       "#1a44cc",
        "input_bg":     "#ffffff",
        "input_border": "#c5d8ee",
        "chart_bg":     "#ffffff",
        "chart_text":   "#5a7a9a",
        "chart_grid":   "#e4edf8",
        "wc_bg":        "#f8faff",
        "rep_bg":       "#eef4ff",
        "rep_border":   "#c5d8ee",
        "div":          "#dce8f5",
        "sec_label":    "#1548a8",
        "tag_new_bg":   "#d6f5e3",
        "tag_new_fg":   "#126030",
        "btn_bg":       "#ffffff",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  CSS INJECTION
# ─────────────────────────────────────────────────────────────────────────────
def _inject_css(C: dict, dark: bool) -> None:
    shadow_card = ("0 4px 24px rgba(0,0,0,0.40)"
                   if dark else "0 2px 16px rgba(12,28,54,0.08)")
    shadow_hover = ("0 8px 40px rgba(0,0,0,0.55)"
                    if dark else "0 6px 28px rgba(12,28,54,0.14)")
    st.markdown(f"""
<style>
/* ── Fonts ──────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,700;0,800;1,700&display=swap');

/* ── Base reset ─────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; }}
html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}}

/* ── App background ─────────────────────────────────────────── */
.stApp {{ background: {C['bg']} !important; }}
.block-container {{ padding-top: 1.5rem !important; padding-bottom: 3rem !important; }}

/* ── Global text — covers every element ────────────────────── */
p, span, div, li, td, th, small, em, strong, label,
.stMarkdown, .stText, .stCaption, .element-container,
[class*="stMarkdown"] p, [class*="stMarkdown"] span {{
    color: {C['text']} !important;
}}
h1, h2, h3, h4, h5, h6 {{ color: {C['text']} !important; }}
strong {{ color: {C['text']} !important; font-weight: 700; }}
a {{ color: {C['accent']} !important; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
code, pre {{
    font-family: 'DM Mono', monospace !important;
    background: {C['input_bg']} !important;
    color: {C['accent2']} !important;
    border: 1px solid {C['card_border']} !important;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.84em;
}}

/* ── Sidebar ────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {C['sidebar_bg']} !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
    min-width: 260px !important;
}}
/* All sidebar text forced white-ish so it's visible on dark sidebar */
section[data-testid="stSidebar"] * {{
    color: #c0d4ec !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] strong {{
    color: #ffffff !important;
}}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.08) !important;
    margin: 0.75rem 0 !important;
}}
/* Sidebar labels */
section[data-testid="stSidebar"] label {{
    color: #7aaad4 !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}}
/* Sidebar widget backgrounds */
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stMultiSelect > div > div {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: #d0e4f8 !important;
    border-radius: 8px !important;
}}
section[data-testid="stSidebar"] .stMultiSelect span,
section[data-testid="stSidebar"] .stSelectbox span {{
    color: #d0e4f8 !important;
}}
/* Radio buttons in sidebar */
section[data-testid="stSidebar"] .stRadio label {{
    color: #c0d4ec !important;
    font-size: 0.875rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-weight: 400 !important;
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
    color: #c0d4ec !important;
}}
/* Slider track and thumb */
section[data-testid="stSidebar"] .stSlider [data-testid="stSlider"] {{
    color: {C['accent']} !important;
}}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {{
    color: {C['accent']} !important;
}}
/* Checkbox in sidebar (the theme toggle) */
section[data-testid="stSidebar"] .stCheckbox label {{
    color: #ffffff !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}}
section[data-testid="stSidebar"] .stCheckbox {{
    background: rgba(74,144,255,0.12) !important;
    border: 1px solid rgba(74,144,255,0.25) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin-bottom: 4px !important;
}}
/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,80,80,0.12) !important;
    color: #ff8888 !important;
    border: 1px solid rgba(255,80,80,0.30) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 8px 0 !important;
    transition: all 0.2s !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,80,80,0.25) !important;
    border-color: rgba(255,80,80,0.5) !important;
}}
/* Sidebar markdown info text */
section[data-testid="stSidebar"] .stMarkdown p {{
    color: #9ab8d8 !important;
    font-size: 0.82rem !important;
    line-height: 1.6 !important;
}}
section[data-testid="stSidebar"] .stMarkdown strong {{
    color: #d0e4f8 !important;
}}
/* Multi-select tag pills in sidebar */
section[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background: rgba(74,144,255,0.2) !important;
    color: #a8ccff !important;
    border: none !important;
}}
/* Dropdown options for sidebar selects */
[data-baseweb="popover"] {{
    background: #0c1c36 !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
}}
[data-baseweb="popover"] li {{
    background: #0c1c36 !important;
    color: #c0d4ec !important;
}}
[data-baseweb="popover"] li:hover {{
    background: rgba(74,144,255,0.15) !important;
}}
[data-baseweb="menu"] {{
    background: #0c1c36 !important;
}}

/* ── Metric / KPI cards ──────────────────────────────────────── */
div[data-testid="metric-container"] {{
    background: {C['card_bg']} !important;
    border: 1.5px solid {C['card_border']} !important;
    border-radius: 16px !important;
    padding: 20px 22px !important;
    box-shadow: {shadow_card} !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}}
div[data-testid="metric-container"]:hover {{
    transform: translateY(-3px) !important;
    box-shadow: {shadow_hover} !important;
}}
div[data-testid="metric-container"] label {{
    color: {C['muted']} !important;
    font-size: 0.67rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C['text']} !important;
    font-size: 1.95rem !important;
    font-weight: 700 !important;
    line-height: 1.15 !important;
    font-family: 'Fraunces', serif !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] span {{
    color: inherit !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}}

/* ── Cards ───────────────────────────────────────────────────── */
.cl-card {{
    background: {C['card_bg']};
    border: 1.5px solid {C['card_border']};
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 18px;
    box-shadow: {shadow_card};
    transition: box-shadow 0.2s ease;
}}
.cl-card:hover {{
    box-shadow: {shadow_hover};
}}
.cl-card h4 {{
    color: {C['text']} !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1px !important;
    margin: 0 0 16px !important;
}}
.cl-card p {{
    color: {C['text2']} !important;
    line-height: 1.65 !important;
    font-size: 0.9rem !important;
}}

/* ── Hero banner ─────────────────────────────────────────────── */
.hero {{
    background: linear-gradient(135deg, {C['hero_a']} 0%, {C['hero_b']} 100%);
    border-radius: 20px;
    padding: 36px 44px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 60% 80% at 85% 15%, rgba(74,144,255,0.25) 0%, transparent 60%),
        radial-gradient(ellipse 50% 60% at 15% 85%, rgba(0,224,160,0.15) 0%, transparent 55%);
    pointer-events: none;
}}
.hero-inner {{
    position: relative;
    z-index: 1;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 24px;
}}
.hero h1 {{
    font-family: 'Fraunces', serif !important;
    color: #ffffff !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
    letter-spacing: -1px !important;
    margin: 0 !important;
}}
.hero-sub {{
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.9rem !important;
    margin-top: 8px !important;
    line-height: 1.55 !important;
}}
.hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(74,144,255,0.22);
    border: 1px solid rgba(74,144,255,0.45);
    border-radius: 30px;
    padding: 4px 14px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #80bfff !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 14px;
}}
.hero-stats {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: flex-start;
}}
.hero-stat {{
    background: rgba(255,255,255,0.09);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 12px;
    padding: 12px 20px;
    text-align: center;
    min-width: 90px;
    backdrop-filter: blur(10px);
}}
.hero-stat-lbl {{
    color: rgba(255,255,255,0.52) !important;
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    margin-bottom: 4px !important;
}}
.hero-stat-val {{
    color: #ffffff !important;
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    font-family: 'Fraunces', serif !important;
    line-height: 1 !important;
}}

/* ── Section labels ──────────────────────────────────────────── */
.sec-label {{
    font-size: 0.62rem !important;
    font-weight: 800 !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
    color: {C['sec_label']} !important;
    margin: 32px 0 14px !important;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sec-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {C['div']};
}}

/* ── Submit form wrap ────────────────────────────────────────── */
.submit-wrap {{
    background: {C['card_bg']};
    border: 2px solid {C['accent']};
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 18px;
    box-shadow: 0 0 0 4px {'rgba(74,144,255,0.08)' if dark else 'rgba(21,72,168,0.06)'};
}}
.submit-wrap h3 {{
    color: {C['text']} !important;
    font-family: 'Fraunces', serif !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    margin: 0 0 6px !important;
}}
.submit-desc {{
    color: {C['text2']} !important;
    font-size: 0.875rem !important;
    line-height: 1.65 !important;
    margin: 0 0 20px !important;
}}

/* ── All input elements ──────────────────────────────────────── */
.stTextArea textarea {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['input_border']} !important;
    border-radius: 10px !important;
    color: {C['text']} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    line-height: 1.6 !important;
    padding: 12px 14px !important;
    transition: border-color 0.2s !important;
}}
.stTextArea textarea::placeholder {{ color: {C['muted']} !important; opacity: 1 !important; }}
.stTextArea textarea:focus {{
    border-color: {C['accent']} !important;
    box-shadow: 0 0 0 3px {'rgba(74,144,255,0.14)' if dark else 'rgba(21,72,168,0.09)'} !important;
    outline: none !important;
}}
.stTextInput input {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['input_border']} !important;
    border-radius: 10px !important;
    color: {C['text']} !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 10px 12px !important;
}}
.stTextInput input::placeholder {{ color: {C['muted']} !important; opacity: 1 !important; }}
.stTextInput input:focus {{
    border-color: {C['accent']} !important;
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
    color: {C['text']} !important;
}}
/* Main area labels (not sidebar) */
.main .stSelectbox label, .main .stMultiSelect label,
.main .stTextArea label, .main .stTextInput label,
.main .stSlider label, .main .stFileUploader label {{
    color: {C['text']} !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}}
[data-baseweb="tag"] {{
    background: {C['neu_bg']} !important;
    color: {C['neu_fg']} !important;
    border: none !important;
}}

/* ── Buttons ─────────────────────────────────────────────────── */
/* Primary form submit */
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
div[data-testid="stForm"] button {{
    background: linear-gradient(135deg, {C['accent']} 0%, {C['accent2']} 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100% !important;
    cursor: pointer !important;
    letter-spacing: 0.2px !important;
    transition: opacity 0.2s, transform 0.15s !important;
}}
div[data-testid="stForm"] button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}}
/* Download buttons */
.stDownloadButton > button {{
    background: {C['accent']} !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 11px 22px !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}}
.stDownloadButton > button:hover {{ opacity: 0.85 !important; }}
/* Generic st.button in main area */
.main .stButton > button {{
    background: {C['btn_bg']} !important;
    color: {C['accent']} !important;
    border: 1.5px solid {C['accent']} !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
}}
.main .stButton > button:hover {{
    background: {C['accent']} !important;
    color: #ffffff !important;
}}

/* ── File uploader ───────────────────────────────────────────── */
[data-testid="stFileUploader"] {{
    background: {C['card_bg']} !important;
    border: 2px dashed {C['card_border']} !important;
    border-radius: 12px !important;
    padding: 8px !important;
}}
[data-testid="stFileUploader"] * {{ color: {C['text2']} !important; }}

/* ── Dataframe ───────────────────────────────────────────────── */
.stDataFrame {{ border-radius: 12px !important; overflow: hidden !important; }}
.stDataFrame thead th {{
    background: {'#0f1e30' if dark else '#e8f0fc'} !important;
    color: {C['text']} !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}
.stDataFrame tbody td {{
    color: {C['text']} !important;
    background: {C['card_bg']} !important;
    font-size: 0.875rem !important;
}}
.stDataFrame tbody tr:nth-child(even) td {{
    background: {'#0e1c2c' if dark else '#f5f8ff'} !important;
}}

/* ── Alerts ──────────────────────────────────────────────────── */
div[data-testid="stAlert"] {{ border-radius: 12px !important; }}
div[data-testid="stAlert"] p {{ color: inherit !important; }}

/* ── Expander ────────────────────────────────────────────────── */
details {{
    background: {C['card_bg']} !important;
    border: 1.5px solid {C['card_border']} !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    margin-bottom: 10px !important;
}}
details summary {{
    color: {C['text']} !important;
    font-weight: 600 !important;
    padding: 14px 20px !important;
    background: {C['card_bg']} !important;
    cursor: pointer !important;
    font-size: 0.9rem !important;
    transition: background 0.15s !important;
}}
details summary:hover {{ background: {C['card_hover']} !important; }}
details[open] > summary {{ border-bottom: 1px solid {C['card_border']} !important; }}

/* ── Tabs ────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: {C['card_bg']} !important;
    border-bottom: 2px solid {C['card_border']} !important;
    gap: 2px !important;
    padding: 0 6px !important;
    border-radius: 14px 14px 0 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {C['muted']} !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 11px 18px !important;
    border-radius: 10px 10px 0 0 !important;
    transition: all 0.15s !important;
}}
.stTabs [aria-selected="true"] {{
    color: {C['accent']} !important;
    font-weight: 700 !important;
    background: {C['bg']} !important;
    border-bottom: 2.5px solid {C['accent']} !important;
}}
.stTabs [data-testid="stTabsContent"] {{
    background: {C['card_bg']} !important;
    border: 1.5px solid {C['card_border']} !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
    padding: 22px 20px !important;
}}

/* ── Sentiment pills ─────────────────────────────────────────── */
.tag-pos {{background:{C['pos_bg']};color:{C['pos_fg']};padding:3px 12px;border-radius:30px;font-size:0.75rem;font-weight:700;display:inline-block;}}
.tag-neg {{background:{C['neg_bg']};color:{C['neg_fg']};padding:3px 12px;border-radius:30px;font-size:0.75rem;font-weight:700;display:inline-block;}}
.tag-neu {{background:{C['neu_bg']};color:{C['neu_fg']};padding:3px 12px;border-radius:30px;font-size:0.75rem;font-weight:700;display:inline-block;}}
.tag-new {{background:{C['tag_new_bg']};color:{C['tag_new_fg']};padding:2px 8px;border-radius:20px;font-size:0.63rem;font-weight:800;display:inline-block;text-transform:uppercase;letter-spacing:0.5px;vertical-align:middle;margin-left:6px;}}

/* ── Latest comment cards ────────────────────────────────────── */
.latest-card {{
    background: {C['card_bg']};
    border: 1.5px solid {C['card_border']};
    border-left: 4px solid {C['accent']};
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 12px;
    transition: box-shadow 0.18s;
}}
.latest-card:hover {{ box-shadow: {shadow_hover}; }}
.latest-meta {{ color: {C['muted']}; font-size: 0.76rem; margin-top: 6px; }}
.latest-quote {{ color: {C['text']}; font-size: 0.9rem; line-height: 1.55; margin: 6px 0; font-style: italic; }}

/* ── Confidence bar ──────────────────────────────────────────── */
.conf-bar-wrap {{width:100%;height:5px;background:{C['card_border']};border-radius:3px;overflow:hidden;margin-top:8px;}}
.conf-bar-fill {{height:100%;border-radius:3px;background:linear-gradient(90deg,{C['accent']},{C['accent2']});}}

/* ── Report box ──────────────────────────────────────────────── */
.report-box {{
    background: {C['rep_bg']};
    border: 1.5px solid {C['rep_border']};
    border-radius: 12px;
    padding: 20px 24px;
    font-family: 'DM Mono', monospace;
    font-size: 0.74rem;
    color: {C['text']} !important;
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.8;
}}

/* ── Stat strip ──────────────────────────────────────────────── */
.stat-strip {{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}}
.stat-pill {{background:{C['card_bg']};border:1.5px solid {C['card_border']};border-radius:30px;padding:7px 16px;font-size:0.8rem;font-weight:600;color:{C['text2']};white-space:nowrap;}}

/* ── Dividers & captions ─────────────────────────────────────── */
hr {{ border-color: {C['div']} !important; opacity: 0.6 !important; }}
.stCaption, caption, small {{ color: {C['muted']} !important; font-size: 0.8rem !important; }}

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {C['card_bg']}; }}
::-webkit-scrollbar-thumb {{ background: {C['div']}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C['muted']}; }}

/* ── Hide Streamlit chrome ───────────────────────────────────── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SEED DATASET  — 50 hand-authored comments, 6 policy domains
# ─────────────────────────────────────────────────────────────────────────────
_BASE_DATE = datetime.date(2025, 1, 1)

SEED_DATA: list[tuple[str, str, int]] = [
    # Economy & Tax
    ("The revised business grant scheme genuinely helped us survive the slow season.", "Economy & Tax", 15),
    ("Another property tax hike with zero improvement in local services is inexcusable.", "Economy & Tax", 8),
    ("Corporate incentives for the new tech park will create high-paying jobs. Strong policy.", "Economy & Tax", 22),
    ("Hiking sales tax on essentials during a cost-of-living crisis shows total disregard for families.", "Economy & Tax", 5),
    ("The economic regeneration zone has brought three new employers to our district this year.", "Economy & Tax", 40),
    ("The council's budget transparency portal is excellent — every citizen should use it.", "Economy & Tax", 55),
    ("Hidden fees in the new business licensing process are driving small traders away.", "Economy & Tax", 70),
    ("Reducing stamp duty for first-time buyers is exactly the kind of targeted relief we needed.", "Economy & Tax", 90),
    # Infrastructure
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
    # Housing
    ("The community land trust pilot in Westgate is the most progressive housing policy in years.", "Housing", 20),
    ("Retrospective planning approval for the illegal riverside development sets a terrible precedent.", "Housing", 30),
    ("Purpose-built student accommodation near the university is relieving pressure on family housing.", "Housing", 45),
    ("Permitted development rights abuse is converting quality office space into substandard flats.", "Housing", 58),
    ("The rent-to-buy scheme gave my family a realistic pathway to ownership after seven years of renting.", "Housing", 72),
    ("Green-belt encroachment for luxury estates while social housing waiting lists grow is unforgivable.", "Housing", 82),
    ("Retrofit grants for Victorian terraces will reduce emissions and fuel poverty simultaneously.", "Housing", 95),
    ("The planning portal redesign is a genuine improvement — applications take half the time now.", "Housing", 115),
    ("Mixed-tenure social housing developments foster much healthier communities than segregated estates.", "Housing", 130),
    # Environment & Parks
    ("The river rewilding project has restored otter and kingfisher populations. Remarkable work.", "Environment & Parks", 10),
    ("Industrial effluent discharge near the estuary has not been properly investigated despite reports.", "Environment & Parks", 25),
    ("Community allotment expansion programme has a two-year waiting list — scale it up urgently.", "Environment & Parks", 38),
    ("The new air quality monitoring network finally gives us real-time data to hold polluters accountable.", "Environment & Parks", 52),
    ("Replacing grass verges with wildflower meadows is beautiful, cheap, and brilliant for biodiversity.", "Environment & Parks", 65),
    ("Single-use plastic ban in council-run venues should extend to all licensed premises immediately.", "Environment & Parks", 78),
    ("The waste-to-energy plant proposal near primary schools is deeply alarming and must be refused.", "Environment & Parks", 92),
    ("Urban tree canopy target of 25% by 2030 is ambitious and the right direction for climate resilience.", "Environment & Parks", 105),
    ("Contaminated land remediation at the old gasworks site is long overdue — residents deserve answers.", "Environment & Parks", 120),
    # Public Safety
    ("Neighbourhood watch digital integration with the council portal has visibly reduced burglaries.", "Public Safety", 14),
    ("Knife crime intervention programmes for at-risk youth deserve far more sustained investment.", "Public Safety", 32),
    ("Ambulance response times in rural postcodes remain dangerously above the national target.", "Public Safety", 47),
    ("The new community safety hub brings police, social services, and housing under one roof. Excellent.", "Public Safety", 63),
    ("CCTV expansion without a clear data governance policy is surveillance creep, not public safety.", "Public Safety", 80),
    ("The fire station closure in Millbrook leaves 15,000 residents with unacceptably slow coverage.", "Public Safety", 96),
    # Education & Services
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
        pol  = round(blob.sentiment.polarity, 4)
        subj = round(blob.sentiment.subjectivity, 4)
        sent = "Positive" if pol > 0.08 else ("Negative" if pol < -0.08 else "Neutral")
        kws  = TOPIC_KEYWORDS.get(theme, [])
        hits = sum(1 for kw in kws if kw.lower() in comment.lower())
        conf = min(int(hits / max(len(kws), 1) * 100 + 40), 100)
        rows.append({
            "Comment":      comment,
            "Theme":        theme,
            "Sentiment":    sent,
            "Polarity":     pol,
            "Subjectivity": subj,
            "Confidence %": conf,
            "Source":       "Seed Dataset",
            "Date":         (_BASE_DATE + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d"),
            "Submitted At": "—",
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
#  NLP HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def detect_theme(text: str) -> tuple[str, int]:
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl)
              for t, kws in TOPIC_KEYWORDS.items()}
    scores = {t: s for t, s in scores.items() if s > 0}
    if not scores:
        return "General / Other", 30
    best = max(scores, key=scores.get)
    conf = min(int(scores[best] / len(TOPIC_KEYWORDS[best]) * 100 + 40), 100)
    return best, conf


def run_nlp(text: str) -> dict:
    blob  = TextBlob(str(text))
    pol   = round(blob.sentiment.polarity, 4)
    subj  = round(blob.sentiment.subjectivity, 4)
    sent  = "Positive" if pol > 0.08 else ("Negative" if pol < -0.08 else "Neutral")
    theme, conf = detect_theme(text)
    return {"Sentiment": sent, "Polarity": pol, "Subjectivity": subj,
            "Theme": theme, "confidence": conf}


def build_full_df() -> pd.DataFrame:
    base  = build_seed_df().copy()
    extra = st.session_state.submitted_comments + st.session_state.uploaded_rows
    if extra:
        return pd.concat([pd.DataFrame(extra), base], ignore_index=True)
    return base


# ─────────────────────────────────────────────────────────────────────────────
#  CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────
SCOL = {"Positive": "#00cc88", "Neutral": "#4a90ff", "Negative": "#ff4444"}
TPAL = ["#4a90ff", "#00e0a0", "#f5a623", "#b06bff", "#ff7c5c", "#00d4ff", "#a3e635"]

EXTRA_STOP = {
    "will","city","new","one","also","get","make","need","use","say","go","come",
    "want","people","think","know","good","much","really","well","way","time","year",
    "many","still","even","back","us","our","more","very","been","have","this","that",
    "with","from","they","their","were","are","has","had","not","but","for","and",
    "the","its","into","just","can","should","would","could","must","been","than",
}
THEME_CMAPS = {
    "Economy & Tax": "YlOrBr",
    "Infrastructure": "Blues",
    "Housing": "Purples",
    "Environment & Parks": "Greens",
    "Public Safety": "Oranges",
    "Education & Services": "PuBuGn",
    "General / Other": "Greys",
}


def _style_ax(fig, ax, C):
    fig.patch.set_facecolor(C["chart_bg"])
    ax.set_facecolor(C["chart_bg"])
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(C["chart_grid"])
    ax.spines["bottom"].set_color(C["chart_grid"])
    ax.tick_params(colors=C["chart_text"], labelsize=9)
    ax.yaxis.grid(True, color=C["chart_grid"], linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()


def _show(fig):
    """Render figure then immediately free memory."""
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def chart_sentiment(df, C):
    counts = df["Sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative"], fill_value=0)
    fig, ax = plt.subplots(figsize=(5, 3.4))
    bars = ax.bar(counts.index, counts.values,
                  color=[SCOL[s] for s in counts.index],
                  edgecolor=C["chart_bg"], linewidth=2, width=0.46, zorder=3)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.15, str(int(h)),
                ha="center", va="bottom", fontsize=12, fontweight="bold",
                color=C["text"], fontfamily="DM Sans")
    ax.set_ylabel("Comments", fontsize=9.5, color=C["chart_text"])
    ax.set_ylim(0, max(counts.max(), 1) + 3)
    ax.tick_params(axis="x", colors=C["text"], labelsize=10.5)
    _style_ax(fig, ax, C)
    return fig


def chart_themes(df, C):
    counts = df["Theme"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 3.6))
    bars = ax.barh(counts.index, counts.values,
                   color=TPAL[:len(counts)],
                   edgecolor=C["chart_bg"], linewidth=1.2, height=0.5, zorder=3)
    for b in bars:
        w = b.get_width()
        ax.text(w + 0.1, b.get_y() + b.get_height() / 2, str(int(w)),
                va="center", fontsize=10, fontweight="bold",
                color=C["text"], fontfamily="DM Sans")
    ax.set_xlabel("Comments", fontsize=9.5, color=C["chart_text"])
    ax.set_xlim(0, max(counts.max(), 1) + 2.5)
    ax.invert_yaxis()
    ax.tick_params(axis="y", colors=C["text"], labelsize=8.5)
    ax.xaxis.grid(True, color=C["chart_grid"], linewidth=0.5, zorder=0)
    ax.yaxis.grid(False)
    fig.patch.set_facecolor(C["chart_bg"])
    ax.set_facecolor(C["chart_bg"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(C["chart_grid"])
    plt.tight_layout()
    return fig


def chart_polarity(df, C):
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.hist(df["Polarity"], bins=16, color=C["accent"],
            edgecolor=C["chart_bg"], linewidth=0.8, zorder=3, alpha=0.88)
    ax.axvline(0, color=C["muted"], linestyle="--", linewidth=1.4)
    mv = df["Polarity"].mean()
    ax.axvline(mv, color="#f5a623", linestyle="-", linewidth=2,
               label=f"Mean  {mv:+.2f}")
    ax.set_xlabel("Polarity  (−1 negative → +1 positive)",
                  fontsize=9.5, color=C["chart_text"])
    ax.set_ylabel("Frequency", fontsize=9.5, color=C["chart_text"])
    leg = ax.legend(fontsize=9, framealpha=0.35, facecolor=C["chart_bg"])
    for t in leg.get_texts():
        t.set_color(C["text"])
    _style_ax(fig, ax, C)
    return fig


def chart_stacked(df, C):
    pivot = df.groupby(["Theme", "Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive", "Neutral", "Negative"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[["Positive", "Neutral", "Negative"]]
    fig, ax = plt.subplots(figsize=(5, 3.6))
    bot = pd.Series([0.0] * len(pivot), index=pivot.index)
    for s, color in SCOL.items():
        ax.bar(pivot.index, pivot[s], bottom=bot, color=color,
               label=s, edgecolor=C["chart_bg"], linewidth=0.6)
        bot = bot + pivot[s]
    ax.set_ylabel("Comments", fontsize=9.5, color=C["chart_text"])
    ax.tick_params(axis="x", rotation=28, labelsize=8, colors=C["text"])
    ax.tick_params(axis="y", colors=C["text"])
    leg = ax.legend(fontsize=9, loc="upper right",
                    framealpha=0.35, facecolor=C["chart_bg"])
    for t in leg.get_texts():
        t.set_color(C["text"])
    _style_ax(fig, ax, C)
    return fig


def chart_scatter(df, C):
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for sent, color in SCOL.items():
        s = df[df["Sentiment"] == sent]
        ax.scatter(s["Polarity"], s["Subjectivity"], c=color, label=sent,
                   alpha=0.7, s=52, edgecolors=C["chart_bg"],
                   linewidths=0.8, zorder=3)
    ax.axvline(0, color=C["muted"], linestyle="--", linewidth=1, alpha=0.6)
    ax.axhline(0.5, color=C["muted"], linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("Polarity Score", fontsize=9.5, color=C["chart_text"])
    ax.set_ylabel("Subjectivity Score", fontsize=9.5, color=C["chart_text"])
    for x, y, lbl in [(-0.95, 0.97, "Negative\nSubjective"),
                       (0.52, 0.97, "Positive\nSubjective"),
                       (-0.95, 0.03, "Negative\nObjective"),
                       (0.52, 0.03, "Positive\nObjective")]:
        ax.text(x, y, lbl, fontsize=7.2, color=C["muted"],
                va="top" if y > 0.5 else "bottom")
    leg = ax.legend(fontsize=9, framealpha=0.35, facecolor=C["chart_bg"])
    for t in leg.get_texts():
        t.set_color(C["text"])
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.05, 1.05)
    _style_ax(fig, ax, C)
    return fig


def chart_timeline(df, C):
    def _empty():
        fig, ax = plt.subplots(figsize=(10, 2.4))
        ax.text(0.5, 0.5, "No date data available",
                ha="center", va="center", color=C["muted"], fontsize=11)
        ax.axis("off")
        fig.patch.set_facecolor(C["chart_bg"])
        return fig

    if "Date" not in df.columns:
        return _empty()
    df2 = df.copy()
    df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce")
    df2 = df2.dropna(subset=["Date"])
    if df2.empty:
        return _empty()
    df2["Week"] = df2["Date"].dt.to_period("W").dt.start_time
    weekly = df2.groupby(["Week", "Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive", "Neutral", "Negative"]:
        if col not in weekly.columns:
            weekly[col] = 0
    fig, ax = plt.subplots(figsize=(10, 2.7))
    for s, color in SCOL.items():
        ax.fill_between(weekly.index, weekly[s], alpha=0.18, color=color)
        ax.plot(weekly.index, weekly[s], color=color, linewidth=2,
                label=s, marker="o", markersize=3.5)
    ax.set_ylabel("Count", fontsize=9, color=C["chart_text"])
    ax.tick_params(axis="x", rotation=22, labelsize=8, colors=C["text"])
    ax.tick_params(axis="y", colors=C["text"])
    leg = ax.legend(fontsize=9, framealpha=0.35, facecolor=C["chart_bg"],
                    loc="upper left")
    for t in leg.get_texts():
        t.set_color(C["text"])
    _style_ax(fig, ax, C)
    return fig


def make_wordcloud(series: pd.Series, cmap: str, C: dict):
    text = " ".join(series.astype(str).tolist()).strip()
    fig, ax = plt.subplots(figsize=(6, 2.7))
    fig.patch.set_facecolor(C["wc_bg"])
    ax.set_facecolor(C["wc_bg"])
    if len(text.split()) < 5:
        ax.text(0.5, 0.5, "Add more comments to generate a word cloud",
                ha="center", va="center", fontsize=10, color=C["muted"])
        ax.axis("off")
        return fig
    try:
        wc = WordCloud(
            width=800, height=270,
            background_color=C["wc_bg"],
            colormap=cmap,
            max_words=55,
            collocations=False,
            prefer_horizontal=0.80,
            stopwords=STOPWORDS.union(EXTRA_STOP),
            min_font_size=10,
        ).generate(text)
        ax.imshow(wc, interpolation="bilinear")
    except Exception:
        ax.text(0.5, 0.5, "Word cloud unavailable",
                ha="center", va="center", color=C["muted"])
    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  POLICY INSIGHT REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_report(df: pd.DataFrame) -> str:
    n = len(df)
    if n == 0:
        return "No data to report."
    pos  = (df["Sentiment"] == "Positive").sum()
    neg  = (df["Sentiment"] == "Negative").sum()
    neu  = (df["Sentiment"] == "Neutral").sum()
    live = len(df[df["Source"] != "Seed Dataset"])
    now  = datetime.datetime.now().strftime("%d %B %Y  %H:%M")

    L = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║       C I T I Z E N L E N S   —   P O L I C Y              ║",
        "║             I N S I G H T   R E P O R T                     ║",
        "╚══════════════════════════════════════════════════════════════╝",
        f"\n  Generated  : {now}",
        f"  Comments   : {n} total  ({live} live submissions, {n - live} seed data)",
        "",
        "── OVERALL SENTIMENT ──────────────────────────────────────────",
        f"  ✅  Positive    : {pos:>4}  ({round(pos / n * 100)}%)",
        f"  ➖  Neutral     : {neu:>4}  ({round(neu / n * 100)}%)",
        f"  ❌  Negative    : {neg:>4}  ({round(neg / n * 100)}%)",
        f"  📊  Avg Polarity     : {df['Polarity'].mean():+.4f}",
        f"  📐  Avg Subjectivity : {df['Subjectivity'].mean():.4f}",
        "",
        "── PER-THEME BREAKDOWN ────────────────────────────────────────",
    ]

    stats = df.groupby("Theme").agg(
        Count=("Sentiment", "count"),
        Pos=("Sentiment", lambda x: (x == "Positive").sum()),
        Neg=("Sentiment", lambda x: (x == "Negative").sum()),
        Neu=("Sentiment", lambda x: (x == "Neutral").sum()),
        Pol=("Polarity", "mean"),
        Subj=("Subjectivity", "mean"),
    ).sort_values("Count", ascending=False)

    for theme, r in stats.iterrows():
        mood = "🟢" if r["Pol"] > 0.06 else ("🔴" if r["Pol"] < -0.06 else "🟡")
        L += [
            f"\n  {mood}  {theme}",
            f"      Comments : {int(r['Count'])}  |  "
            f"✅ {int(r['Pos'])} pos  ➖ {int(r['Neu'])} neu  ❌ {int(r['Neg'])} neg",
            f"      Avg Polarity : {r['Pol']:+.4f}   "
            f"Avg Subjectivity : {r['Subj']:.4f}",
        ]

    for label, method, sentiment in [
        ("TOP 3 MOST POSITIVE COMMENTS", "nlargest",  "Positive"),
        ("TOP 3 MOST NEGATIVE COMMENTS", "nsmallest", "Negative"),
    ]:
        L.append(f"\n\n── {label} {'─' * (53 - len(label))}")
        subset = df[df["Sentiment"] == sentiment]
        fn     = getattr(subset, method)
        for i, (_, r) in enumerate(fn(3, "Polarity").iterrows(), 1):
            L += [
                f"\n  {i}.  [{r['Polarity']:+.4f}]  {r['Theme']}",
                f'        "{r["Comment"]}"',
            ]

    L += ["", "", "── POLICY RECOMMENDATIONS ─────────────────────────────────────",
          "  Themes ranked by urgency (negative comment count):", ""]
    neg_t = (df[df["Sentiment"] == "Negative"]
             .groupby("Theme").size().sort_values(ascending=False))
    for i, (t, c) in enumerate(neg_t.items(), 1):
        L.append(f"  {i}.  ⚠️  {t:36s}  {'█' * min(c, 20)}  ({c})")

    L += ["", "  Themes with strongest positive sentiment:", ""]
    pos_t = (df[df["Sentiment"] == "Positive"]
             .groupby("Theme").size().sort_values(ascending=False))
    for i, (t, c) in enumerate(pos_t.items(), 1):
        L.append(f"  {i}.  ✅  {t:36s}  {'█' * min(c, 20)}  ({c})")

    L += [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║  CitizenLens v3.0  |  Open Government Hackathon 2025        ║",
        "║  Streamlit · TextBlob · WordCloud · Matplotlib · MIT        ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ]
    return "\n".join(L)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    # THE FIX: Use st.checkbox for the dark mode toggle.
    # st.checkbox triggers Streamlit's own internal rerun when its value
    # changes, which PRESERVES the sidebar open/closed state — unlike
    # manually calling st.rerun() which resets it.
    # ─────────────────────────────────────────────────────────────────────────
    with st.sidebar:

        # ── Branding ──────────────────────────────────────────────────────────
        st.markdown("""
<div style="padding: 4px 0 16px 0;">
  <div style="font-family:'Fraunces',serif;font-size:1.25rem;font-weight:800;
              color:#ffffff;letter-spacing:-0.5px;">🏛️ CitizenLens</div>
  <div style="font-size:0.72rem;color:#5a88b8;font-weight:600;
              text-transform:uppercase;letter-spacing:1.2px;margin-top:2px;">
    Policy Intelligence Platform
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")

        # ── THEME TOGGLE — st.checkbox, no manual st.rerun() ──────────────────
        # Streamlit re-renders on checkbox change while keeping sidebar open.
        dark_checked = st.checkbox(
            "🌙  Dark Mode",
            value=st.session_state.dark_mode,
            key="dark_mode",          # directly bound to session_state.dark_mode
            help="Toggle between light and dark theme",
        )
        # dark_checked IS st.session_state.dark_mode (same key) — no rerun needed.
        # The page re-renders automatically when the checkbox changes.

        st.markdown("---")

        # ── Filters ────────────────────────────────────────────────────────────
        st.markdown("**🔍  Filters**")

        df_all = build_full_df()
        all_themes = sorted(df_all["Theme"].unique().tolist())

        sel_themes = st.multiselect(
            "Policy Theme", all_themes, default=all_themes,
            help="Select one or more policy areas to display",
        )
        sel_sents = st.multiselect(
            "Sentiment", ["Positive", "Neutral", "Negative"],
            default=["Positive", "Neutral", "Negative"],
        )

        p_min = float(df_all["Polarity"].min())
        p_max = float(df_all["Polarity"].max())
        pol_r  = st.slider("Polarity Range",  p_min, p_max, (p_min, p_max), 0.01)
        subj_r = st.slider("Subjectivity Range", 0.0, 1.0, (0.0, 1.0), 0.05)

        st.markdown("---")

        src_filter = st.radio(
            "Data Source",
            ["All", "Live & Uploaded Only", "Seed Data Only"],
            index=0,
        )

        st.markdown("---")

        # ── Stats ──────────────────────────────────────────────────────────────
        live_n = len(st.session_state.submitted_comments)
        up_n   = len(st.session_state.uploaded_rows)
        st.markdown(f"**📬 Live submissions:** `{live_n}`")
        st.markdown(f"**📂 Uploaded rows:** `{up_n}`")

        if live_n + up_n > 0:
            if st.button("🗑️  Clear Live Data", use_container_width=True):
                st.session_state.submitted_comments = []
                st.session_state.uploaded_rows = []
                st.rerun()

        st.markdown("---")

        # ── How it works ───────────────────────────────────────────────────────
        st.markdown("""
**How it works**

1. Submit a comment or upload a CSV  
2. TextBlob scores sentiment & subjectivity  
3. Keyword clustering assigns a policy theme  
4. All charts update instantly  
5. Download the Policy Insight Report
""")

    # ── Re-read DARK from session_state (checkbox may have changed it) ─────────
    DARK = st.session_state.dark_mode
    C    = _palette(DARK)
    _inject_css(C, DARK)

    # ── FILTER DATA ────────────────────────────────────────────────────────────
    df = build_full_df()
    if src_filter == "Live & Uploaded Only":
        df = df[df["Source"] != "Seed Dataset"]
    elif src_filter == "Seed Data Only":
        df = df[df["Source"] == "Seed Dataset"]

    filtered = df[
        df["Theme"].isin(sel_themes) &
        df["Sentiment"].isin(sel_sents) &
        df["Polarity"].between(pol_r[0], pol_r[1]) &
        df["Subjectivity"].between(subj_r[0], subj_r[1])
    ].copy()

    total     = len(filtered)
    pos_count = (filtered["Sentiment"] == "Positive").sum()
    neg_count = (filtered["Sentiment"] == "Negative").sum()
    neu_count = (filtered["Sentiment"] == "Neutral").sum()
    avg_pol   = float(filtered["Polarity"].mean())   if total else 0.0
    avg_subj  = float(filtered["Subjectivity"].mean()) if total else 0.0

    # ── HERO ───────────────────────────────────────────────────────────────────
    mode_lbl = "🌙 Dark Mode" if DARK else "☀️ Light Mode"
    st.markdown(f"""
<div class="hero">
  <div class="hero-inner">
    <div>
      <div class="hero-badge">🏆 Open Government Hackathon 2025</div>
      <h1>CitizenLens</h1>
      <p class="hero-sub">
        AI-powered policy comment intelligence &nbsp;·&nbsp;
        Sentiment analysis · Topic clustering · Visual reports &nbsp;·&nbsp; {mode_lbl}
      </p>
    </div>
    <div class="hero-stats">
      <div class="hero-stat">
        <div class="hero-stat-lbl">Total</div>
        <div class="hero-stat-val">{len(df)}</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-lbl">Themes</div>
        <div class="hero-stat-val">{df['Theme'].nunique()}</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-lbl">Live</div>
        <div class="hero-stat-val">{live_n + up_n}</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── TABS ────────────────────────────────────────────────────────────────────
    tab_submit, tab_dash, tab_upload, tab_about = st.tabs([
        "✍️  Submit Comment",
        "📊  Dashboard",
        "📂  Bulk Upload",
        "ℹ️  About",
    ])

    # ═══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — SUBMIT COMMENT
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_submit:
        st.markdown('<p class="sec-label">✍️ Share Your View on Local Policies</p>',
                    unsafe_allow_html=True)

        st.markdown("""
<div class="submit-wrap">
  <h3>💬 What do you think about local government policies?</h3>
  <p class="submit-desc">
    Write your comment below — in your own words, on any policy topic.
    CitizenLens instantly scores sentiment, measures subjectivity, detects the
    policy theme, and adds your feedback to the live dashboard for policymakers.
  </p>
</div>
""", unsafe_allow_html=True)

        with st.form("comment_form", clear_on_submit=True):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                user_text = st.text_area(
                    "Your comment *",
                    placeholder=(
                        'e.g. "The new cycle lanes on the high street have transformed '
                        'my morning commute. More people are cycling and air quality has '
                        'visibly improved. Please keep investing in this."'
                    ),
                    height=130,
                )
            with col_b:
                policy_hint = st.selectbox(
                    "Policy area (optional)",
                    ["Auto-detect 🤖"] + list(TOPIC_KEYWORDS.keys()) + ["General / Other"],
                    help="Leave as Auto-detect or choose manually.",
                )
                name_in     = st.text_input("Your name (optional)", placeholder="Anonymous")
                location_in = st.text_input("Location (optional)", placeholder="e.g. District 4")

            submitted = st.form_submit_button(
                "🔍  Analyze & Submit Comment",
                use_container_width=True,
            )

            if submitted:
                txt = user_text.strip()
                if len(txt) < 10:
                    st.error("⚠️  Please write at least 10 characters.")
                else:
                    nlp = run_nlp(txt)
                    if "Auto-detect" not in policy_hint:
                        nlp["Theme"]      = policy_hint
                        nlp["confidence"] = 99
                    row = {
                        "Comment":      txt,
                        "Theme":        nlp["Theme"],
                        "Sentiment":    nlp["Sentiment"],
                        "Polarity":     nlp["Polarity"],
                        "Subjectivity": nlp["Subjectivity"],
                        "Confidence %": nlp["confidence"],
                        "Source":       f"Live — {name_in.strip() or 'Anonymous'}",
                        "Date":         datetime.date.today().strftime("%Y-%m-%d"),
                        "Submitted At": datetime.datetime.now().strftime("%H:%M:%S"),
                    }
                    st.session_state.submitted_comments.insert(0, row)
                    emoji = ("✅" if nlp["Sentiment"] == "Positive" else
                             "❌" if nlp["Sentiment"] == "Negative" else "➖")
                    mood  = ("Expresses satisfaction." if nlp["Polarity"] >  0.3 else
                             "Expresses serious concern." if nlp["Polarity"] < -0.3 else
                             "Mixed or measured sentiment.")
                    st.success(
                        f"{emoji} **{nlp['Sentiment']}** &nbsp;|&nbsp; "
                        f"Polarity `{nlp['Polarity']:+.4f}` &nbsp;·&nbsp; "
                        f"Subjectivity `{nlp['Subjectivity']:.4f}`\n\n"
                        f"**Theme:** {nlp['Theme']} &nbsp;·&nbsp; "
                        f"**Confidence:** `{nlp['confidence']}%` &nbsp;·&nbsp; _{mood}_"
                    )
                    st.rerun()

        # Recent submissions list
        if st.session_state.submitted_comments:
            st.markdown('<p class="sec-label">📬 Recent Submissions</p>',
                        unsafe_allow_html=True)
            for entry in st.session_state.submitted_comments[:5]:
                tag = ("tag-pos" if entry["Sentiment"] == "Positive" else
                       "tag-neg" if entry["Sentiment"] == "Negative" else "tag-neu")
                st.markdown(f"""
<div class="latest-card">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <span class="{tag}">{entry['Sentiment']}</span>
    <span class="tag-new">NEW</span>
    <span class="latest-meta" style="margin-top:0;">
      {entry.get('Source','—')} &nbsp;·&nbsp; {entry['Theme']} &nbsp;·&nbsp; {entry.get('Submitted At','—')}
    </span>
  </div>
  <p class="latest-quote">"{entry['Comment']}"</p>
  <div class="conf-bar-wrap">
    <div class="conf-bar-fill" style="width:{entry.get('Confidence %', 50)}%;"></div>
  </div>
  <div class="latest-meta" style="margin-top:6px;">
    Polarity&nbsp;<strong>{entry['Polarity']:+.4f}</strong> &nbsp;·&nbsp;
    Subjectivity&nbsp;<strong>{entry['Subjectivity']:.4f}</strong> &nbsp;·&nbsp;
    Topic confidence&nbsp;<strong>{entry.get('Confidence %','?')}%</strong>
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("💡  No live submissions yet — be the first to submit a comment above!")

    # ═══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_dash:

        # KPI row
        st.markdown('<p class="sec-label">📊 Overview Metrics</p>',
                    unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("💬 Total Comments", total)
        c2.metric("✅ Positive",  pos_count,
                  delta=f"{round(pos_count / total * 100) if total else 0}%")
        c3.metric("➖ Neutral",   neu_count,
                  delta=f"{round(neu_count / total * 100) if total else 0}%",
                  delta_color="off")
        c4.metric("❌ Negative",  neg_count,
                  delta=f"{round(neg_count / total * 100) if total else 0}%",
                  delta_color="inverse")
        c5.metric("📈 Avg Polarity",     f"{avg_pol:+.3f}")
        c6.metric("🔬 Avg Subjectivity", f"{avg_subj:.3f}")

        if total == 0:
            st.warning("⚠️  No comments match the current filters. Adjust the sidebar filters.")
            return

        # Charts row 1
        st.markdown('<p class="sec-label">📈 Sentiment & Theme Analysis</p>',
                    unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="cl-card"><h4>🎭 Sentiment Distribution</h4>',
                        unsafe_allow_html=True)
            _show(chart_sentiment(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="cl-card"><h4>🗂️ Comments by Policy Theme</h4>',
                        unsafe_allow_html=True)
            _show(chart_themes(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)

        # Charts row 2
        cc, cd = st.columns(2)
        with cc:
            st.markdown('<div class="cl-card"><h4>📉 Polarity Score Distribution</h4>',
                        unsafe_allow_html=True)
            _show(chart_polarity(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)
        with cd:
            st.markdown('<div class="cl-card"><h4>🧩 Sentiment by Theme — Stacked</h4>',
                        unsafe_allow_html=True)
            _show(chart_stacked(filtered, C))
            st.markdown('</div>', unsafe_allow_html=True)

        # Full-width scatter
        st.markdown('<div class="cl-card"><h4>🔬 Subjectivity vs Polarity Scatter</h4>',
                    unsafe_allow_html=True)
        _show(chart_scatter(filtered, C))
        st.caption("Each point is one comment. "
                   "Horizontal axis = sentiment direction. "
                   "Vertical axis = opinion vs fact balance.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Full-width timeline
        st.markdown('<div class="cl-card"><h4>📅 Sentiment Trend Over Time</h4>',
                    unsafe_allow_html=True)
        _show(chart_timeline(filtered, C))
        st.caption("Weekly aggregated comment counts by sentiment, based on submission date.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Word clouds
        st.markdown('<p class="sec-label">☁️ Word Clouds by Policy Theme</p>',
                    unsafe_allow_html=True)
        st.caption("Word size reflects frequency within each theme. "
                   "Each theme uses a distinct colour palette.")

        themes_present = sorted(filtered["Theme"].unique().tolist())
        if themes_present:
            for i in range(0, len(themes_present), 2):
                wc_left, wc_right = st.columns(2)
                for j, col in enumerate([wc_left, wc_right]):
                    idx = i + j
                    if idx >= len(themes_present):
                        break
                    tn   = themes_present[idx]
                    tc   = filtered[filtered["Theme"] == tn]["Comment"]
                    tp   = (filtered[filtered["Theme"] == tn]["Sentiment"] == "Positive").sum()
                    tnu  = (filtered[filtered["Theme"] == tn]["Sentiment"] == "Neutral").sum()
                    tng  = (filtered[filtered["Theme"] == tn]["Sentiment"] == "Negative").sum()
                    tavg = filtered[filtered["Theme"] == tn]["Polarity"].mean()
                    with col:
                        st.markdown(f'<div class="cl-card"><h4>☁️ {tn}</h4>',
                                    unsafe_allow_html=True)
                        st.caption(f"{len(tc)} comments &nbsp;·&nbsp; "
                                   f"✅ {tp} pos &nbsp;➖ {tnu} neu &nbsp;❌ {tng} neg "
                                   f"&nbsp;·&nbsp; avg polarity {tavg:+.3f}")
                        _show(make_wordcloud(tc, THEME_CMAPS.get(tn, "viridis"), C))
                        st.markdown('</div>', unsafe_allow_html=True)

        # Theme deep-dive expander
        st.markdown('<p class="sec-label">🔬 Theme Deep Dive</p>',
                    unsafe_allow_html=True)
        with st.expander("Expand to read every comment by theme", expanded=False):
            if themes_present:
                for ttab, tname in zip(st.tabs(themes_present), themes_present):
                    with ttab:
                        tdf  = filtered[filtered["Theme"] == tname].copy()
                        tavg = tdf["Polarity"].mean()
                        mood = ("🟢 Mostly Positive" if tavg >  0.06 else
                                "🔴 Mostly Negative" if tavg < -0.06 else "🟡 Mixed")
                        st.markdown(
                            f"**{len(tdf)} comments** &nbsp;·&nbsp; {mood} "
                            f"&nbsp;·&nbsp; Avg polarity: **{tavg:+.4f}**"
                        )
                        st.dataframe(
                            tdf[["Comment", "Sentiment", "Polarity", "Subjectivity",
                                 "Confidence %", "Source", "Date"]]
                            .reset_index(drop=True),
                            use_container_width=True,
                        )

        # Full data table
        st.markdown('<p class="sec-label">📋 All Comments</p>',
                    unsafe_allow_html=True)
        st.caption(f"Showing **{total}** of **{len(df)}** comments · "
                   "Sentiment column is colour-coded")

        def _colour_sentiment(val: str) -> str:
            return {
                "Positive": f"background-color:{C['pos_bg']};color:{C['pos_fg']};font-weight:700;",
                "Negative": f"background-color:{C['neg_bg']};color:{C['neg_fg']};font-weight:700;",
                "Neutral":  f"background-color:{C['neu_bg']};color:{C['neu_fg']};font-weight:700;",
            }.get(val, "")

        st.dataframe(
            filtered.reset_index(drop=True)
            .style.map(_colour_sentiment, subset=["Sentiment"]),
            use_container_width=True,
            height=380,
        )

        # Export
        st.markdown('<p class="sec-label">💾 Export</p>', unsafe_allow_html=True)
        ex1, ex2 = st.columns(2)
        with ex1:
            st.markdown('<div class="cl-card"><h4>📊 Enriched Dataset — CSV</h4>',
                        unsafe_allow_html=True)
            st.markdown(
                f"<p>All {total} filtered comments with Sentiment, Polarity, "
                f"Subjectivity, Theme, and Confidence scores — ready for Excel "
                f"or further analysis.</p>",
                unsafe_allow_html=True,
            )
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
                "<p>Executive report: sentiment overview, per-theme breakdown, "
                "top and worst comments, and ranked policy recommendations.</p>",
                unsafe_allow_html=True,
            )
            st.download_button(
                "📄  Download Policy Report",
                generate_report(filtered).encode("utf-8"),
                f"citizenlens_report_{datetime.date.today()}.txt",
                "text/plain",
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("👀 Preview Policy Report", expanded=False):
            st.markdown(
                f'<div class="report-box">{generate_report(filtered)}</div>',
                unsafe_allow_html=True,
            )

    # ═══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — BULK UPLOAD
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_upload:
        st.markdown('<p class="sec-label">📂 Bulk Upload Existing Feedback</p>',
                    unsafe_allow_html=True)
        st.markdown("""
<div class="cl-card">
  <h4>📤 Upload a CSV file of citizen comments</h4>
  <p>
    Upload any CSV that contains a <code>comment</code> or <code>Comment</code> column.
    CitizenLens runs the full NLP pipeline on every row automatically.<br>
    Optional extra columns: <code>source</code>, <code>date</code>, <code>name</code>.
  </p>
</div>
""", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="Must contain a 'comment' column.",
        )
        if uploaded:
            try:
                raw     = pd.read_csv(uploaded)
                col_map = {c.lower(): c for c in raw.columns}
                if "comment" not in col_map:
                    st.error("❌  No 'comment' column found. Check your CSV headers.")
                else:
                    cc = col_map["comment"]
                    with st.spinner(f"Analyzing {len(raw)} comments — please wait…"):
                        new_rows = []
                        for _, row in raw.iterrows():
                            txt = str(row[cc]).strip()
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
                                "Source":       str(row.get("source",
                                                    row.get("Source", "CSV Upload"))),
                                "Date":         str(row.get("date",
                                                    row.get("Date",
                                                    datetime.date.today()))),
                                "Submitted At": datetime.datetime.now().strftime("%H:%M:%S"),
                            })
                        st.session_state.uploaded_rows += new_rows
                    st.success(
                        f"✅  **{len(new_rows)} comments imported and analyzed.** "
                        f"Switch to the Dashboard tab to see the updated charts."
                    )
                    st.dataframe(
                        pd.DataFrame(new_rows)[["Comment", "Sentiment", "Polarity", "Theme"]]
                        .head(10),
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"❌  Could not process file: {e}")

        st.markdown("""
<div class="cl-card" style="margin-top:18px;">
  <h4>📋 Expected CSV Format</h4>
  <p>Only the <code>comment</code> column is required. Example:</p>
</div>
""", unsafe_allow_html=True)
        example = pd.DataFrame({
            "comment": [
                "The new park renovation has completely transformed our neighbourhood.",
                "Bus routes to rural areas are still inadequate despite repeated promises.",
                "Affordable housing targets are not being met — we need accountability.",
            ],
            "source": ["Resident Survey", "Public Forum", "Email Submission"],
            "date":   ["2025-03-01", "2025-03-15", "2025-04-01"],
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

    # ═══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — ABOUT
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_about:
        st.markdown('<p class="sec-label">ℹ️ About CitizenLens</p>',
                    unsafe_allow_html=True)
        st.markdown("""
<div class="cl-card">
  <h4>🏛️ What is CitizenLens?</h4>
  <p>
    CitizenLens is an open-source AI platform that transforms raw citizen feedback
    into structured policy intelligence. Instead of thousands of comments sitting
    unread in government inboxes, CitizenLens runs every comment through a
    natural language processing pipeline — scoring sentiment, measuring subjectivity,
    and clustering by policy topic — then visualises the results in a real-time
    dashboard that policymakers can act on.
  </p>
</div>

<div class="cl-card">
  <h4>🧠 NLP Pipeline</h4>
  <p>
    <strong>Step 1 — Sentiment Scoring:</strong> TextBlob calculates a polarity
    score (−1.0 to +1.0) and a subjectivity score (0.0 to 1.0) using pattern-based
    analysis. Threshold: &gt;+0.08 = Positive, &lt;−0.08 = Negative, else Neutral.
    <br><br>
    <strong>Step 2 — Topic Clustering:</strong> A custom keyword-frequency dictionary
    spans 6 policy domains (120+ keywords). Hit count relative to domain size
    produces a Confidence % score, with a +40 base to avoid zero-confidence
    single-keyword matches.
    <br><br>
    <strong>Step 3 — Visualisation:</strong> Six chart types and per-theme word
    clouds update live as sidebar filters change. The Policy Report aggregates
    everything into a structured executive summary.
  </p>
</div>

<div class="cl-card">
  <h4>📊 Dataset</h4>
  <p>
    The 50-row seed dataset is original, hand-authored content covering six policy
    domains. It was written specifically for this project — not scraped, copied,
    or sourced from any restricted or government-only dataset. This satisfies the
    hackathon requirement: <em>"Teams must use only publicly available or
    self-generated datasets."</em>
  </p>
</div>

<div class="cl-card">
  <h4>🛠️ Tech Stack</h4>
  <div class="stat-strip">
    <div class="stat-pill">🔴 Streamlit — UI</div>
    <div class="stat-pill">🧠 TextBlob — NLP</div>
    <div class="stat-pill">🐼 Pandas — Data</div>
    <div class="stat-pill">☁️ WordCloud</div>
    <div class="stat-pill">📈 Matplotlib</div>
    <div class="stat-pill">🚀 Streamlit Cloud</div>
    <div class="stat-pill">🐙 GitHub</div>
  </div>
</div>

<div class="cl-card">
  <h4>⚖️ Ethics & License</h4>
  <p>
    MIT licensed. No personal data is stored beyond the browser session.
    Submitted comments live in Streamlit session state only — never written to disk
    or sent to any external server. The NLP engine informs human policymakers;
    it never makes autonomous decisions. All outputs require human review.
  </p>
</div>
""", unsafe_allow_html=True)

    # Footer
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{C['muted']};font-size:0.75rem;'>"
        "CitizenLens v3.0 &nbsp;·&nbsp; "
        "Streamlit · TextBlob · WordCloud · Matplotlib &nbsp;·&nbsp; "
        "Open Government Hackathon 2025 &nbsp;·&nbsp; MIT License"
        "</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
