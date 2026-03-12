# =============================================================================
#  CitizenLens  — AI-Powered Policy Comment Intelligence Platform
#  Version     : 2.2.0  (toggle-fix release)
#  Built for   : Open Government Hackathon 2025  |  License: MIT
#
#  HOW DARK/LIGHT TOGGLE WORKS IN THIS VERSION
#  ─────────────────────────────────────────────
#  The toggle is rendered at the very TOP of the main page (not inside the
#  sidebar) using st.columns. This means it is ALWAYS visible and clickable
#  regardless of sidebar state, screen size, or reruns.
#  Clicking it flips st.session_state.dark_mode and calls st.rerun().
# =============================================================================

import io
import datetime
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS

matplotlib.use("Agg")

# =============================================================================
#  PAGE CONFIG  (must be first Streamlit call)
# =============================================================================
st.set_page_config(
    page_title="CitizenLens | Policy Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
#  SESSION STATE
# =============================================================================
for key, default in [
    ("dark_mode", False),
    ("submitted_comments", []),
    ("uploaded_rows", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

DARK = st.session_state.dark_mode

# =============================================================================
#  COLOUR PALETTE
# =============================================================================
def palette(dark):
    if dark:
        return dict(
            bg="#0e1621",         sidebar="#090f18",
            card="#162032",       card_border="#1e3050",  card_hover="#1e2d45",
            hero_a="#090f18",     hero_b="#0a2250",
            text="#dce8ff",       text2="#7a9cc8",        muted="#5a7899",
            accent="#3d8eff",     accent2="#00e5b0",      accent3="#ff6b6b",
            pos="#00d68f",        neg="#ff4d4d",          neu="#5b9bf5",
            pos_bg="#012d1a",     pos_fg="#00d68f",
            neg_bg="#2d0101",     neg_fg="#ff4d4d",
            neu_bg="#011833",     neu_fg="#5b9bf5",
            input_bg="#162032",   input_border="#1e3050",
            chart_bg="#162032",   chart_text="#8aaed4",   chart_grid="#1e3050",
            wc_bg="#162032",
            rep_bg="#0c1825",     rep_border="#1e3050",
            dl="#3d8eff",         submit="#3d8eff",
            div="#1e3050",        sec="#3d8eff",
            tag_new_bg="#012d1a", tag_new_fg="#00d68f",
        )
    else:
        return dict(
            bg="#f0f5fc",         sidebar="#0d1e38",
            card="#ffffff",       card_border="#d4e3f7",  card_hover="#f5f9ff",
            hero_a="#0d1e38",     hero_b="#1546a0",
            text="#0d1e38",       text2="#2d4e7a",        muted="#5a7899",
            accent="#1546a0",     accent2="#00a87a",      accent3="#e03e3e",
            pos="#16a34a",        neg="#dc2626",          neu="#2563eb",
            pos_bg="#dcfce7",     pos_fg="#15803d",
            neg_bg="#fee2e2",     neg_fg="#b91c1c",
            neu_bg="#dbeafe",     neu_fg="#1d4ed8",
            input_bg="#ffffff",   input_border="#c2d6f0",
            chart_bg="#ffffff",   chart_text="#4a6a8a",   chart_grid="#e4edf8",
            wc_bg="#f5f9ff",
            rep_bg="#eef5ff",     rep_border="#c2d6f0",
            dl="#1546a0",         submit="#1546a0",
            div="#d4e3f7",        sec="#1546a0",
            tag_new_bg="#dcfce7", tag_new_fg="#15803d",
        )

C = palette(DARK)

# =============================================================================
#  CSS INJECTION
# =============================================================================
def inject_css(C, dark):
    shadow = "0 8px 32px rgba(0,0,0,0.35)" if dark else "0 4px 20px rgba(13,30,56,0.08)"
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*,*::before,*::after{{box-sizing:border-box;}}
html,body,[class*="css"]{{font-family:'Plus Jakarta Sans',sans-serif!important;}}
.stApp{{background:{C['bg']}!important;}}

/* ── Universal text ───────────────────────────────────────── */
p,span,div,li,td,th,small,em,strong,
.stMarkdown,.stText,.stCaption,.element-container{{color:{C['text']}!important;}}
h1,h2,h3,h4,h5,h6{{color:{C['text']}!important;}}
strong{{color:{C['text']}!important;font-weight:700;}}
a{{color:{C['accent']}!important;}}
code{{
  background:{C['card']}!important;color:{C['accent2']}!important;
  border:1px solid {C['card_border']}!important;border-radius:5px;
  padding:1px 6px;font-family:'JetBrains Mono',monospace!important;font-size:0.85em;
}}

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"]{{
  background:{C['sidebar']}!important;
  border-right:1px solid rgba(255,255,255,0.06)!important;
}}
section[data-testid="stSidebar"] *{{color:#b8cfe8!important;}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] strong{{color:#ffffff!important;}}
section[data-testid="stSidebar"] hr{{border-color:rgba(255,255,255,0.1)!important;}}
section[data-testid="stSidebar"] label{{
  color:#8aaed4!important;font-size:0.75rem!important;font-weight:700!important;
  text-transform:uppercase!important;letter-spacing:0.8px!important;
}}
section[data-testid="stSidebar"] .stRadio label{{
  color:#b8cfe8!important;text-transform:none!important;
  font-size:0.88rem!important;letter-spacing:0!important;
}}
section[data-testid="stSidebar"] .stMultiSelect>div>div,
section[data-testid="stSidebar"] .stSelectbox>div>div{{
  background:rgba(255,255,255,0.07)!important;
  border-color:rgba(255,255,255,0.12)!important;color:#dce8ff!important;
}}

/* ── Theme toggle strip (top of main area) ────────────────── */
.toggle-strip{{
  display:flex;align-items:center;justify-content:flex-end;
  margin-bottom:18px;gap:12px;
}}
.toggle-strip .mode-label{{
  font-size:0.8rem;font-weight:700;color:{C['muted']};
}}

/* ── KPI cards ────────────────────────────────────────────── */
div[data-testid="metric-container"]{{
  background:{C['card']}!important;border:1.5px solid {C['card_border']}!important;
  border-radius:18px!important;padding:22px 26px!important;
  box-shadow:{shadow}!important;transition:transform 0.22s,box-shadow 0.22s!important;
}}
div[data-testid="metric-container"]:hover{{
  transform:translateY(-4px)!important;
  box-shadow:0 12px 36px rgba(0,0,0,{'0.4' if dark else '0.12'})!important;
}}
div[data-testid="metric-container"] label{{
  color:{C['muted']}!important;font-size:0.68rem!important;font-weight:800!important;
  text-transform:uppercase!important;letter-spacing:1px!important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{{
  font-size:2.1rem!important;font-weight:800!important;
  color:{C['text']}!important;line-height:1.1!important;
}}

/* ── Cards ────────────────────────────────────────────────── */
.cl-card{{
  background:{C['card']};border:1.5px solid {C['card_border']};
  border-radius:18px;padding:26px;margin-bottom:20px;box-shadow:{shadow};
}}
.cl-card h4{{
  color:{C['text']}!important;font-size:0.92rem!important;
  font-weight:800!important;margin:0 0 18px!important;
}}
.cl-card p{{color:{C['text2']}!important;}}

/* ── Hero ─────────────────────────────────────────────────── */
.hero{{
  background:linear-gradient(140deg,{C['hero_a']} 0%,{C['hero_b']} 100%);
  border-radius:22px;padding:40px 48px;margin-bottom:24px;
  position:relative;overflow:hidden;
}}
.hero::before{{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 90% 20%,rgba(61,142,255,0.22) 0%,transparent 55%),
             radial-gradient(ellipse at 10% 80%,rgba(0,229,176,0.12) 0%,transparent 50%);
}}
.hero-inner{{position:relative;z-index:1;}}
.hero h1{{color:#fff!important;font-size:2.1rem!important;font-weight:800!important;margin:0!important;}}
.hero-sub{{color:rgba(255,255,255,0.72)!important;font-size:0.92rem!important;margin:8px 0 0!important;}}
.hero-badge{{
  display:inline-flex;align-items:center;gap:7px;
  background:rgba(61,142,255,0.2);border:1px solid rgba(61,142,255,0.4);
  border-radius:30px;padding:5px 16px;font-size:0.72rem;font-weight:700;
  color:#7ec4ff!important;letter-spacing:0.8px;text-transform:uppercase;margin-bottom:16px;
}}
.hero-stat{{
  background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.15);
  border-radius:14px;padding:14px 22px;text-align:center;min-width:110px;
}}
.hero-stat-label{{color:rgba(255,255,255,0.6)!important;font-size:0.62rem!important;
  font-weight:700!important;text-transform:uppercase!important;letter-spacing:1px!important;}}
.hero-stat-val{{color:#fff!important;font-size:2rem!important;font-weight:800!important;line-height:1!important;}}

/* ── Section label ────────────────────────────────────────── */
.section-label{{
  font-size:0.65rem!important;font-weight:800!important;letter-spacing:2.5px!important;
  text-transform:uppercase!important;color:{C['sec']}!important;
  margin:36px 0 16px!important;display:flex;align-items:center;gap:10px;
}}
.section-label::after{{content:'';flex:1;height:1px;background:{C['div']};}}

/* ── Submit wrap ──────────────────────────────────────────── */
.submit-wrap{{
  background:{C['card']};border:2px solid {C['accent']};border-radius:20px;
  padding:30px 34px;margin-bottom:20px;
  box-shadow:0 0 0 5px {'rgba(61,142,255,0.08)' if dark else 'rgba(21,70,160,0.06)'};
}}
.submit-wrap h3{{color:{C['text']}!important;font-size:1.1rem!important;font-weight:800!important;margin:0 0 4px!important;}}
.submit-desc{{color:{C['text2']}!important;font-size:0.875rem!important;margin:0 0 22px!important;line-height:1.6!important;}}

/* ── Inputs ───────────────────────────────────────────────── */
.stTextArea textarea{{
  background:{C['input_bg']}!important;border:1.5px solid {C['input_border']}!important;
  border-radius:12px!important;color:{C['text']}!important;
  font-size:0.95rem!important;line-height:1.6!important;padding:12px 16px!important;
}}
.stTextArea textarea::placeholder{{color:{C['muted']}!important;opacity:1!important;}}
.stTextArea textarea:focus{{border-color:{C['accent']}!important;outline:none!important;}}
.stTextInput input{{
  background:{C['input_bg']}!important;border:1.5px solid {C['input_border']}!important;
  border-radius:10px!important;color:{C['text']}!important;
}}
.stTextInput input::placeholder{{color:{C['muted']}!important;}}
.stSelectbox>div>div{{
  background:{C['input_bg']}!important;border:1.5px solid {C['input_border']}!important;
  border-radius:10px!important;color:{C['text']}!important;
}}
.stMultiSelect>div>div{{
  background:{C['input_bg']}!important;border:1.5px solid {C['input_border']}!important;
  border-radius:10px!important;color:{C['text']}!important;
}}
.stSelectbox label,.stMultiSelect label,.stTextArea label,
.stTextInput label,.stSlider label,.stRadio label,.stFileUploader label{{
  color:{C['text']}!important;font-weight:700!important;font-size:0.875rem!important;
}}
[data-baseweb="popover"] li,[data-baseweb="menu"] li{{
  background:{C['card']}!important;color:{C['text']}!important;
}}
[data-baseweb="popover"] li:hover,[data-baseweb="menu"] li:hover{{
  background:{C['card_border']}!important;
}}
[data-baseweb="tag"]{{background:{C['neu_bg']}!important;color:{C['neu_fg']}!important;}}

/* ── Buttons ──────────────────────────────────────────────── */
div[data-testid="stForm"] button{{
  background:linear-gradient(135deg,{C['submit']},{C['accent2']})!important;
  color:white!important;border:none!important;border-radius:12px!important;
  padding:13px 28px!important;font-weight:700!important;font-size:0.95rem!important;
  width:100%!important;cursor:pointer!important;
}}
.stDownloadButton>button{{
  background:{C['dl']}!important;color:white!important;border:none!important;
  border-radius:12px!important;padding:12px 24px!important;font-weight:700!important;
  width:100%!important;
}}
.stButton>button{{
  background:{C['card']}!important;color:{C['accent']}!important;
  border:1.5px solid {C['accent']}!important;border-radius:10px!important;
  font-weight:700!important;transition:all 0.2s!important;
  padding:10px 20px!important;
}}
.stButton>button:hover{{
  background:{C['accent']}!important;color:white!important;
}}

/* ── File uploader ────────────────────────────────────────── */
[data-testid="stFileUploader"]{{
  background:{C['card']}!important;border:2px dashed {C['card_border']}!important;
  border-radius:14px!important;padding:10px!important;
}}
[data-testid="stFileUploader"] *{{color:{C['text2']}!important;}}

/* ── Dataframe ────────────────────────────────────────────── */
.stDataFrame{{border-radius:14px!important;overflow:hidden!important;}}
.stDataFrame thead th{{
  background:{'#1a2d45' if dark else '#eaf1fc'}!important;color:{C['text']}!important;
  font-weight:700!important;font-size:0.82rem!important;
}}
.stDataFrame tbody td{{color:{C['text']}!important;background:{C['card']}!important;font-size:0.875rem!important;}}
.stDataFrame tbody tr:nth-child(even) td{{background:{'#162032' if dark else '#f7f9fd'}!important;}}

/* ── Alerts ───────────────────────────────────────────────── */
div[data-testid="stAlert"]{{border-radius:14px!important;}}
div[data-testid="stAlert"] p{{color:inherit!important;}}

/* ── Expander ─────────────────────────────────────────────── */
details{{
  background:{C['card']}!important;border:1.5px solid {C['card_border']}!important;
  border-radius:16px!important;overflow:hidden!important;margin-bottom:10px!important;
}}
details summary{{
  color:{C['text']}!important;font-weight:700!important;padding:16px 22px!important;
  background:{C['card']}!important;cursor:pointer!important;font-size:0.92rem!important;
}}
details summary:hover{{background:{C['card_hover']}!important;}}
details[open]>summary{{border-bottom:1px solid {C['card_border']}!important;}}

/* ── Tabs ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]{{
  background:{C['card']}!important;border-bottom:2px solid {C['card_border']}!important;
  gap:4px!important;padding:0 8px!important;border-radius:14px 14px 0 0!important;
}}
.stTabs [data-baseweb="tab"]{{
  color:{C['muted']}!important;font-weight:600!important;
  padding:12px 18px!important;border-radius:10px 10px 0 0!important;
}}
.stTabs [aria-selected="true"]{{
  color:{C['accent']}!important;font-weight:800!important;
  background:{C['bg']}!important;border-bottom:2px solid {C['accent']}!important;
}}
.stTabs [data-testid="stTabsContent"]{{
  background:{C['card']}!important;border:1.5px solid {C['card_border']}!important;
  border-top:none!important;border-radius:0 0 14px 14px!important;padding:20px!important;
}}

/* ── Sentiment tags ───────────────────────────────────────── */
.tag-pos{{background:{C['pos_bg']};color:{C['pos_fg']};padding:3px 13px;border-radius:30px;font-size:0.75rem;font-weight:700;display:inline-block;}}
.tag-neg{{background:{C['neg_bg']};color:{C['neg_fg']};padding:3px 13px;border-radius:30px;font-size:0.75rem;font-weight:700;display:inline-block;}}
.tag-neu{{background:{C['neu_bg']};color:{C['neu_fg']};padding:3px 13px;border-radius:30px;font-size:0.75rem;font-weight:700;display:inline-block;}}
.tag-new{{background:{C['tag_new_bg']};color:{C['tag_new_fg']};padding:2px 9px;border-radius:20px;font-size:0.65rem;font-weight:800;display:inline-block;text-transform:uppercase;letter-spacing:0.5px;vertical-align:middle;margin-left:6px;}}

/* ── Latest comment cards ─────────────────────────────────── */
.latest-card{{
  background:{C['card']};border:1.5px solid {C['card_border']};
  border-left:4px solid {C['accent']};border-radius:14px;padding:16px 22px;margin-bottom:14px;
}}
.latest-meta{{color:{C['muted']};font-size:0.78rem;margin-top:8px;}}
.latest-quote{{color:{C['text']};font-size:0.93rem;line-height:1.55;margin:6px 0;font-style:italic;}}

/* ── Report box ───────────────────────────────────────────── */
.report-box{{
  background:{C['rep_bg']};border:1.5px solid {C['rep_border']};border-radius:14px;
  padding:22px 26px;font-family:'JetBrains Mono',monospace;font-size:0.75rem;
  color:{C['text']}!important;white-space:pre-wrap;max-height:380px;overflow-y:auto;line-height:1.75;
}}

/* ── Confidence bar ───────────────────────────────────────── */
.conf-bar-wrap{{width:100%;height:6px;background:{C['card_border']};border-radius:3px;overflow:hidden;}}
.conf-bar-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,{C['accent']},{C['accent2']});}}

/* ── Stat strip ───────────────────────────────────────────── */
.stat-strip{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px;}}
.stat-pill{{background:{C['card']};border:1.5px solid {C['card_border']};border-radius:30px;padding:8px 18px;font-size:0.82rem;font-weight:700;color:{C['text2']};white-space:nowrap;}}

hr{{border-color:{C['div']}!important;opacity:0.7!important;}}
.stCaption,caption,small{{color:{C['muted']}!important;}}
#MainMenu,footer,header{{visibility:hidden;}}
</style>
""", unsafe_allow_html=True)

inject_css(C, DARK)

# =============================================================================
#  TOPIC KEYWORDS  (defined before build_seed_df so the cached fn can use it)
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

# =============================================================================
#  SEED DATASET
# =============================================================================
_BASE_DATE = datetime.date(2025, 1, 1)
SEED_DATA = [
    ("The revised business grant scheme genuinely helped us survive the slow season.","Economy & Tax",15),
    ("Another property tax hike with zero improvement in local services is inexcusable.","Economy & Tax",8),
    ("Corporate incentives for the new tech park will create high-paying jobs. Strong policy.","Economy & Tax",22),
    ("Hiking sales tax on essentials during a cost-of-living crisis shows total disregard for families.","Economy & Tax",5),
    ("The economic regeneration zone has brought three new employers to our district this year.","Economy & Tax",40),
    ("The council's budget transparency portal is excellent — every citizen should use it.","Economy & Tax",55),
    ("Hidden fees in the new business licensing process are driving small traders away.","Economy & Tax",70),
    ("Reducing stamp duty for first-time buyers is exactly the kind of targeted relief we needed.","Economy & Tax",90),
    ("The segregated cycle highway on the waterfront is world-class — our city finally gets it.","Infrastructure",12),
    ("Unrepaired sinkholes on the industrial estate have damaged two delivery vehicles this month.","Infrastructure",18),
    ("The new intercity rail link will transform commuting and reduce congestion enormously.","Infrastructure",28),
    ("Bus routes cut by 40% since last year — rural communities are completely isolated now.","Infrastructure",35),
    ("EV charging stations in every council car park by year-end is an ambitious but achievable target.","Infrastructure",50),
    ("The harbour bridge closure with zero alternative route was catastrophically mismanaged.","Infrastructure",60),
    ("Pavement tactile paving upgrades across the city centre have improved accessibility significantly.","Infrastructure",75),
    ("Flood drainage on the south ring road is completely inadequate — it floods every winter.","Infrastructure",85),
    ("Smart traffic signals at the five busiest junctions have cut rush-hour delays by 18%.","Infrastructure",100),
    ("The long-promised footbridge connecting the station to the business park is still not built.","Infrastructure",110),
    ("The community land trust pilot in Westgate is the most progressive housing policy in years.","Housing",20),
    ("Retrospective planning approval for the illegal riverside development sets a terrible precedent.","Housing",30),
    ("Purpose-built student accommodation near the university is relieving pressure on family housing.","Housing",45),
    ("Permitted development rights abuse is converting quality office space into substandard flats.","Housing",58),
    ("The rent-to-buy scheme gave my family a realistic pathway to ownership after seven years of renting.","Housing",72),
    ("Green-belt encroachment for luxury estates while social housing waiting lists grow is unforgivable.","Housing",82),
    ("Retrofit grants for Victorian terraces will reduce emissions and fuel poverty simultaneously.","Housing",95),
    ("The planning portal redesign is a genuine improvement — applications take half the time now.","Housing",115),
    ("Mixed-tenure social housing developments foster much healthier communities than segregated estates.","Housing",130),
    ("The river rewilding project has restored otter and kingfisher populations. Remarkable work.","Environment & Parks",10),
    ("Industrial effluent discharge near the estuary has not been properly investigated despite reports.","Environment & Parks",25),
    ("Community allotment expansion programme has a two-year waiting list — scale it up urgently.","Environment & Parks",38),
    ("The new air quality monitoring network finally gives us real-time data to hold polluters accountable.","Environment & Parks",52),
    ("Replacing grass verges with wildflower meadows is beautiful, cheap, and brilliant for biodiversity.","Environment & Parks",65),
    ("Single-use plastic ban in council-run venues should extend to all licensed premises immediately.","Environment & Parks",78),
    ("The waste-to-energy plant proposal near primary schools is deeply alarming and must be refused.","Environment & Parks",92),
    ("Urban tree canopy target of 25% by 2030 is ambitious and the right direction for climate resilience.","Environment & Parks",105),
    ("Contaminated land remediation at the old gasworks site is long overdue — residents deserve answers.","Environment & Parks",120),
    ("Neighbourhood watch digital integration with the council portal has visibly reduced burglaries.","Public Safety",14),
    ("Knife crime intervention programmes for at-risk youth deserve far more sustained investment.","Public Safety",32),
    ("Ambulance response times in rural postcodes remain dangerously above the national target.","Public Safety",47),
    ("The new community safety hub brings police, social services, and housing under one roof. Excellent.","Public Safety",63),
    ("CCTV expansion without a clear data governance policy is surveillance creep, not public safety.","Public Safety",80),
    ("The fire station closure in Millbrook leaves 15,000 residents with unacceptably slow coverage.","Public Safety",96),
    ("Early years literacy programme results show a 22% improvement in school readiness. Keep investing.","Education & Services",17),
    ("Adult education centre cuts mean workers cannot access the retraining they need after redundancy.","Education & Services",33),
    ("Free school meals extension to all primary pupils is a straightforward public health intervention.","Education & Services",48),
    ("The new community hub model co-locating library, health, and job-centre services is inspired.","Education & Services",67),
    ("Special educational needs funding shortfall is forcing schools to exclude children who need support.","Education & Services",84),
    ("Digital inclusion tablets for care home residents bridging the connectivity gap — wonderful scheme.","Education & Services",102),
    ("Closing the only youth centre in Northfield will push teenagers onto streets. Short-sighted saving.","Education & Services",118),
    ("Graduate retention grants for healthcare professionals have reduced vacancy rates by a third.","Education & Services",135),
]

@st.cache_data
def build_seed_df():
    rows = []
    for comment, theme, day_offset in SEED_DATA:
        blob = TextBlob(comment)
        pol  = round(blob.sentiment.polarity, 4)
        subj = round(blob.sentiment.subjectivity, 4)
        sent = "Positive" if pol > 0.08 else ("Negative" if pol < -0.08 else "Neutral")
        kws  = TOPIC_KEYWORDS.get(theme, [])
        hits = sum(1 for kw in kws if kw.lower() in comment.lower())
        conf = min(int(hits / max(len(kws),1) * 100 + 40), 100)
        rows.append({
            "Comment": comment, "Theme": theme, "Sentiment": sent,
            "Polarity": pol, "Subjectivity": subj, "Confidence %": conf,
            "Source": "Seed Dataset",
            "Date": (_BASE_DATE + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d"),
            "Submitted At": "—",
        })
    return pd.DataFrame(rows)

# =============================================================================
#  NLP
# =============================================================================
def detect_theme(text):
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in TOPIC_KEYWORDS.items()}
    scores = {t: s for t, s in scores.items() if s}
    if not scores:
        return "General / Other", 30
    best = max(scores, key=scores.get)
    return best, min(int(scores[best] / len(TOPIC_KEYWORDS[best]) * 100 + 40), 100)

def run_nlp(text):
    blob = TextBlob(str(text))
    pol  = round(blob.sentiment.polarity, 4)
    subj = round(blob.sentiment.subjectivity, 4)
    sent = "Positive" if pol > 0.08 else ("Negative" if pol < -0.08 else "Neutral")
    theme, conf = detect_theme(text)
    return dict(Sentiment=sent, Polarity=pol, Subjectivity=subj, Theme=theme, confidence=conf)

def build_full_df():
    base  = build_seed_df().copy()
    extra = st.session_state.submitted_comments + st.session_state.uploaded_rows
    if extra:
        return pd.concat([pd.DataFrame(extra), base], ignore_index=True)
    return base

# =============================================================================
#  CHARTS
# =============================================================================
SCOL = {"Positive":"#00d68f","Neutral":"#5b9bf5","Negative":"#ff4d4d"}
TPAL = ["#3d8eff","#00e5b0","#f5a623","#b06bff","#ff7c5c","#00d4ff","#a3e635"]

def _style(fig, ax, C):
    fig.patch.set_facecolor(C["chart_bg"]); ax.set_facecolor(C["chart_bg"])
    ax.spines[["top","right"]].set_visible(False)
    ax.spines["left"].set_color(C["chart_grid"]); ax.spines["bottom"].set_color(C["chart_grid"])
    ax.tick_params(colors=C["chart_text"], labelsize=9.5)
    ax.yaxis.grid(True, color=C["chart_grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True); plt.tight_layout()

def _show(fig):
    st.pyplot(fig); plt.close(fig)

def chart_sentiment(df, C):
    counts = df["Sentiment"].value_counts().reindex(["Positive","Neutral","Negative"], fill_value=0)
    fig, ax = plt.subplots(figsize=(5,3.6))
    bars = ax.bar(counts.index, counts.values, color=[SCOL[s] for s in counts.index],
                  edgecolor=C["chart_bg"], linewidth=2.5, width=0.48, zorder=3)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+0.2, str(int(h)),
                ha="center", va="bottom", fontsize=13, fontweight="bold", color=C["text"])
    ax.set_ylabel("Comments", fontsize=10, color=C["chart_text"])
    ax.set_ylim(0, max(counts.max(),1)+3)
    ax.tick_params(axis="x", colors=C["text"], labelsize=11)
    _style(fig, ax, C); return fig

def chart_themes(df, C):
    counts = df["Theme"].value_counts()
    fig, ax = plt.subplots(figsize=(5,3.8))
    bars = ax.barh(counts.index, counts.values, color=TPAL[:len(counts)],
                   edgecolor=C["chart_bg"], linewidth=1.5, height=0.52, zorder=3)
    for b in bars:
        w = b.get_width()
        ax.text(w+0.15, b.get_y()+b.get_height()/2, str(int(w)),
                va="center", fontsize=11, fontweight="bold", color=C["text"])
    ax.set_xlabel("Comments", fontsize=10, color=C["chart_text"])
    ax.set_xlim(0, max(counts.max(),1)+2.5); ax.invert_yaxis()
    ax.tick_params(axis="y", colors=C["text"])
    ax.xaxis.grid(True, color=C["chart_grid"], linewidth=0.6, zorder=0); ax.yaxis.grid(False)
    fig.patch.set_facecolor(C["chart_bg"]); ax.set_facecolor(C["chart_bg"])
    ax.spines[["top","right","left"]].set_visible(False); ax.spines["bottom"].set_color(C["chart_grid"])
    plt.tight_layout(); return fig

def chart_polarity(df, C):
    fig, ax = plt.subplots(figsize=(5,3.4))
    ax.hist(df["Polarity"], bins=16, color=C["accent"], edgecolor=C["chart_bg"], linewidth=1, zorder=3, alpha=0.85)
    ax.axvline(0, color=C["muted"], linestyle="--", linewidth=1.5)
    mv = df["Polarity"].mean()
    ax.axvline(mv, color="#f5a623", linestyle="-", linewidth=2, label=f"Mean {mv:+.2f}")
    ax.set_xlabel("Polarity  (−1 → +1)", fontsize=10, color=C["chart_text"])
    ax.set_ylabel("Frequency", fontsize=10, color=C["chart_text"])
    leg = ax.legend(fontsize=9, framealpha=0.4, facecolor=C["chart_bg"])
    for t in leg.get_texts(): t.set_color(C["text"])
    _style(fig, ax, C); return fig

def chart_stacked(df, C):
    pivot = df.groupby(["Theme","Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive","Neutral","Negative"]:
        if col not in pivot.columns: pivot[col] = 0
    pivot = pivot[["Positive","Neutral","Negative"]]
    fig, ax = plt.subplots(figsize=(5,3.8))
    bot = pd.Series([0.0]*len(pivot), index=pivot.index)
    for s, color in SCOL.items():
        ax.bar(pivot.index, pivot[s], bottom=bot, color=color, label=s,
               edgecolor=C["chart_bg"], linewidth=0.8)
        bot = bot + pivot[s]
    ax.set_ylabel("Comments", fontsize=10, color=C["chart_text"])
    ax.tick_params(axis="x", rotation=26, labelsize=8.5, colors=C["text"])
    ax.tick_params(axis="y", colors=C["text"])
    leg = ax.legend(fontsize=9, loc="upper right", framealpha=0.4, facecolor=C["chart_bg"])
    for t in leg.get_texts(): t.set_color(C["text"])
    _style(fig, ax, C); return fig

def chart_scatter(df, C):
    fig, ax = plt.subplots(figsize=(5,3.6))
    for sent, color in SCOL.items():
        s = df[df["Sentiment"]==sent]
        ax.scatter(s["Polarity"], s["Subjectivity"], c=color, label=sent,
                   alpha=0.72, s=55, edgecolors=C["chart_bg"], linewidths=1, zorder=3)
    ax.axvline(0, color=C["muted"], linestyle="--", linewidth=1, alpha=0.6)
    ax.axhline(0.5, color=C["muted"], linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("Polarity Score", fontsize=10, color=C["chart_text"])
    ax.set_ylabel("Subjectivity Score", fontsize=10, color=C["chart_text"])
    for x,y,lbl in [(-0.95,0.97,"Negative\nSubjective"),(0.55,0.97,"Positive\nSubjective"),
                     (-0.95,0.03,"Negative\nObjective"),(0.55,0.03,"Positive\nObjective")]:
        ax.text(x,y,lbl,fontsize=7.5,color=C["muted"],va="top" if y>0.5 else "bottom")
    leg = ax.legend(fontsize=9, framealpha=0.4, facecolor=C["chart_bg"])
    for t in leg.get_texts(): t.set_color(C["text"])
    ax.set_xlim(-1.1,1.1); ax.set_ylim(-0.05,1.05)
    _style(fig, ax, C); return fig

def chart_timeline(df, C):
    empty_fig = lambda: (plt.subplots(figsize=(10,2.5))[0]
                         if False else _empty_timeline(C))
    def _empty_timeline(C):
        fig, ax = plt.subplots(figsize=(10,2.5))
        ax.text(0.5,0.5,"No date data available",ha="center",va="center",color=C["muted"])
        ax.axis("off"); fig.patch.set_facecolor(C["chart_bg"]); return fig
    if "Date" not in df.columns: return _empty_timeline(C)
    df2 = df.copy(); df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce")
    df2 = df2.dropna(subset=["Date"])
    if df2.empty: return _empty_timeline(C)
    df2["Week"] = df2["Date"].dt.to_period("W").dt.start_time
    weekly = df2.groupby(["Week","Sentiment"]).size().unstack(fill_value=0)
    for col in ["Positive","Neutral","Negative"]:
        if col not in weekly.columns: weekly[col] = 0
    fig, ax = plt.subplots(figsize=(10,2.8))
    for s, color in SCOL.items():
        ax.fill_between(weekly.index, weekly[s], alpha=0.2, color=color)
        ax.plot(weekly.index, weekly[s], color=color, linewidth=2,
                label=s, marker="o", markersize=4)
    ax.set_ylabel("Count", fontsize=9, color=C["chart_text"])
    ax.tick_params(axis="x", rotation=25, labelsize=8, colors=C["text"])
    ax.tick_params(axis="y", colors=C["text"])
    leg = ax.legend(fontsize=9, framealpha=0.4, facecolor=C["chart_bg"], loc="upper left")
    for t in leg.get_texts(): t.set_color(C["text"])
    _style(fig, ax, C); return fig

EXTRA_STOP = {"will","city","new","one","also","get","make","need","use","say","go","come",
              "want","people","think","know","good","much","really","well","way","time","year",
              "many","still","even","back","us","our","more","very","been","have","this","that",
              "with","from","they","their","were","are","has","had","not","but","for","and","the","its","into"}
THEME_CMAPS = {"Economy & Tax":"YlOrBr","Infrastructure":"Blues","Housing":"Purples",
               "Environment & Parks":"Greens","Public Safety":"Oranges",
               "Education & Services":"PuBuGn","General / Other":"Greys"}

def make_wordcloud(series, cmap, C):
    text = " ".join(series.astype(str).tolist()).strip()
    fig, ax = plt.subplots(figsize=(6,2.8))
    fig.patch.set_facecolor(C["wc_bg"]); ax.set_facecolor(C["wc_bg"])
    if len(text.split()) < 5:
        ax.text(0.5,0.5,"Add more comments for a word cloud",ha="center",va="center",
                fontsize=11,color=C["muted"]); ax.axis("off"); return fig
    try:
        wc = WordCloud(width=820,height=300,background_color=C["wc_bg"],colormap=cmap,
                       max_words=60,collocations=False,prefer_horizontal=0.78,
                       stopwords=STOPWORDS.union(EXTRA_STOP),min_font_size=10).generate(text)
        ax.imshow(wc, interpolation="bilinear")
    except Exception:
        ax.text(0.5,0.5,"Word cloud unavailable",ha="center",va="center",color=C["muted"])
    ax.axis("off"); plt.tight_layout(pad=0); return fig

# =============================================================================
#  REPORT
# =============================================================================
def generate_report(df):
    n = len(df)
    if n == 0: return "No data to report."
    pos = (df["Sentiment"]=="Positive").sum()
    neg = (df["Sentiment"]=="Negative").sum()
    neu = (df["Sentiment"]=="Neutral").sum()
    avg = df["Polarity"].mean()
    live = len(df[df["Source"] != "Seed Dataset"])
    now  = datetime.datetime.now().strftime("%d %B %Y  %H:%M")
    L = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║        C I T I Z E N L E N S   —   P O L I C Y             ║",
        "║              I N S I G H T   R E P O R T                    ║",
        "╚══════════════════════════════════════════════════════════════╝",
        f"\n  Generated  : {now}",
        f"  Comments   : {n} analyzed  ({live} live, {n-live} seed)",
        f"  Filters    : see dashboard sidebar\n",
        "── OVERALL SENTIMENT ──────────────────────────────────────────",
        f"  ✅ Positive   : {pos:>4}  ({round(pos/n*100)}%)",
        f"  ➖ Neutral    : {neu:>4}  ({round(neu/n*100)}%)",
        f"  ❌ Negative   : {neg:>4}  ({round(neg/n*100)}%)",
        f"  📊 Avg Polarity     : {avg:+.4f}",
        f"  📐 Avg Subjectivity : {df['Subjectivity'].mean():.4f}\n",
        "── PER-THEME BREAKDOWN ────────────────────────────────────────",
    ]
    stats = df.groupby("Theme").agg(
        Count=("Sentiment","count"),
        Pos=("Sentiment",lambda x:(x=="Positive").sum()),
        Neg=("Sentiment",lambda x:(x=="Negative").sum()),
        Neu=("Sentiment",lambda x:(x=="Neutral").sum()),
        Pol=("Polarity","mean"),Subj=("Subjectivity","mean"),
    ).sort_values("Count", ascending=False)
    for theme, r in stats.iterrows():
        mood = "🟢" if r["Pol"]>0.06 else ("🔴" if r["Pol"]<-0.06 else "🟡")
        L += [f"\n  {mood}  {theme}",
              f"     Comments:{int(r['Count'])}  ✅{int(r['Pos'])} ➖{int(r['Neu'])} ❌{int(r['Neg'])}",
              f"     Avg Polarity:{r['Pol']:+.4f}  Avg Subjectivity:{r['Subj']:.4f}"]
    for label, method, col in [("MOST POSITIVE","nlargest","Positive"),("MOST NEGATIVE","nsmallest","Negative")]:
        L.append(f"\n\n── TOP 3 {label} ──────────────────────────────")
        fn = getattr(df[df["Sentiment"]==col], method)
        for i,(_, r) in enumerate(fn(3,"Polarity").iterrows(), 1):
            L += [f"\n  {i}.  [{r['Polarity']:+.4f}]  {r['Theme']}", f'       "{r["Comment"]}"']
    L.append("\n\n── POLICY RECOMMENDATIONS ─────────────────────────────────────")
    neg_t = df[df["Sentiment"]=="Negative"].groupby("Theme").size().sort_values(ascending=False)
    for i,(t,c) in enumerate(neg_t.items(),1):
        L.append(f"  {i}. ⚠️  {t:35s}  {'█'*min(c,20)}  ({c})")
    pos_t = df[df["Sentiment"]=="Positive"].groupby("Theme").size().sort_values(ascending=False)
    L.append("\n  Best practice themes:\n")
    for i,(t,c) in enumerate(pos_t.items(),1):
        L.append(f"  {i}. ✅  {t:35s}  {'█'*min(c,20)}  ({c})")
    L += ["\n\n╔══════════════════════════════════════════════════════════════╗",
          "║  CitizenLens  |  Open Government Hackathon 2025  |  v2.2   ║",
          "╚══════════════════════════════════════════════════════════════╝"]
    return "\n".join(L)

# =============================================================================
#  MAIN
# =============================================================================
def main():
    # ── SIDEBAR — filters only (no toggle here) ───────────────────────────────
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        df_all = build_full_df()
        all_themes = sorted(df_all["Theme"].unique().tolist())
        sel_themes = st.multiselect("Policy Theme", all_themes, default=all_themes)
        sel_sents  = st.multiselect("Sentiment", ["Positive","Neutral","Negative"],
                                    default=["Positive","Neutral","Negative"])
        p_min = float(df_all["Polarity"].min())
        p_max = float(df_all["Polarity"].max())
        pol_r  = st.slider("Polarity Range", p_min, p_max, (p_min, p_max), 0.01)
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

    # ── DARK / LIGHT TOGGLE — always visible at top of main area ──────────────
    # Rendered OUTSIDE the sidebar so it is never hidden when sidebar collapses.
    tog_col, _, label_col = st.columns([1, 6, 2])
    with tog_col:
        toggle_label = "☀️ Light Mode" if DARK else "🌙 Dark Mode"
        if st.button(toggle_label, key="dark_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with label_col:
        st.markdown(
            f"<p style='text-align:right;color:{C['muted']};font-size:0.8rem;"
            f"margin-top:10px;font-weight:600;'>"
            f"{'🌙 Dark Mode' if DARK else '☀️ Light Mode'} active</p>",
            unsafe_allow_html=True,
        )

    # ── FILTER DATA ──────────────────────────────────────────────────────────
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
    st.markdown(f"""
<div class="hero"><div class="hero-inner">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:20px;">
    <div>
      <div class="hero-badge">🏆 Open Government Hackathon 2025</div>
      <h1>🏛️ CitizenLens</h1>
      <p class="hero-sub">AI-powered policy comment intelligence &nbsp;·&nbsp; Sentiment · Topic Clustering · Reports &nbsp;·&nbsp; {'🌙 Dark' if DARK else '☀️ Light'} Mode</p>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <div class="hero-stat"><div class="hero-stat-label">Total</div><div class="hero-stat-val">{len(df)}</div></div>
      <div class="hero-stat"><div class="hero-stat-label">Themes</div><div class="hero-stat-val">{df['Theme'].nunique()}</div></div>
      <div class="hero-stat"><div class="hero-stat-label">Live</div><div class="hero-stat-val">{live_n+up_n}</div></div>
    </div>
  </div>
</div></div>
""", unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab_submit, tab_dash, tab_upload, tab_about = st.tabs([
        "✍️  Submit Comment", "📊  Dashboard", "📂  Bulk Upload", "ℹ️  About",
    ])

    # =========================================================================
    #  TAB 1 — SUBMIT
    # =========================================================================
    with tab_submit:
        st.markdown('<p class="section-label">✍️ Share Your View on City Policies</p>',
                    unsafe_allow_html=True)
        st.markdown(f"""
<div class="submit-wrap">
  <h3>💬 What do you think about local government policies?</h3>
  <p class="submit-desc">Write your comment below. CitizenLens will instantly analyze sentiment,
  subjectivity, and policy topic — then add it to the live dashboard.</p>
</div>""", unsafe_allow_html=True)

        with st.form("comment_form", clear_on_submit=True):
            col_a, col_b = st.columns([3,1])
            with col_a:
                user_text = st.text_area("Your comment *",
                    placeholder='e.g. "The new cycle lanes have transformed my commute. More people are cycling and air quality has improved."',
                    height=130)
            with col_b:
                policy_hint = st.selectbox("Policy area (optional)",
                    ["Auto-detect 🤖"] + list(TOPIC_KEYWORDS.keys()) + ["General / Other"])
                name_in     = st.text_input("Your name (optional)", placeholder="Anonymous")
                location_in = st.text_input("Location (optional)", placeholder="e.g. District 4")

            if st.form_submit_button("🔍  Analyze & Submit", use_container_width=True):
                txt = user_text.strip()
                if len(txt) < 10:
                    st.error("⚠️  Please write at least 10 characters.")
                else:
                    nlp = run_nlp(txt)
                    if "Auto-detect" not in policy_hint:
                        nlp["Theme"] = policy_hint; nlp["confidence"] = 99
                    st.session_state.submitted_comments.insert(0, {
                        "Comment":txt,"Theme":nlp["Theme"],"Sentiment":nlp["Sentiment"],
                        "Polarity":nlp["Polarity"],"Subjectivity":nlp["Subjectivity"],
                        "Confidence %":nlp["confidence"],
                        "Source":f"Live — {name_in.strip() or 'Anonymous'}",
                        "Date":datetime.date.today().strftime("%Y-%m-%d"),
                        "Submitted At":datetime.datetime.now().strftime("%H:%M:%S"),
                    })
                    emoji = "✅" if nlp["Sentiment"]=="Positive" else ("❌" if nlp["Sentiment"]=="Negative" else "➖")
                    st.success(f"{emoji} **{nlp['Sentiment']}** · Polarity `{nlp['Polarity']:+.4f}` · "
                               f"Subjectivity `{nlp['Subjectivity']:.4f}` · Theme **{nlp['Theme']}** · "
                               f"Confidence `{nlp['confidence']}%`")
                    st.rerun()

        if st.session_state.submitted_comments:
            st.markdown('<p class="section-label">📬 Recent Submissions</p>', unsafe_allow_html=True)
            for entry in st.session_state.submitted_comments[:5]:
                tag = "tag-pos" if entry["Sentiment"]=="Positive" else ("tag-neg" if entry["Sentiment"]=="Negative" else "tag-neu")
                st.markdown(f"""
<div class="latest-card">
  <span class="latest-meta">{entry.get('Source','—')} · {entry['Theme']} · {entry.get('Submitted At','—')}</span>
  <span class="{tag}">{entry['Sentiment']}</span><span class="tag-new">NEW</span>
  <p class="latest-quote">"{entry['Comment']}"</p>
  <div class="conf-bar-wrap" style="margin-top:8px;">
    <div class="conf-bar-fill" style="width:{entry.get('Confidence %',50)}%;"></div>
  </div>
  <span class="latest-meta">Polarity {entry['Polarity']:+.4f} · Subjectivity {entry['Subjectivity']:.4f} · Confidence {entry.get('Confidence %','?')}%</span>
</div>""", unsafe_allow_html=True)
        else:
            st.info("💡  No live submissions yet — be the first to submit above!")

    # =========================================================================
    #  TAB 2 — DASHBOARD
    # =========================================================================
    with tab_dash:
        st.markdown('<p class="section-label">📊 Overview Metrics</p>', unsafe_allow_html=True)
        k1,k2,k3,k4,k5,k6 = st.columns(6)
        k1.metric("💬 Total", total)
        k2.metric("✅ Positive", pos_count, delta=f"{round(pos_count/total*100) if total else 0}%")
        k3.metric("➖ Neutral", neu_count, delta=f"{round(neu_count/total*100) if total else 0}%", delta_color="off")
        k4.metric("❌ Negative", neg_count, delta=f"{round(neg_count/total*100) if total else 0}%", delta_color="inverse")
        k5.metric("📈 Avg Polarity", f"{avg_pol:+.3f}")
        k6.metric("🔬 Avg Subjectivity", f"{avg_subj:.3f}")

        if total == 0:
            st.warning("⚠️  No comments match your current filters.")
            return

        st.markdown('<p class="section-label">📈 Sentiment & Theme Analysis</p>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="cl-card"><h4>🎭 Sentiment Distribution</h4>', unsafe_allow_html=True)
            _show(chart_sentiment(filtered, C)); st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="cl-card"><h4>🗂️ Comments by Policy Theme</h4>', unsafe_allow_html=True)
            _show(chart_themes(filtered, C)); st.markdown('</div>', unsafe_allow_html=True)

        cc, cd = st.columns(2)
        with cc:
            st.markdown('<div class="cl-card"><h4>📉 Polarity Distribution</h4>', unsafe_allow_html=True)
            _show(chart_polarity(filtered, C)); st.markdown('</div>', unsafe_allow_html=True)
        with cd:
            st.markdown('<div class="cl-card"><h4>🧩 Sentiment by Theme (Stacked)</h4>', unsafe_allow_html=True)
            _show(chart_stacked(filtered, C)); st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="cl-card"><h4>🔬 Subjectivity vs Polarity Scatter</h4>', unsafe_allow_html=True)
        _show(chart_scatter(filtered, C))
        st.caption("Each dot = one comment. Horizontal = sentiment. Vertical = opinion vs fact.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="cl-card"><h4>📅 Sentiment Trend Over Time</h4>', unsafe_allow_html=True)
        _show(chart_timeline(filtered, C))
        st.caption("Weekly aggregated sentiment by submission date.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Word clouds
        st.markdown('<p class="section-label">☁️ Word Clouds by Policy Theme</p>', unsafe_allow_html=True)
        themes_present = sorted(filtered["Theme"].unique().tolist())
        if themes_present:
            for i in range(0, len(themes_present), 2):
                wc1, wc2 = st.columns(2)
                for j, col in enumerate([wc1, wc2]):
                    idx = i+j
                    if idx < len(themes_present):
                        tn = themes_present[idx]
                        tc = filtered[filtered["Theme"]==tn]["Comment"]
                        tp = (filtered[filtered["Theme"]==tn]["Sentiment"]=="Positive").sum()
                        tn2= (filtered[filtered["Theme"]==tn]["Sentiment"]=="Neutral").sum()
                        tng= (filtered[filtered["Theme"]==tn]["Sentiment"]=="Negative").sum()
                        ta = filtered[filtered["Theme"]==tn]["Polarity"].mean()
                        with col:
                            st.markdown(f'<div class="cl-card"><h4>☁️ {tn}</h4>', unsafe_allow_html=True)
                            st.caption(f"{len(tc)} comments · ✅{tp} ➖{tn2} ❌{tng} · avg {ta:+.3f}")
                            _show(make_wordcloud(tc, THEME_CMAPS.get(tn,"viridis"), C))
                            st.markdown('</div>', unsafe_allow_html=True)

        # Deep dive
        st.markdown('<p class="section-label">🔬 Theme Deep Dive</p>', unsafe_allow_html=True)
        with st.expander("Expand — read every comment by theme", expanded=False):
            if themes_present:
                for ttab, tname in zip(st.tabs(themes_present), themes_present):
                    with ttab:
                        tdf = filtered[filtered["Theme"]==tname].copy()
                        tavg = tdf["Polarity"].mean()
                        mood = "🟢 Mostly Positive" if tavg>0.06 else ("🔴 Mostly Negative" if tavg<-0.06 else "🟡 Mixed")
                        st.markdown(f"**{len(tdf)} comments** · {mood} · Avg polarity: **{tavg:+.4f}**")
                        st.dataframe(tdf[["Comment","Sentiment","Polarity","Subjectivity","Confidence %","Source","Date"]].reset_index(drop=True), use_container_width=True)

        # Data table
        st.markdown('<p class="section-label">📋 All Comments</p>', unsafe_allow_html=True)
        st.caption(f"Showing **{total}** of **{len(df)}** comments")

        def colour_row(val):
            return {
                "Positive": f"background-color:{C['pos_bg']};color:{C['pos_fg']};font-weight:700;",
                "Negative": f"background-color:{C['neg_bg']};color:{C['neg_fg']};font-weight:700;",
                "Neutral":  f"background-color:{C['neu_bg']};color:{C['neu_fg']};font-weight:700;",
            }.get(val, "")

        st.dataframe(
            filtered.reset_index(drop=True).style.map(colour_row, subset=["Sentiment"]),
            use_container_width=True, height=380,
        )

        # Export
        st.markdown('<p class="section-label">💾 Export</p>', unsafe_allow_html=True)
        ex1, ex2 = st.columns(2)
        with ex1:
            st.markdown('<div class="cl-card"><h4>📊 Enriched Dataset — CSV</h4>', unsafe_allow_html=True)
            buf = io.StringIO(); filtered.to_csv(buf, index=False)
            st.download_button("⬇️  Download CSV", buf.getvalue().encode(),
                               f"citizenlens_{datetime.date.today()}.csv", "text/csv")
            st.markdown('</div>', unsafe_allow_html=True)
        with ex2:
            st.markdown('<div class="cl-card"><h4>📄 Policy Insight Report — TXT</h4>', unsafe_allow_html=True)
            st.download_button("📄  Download Policy Report", generate_report(filtered).encode(),
                               f"citizenlens_report_{datetime.date.today()}.txt", "text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("👀 Preview Policy Report", expanded=False):
            st.markdown(f'<div class="report-box">{generate_report(filtered)}</div>', unsafe_allow_html=True)

    # =========================================================================
    #  TAB 3 — BULK UPLOAD
    # =========================================================================
    with tab_upload:
        st.markdown('<p class="section-label">📂 Bulk Upload Existing Feedback</p>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="cl-card">
  <h4>📤 Upload a CSV of citizen comments</h4>
  <p>Must contain a <code>comment</code> column. Optional: <code>source</code>, <code>date</code>.</p>
</div>""", unsafe_allow_html=True)

        uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
        if uploaded:
            try:
                raw = pd.read_csv(uploaded)
                col_map = {c.lower(): c for c in raw.columns}
                if "comment" not in col_map:
                    st.error("❌  CSV must have a 'comment' column.")
                else:
                    cc = col_map["comment"]
                    with st.spinner(f"Analyzing {len(raw)} comments…"):
                        new_rows = []
                        for _, row in raw.iterrows():
                            txt = str(row[cc]).strip()
                            if len(txt) < 3: continue
                            nlp = run_nlp(txt)
                            new_rows.append({
                                "Comment":txt,"Theme":nlp["Theme"],"Sentiment":nlp["Sentiment"],
                                "Polarity":nlp["Polarity"],"Subjectivity":nlp["Subjectivity"],
                                "Confidence %":nlp["confidence"],
                                "Source":str(row.get("source", row.get("Source","CSV Upload"))),
                                "Date":str(row.get("date", row.get("Date", datetime.date.today()))),
                                "Submitted At":datetime.datetime.now().strftime("%H:%M:%S"),
                            })
                        st.session_state.uploaded_rows += new_rows
                    st.success(f"✅  **{len(new_rows)} comments imported!** Switch to Dashboard.")
                    st.dataframe(pd.DataFrame(new_rows)[["Comment","Sentiment","Polarity","Theme"]].head(10), use_container_width=True)
            except Exception as e:
                st.error(f"❌  Could not process file: {e}")

        st.markdown(f'<div class="cl-card" style="margin-top:20px;"><h4>📋 CSV Format Example</h4></div>', unsafe_allow_html=True)
        ex = pd.DataFrame({
            "comment":["The new park renovation transformed our neighbourhood.",
                        "Bus routes to rural areas are still inadequate.",
                        "Affordable housing targets are not being met."],
            "source":["Resident Survey","Public Forum","Email"],
            "date":["2025-03-01","2025-03-15","2025-04-01"],
        })
        st.dataframe(ex, use_container_width=True)
        buf2 = io.StringIO(); ex.to_csv(buf2, index=False)
        st.download_button("⬇️  Download Template CSV", buf2.getvalue().encode(), "citizenlens_template.csv", "text/csv")

    # =========================================================================
    #  TAB 4 — ABOUT
    # =========================================================================
    with tab_about:
        st.markdown('<p class="section-label">ℹ️ About CitizenLens</p>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="cl-card"><h4>🏛️ What is CitizenLens?</h4>
<p>CitizenLens is an open-source AI platform that makes citizen feedback useful for policymakers at scale.
Every comment is run through an NLP pipeline — scoring sentiment, measuring subjectivity,
and clustering by policy topic — then visualised in a real-time dashboard.</p></div>

<div class="cl-card"><h4>🧠 NLP Pipeline</h4>
<p><strong>Step 1 — Sentiment:</strong> TextBlob polarity (−1.0 to +1.0) and subjectivity (0 to 1.0).
Above +0.08 = Positive, below −0.08 = Negative, otherwise Neutral.<br><br>
<strong>Step 2 — Topic Clustering:</strong> Keyword-frequency dictionary across 6 policy domains
produces a Confidence % score.<br><br>
<strong>Step 3 — Visualisation:</strong> 6 chart types + per-theme word clouds update live with filters.</p></div>

<div class="cl-card"><h4>🛠️ Tech Stack</h4>
<div class="stat-strip">
  <div class="stat-pill">🔴 Streamlit</div><div class="stat-pill">🧠 TextBlob</div>
  <div class="stat-pill">🐼 Pandas</div><div class="stat-pill">☁️ WordCloud</div>
  <div class="stat-pill">📈 Matplotlib</div><div class="stat-pill">🚀 Streamlit Cloud</div>
</div></div>

<div class="cl-card"><h4>⚖️ License & Ethics</h4>
<p>MIT licensed. No personal data stored beyond the session. Comments exist in browser
session state only — never written to disk or sent to external servers.
All NLP outputs are advisory only — human review always required.</p></div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{C['muted']};font-size:11px;'>"
        "CitizenLens v2.2 &nbsp;·&nbsp; Streamlit · TextBlob · WordCloud · Matplotlib &nbsp;·&nbsp; "
        f"Open Government Hackathon 2025 &nbsp;·&nbsp; {'🌙 Dark' if DARK else '☀️ Light'} Mode</p>",
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
