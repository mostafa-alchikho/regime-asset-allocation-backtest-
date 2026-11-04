import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import statsmodels.api as sm

st.set_page_config(
    page_title="Regime-basierte Asset Allocation",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
# FARBEN
# =============================================================
CYAN, AMBER, ROSE, GREEN, VIOLET = "#38BDF8", "#F59E0B", "#FB7185", "#34D399", "#A78BFA"
TEXT, MUTED = "#E6EDF7", "#8FA0B8"

# =============================================================
# STYLE: DUNKLES GLAS
# =============================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
  --text:#E6EDF7; --muted:#8FA0B8; --border:rgba(255,255,255,.10);
  --cyan:#38BDF8; --amber:#F59E0B; --rose:#FB7185; --green:#34D399; --violet:#A78BFA;
}
html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]):not([class*="material"]){
  font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
[data-testid="stIconMaterial"], [class*="material-symbols"]{ font-family:'Material Symbols Rounded','Material Icons' !important; }

/* Hintergrund mit weichen Farbflaechen, damit das Glas etwas zum Verwischen hat */
.stApp{
  background:
    radial-gradient(900px 600px at 10% -8%,  rgba(56,189,248,.18), transparent 60%),
    radial-gradient(800px 600px at 98% 2%,   rgba(167,139,250,.16), transparent 60%),
    radial-gradient(1000px 700px at 55% 112%, rgba(52,211,153,.09), transparent 60%),
    #070B14;
  background-attachment: fixed;
  color: var(--text);
}
header[data-testid="stHeader"]{ background:transparent; }
footer{ visibility:hidden; }
.block-container{ padding-top:2.4rem; max-width:1300px; }
::selection{ background:rgba(56,189,248,.35); }
::-webkit-scrollbar{ width:10px; height:10px; }
::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.14); border-radius:10px; }
::-webkit-scrollbar-thumb:hover{ background:rgba(56,189,248,.45); }

