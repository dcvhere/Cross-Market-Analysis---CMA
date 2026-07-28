%%writefile CMA-1-streamlit.py

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from datetime import date

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(layout="wide", page_title="Market Analysis Pro Dashboard", page_icon="📊")

# ==========================================
# 2. DATABASE CONNECTION (Cached for performance)
# ==========================================
DB_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
DB_USER = "iatXFmXH7cy5Eyv.root"
DB_PASSWORD = "ndGScqvE2B1dpP9p"
DB_PORT = 4000
DB_NAME = "market_data_db"

@st.cache_resource
def get_db_engine():
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(DATABASE_URL, connect_args={"ssl": {"ssl": True}})

engine = get_db_engine()

def run_query(query, params=None):
    """Executes a SQL query and returns a pandas DataFrame."""
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return pd.DataFrame()

# ==========================================
# 3. PAGE RENDER FUNCTIONS
# ==========================================
def render_home():
    st.subheader("🏠 Multi-Asset Market Overview")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    btc = run_query("SELECT price_inr FROM crypto_historical_prices WHERE coin_id='bitcoin' ORDER BY date DESC LIMIT 1")
    oil = run_query("SELECT price FROM oil_processed_prices ORDER BY date DESC LIMIT 1")
    stocks = run_query("SELECT AVG(close_price) as avg_p FROM stock_processed_data")
    
    col1.metric("🪙 Bitcoin (Latest)", f"₹{btc.iloc[0,0]:,.0f}" if not btc.empty else "N/A")
    col2.metric("🛢️ WTI Crude Oil", f"${oil.iloc[0,0]:.2f}" if not oil.empty else "N/A")
    col3.metric("📈 Stock Index Avg", f"{stocks.iloc[0,0]:,.2f}" if not stocks.empty else "N/A")

def render_crypto():
    st.header("🪙 Cryptocurrency Analysis")
    choice = st.selectbox("📊 Select Analysis View", [
        "Top 5 Coins by Market Cap",
        "High Circulating Supply Ratio (>90%)",
        "Coins within 10% of ATH",
        "Volume > $1B Ranking",
        "Bitcoin Trend (Feb 2026)"
    ])
    
    df = pd.DataFrame()
    st.markdown("---")
    
    if "Top 5" in choice:
        df = run_query("SELECT name, symbol, current_price, market_cap FROM crypto_processed_current ORDER BY market_cap DESC LIMIT 5")
        if not df.empty:
            st.plotly_chart(px.bar(df, x='name', y='market_cap', title="Market Cap of Top 5 Coins", color='name'), use_container_width=True)
            
    elif "Circulating" in choice:
        df = run_query("SELECT name, symbol, (circulating_supply / total_supply) as supply_ratio FROM crypto_processed_current WHERE total_supply > 0 AND (circulating_supply / total_supply) > 0.9")
        if not df.empty:
            st.plotly_chart(px.pie(df, names='name', values='supply_ratio', title="Coins with >90% Supply Ratio"), use_container_width=True)
            
    elif "10%" in choice:
        df = run_query("SELECT name, symbol, current_price, ath FROM crypto_current_market WHERE ath > 0 AND (current_price / ath) >= 0.9")
        if not df.empty:
            st.plotly_chart(px.bar(df, x='symbol', y=['current_price', 'ath'], barmode='group', title="Current Price vs All-Time High"), use_container_width=True)
            
    elif "$1B" in choice:
        df = run_query("SELECT name, market_cap_rank, total_volume FROM crypto_current_market WHERE total_volume > 1000000000 ORDER BY market_cap_rank")
        if not df.empty:
            st.plotly_chart(px.scatter(df, x='market_cap_rank', y='total_volume', size='total_volume', color='name', title="Volume > $1B by Market Cap Rank"), use_container_width=True)
            
    else:
        df = run_query("SELECT date, price_inr FROM crypto_historical_prices WHERE coin_id='bitcoin' AND date LIKE '2026-02%'")
        if not df.empty:
            st.line_chart(df.set_index('date'))

    if not df.empty:
        with st.expander("🔍 View Raw Data", expanded=False):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No data available for this query.")

def render_oil():
    st.header("🛢️ Crude Oil Analytics")
    choice = st.selectbox("📊 Select Analysis View", ["Highest Price (Last 5 Years)", "Average Annual Price", "COVID Crash 2020", "Annual Volatility"])
    
    df = pd.DataFrame()
    st.markdown("---")
    
    if "Highest" in choice:
        df = run_query("SELECT date, price FROM oil_processed_prices WHERE date >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) ORDER BY price DESC LIMIT 1")
        if not df.empty:
            st.metric("📈 5-Year High Price", f"${df.iloc[0,1]:.2f}", f"Date: {df.iloc[0,0]}")
            
    elif "Average Annual" in choice:
        df = run_query("SELECT YEAR(date) as Year, AVG(price) as Avg_Price FROM oil_processed_prices GROUP BY Year ORDER BY Year DESC")
        if not df.empty:
            st.plotly_chart(px.line(df, x='Year', y='Avg_Price', title="Annual Average Oil Price", markers=True), use_container_width=True)
            
    elif "COVID" in choice:
        df = run_query("SELECT date, price FROM oil_processed_prices WHERE date BETWEEN '2020-03-01' AND '2020-04-30'")
        if not df.empty:
            st.markdown("#### COVID Crash 2020 (March - April)")
            st.line_chart(df.set_index('date'))
            
    else:
        df = run_query("SELECT YEAR(date) as Year, (MAX(price) - MIN(price)) as Range FROM oil_processed_prices GROUP BY Year")
        if not df.empty:
            st.markdown("#### Annual Price Volatility (Max - Min)")
            st.bar_chart(df.set_index('Year'))

    if not df.empty:
        with st.expander("🔍 View Raw Data", expanded=False):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No data available for this query.")

