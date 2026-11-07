import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.oanda import OandaClient, OANDA_INSTRUMENTS, scan_instruments
from agents.engine import run_desk

st.set_page_config(page_title="APEX AI Trading Desk", page_icon="📈", layout="wide")
st.title("📈 APEX AI Trading Desk")
st.caption("Six-agent market intelligence • OANDA REST v20 • Gold + Forex • Analysis only")

def secret(key):
    try:
        return st.secrets.get(key, os.getenv(key, ""))
    except Exception:
        return os.getenv(key, "")

with st.sidebar:
    st.header("OANDA connection")
    environment = st.selectbox("Environment", ["practice", "live"])
    token = secret("OANDA_API_TOKEN")
    st.success("API token configured") if token else st.warning("Add OANDA_API_TOKEN to secrets")
    st.divider()
    instruments = st.multiselect("Markets to scan", list(OANDA_INSTRUMENTS),
        default=["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"])
    symbol = st.selectbox("Chart instrument", instruments or list(OANDA_INSTRUMENTS))
    timeframe = st.selectbox("Timeframe", ["M1", "M2", "M5", "M15", "M30", "H1", "H4"])
    count = st.slider("Candles", 100, 1000, 500, 50)
    risk_pct = st.slider("Risk reference (%)", 0.1, 2.0, 0.5, 0.1)
    st.caption("No orders are placed. Signals are analytical candidates only.")

client = OandaClient(token, environment) if token else None
chart_tab, scan_tab, agents_tab, setup_tab = st.tabs(["📊 Candlestick chart", "🔎 Market scanner", "🤖 Agent reports", "⚙️ Setup"])

with chart_tab:
    st.subheader(f"{OANDA_INSTRUMENTS[symbol]} · {timeframe}")
    if st.button("Fetch OANDA candles", type="primary"):
        if not client:
            st.error("Configure your OANDA API token in Streamlit secrets.")
        else:
            try:
                st.session_state["candles"] = client.get_candles(symbol, timeframe, count)
                st.session_state["chart_symbol"] = symbol
            except Exception as exc:
                st.error(str(exc))
    df = st.session_state.get("candles")
    if df is not None and st.session_state.get("chart_symbol") == symbol:
        fig = go.Figure([go.Candlestick(x=df.time, open=df.open, high=df.high, low=df.low, close=df.close)])
        fig.update_layout(template="plotly_dark", height=560, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Completed midpoint candles only. OANDA candle volume is tick count, not centralised traded volume.")
        if st.button("Run six agents on chart"):
            st.session_state["agent_result"] = run_desk(df, symbol, timeframe, risk_pct)
    else:
        st.info("Fetch candles to display the chart.")

with scan_tab:
    st.subheader("Multi-market scanner")
    if st.button("Scan selected instruments", type="primary"):
        if not client:
            st.error("Configure your OANDA API token in Streamlit secrets.")
        elif not instruments:
            st.warning("Select at least one instrument.")
        else:
            with st.spinner("Fetching completed candles and running agents..."):
                try:
                    st.session_state["scan_results"] = scan_instruments(client, instruments, timeframe, min(count, 500), risk_pct)
                except Exception as exc:
                    st.error(str(exc))
    if st.session_state.get("scan_results"):
        st.dataframe(pd.DataFrame(st.session_state["scan_results"]), use_container_width=True, hide_index=True)

with agents_tab:
    result = st.session_state.get("agent_result")
    if result:
        a,b,c = st.columns(3)
        a.metric("Chief decision", result["decision"])
        b.metric("Directional votes", f'{result["votes"]}/4')
        c.metric("Risk gate", result["risk_status"])
        st.info(result["summary"])
        if result["levels"]:
            a,b,c,d = st.columns(4)
            a.metric("Entry reference", f'{result["levels"]["entry"]:.5f}')
            b.metric("Stop", f'{result["levels"]["stop"]:.5f}')
            c.metric("TP1", f'{result["levels"]["tp1"]:.5f}')
            d.metric("TP2", f'{result["levels"]["tp2"]:.5f}')
        for agent in result["agents"]:
            with st.expander(f'{agent["name"]} — {agent["stance"]}', expanded=True):
                st.write(agent["finding"])
                st.caption(agent["evidence"])
    else:
        st.info("Run the agents from the candlestick chart tab.")

with setup_tab:
    st.markdown("""
    Create `.streamlit/secrets.toml` locally, or add these values in Streamlit Community Cloud → App settings → Secrets:

    ```toml
    OANDA_API_TOKEN = "your-personal-access-token"
    OANDA_ACCOUNT_ID = "your-v20-account-id"
    ```

    Start with **practice**. Never commit your real secrets file to GitHub.
    """)
    st.markdown("[OANDA REST v20 documentation](https://developer.oanda.com/rest-live-v20/introduction/) · [API token instructions](https://help.oanda.com/us/en/faqs/rest-v20-api-troubleshooting-guide.htm)")
    st.warning("Your OANDA account must support REST v20. The account ID is retained for future account-specific pricing features.")

st.divider()
st.caption("APEX AI Trading Desk v1.1 • OANDA API • Analysis and signals only • No execution")