/* Sidebar als Glas */
section[data-testid="stSidebar"]{
  background:rgba(9,14,26,.70);
  backdrop-filter:blur(22px) saturate(140%); -webkit-backdrop-filter:blur(22px) saturate(140%);
  border-right:1px solid var(--border);
}
section[data-testid="stSidebar"] > div{ background:transparent; }
.side-title{ font-size:15px; font-weight:700; letter-spacing:-.2px; color:#fff; margin:2px 0 2px; }
.side-sub{ font-size:12px; color:var(--muted); margin-bottom:10px; }
.side-h{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.9px; color:var(--cyan); margin:14px 0 2px; }
div[data-testid="stSlider"] [role="slider"]{ background:#38BDF8 !important; box-shadow:0 0 0 4px rgba(56,189,248,.22); }
div[data-testid="stSlider"] [role="slider"]:hover{ box-shadow:0 0 0 7px rgba(56,189,248,.28); }

/* Glas-Karten */
.glass{
  position:relative; overflow:hidden;
  background:linear-gradient(145deg, rgba(255,255,255,.075), rgba(255,255,255,.025));
  backdrop-filter:blur(18px) saturate(150%); -webkit-backdrop-filter:blur(18px) saturate(150%);
  border:1px solid var(--border); border-radius:16px; padding:18px 20px;
  box-shadow:0 10px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.09);
  transition:transform .25s cubic-bezier(.2,.8,.2,1), border-color .25s, box-shadow .25s;
}
.glass::before{            /* Lichtfleck, der der Maus folgt */
  content:""; position:absolute; inset:0; pointer-events:none; opacity:0; transition:opacity .25s;
  background:radial-gradient(280px circle at var(--mx,50%) var(--my,0%), rgba(56,189,248,.17), transparent 62%);
}
.glass:hover{
  transform:translateY(-3px); border-color:rgba(56,189,248,.42);
  box-shadow:0 18px 50px rgba(0,0,0,.45), 0 0 42px -10px rgba(56,189,248,.40), inset 0 1px 0 rgba(255,255,255,.12);
}
.glass:hover::before{ opacity:1; }

/* Plotly-Diagramme als Glasflaechen */
div[data-testid="stPlotlyChart"]{
  background:linear-gradient(145deg, rgba(255,255,255,.065), rgba(255,255,255,.02));
  backdrop-filter:blur(18px) saturate(150%); -webkit-backdrop-filter:blur(18px) saturate(150%);
  border:1px solid var(--border); border-radius:16px; padding:10px 8px 2px;
  box-shadow:0 10px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.09);
  transition:border-color .25s, box-shadow .25s;
}
div[data-testid="stPlotlyChart"]:hover{
  border-color:rgba(56,189,248,.34);
  box-shadow:0 14px 46px rgba(0,0,0,.42), 0 0 36px -12px rgba(56,189,248,.35), inset 0 1px 0 rgba(255,255,255,.10);
}
.modebar{ background:transparent !important; }
.modebar-btn path{ fill:#8FA0B8 !important; }
.modebar-btn:hover path{ fill:#38BDF8 !important; }

/* Kopfbereich */
.kicker{ font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--cyan); margin-bottom:8px; }
.hero-title{
  font-size:2.35rem; line-height:1.12; font-weight:800; letter-spacing:-.035em; margin:0 0 8px;
  background:linear-gradient(90deg,#fff 0%, #A5DBF8 55%, #B9A6FF 100%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:transparent;
}
.hero-sub{ font-size:14px; color:#A9B7CC; margin-bottom:14px; }
.chip{
  display:inline-flex; align-items:center; gap:6px; margin:0 6px 8px 0; padding:5px 12px; border-radius:999px;
  background:rgba(255,255,255,.055); border:1px solid var(--border); color:#B9C6DA; font-size:12px; font-weight:500;
  backdrop-filter:blur(10px); transition:all .2s;
}
.chip:hover{ background:rgba(56,189,248,.12); border-color:rgba(56,189,248,.40); color:#fff; transform:translateY(-1px); }
.chip.ok{ border-color:rgba(52,211,153,.40); color:#7CE9BF; }
.chip.warn{ border-color:rgba(245,158,11,.45); color:#FBC25E; }

/* Kennzahlen */
.kpi-l{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.8px; color:var(--muted); margin-bottom:6px; }
.kpi-v{ font-size:28px; font-weight:700; letter-spacing:-.03em; color:#fff; font-variant-numeric:tabular-nums; margin-bottom:8px; }
.badge{ display:inline-block; font-size:11px; font-weight:600; padding:3px 9px; border-radius:999px; font-variant-numeric:tabular-nums; }
.badge.pos{ background:rgba(52,211,153,.14); color:#5EEAB0; border:1px solid rgba(52,211,153,.30); }
.badge.neg{ background:rgba(251,113,133,.14); color:#FDA4B1; border:1px solid rgba(251,113,133,.32); }
.badge.neu{ background:rgba(56,189,248,.12); color:#7DD3FC; border:1px solid rgba(56,189,248,.28); }

.sec{ font-size:15px; font-weight:700; letter-spacing:-.2px; color:#fff; margin:18px 0 8px; }
.sec span{ font-size:12px; font-weight:500; color:var(--muted); margin-left:8px; }

/* Tabelle */
table.gt{ width:100%; border-collapse:separate; border-spacing:0; font-size:13px; font-variant-numeric:tabular-nums; }
table.gt th{ text-align:right; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.7px; color:var(--muted); padding:0 8px 10px; }
table.gt th:first-child, table.gt td:first-child{ text-align:left; }
table.gt td{ text-align:right; padding:11px 8px; border-top:1px solid rgba(255,255,255,.07); color:#D5DEEC; transition:background .15s; }
table.gt td.hi{ color:#fff; font-weight:600; }
table.gt td.pos{ color:#5EEAB0; font-weight:600; }
table.gt td.neg{ color:#FDA4B1; font-weight:600; }
table.gt, table.gt th, table.gt td{ border:0 !important; white-space:nowrap; }
table.gt td{ border-top:1px solid rgba(255,255,255,.07) !important; }
table.gt tr:first-child td{ border-top:0 !important; }
table.gt th{ background:transparent !important; }
table.gt tr:hover td{ background:rgba(56,189,248,.07) !important; }

.mini-row{ display:flex; align-items:baseline; gap:10px; margin-bottom:8px; font-variant-numeric:tabular-nums; }
.mini-row .s{ font-size:22px; font-weight:700; color:var(--cyan); }
.mini-row .b{ font-size:16px; font-weight:600; color:var(--amber); }
.mini-row .vs{ font-size:12px; color:var(--muted); }
.note{ font-size:12.5px; line-height:1.6; color:#9FB0C7; margin-top:12px; }
.note b{ color:#D5DEEC; }
.glass h4{ margin:0 0 10px; font-size:14px; font-weight:700; color:var(--cyan); }
ul.clean{ margin:0; padding-left:18px; color:#C3CFE2; font-size:13.5px; line-height:1.75; }
ul.clean b{ color:#fff; }

/* Tabs (neue role-basierte und aeltere baseweb-Struktur) */
.stTabs [role="tablist"], .stTabs [data-baseweb="tab-list"]{
  gap:6px; padding:5px; width:fit-content; max-width:100%; background:rgba(255,255,255,.045);
  border:1px solid var(--border) !important; border-radius:14px; backdrop-filter:blur(14px);
}
.stTabs [role="tab"], .stTabs [data-baseweb="tab"]{
  height:38px; padding:0 16px; border-radius:10px; background:transparent; color:#9AA9C0; border:0;
  display:flex; align-items:center; cursor:pointer; transition:all .2s;
}
.stTabs [role="tab"] p, .stTabs [data-baseweb="tab"] p{ margin:0; font-size:13px; font-weight:600; color:inherit; }
.stTabs [role="tab"]:hover, .stTabs [data-baseweb="tab"]:hover{ color:#fff; background:rgba(255,255,255,.07); }
.stTabs [role="tab"][aria-selected="true"], .stTabs [data-baseweb="tab"][aria-selected="true"]{
  color:#fff !important;
  background:linear-gradient(135deg, rgba(56,189,248,.30), rgba(167,139,250,.24));
  box-shadow:inset 0 0 0 1px rgba(56,189,248,.38);
}
.stTabs [role="tab"] > div[data-rac], .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none !important; }
.stTabs [role="tablist"] + div, .stTabs [data-baseweb="tab-border"]{ border:0 !important; }

@media (prefers-reduced-motion: reduce){ .glass, .chip{ transition:none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================
# HILFSFUNKTIONEN (Formatierung deutsch: Dezimalkomma)
# =============================================================
def fnum(x, d=2, sign=False):
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace(".", ",")


def pc(x, d=2, sign=False):
    return fnum(x * 100, d, sign) + " %"


def tone(x, good_if_positive=True, eps=1e-12):
    if abs(x) < eps:
        return "neu"
    return "pos" if (x > 0) == good_if_positive else "neg"


def show(fig):
    cfg = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg)
    except TypeError:                      # aeltere Streamlit-Versionen
        st.plotly_chart(fig, use_container_width=True, config=cfg)


def style(fig, h=380, hover="x unified"):
    fig.update_layout(
        height=h, separators=",.",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        margin=dict(l=52, r=22, t=46, b=44), hovermode=hover,
        hoverlabel=dict(bgcolor="rgba(10,16,30,.94)", bordercolor=CYAN,
                        font=dict(family="Inter, sans-serif", size=12, color="#FFFFFF")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#B9C6DA")),
        xaxis=dict(gridcolor="rgba(255,255,255,.05)", zeroline=False, linecolor="rgba(255,255,255,.12)",
                   tickfont=dict(color=MUTED), showspikes=True, spikemode="across", spikesnap="cursor",
                   spikecolor="rgba(56,189,248,.55)", spikethickness=1, spikedash="dot"),
        yaxis=dict(gridcolor="rgba(255,255,255,.05)", zeroline=True, zerolinecolor="rgba(255,255,255,.18)",
                   linecolor="rgba(0,0,0,0)", tickfont=dict(color=MUTED)),
    )
    return fig


# =============================================================
# DATEN
# =============================================================
@st.cache_data(ttl=3600 * 24, show_spinner="Marktdaten werden geladen ...")
def load_market_data():
    tickers = {"SPY": "Aktien", "IEF": "Staatsanleihen", "GLD": "Gold", "SHV": "Cash"}
    px = yf.download(list(tickers.keys()), start="2007-01-01", end="2026-11-01",
                     auto_adjust=True, progress=False)["Close"]
    px = px[list(tickers.keys())]
    px = px.groupby(px.index.to_period("M")).last()
    px.index = px.index.to_timestamp(how="end").normalize()
    rets = px.pct_change().dropna()
    rets.columns = [tickers[c] for c in rets.columns]

    fx_raw = yf.download("EURUSD=X", start="2007-01-01", end="2026-11-01",
                         auto_adjust=True, progress=False)["Close"].squeeze()
    fx = fx_raw.groupby(fx_raw.index.to_period("M")).last()
    fx.index = fx.index.to_timestamp(how="end").normalize()
    fx_ret = fx.pct_change().dropna()

    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDPRO"
    ind = pd.read_csv(url, index_col=0, parse_dates=True).iloc[:, 0]
    ind = pd.to_numeric(ind, errors="coerce").dropna()
    ind = ind[ind.index >= "2005-01-01"]
    ind.index = ind.index.to_period("M").to_timestamp(how="end").normalize()
    return rets, fx_ret, ind


try:
    rets, fx_ret, ind = load_market_data()
except Exception as e:
    st.error("Die Marktdaten (Yahoo Finance / FRED) konnten gerade nicht geladen werden. "
             "Bitte die Seite in einer Minute neu laden. Technische Meldung: " + str(e))
    st.stop()

# =============================================================
# SIDEBAR
# =============================================================
DEFAULTS = dict(window=12, lag=2, cost=0.10, up=(70, 20, 10), dn=(30, 40, 15))

with st.sidebar:
    st.markdown('<div class="side-title">Parameter</div>'
                '<div class="side-sub">Annahmen live verändern und Auswirkungen sehen</div>',
                unsafe_allow_html=True)
    currency = st.radio("Währungsperspektive", ["USD (Basis)", "EUR (ungehedgt)"], index=0)

    st.markdown('<div class="side-h">1 · Signal & Kosten</div>', unsafe_allow_html=True)
    window = st.slider("Trendfenster Ø (Monate)", 3, 24, DEFAULTS["window"], 1)
    lag = st.slider("Publikationsverzögerung (Monate)", 0, 4, DEFAULTS["lag"],
                    help="Lag 0 erzeugt Look-ahead-Bias. Lag 2 entspricht der realen Verzögerung der Daten.")
    cost_pct = st.slider("Transaktionskosten (%)", 0.0, 0.5, DEFAULTS["cost"], 0.05)
    cost = cost_pct / 100.0

    st.markdown('<div class="side-h">2 · Gewichte bei steigendem Wachstum</div>', unsafe_allow_html=True)
    w_up_a = st.slider("Aktien (%)", 0, 100, DEFAULTS["up"][0], 5, key="up_a")
    w_up_b = st.slider("Staatsanleihen (%)", 0, 100, DEFAULTS["up"][1], 5, key="up_b")
    w_up_g = st.slider("Gold (%)", 0, 100, DEFAULTS["up"][2], 5, key="up_g")
    w_up_c = max(0, 100 - (w_up_a + w_up_b + w_up_g))
    st.caption(f"Cash (automatisch): {w_up_c} %")

    st.markdown('<div class="side-h">3 · Gewichte bei fallendem Wachstum</div>', unsafe_allow_html=True)
    w_dn_a = st.slider("Aktien (%)", 0, 100, DEFAULTS["dn"][0], 5, key="dn_a")
    w_dn_b = st.slider("Staatsanleihen (%)", 0, 100, DEFAULTS["dn"][1], 5, key="dn_b")
    w_dn_g = st.slider("Gold (%)", 0, 100, DEFAULTS["dn"][2], 5, key="dn_g")
    w_dn_c = max(0, 100 - (w_dn_a + w_dn_b + w_dn_g))
    st.caption(f"Cash (automatisch): {w_dn_c} %")

    if (w_up_a + w_up_b + w_up_g) > 100 or (w_dn_a + w_dn_b + w_dn_g) > 100:
        st.warning("Gewichte über 100 % werden automatisch auf 100 % skaliert.")

is_default = (window == DEFAULTS["window"] and lag == DEFAULTS["lag"]
              and abs(cost_pct - DEFAULTS["cost"]) < 1e-9
              and (w_up_a, w_up_b, w_up_g) == DEFAULTS["up"] and (w_dn_a, w_dn_b, w_dn_g) == DEFAULTS["dn"])


# =============================================================
# BACKTEST-ENGINE (identisch zur Logik im Colab-Notebook)
# =============================================================
def build_regime(ind, window, lag):
    ma = ind.rolling(window).mean()
    up = (ind > ma).astype(float).where(ma.notna())
    if lag > 0:
        up.index = up.index + pd.offsets.MonthEnd(lag)
    return up


def backtest(target, r, cost):
    net, turn = [], []
    prev_w = target.iloc[0]
    for t in r.index:
        w = target.loc[t]
        tn = (w - prev_w).abs().sum()
        gross = (w * r.loc[t]).sum()
        net.append(gross - tn * cost)
        turn.append(tn)
        prev_w = w * (1 + r.loc[t]) / (1 + gross)
    return pd.Series(net, index=r.index), pd.Series(turn, index=r.index)


def calc_metrics(x, rf):
    n = len(x)
    cagr = (1 + x).prod() ** (12 / n) - 1
    vol = x.std() * np.sqrt(12)
    ex = x - rf
    sharpe = ex.mean() * 12 / (ex.std() * np.sqrt(12)) if ex.std() > 0 else 0.0
    cum = (1 + x).cumprod()
    mdd = (cum / np.maximum(cum.cummax(), 1.0) - 1).min()
    return {"CAGR": cagr, "Vola": vol, "Sharpe": sharpe, "MaxDD": mdd}


def norm_weights(a, b, g, c):
    tot = a + b + g + c
    return {"Aktien": a / tot, "Staatsanleihen": b / tot, "Gold": g / tot, "Cash": c / tot}


W_UP = norm_weights(w_up_a, w_up_b, w_up_g, w_up_c)
W_DOWN = norm_weights(w_dn_a, w_dn_b, w_dn_g, w_dn_c)
W_BENCH = {"Aktien": 0.60, "Staatsanleihen": 0.40, "Gold": 0.0, "Cash": 0.0}

BT_START = "2008-01-31"
reg = build_regime(ind, window, lag).reindex(rets.index).loc[BT_START:].dropna()
common_idx = reg.index.intersection(rets.index)
r_curr = rets.loc[common_idx].copy()
reg = reg.loc[common_idx]

is_eur = currency.startswith("EUR")
if is_eur:
    fx_common = fx_ret.reindex(common_idx).fillna(0)
    for col in r_curr.columns:
        r_curr[col] = (1 + r_curr[col]) / (1 + fx_common) - 1

tgt = pd.DataFrame([W_UP if g == 1 else W_DOWN for g in reg], index=r_curr.index)[r_curr.columns]
ben = pd.DataFrame([W_BENCH] * len(r_curr), index=r_curr.index)[r_curr.columns]
strat_rets, turnover = backtest(tgt, r_curr, cost)
bench_rets, _ = backtest(ben, r_curr, cost)
cash_curr = r_curr["Cash"]

# In der EUR-Ansicht traegt "Cash" (SHV) selbst Waehrungsrisiko -> Sharpe dann ohne Zinsabzug
rf = pd.Series(0.0, index=cash_curr.index) if is_eur else cash_curr
sharpe_lbl = "Sharpe (ohne Zins)" if is_eur else "Sharpe-Ratio"
m_s = calc_metrics(strat_rets, rf)
m_b = calc_metrics(bench_rets, rf)
n_switch = int((reg.diff().abs() == 1).sum())
y0, y1 = r_curr.index.min().year, r_curr.index.max().year

# =============================================================
# KOPFBEREICH
# =============================================================
chip_state = ('<span class="chip ok">● Vorab festgelegte Parameter</span>' if is_default
              else '<span class="chip warn">● Explorativ: Parameter verändert</span>')
st.markdown(
    '<div class="kicker">Quantitative Asset Allocation</div>'
    '<div class="hero-title">Regime-basierte Asset Allocation</div>'
    '<div class="hero-sub">Interaktiver Backtest: Wachstumssignal gegen ein statisches 60/40-Portfolio</div>'
    f'<span class="chip">Signal: US-Industrieproduktion vs. {window}-Monats-Ø</span>'
    f'<span class="chip">Verzögerung: {lag} Monate</span>'
    f'<span class="chip">Kosten: {fnum(cost_pct)} %</span>'
    f'<span class="chip">Basis: {currency}</span>'
    f'<span class="chip">Zeitraum: {y0}–{y1}</span>' + chip_state,
    unsafe_allow_html=True)
st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)


def kpi(label, value, badge, tn):
    return (f'<div class="glass"><div class="kpi-l">{label}</div><div class="kpi-v">{value}</div>'
            f'<span class="badge {tn}">{badge}</span></div>')


k = st.columns(5, gap="medium")
d_cagr, d_sh, d_dd = m_s["CAGR"] - m_b["CAGR"], m_s["Sharpe"] - m_b["Sharpe"], m_s["MaxDD"] - m_b["MaxDD"]
k[0].markdown(kpi("Rendite p.a. (netto)", pc(m_s["CAGR"]), pc(d_cagr, 2, True).replace(" %", " %p") + " vs. 60/40",
                  tone(d_cagr)), unsafe_allow_html=True)
k[1].markdown(kpi(sharpe_lbl, fnum(m_s["Sharpe"]), fnum(d_sh, 2, True) + " vs. 60/40", tone(d_sh)),
              unsafe_allow_html=True)
k[2].markdown(kpi("Max. Drawdown", pc(m_s["MaxDD"]), pc(d_dd, 2, True).replace(" %", " %p") + " Puffer",
                  tone(d_dd)), unsafe_allow_html=True)
k[3].markdown(kpi("Turnover p.a.", pc(turnover.mean() * 12, 0), f"{n_switch} Regimewechsel", "neu"),
              unsafe_allow_html=True)
k[4].markdown(kpi("Look-ahead-Schutz", f"{lag} Monate",
                  "Achtung: Look-ahead-Bias" if lag == 0 else "Ex ante verzögert",
                  "neg" if lag == 0 else "pos"), unsafe_allow_html=True)
st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Performance & Risiko", "CAPM & Alpha", "Bootstrap-Test", "Methodik & Grenzen"])

# =============================================================
# TAB 1: PERFORMANCE
# =============================================================
with tab1:
    cum_s = (1 + strat_rets).cumprod() * 100
    cum_b = (1 + bench_rets).cumprod() * 100
    st.markdown('<div class="sec">Vermögensentwicklung<span>Start = 100, nach Kosten</span></div>',
                unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cum_s.index, y=cum_s.values, mode="lines", name="Regime-Strategie",
                             line=dict(color=CYAN, width=2.8), hovertemplate="%{y:.1f}<extra>Strategie</extra>"))
    fig.add_trace(go.Scatter(x=cum_b.index, y=cum_b.values, mode="lines", name="60/40-Benchmark",
                             line=dict(color=AMBER, width=2, dash="dash"), hovertemplate="%{y:.1f}<extra>60/40</extra>"))
    for a, b, lab in [("2008-01-31", "2009-03-31", "Finanzkrise"), ("2020-02-01", "2020-04-30", "Corona"),
                      ("2022-01-01", "2022-12-31", "Zinsschock")]:
        if pd.Timestamp(a) >= cum_s.index.min():
            fig.add_vrect(x0=a, x1=b, fillcolor="rgba(251,113,133,.09)", line_width=0, layer="below",
                          annotation_text=lab, annotation_position="top left",
                          annotation_font=dict(size=10, color=MUTED))
    style(fig, 400)
    fig.update_xaxes(rangeselector=dict(
        buttons=[dict(count=5, label="5J", step="year", stepmode="backward"),
                 dict(count=10, label="10J", step="year", stepmode="backward"),
                 dict(step="all", label="Alles")],
        bgcolor="rgba(255,255,255,.06)", activecolor="rgba(56,189,248,.35)", bordercolor="rgba(255,255,255,.10)",
        borderwidth=1, font=dict(color=TEXT, size=11), x=0, y=1.02, yanchor="bottom"))
    show(fig)

    col_a, col_b = st.columns([11, 9], gap="medium")
    with col_a:
        st.markdown('<div class="sec">Verlustphasen<span>Abstand zum bisherigen Höchststand</span></div>',
                    unsafe_allow_html=True)

        def underwater(x):
            c = (1 + x).cumprod()
            return (c / np.maximum(c.cummax(), 1.0) - 1) * 100

        fd = go.Figure()
        fd.add_trace(go.Scatter(x=strat_rets.index, y=underwater(strat_rets), name="Regime-Strategie",
                                mode="lines", line=dict(color=CYAN, width=2), fill="tozeroy",
                                fillcolor="rgba(56,189,248,.16)", hovertemplate="%{y:.1f} %<extra>Strategie</extra>"))
        fd.add_trace(go.Scatter(x=bench_rets.index, y=underwater(bench_rets), name="60/40-Benchmark",
                                mode="lines", line=dict(color=AMBER, width=1.6), fill="tozeroy",
                                fillcolor="rgba(245,158,11,.10)", hovertemplate="%{y:.1f} %<extra>60/40</extra>"))
        style(fd, 300)
        fd.update_yaxes(ticksuffix=" %")
        show(fd)
    with col_b:
        st.markdown('<div class="sec">Kennzahlen</div>', unsafe_allow_html=True)
        rows = [
            ("Rendite p.a.", pc(m_s["CAGR"]), pc(m_b["CAGR"]), pc(d_cagr, 2, True).replace(" %", " %p"), tone(d_cagr)),
            ("Volatilität p.a.", pc(m_s["Vola"]), pc(m_b["Vola"]),
             pc(m_s["Vola"] - m_b["Vola"], 2, True).replace(" %", " %p"), tone(m_s["Vola"] - m_b["Vola"], False)),
            (sharpe_lbl, fnum(m_s["Sharpe"]), fnum(m_b["Sharpe"]), fnum(d_sh, 2, True), tone(d_sh)),
            ("Max. Drawdown", pc(m_s["MaxDD"]), pc(m_b["MaxDD"]), pc(d_dd, 2, True).replace(" %", " %p"), tone(d_dd)),
        ]
        body = "".join(f'<tr><td>{a}</td><td class="hi">{b}</td><td>{c}</td><td class="{t}">{d}</td></tr>'
                       for a, b, c, d, t in rows)
        st.markdown('<div class="glass"><table class="gt"><tr><th>Kennzahl</th><th>Strategie</th><th>60/40</th>'
                    f'<th>Δ</th></tr>{body}</table></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec">Krisenphasen im Detail<span>Gesamtrendite im Zeitraum</span></div>',
                unsafe_allow_html=True)

    def per(x, a, b):
        sl = x.loc[a:b]
        return (1 + sl).prod() - 1 if len(sl) else np.nan

    cr = st.columns(3, gap="medium")
    for col, (lab, a, b) in zip(cr, [("Finanzkrise 2008/09", "2008-01-31", "2009-03-31"),
                                     ("Corona 2020", "2020-02-01", "2020-04-30"),
                                     ("Zinsschock 2022", "2022-01-01", "2022-12-31")]):
        s, bb = per(strat_rets, a, b), per(bench_rets, a, b)
        if np.isnan(s):
            continue
        col.markdown(
            f'<div class="glass"><div class="kpi-l">{lab}</div>'
            f'<div class="mini-row"><span class="s">{pc(s, 1, True)}</span><span class="vs">vs.</span>'
            f'<span class="b">{pc(bb, 1, True)}</span></div>'
            f'<span class="badge {tone(s - bb)}">{pc(s - bb, 1, True).replace(" %", " %p")} Differenz</span></div>',
            unsafe_allow_html=True)

# =============================================================
# TAB 2: CAPM
# =============================================================
with tab2:
    mkt_ex = (r_curr["Aktien"] - cash_curr).values
    strat_ex = (strat_rets - cash_curr).values
    ols = sm.OLS(strat_ex, sm.add_constant(mkt_ex)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    alpha_m, beta = float(ols.params[0]), float(ols.params[1])
    alpha_ann = alpha_m * 12
    p_alpha, t_alpha, r_sq = float(ols.pvalues[0]), float(ols.tvalues[0]), float(ols.rsquared)

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        st.markdown('<div class="sec">CAPM-Streudiagramm<span>Monatliche Überrenditen gegenüber Cash</span></div>',
                    unsafe_allow_html=True)
        dates = strat_rets.index.strftime("%m/%Y")
        regv = reg.values
        fc = go.Figure()
        fc.add_trace(go.Scatter(x=mkt_ex * 100, y=strat_ex * 100, mode="markers", hoverinfo="skip", showlegend=False,
                                marker=dict(size=19, opacity=0.13,
                                            color=[CYAN if g == 1 else AMBER for g in regv])))   # Leuchtrand
        for val, lab, colr in [(1, "Wachstum steigt", CYAN), (0, "Wachstum fällt", AMBER)]:
            msk = regv == val
            fc.add_trace(go.Scatter(
                x=mkt_ex[msk] * 100, y=strat_ex[msk] * 100, mode="markers", name=lab, customdata=dates[msk],
                marker=dict(size=9, color=colr, opacity=0.92, line=dict(width=1.2, color="rgba(255,255,255,.9)")),
                hovertemplate="<b>%{customdata}</b><br>Markt: %{x:.2f} %<br>Strategie: %{y:.2f} %<extra>" + lab + "</extra>"))
        xl = np.linspace(mkt_ex.min(), mkt_ex.max(), 100)
        fc.add_trace(go.Scatter(x=xl * 100, y=(alpha_m + beta * xl) * 100, mode="lines", name=f"OLS (β = {fnum(beta)})",
                                line=dict(color=ROSE, width=2.8), hoverinfo="skip"))
        fc.add_trace(go.Scatter(x=xl * 100, y=xl * 100, mode="lines", name="Marktlinie (β = 1)",
                                line=dict(color="rgba(255,255,255,.35)", width=1.4, dash="dot"), hoverinfo="skip"))
        style(fc, 430, hover="closest")
        fc.update_xaxes(title_text="Markt-Überrendite (SPY − Cash, % je Monat)", ticksuffix=" %", showspikes=False)
        fc.update_yaxes(title_text="Strategie-Überrendite (% je Monat)", ticksuffix=" %", showspikes=False)
        show(fc)

    with c2:
        st.markdown('<div class="sec">Regressionsergebnis</div>', unsafe_allow_html=True)
        sig = ("statistisch signifikant (p < 0,05)" if p_alpha < 0.05
               else f"statistisch nicht signifikant (p = {fnum(p_alpha, 3)})")
        st.markdown(
            '<div class="glass"><table class="gt">'
            f'<tr><td>Markt-Beta (β)</td><td class="hi">{fnum(beta)}</td></tr>'
            f'<tr><td>Alpha p.a.</td><td class="hi">{fnum(alpha_ann * 100, 2, True)} %</td></tr>'
            f'<tr><td>t-Wert (Alpha, HAC)</td><td>{fnum(t_alpha)}</td></tr>'
            f'<tr><td>p-Wert (Alpha)</td><td>{fnum(p_alpha, 3)}</td></tr>'
            f'<tr><td>Bestimmtheitsmaß R²</td><td>{fnum(r_sq)}</td></tr>'
            f'<tr><td>Monate</td><td>{len(strat_ex)}</td></tr></table>'
            f'<div class="note"><b>Einordnung:</b> Mit β = {fnum(beta)} nimmt die Strategie im Schnitt rund '
            f'{beta * 100:.0f} % der Aktienmarkt-Schwankung mit. Das Alpha von {fnum(alpha_ann * 100, 2, True)} % p.a. '
            f'ist {sig}. Der Marktfaktor enthält nur Aktien: Der Beitrag von Anleihen und Gold landet im Alpha. '
            'Es ist deshalb kein reiner Beleg für Timing-Können.</div></div>', unsafe_allow_html=True)
        if is_eur:
            st.caption("EUR-Ansicht: Überrenditen gegenüber dem in Euro umgerechneten Cash-ETF.")

# =============================================================
# TAB 3: BOOTSTRAP
# =============================================================
@st.cache_data(show_spinner=False)
def bootstrap_cagr_diff(s_arr, b_arr, block_len=12, n_boot=2000, seed=42):
    n = len(s_arr)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block_len))
    start = rng.integers(0, n, size=(n_boot, nb))
    idx = ((start[:, :, None] + np.arange(block_len)[None, None, :]) % n).reshape(n_boot, -1)[:, :n]
    cs = np.prod(1 + s_arr[idx], axis=1) ** (12 / n) - 1
    cb = np.prod(1 + b_arr[idx], axis=1) ** (12 / n) - 1
    return (cs - cb) * 100


with tab3:
    BLOCK, NBOOT = 12, 2000
    boot = bootstrap_cagr_diff(strat_rets.values, bench_rets.values, BLOCK, NBOOT)
    obs = d_cagr * 100
    p_val = float((boot <= 0).mean())
    lo, hi = np.percentile(boot, [2.5, 97.5])

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        st.markdown(f'<div class="sec">Block-Bootstrap<span>{NBOOT:,} Ziehungen · Blocklänge {BLOCK} Monate</span></div>'
                    .replace(",", "."), unsafe_allow_html=True)
        fb = go.Figure()
        fb.add_vrect(x0=lo, x1=hi, fillcolor="rgba(56,189,248,.07)", line_width=0, layer="below")
        fb.add_trace(go.Histogram(x=boot, nbinsx=40, name="Bootstrap-Ziehungen",
                                  marker=dict(color="rgba(56,189,248,.45)", line=dict(color=CYAN, width=1)),
                                  hovertemplate="Differenz: %{x:.2f} %p<br>Anzahl: %{y}<extra></extra>"))
        fb.add_vline(x=obs, line_width=2.6, line_color=CYAN, annotation_text=f"Beobachtet: {fnum(obs, 2, True)} %p",
                     annotation_position="top right", annotation_font=dict(size=11, color=TEXT))
        fb.add_vline(x=0, line_width=1.8, line_dash="dash", line_color=ROSE, annotation_text="Kein Vorsprung",
                     annotation_position="top left", annotation_font=dict(size=11, color=TEXT))
        style(fb, 400, hover="closest")
        fb.update_xaxes(title_text="Differenz Strategie − 60/40 (%-Punkte p.a.)", showspikes=False)
        fb.update_yaxes(title_text="Häufigkeit", showspikes=False)
        fb.update_layout(showlegend=False, bargap=0.04)
        show(fb)

    with c2:
        st.markdown('<div class="sec">Teststatistik</div>', unsafe_allow_html=True)
        if obs <= 0:
            verdict = "In dieser Einstellung liegt die Strategie nicht vor dem Benchmark."
        elif p_val < 0.05:
            verdict = ("Der Vorsprung ist im Bootstrap statistisch signifikant (p &lt; 0,05). "
                       "Es bleibt ein Backtest mit begrenzter Stichprobe.")
        elif p_val < 0.10:
            verdict = "Der Vorsprung zeigt schwache statistische Evidenz (0,05 ≤ p &lt; 0,10)."
        else:
            verdict = (f"Mit {n_switch} Regimewechseln in {len(strat_rets) / 12:.0f} Jahren lässt sich ein Vorsprung "
                       "dieser Größe nicht sicher vom Zufall unterscheiden. Das heißt nicht „kein Effekt“, sondern: "
                       "Die Datenbasis reicht für eine belastbare Aussage nicht aus.")
        st.markdown(
            '<div class="glass"><table class="gt">'
            f'<tr><td>Beobachtete Differenz</td><td class="hi">{fnum(obs, 2, True)} %p p.a.</td></tr>'
            f'<tr><td>p-Wert (einseitig)</td><td class="hi">{fnum(p_val, 3)}</td></tr>'
            f'<tr><td>95 %-Intervall</td><td>[{fnum(lo, 2, True)} ; {fnum(hi, 2, True)}] %p</td></tr></table>'
            f'<div class="note"><b>Einordnung:</b> {verdict}</div></div>', unsafe_allow_html=True)

# =============================================================
# TAB 4: METHODIK
# =============================================================
with tab4:
    m1, m2 = st.columns(2, gap="medium")
    m1.markdown(
        '<div class="glass"><h4>Methodik</h4><ul class="clean">'
        '<li><b>Daten:</b> SPY, IEF, GLD, SHV (Gesamtrenditen, Yahoo Finance), US-Industrieproduktion INDPRO (FRED), EUR/USD.</li>'
        '<li><b>Signal:</b> Industrieproduktion über bzw. unter ihrem gleitenden Durchschnitt ergibt zwei Regime.</li>'
        '<li><b>Verzögerung:</b> Die Daten erscheinen etwa Mitte des Folgemonats. Standard sind 2 Monate, damit kein Look-ahead-Bias entsteht.</li>'
        '<li><b>Portfolio:</b> Monatliches Rebalancing auf die Zielgewichte des Regimes, Kosten auf das gehandelte Volumen.</li>'
        '<li><b>Benchmark:</b> 60 % Aktien, 40 % Staatsanleihen, monatlich rebalanciert.</li>'
        '<li><b>Euro-Ansicht:</b> Ungesicherte Umrechnung der USD-Renditen. Der Sharpe wird dort ohne Zinsabzug berechnet.</li>'
        '<li><b>Alpha:</b> Regression der Überrendite auf SPY minus Cash, Standardfehler nach Newey-West.</li></ul></div>',
        unsafe_allow_html=True)
    m2.markdown(
        '<div class="glass"><h4>Grenzen</h4><ul class="clean">'
        f'<li>Nur <b>{n_switch} Regimewechsel</b>: statistisch dünne Basis.</li>'
        '<li>Die Industrieproduktion wird nachträglich <b>revidiert</b>. Der Test nutzt revidierte, keine Echtzeitdaten.</li>'
        '<li>Nur US-ETFs in USD. Die Euro-Ansicht ist ungesichert, Hedging-Kosten fehlen.</li>'
        '<li>Vereinfachtes Kostenmodell: pauschaler Satz, keine Spreads oder Steuern.</li>'
        '<li>Der Marktfaktor besteht nur aus Aktien, das Alpha enthält daher auch Anleihen- und Gold-Beiträge.</li>'
        '<li>Die Standardparameter wurden <b>vorab festgelegt</b>. Wer sie verändert, erhält explorative Ergebnisse, keine Out-of-sample-Belege.</li>'
        '<li>Ein Backtest ist kein Beleg für die Zukunft. <b>Keine Anlageberatung.</b></li></ul></div>',
        unsafe_allow_html=True)

st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
st.caption("Eigenes Research-Projekt · Daten: Yahoo Finance und FRED · Keine Anlageberatung. "
           "Vergangene Wertentwicklung ist kein verlässlicher Indikator für zukünftige Ergebnisse.")

# Maus-Effekt: Lichtfleck folgt dem Cursor auf den Glas-Karten.
# Schlaegt etwas fehl, bleibt alles andere unberuehrt (reiner Zusatz-Effekt).
JS_BODY = """
(function(){ try{
  var doc = DOCREF;
  if (doc.__glassBound) return; doc.__glassBound = true;
  doc.addEventListener('mousemove', function(e){
    var el = e.target && e.target.closest ? e.target.closest('.glass') : null;
    if(!el) return;
    var r = el.getBoundingClientRect();
    el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    el.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }, {passive:true});
}catch(err){} })();
"""


def bind_mouse_effect():
    try:                                   # neuere Streamlit-Versionen: Script direkt im Seiten-DOM
        st.html("<script>" + JS_BODY.replace("DOCREF", "document") + "</script>", unsafe_allow_javascript=True)
        return
    except Exception:
        pass
    try:                                   # aeltere Versionen: Script in unsichtbarem iframe
        import streamlit.components.v1 as components
        components.html("<script>" + JS_BODY.replace("DOCREF", "window.parent.document") + "</script>", height=0)
    except Exception:
        pass


bind_mouse_effect()
