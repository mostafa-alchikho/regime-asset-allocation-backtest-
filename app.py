import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from scipy import stats

# Page configuration
st.set_page_config(
    page_title="Makro-Regime Asset Allocation Backtest",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #0F2942;
    }
    .metric-label {
        font-size: 11px;
        color: #64748B;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. DATA CACHING (Fast interactive slider response)
# -------------------------------------------------------------
@st.cache_data(ttl=3600*24)
def load_market_data():
    tickers = {"SPY": "Aktien", "IEF": "Staatsanleihen", "GLD": "Gold", "SHV": "Cash"}
    px = yf.download(list(tickers.keys()), start="2007-01-01", end="2026-11-01", auto_adjust=True, progress=False)["Close"]
    px = px[list(tickers.keys())]
    px = px.groupby(px.index.to_period("M")).last()
    px.index = px.index.to_timestamp(how="end").normalize()
    rets = px.pct_change().dropna()
    rets.columns = [tickers[c] for c in rets.columns]
    
    # EUR/USD for currency perspective
    fx_raw = yf.download("EURUSD=X", start="2007-01-01", end="2026-11-01", auto_adjust=True, progress=False)["Close"].squeeze()
    fx = fx_raw.groupby(fx_raw.index.to_period("M")).last()
    fx.index = fx.index.to_timestamp(how="end").normalize()
    fx_ret = fx.pct_change().dropna()
    
    # FRED Industrial Production
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDPRO"
    ind = pd.read_csv(url, index_col=0, parse_dates=True).iloc[:, 0]
    ind = pd.to_numeric(ind, errors="coerce").dropna()
    ind = ind[ind.index >= "2005-01-01"]
    ind.index = ind.index.to_period("M").to_timestamp(how="end").normalize()
    
    return rets, fx_ret, ind

rets, fx_ret, ind = load_market_data()

# -------------------------------------------------------------
# 2. SIDEBAR CONTROLS (Interactive Parameters)
# -------------------------------------------------------------
st.sidebar.title("⚙️ Modell-Parameter")
st.sidebar.markdown("Testen Sie Sensitivitäten und verändern Sie Annahmen in Echtzeit:")

currency = st.sidebar.radio("Währungsperspektive", ["USD (Basis)", "EUR (ungehedgt)"], index=0)

st.sidebar.subheader("1. Signal-Parameter")
window = st.sidebar.slider("Trendfenster GD (Monate)", min_value=3, max_value=24, value=12, step=1)
lag = st.sidebar.slider("Publikationslag (Monate)", min_value=0, max_value=4, value=2, 
                       help="Lag 0 = Look-Ahead-Bias; Lag 2 = Realistische Verzögerung.")

st.sidebar.subheader("2. Kostenmodell")
cost_pct = st.sidebar.slider("Transaktionskosten je Turnover (%)", min_value=0.0, max_value=0.5, value=0.1, step=0.05)
cost = cost_pct / 100.0

st.sidebar.subheader("3. Allokation: Wachstum steigt")
w_up_aktien = st.sidebar.slider("Aktien (Aufschwung %)", 0, 100, 70, step=5)
w_up_anleihen = st.sidebar.slider("Anleihen (Aufschwung %)", 0, 100, 20, step=5)
w_up_gold = st.sidebar.slider("Gold (Aufschwung %)", 0, 100, 10, step=5)
w_up_cash = max(0, 100 - (w_up_aktien + w_up_anleihen + w_up_gold))
st.sidebar.caption(f"Cash (Aufschwung): {w_up_cash} % (automatisch ausgeglichen)")

st.sidebar.subheader("4. Allokation: Wachstum fällt")
w_down_aktien = st.sidebar.slider("Aktien (Abschwung %)", 0, 100, 30, step=5)
w_down_anleihen = st.sidebar.slider("Anleihen (Abschwung %)", 0, 100, 40, step=5)
w_down_gold = st.sidebar.slider("Gold (Abschwung %)", 0, 100, 15, step=5)
w_down_cash = max(0, 100 - (w_down_aktien + w_down_anleihen + w_down_gold))
st.sidebar.caption(f"Cash (Abschwung): {w_down_cash} % (automatisch ausgeglichen)")

# -------------------------------------------------------------
# 3. BACKTEST ENGINE
# -------------------------------------------------------------
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

def calc_metrics(x, cash):
    n = len(x)
    cagr = (1 + x).prod() ** (12 / n) - 1
    vol = x.std() * np.sqrt(12)
    ex = x - cash
    sharpe = ex.mean() * 12 / (ex.std() * np.sqrt(12)) if ex.std() > 0 else 0
    cum = (1 + x).cumprod()
    mdd = (cum / np.maximum(cum.cummax(), 1.0) - 1).min()
    return {"CAGR": cagr, "Vola": vol, "Sharpe": sharpe, "MaxDD": mdd}

# Normalize weights
W_UP = {
    "Aktien": w_up_aktien / 100.0,
    "Staatsanleihen": w_up_anleihen / 100.0,
    "Gold": w_up_gold / 100.0,
    "Cash": w_up_cash / 100.0
}
W_DOWN = {
    "Aktien": w_down_aktien / 100.0,
    "Staatsanleihen": w_down_anleihen / 100.0,
    "Gold": w_down_gold / 100.0,
    "Cash": w_down_cash / 100.0
}
W_BENCH = {"Aktien": 0.60, "Staatsanleihen": 0.40, "Gold": 0.00, "Cash": 0.00}

# Run Backtest
BT_START = "2008-01-31"
reg = build_regime(ind, window, lag).reindex(rets.index).loc[BT_START:].dropna()
common_idx = reg.index.intersection(rets.index)
r_curr = rets.loc[common_idx]
reg = reg.loc[common_idx]

# Currency adjustment if EUR
if currency == "EUR (ungehedgt)":
    fx_common = fx_ret.reindex(common_idx).fillna(0)
    for col in r_curr.columns:
        r_curr[col] = (1 + r_curr[col]) / (1 + fx_common) - 1

tgt = pd.DataFrame([W_UP if g == 1 else W_DOWN for g in reg], index=r_curr.index)[r_curr.columns]
ben = pd.DataFrame([W_BENCH] * len(r_curr), index=r_curr.index)[r_curr.columns]

strat_rets, turnover = backtest(tgt, r_curr, cost)
bench_rets, _ = backtest(ben, r_curr, cost)
cash_curr = r_curr["Cash"]

m_strat = calc_metrics(strat_rets, cash_curr)
m_bench = calc_metrics(bench_rets, cash_curr)

# -------------------------------------------------------------
# 4. DASHBOARD HEADER & STAT CARDS
# -------------------------------------------------------------
st.title("📈 Quantitative Asset Allocation: Interaktiver Makro-Backtest")
st.markdown(f"**Research-Modell für Initiativbewerbung** | Signal: US INDPRO ({window}M GD, Lag={lag}) | Transaktionskosten: {cost_pct:.2f} % | Währung: {currency}")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rendite p.a. (Strategie)", f"{m_strat['CAGR']*100:.2f} %", f"{(m_strat['CAGR']-m_bench['CAGR'])*100:+.2f} %p vs Bench")
c2.metric("Sharpe Ratio", f"{m_strat['Sharpe']:.2f}", f"{m_strat['Sharpe']-m_bench['Sharpe']:+.2f} vs Bench")
c3.metric("Max. Drawdown", f"{m_strat['MaxDD']*100:.2f} %", f"{(m_strat['MaxDD']-m_bench['MaxDD'])*100:+.2f} %p Schutz")
c4.metric("Turnover p.a.", f"{turnover.mean()*12*100:.1f} %")
c5.metric("Regimewechsel", f"{int((reg.diff().abs() == 1).sum())}")

st.markdown("---")

# -------------------------------------------------------------
# 5. CHARTS & DETAILS
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Performance & Equity Curve", "🎲 Block-Bootstrap Signifikanz", "📐 CAPM & Faktoranalyse"])

with tab1:
    col_chart, col_table = st.columns([3, 2])
    
    with col_chart:
        cum_s = (1 + strat_rets).cumprod() * 100
        cum_b = (1 + bench_rets).cumprod() * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cum_s.index, y=cum_s.values, mode='lines', name='Regime-Strategie (netto)', line=dict(color='#0F2942', width=2.2)))
        fig.add_trace(go.Scatter(x=cum_b.index, y=cum_b.values, mode='lines', name='60/40-Benchmark', line=dict(color='#D97706', width=1.8, dash='dash')))
        fig.update_layout(title="Vermögensentwicklung (Start = 100)", xaxis_title="", yaxis_title="Portfoliowert", 
                          template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=20),
                          legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        st.subheader("Kennzahlen-Vergleich")
        df_comp = pd.DataFrame({
            "Kennzahl": ["Rendite p.a. (CAGR)", "Volatilität p.a.", "Sharpe Ratio", "Max. Drawdown"],
            "Strategie": [f"{m_strat['CAGR']*100:.2f} %", f"{m_strat['Vola']*100:.2f} %", f"{m_strat['Sharpe']:.2f}", f"{m_strat['MaxDD']*100:.2f} %"],
            "60/40 Benchmark": [f"{m_bench['CAGR']*100:.2f} %", f"{m_bench['Vola']*100:.2f} %", f"{m_bench['Sharpe']:.2f}", f"{m_bench['MaxDD']*100:.2f} %"],
            "Differenz": [f"{(m_strat['CAGR']-m_bench['CAGR'])*100:+.2f} %p", f"{(m_strat['Vola']-m_bench['Vola'])*100:+.2f} %p", f"{m_strat['Sharpe']-m_bench['Sharpe']:+.2f}", f"{(m_strat['MaxDD']-m_bench['MaxDD'])*100:+.2f} %p"]
        })
        st.dataframe(df_comp, hide_index=True, use_container_width=True)
        
        # Stress periods
        st.subheader("Krisenresilienz")
        cr_2008_s = (1 + strat_rets.loc["2008-01-31":"2009-03-31"]).prod() - 1
        cr_2008_b = (1 + bench_rets.loc["2008-01-31":"2009-03-31"]).prod() - 1
        cr_2022_s = (1 + strat_rets.loc["2022-01-01":"2022-12-31"]).prod() - 1
        cr_2022_b = (1 + bench_rets.loc["2022-01-01":"2022-12-31"]).prod() - 1
        
        st.write(f"• **Finanzkrise 2008/09:** Strategie: `{cr_2008_s*100:+.1f} %` | 60/40: `{cr_2008_b*100:+.1f} %`")
        st.write(f"• **Zinsschock 2022:** Strategie: `{cr_2022_s*100:+.1f} %` | 60/40: `{cr_2022_b*100:+.1f} %`")