def render_stocks():
    st.header("📈 Stock Market Insights")
    choice = st.selectbox("📊 Select Analysis View", ["NASDAQ Highest Closing Price", "S&P 500 Top 5 Volatility Days", "Monthly Avg Close", "NSEI Volume 2024"])
    
    df = pd.DataFrame()
    st.markdown("---")
    
    if "NASDAQ" in choice:
        df = run_query("SELECT date, close_price FROM stock_processed_data WHERE source = '^IXIC' ORDER BY close_price DESC LIMIT 1")
        if not df.empty:
            st.metric("🏆 NASDAQ ATH", f"{df.iloc[0,1]:,.2f}", f"Date: {df.iloc[0,0]}")
            
    elif "Volatility" in choice:
        df = run_query("SELECT date, (high_price - low_price) as range_diff FROM stock_processed_data WHERE source = '^GSPC' ORDER BY range_diff DESC LIMIT 5")
        if not df.empty:
            st.plotly_chart(px.bar(df, x='date', y='range_diff', title="Top 5 Most Volatile Days (S&P 500)"), use_container_width=True)
            
    elif "Monthly" in choice:
        df = run_query("SELECT source, DATE_FORMAT(date, '%Y-%m') as Month, AVG(close_price) as Avg_Close FROM stock_processed_data GROUP BY source, Month")
        if not df.empty:
            st.plotly_chart(px.line(df, x='Month', y='Avg_Close', color='source', title="Monthly Average Closing Prices"), use_container_width=True)
            
    else:
        df = run_query("SELECT date, volume FROM stock_processed_data WHERE source='^NSEI' AND YEAR(date)=2024")
        if not df.empty:
            st.markdown("#### NSEI Trading Volume (2024)")
            st.area_chart(df.set_index('date'))

    if not df.empty:
        with st.expander("🔍 View Raw Data", expanded=False):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No data available for this query.")

def render_correlation():
    st.header("🔗 Cross-Asset Correlations")
    sub = st.radio("📊 Select Correlation Study", ["Bitcoin vs Oil (Daily - Date Filter)", "Ethereum vs NASDAQ Trends", "Overall Market Correlation"], horizontal=True)
    
    df = pd.DataFrame()
    st.markdown("---")
    
    if "Date Filter" in sub:
        d = st.date_input("🗓️ Select Comparison Date", value=date(2025, 12, 1))
        df = run_query("SELECT c.date, c.price_inr as BTC_Price, o.price as Oil_Price FROM crypto_historical_prices c JOIN oil_processed_prices o ON c.date = o.date WHERE c.coin_id='bitcoin' AND c.date = %s", params=(d,))
        if not df.empty:
            st.plotly_chart(px.bar(df.melt(id_vars='date'), x='variable', y='value', color='variable', title=f"BTC vs Oil Prices on {d}"), use_container_width=True)
        else:
            st.warning(f"No correlation data found for {d}")
            
    elif "Ethereum" in sub:
        df = run_query("SELECT c.date, c.price_inr as Eth_Price, s.close_price as NASDAQ_Close FROM crypto_historical_prices c JOIN stock_processed_data s ON c.date = s.date WHERE c.coin_id='ethereum' AND s.source='^IXIC' ORDER BY c.date DESC LIMIT 100")
        if not df.empty:
            st.plotly_chart(px.line(df, x='date', y=['Eth_Price', 'NASDAQ_Close'], title="Ethereum vs NASDAQ (Last 100 Overlapping Days)"), use_container_width=True)
            
    else:
        df = run_query("SELECT CAST(s.date AS DATE) as Date, s.close_price as SP500, o.price as Oil, c.price_inr/100000 as BTC_Lakhs FROM stock_processed_data s JOIN oil_processed_prices o ON DATE(s.date) = DATE(o.date) JOIN crypto_historical_prices c ON DATE(s.date) = DATE(c.date) WHERE s.source = '^GSPC' AND c.coin_id='bitcoin' ORDER BY Date DESC LIMIT 50")
        if not df.empty:
            st.plotly_chart(px.line(df, x='Date', y=['SP500', 'Oil', 'BTC_Lakhs'], title="S&P 500 vs Oil vs Bitcoin (Scaled in Lakhs)"), use_container_width=True)

    if not df.empty:
        with st.expander("🔍 View Raw Data", expanded=False):
            st.dataframe(df, use_container_width=True)


# ==========================================
# 4. MAIN APP ROUTING
# ==========================================
st.title("📊 Comprehensive Market Analysis Dashboard")

with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["Home", "Cryptocurrency", "Crude Oil", "Stock Market", "Cross-Asset Correlation"],
        icons=["house", "currency-bitcoin", "droplet-fill", "graph-up-arrow", "diagram-3"],
        menu_icon="cast", 
        default_index=0,
    )

if selected == "Home":
    render_home()
elif selected == "Cryptocurrency":
    render_crypto()
elif selected == "Crude Oil":
    render_oil()
elif selected == "Stock Market":
    render_stocks()
elif selected == "Cross-Asset Correlation":
    render_correlation()