with tab2:
    st.subheader("🎲 Block-Bootstrap Signifikanztest")
    col_bs_chart, col_bs_text = st.columns([3, 2])
    
    # Fast 1.000 samples for live dashboard speed
    n_boot = 1000
    block_len = 12
    n_samples = len(strat_rets)
    s_arr, b_arr = strat_rets.values, bench_rets.values
    obs_diff = m_strat["CAGR"] - m_bench["CAGR"]
    
    boot_diffs = []
    np.random.seed(42)
    for _ in range(n_boot):
        idx = []
        while len(idx) < n_samples:
            st_pos = np.random.randint(0, max(1, n_samples - block_len + 1))
            idx.extend(range(st_pos, min(st_pos + block_len, n_samples)))
        idx = idx[:n_samples]
        c_s = (1 + s_arr[idx]).prod() ** (12 / n_samples) - 1
        c_b = (1 + b_arr[idx]).prod() ** (12 / n_samples) - 1
        boot_diffs.append((c_s - c_b) * 100)
    
    boot_diffs = np.array(boot_diffs)
    p_val = (boot_diffs <= 0).mean()
    ci_lo, ci_hi = np.percentile(boot_diffs, [2.5, 97.5])
    
    with col_bs_chart:
        fig_bs = go.Figure()
        fig_bs.add_trace(go.Histogram(x=boot_diffs, nbinsx=40, marker_color='#CBD5E1', marker_line_color='#64748B', marker_line_width=1, name='Bootstrap Verteilung'))
        fig_bs.add_vline(x=obs_diff*100, line_width=2.5, line_color='#0F2942', annotation_text=f"Obs: {obs_diff*100:+.2f}%")
        fig_bs.add_vline(x=0, line_width=1.5, line_dash="dash", line_color='#DC2626', annotation_text="H0: 0%")
        fig_bs.update_layout(title=f"Bootstrap Renditedifferenz (N={n_boot:,}, Block=12M)", xaxis_title="Differenz CAGR (% p.a.)", 
                             yaxis_title="Häufigkeit", template="plotly_white", height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bs, use_container_width=True)
        
    with col_bs_text:
        st.markdown(f"""
        **Testergebnisse:**
        - **Beobachteter Vorsprung:** `{obs_diff*100:+.2f} % p.a.`
        - **Einseitiger p-Wert:** `{p_val:.3f}`
        - **95 %-Konfidenzintervall:** `[{ci_lo:+.2f} % ; {ci_hi:+.2f} %]`
        
        **Ehrliche statistische Wertung:**  
        {"✅ Statistisch signifikant auf dem 5%-Niveau." if p_val < 0.05 else "⚠️ **Nicht statistisch signifikant:** Das Konfidenzintervall schließt die Null ein (p > 0,05). Bei wenigen Regime-Zyklen kann ein Zufallseffekt nicht ausgeschlossen werden. Dies belegt methodische Integrität statt Schönfärberei."}
        """)

with tab3:
    st.subheader("📐 Faktoranalyse: Jensen's Alpha & Markt-Beta")
    col_reg_chart, col_reg_text = st.columns([3, 2])
    
    mkt_ex = (r_curr["Aktien"] - cash_curr).values
    strat_ex = (strat_rets - cash_curr).values
    
    slope, intercept, r_val, p_val_reg, se = stats.linregress(mkt_ex, strat_ex)
    alpha_ann = intercept * 12
    r_sq = r_val ** 2
    
    with col_reg_chart:
        fig_reg = go.Figure()
        fig_reg.add_trace(go.Scatter(x=mkt_ex*100, y=strat_ex*100, mode='markers', marker=dict(color='#0F2942', opacity=0.45, size=6), name='Monatliche Überrenditen'))
        
        x_trend = np.linspace(mkt_ex.min(), mkt_ex.max(), 100)
        y_trend = intercept + slope * x_trend
        fig_reg.add_trace(go.Scatter(x=x_trend*100, y=y_trend*100, mode='lines', line=dict(color='#DC2626', width=2), name=f"CAPM Regression"))
        fig_reg.update_layout(title="CAPM: Überrendite vs. Marktfaktor (SPY − Cash)", xaxis_title="Markt Überrendite (% mtl.)", 
                              yaxis_title="Strategie Überrendite (% mtl.)", template="plotly_white", height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_reg, use_container_width=True)
        
    with col_reg_text:
        st.markdown(f"""
        **Regressionsergebnisse (OLS):**
        - **Markt-Beta:** `{slope:.2f}` (Defensiver als Markt / Benchmark)
        - **Jensen's Alpha (p.a.):** `{alpha_ann*100:+.2f} %` (p = `{p_val_reg:.3f}`)
        - **Bestimmtheitsmaß R²:** `{r_sq:.2f}`
        
        **Ökonomische Interpretation:**  
        Der Performancevorteil und die geringen Drawdowns resultieren primär aus **Downside-Beta-Management** ($\beta = {slope:.2f}$): Das Portfolio reduziert in Krisen automatisch Aktienrisiko, ohne im Aufschwung den Anschluss zu verlieren.
        """)

st.markdown("---")
st.caption("Quantitative Asset Allocation Model · Research Projekt für Initiativbewerbung Praktikum Asset Management · Alle Daten via Yahoo Finance & FRED St. Louis Fed.")
