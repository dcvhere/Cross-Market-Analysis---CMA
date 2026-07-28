
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection details
DB_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
DB_USER = "iatXFmXH7cy5Eyv.root"
DB_PASSWORD = "ndGScqvE2B1dpP9p"
DB_PORT = 4000
DB_NAME = "market_data_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, connect_args={"ssl": {"ssl": True}})

st.set_page_config(layout="wide", page_title="Market Analysis Pro")
st.title("Comprehensive Cross-Market Analysis")

with st.sidebar:
    selected = option_menu(
        "Analysis Modules",
        ["Home", "Cryptocurrency Analysis", "Oil Price Analysis", "Stock Market Analysis", "Cross-Market Correlation"],
        icons=["house", "currency-bitcoin", "droplet", "graph-up", "intersect"],
        default_index=0
    )

def run_query(query):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

if selected == "Home":
    st.markdown("### Market Overview Suite")
    st.write("Comprehensive analysis of Cryptocurrency, Oil, and Global Stock Indices.")

elif selected == "Cryptocurrency Analysis":
    st.header("Crypto Deep Dive")
    q_type = st.selectbox("Select Query:", [
        "Coins within 10% of ATH",
        "Avg Market Cap Rank (Volume > $1B)",
        "Bitcoin Peak Price (Last 365 Days)",
        "Bitcoin Daily Trend (Feb 2026)",
        "Bitcoin % Change (Feb 2026)"
    ])

    if q_type == "Coins within 10% of ATH":
        df = run_query("SELECT name, symbol, current_price, ath FROM crypto_current_market WHERE (current_price / ath) >= 0.9")
        st.dataframe(df)
    elif q_type == "Avg Market Cap Rank (Volume > $1B)":
        df = run_query("SELECT AVG(market_cap_rank) as avg_rank FROM crypto_current_market WHERE total_volume > 1000000000")
        st.metric("Average Rank", f"{df.iloc[0,0]:.2f}")
    elif q_type == "Bitcoin Peak Price (Last 365 Days)":
        df = run_query("SELECT MAX(price_inr) as peak FROM crypto_historical_prices WHERE coin_id = 'bitcoin'")
        st.metric("Peak Price (INR)", f"{df.iloc[0,0]:,.2f}")
    elif q_type == "Bitcoin Daily Trend (Feb 2026)":
        df = run_query("SELECT date, price_inr FROM crypto_historical_prices WHERE coin_id = 'bitcoin' AND date LIKE '2026-02%'")
        st.line_chart(df.set_index('date'))
    elif q_type == "Bitcoin % Change (Feb 2026)":
        df = run_query("SELECT date, price_inr, (price_inr - LAG(price_inr) OVER (ORDER BY date)) / LAG(price_inr) OVER (ORDER BY date) * 100 as pct_change FROM crypto_historical_prices WHERE coin_id = 'bitcoin' AND date LIKE '2026-02%'")
        st.dataframe(df)

elif selected == "Oil Price Analysis":
    st.header("Crude Oil Analysis")
    oil_q = st.selectbox("Select Analysis:", [
        "COVID Crash Prices (March-April 2020)",
        "Lowest Price (Last 5 Years)",
        "Volatility (Max-Min Difference per Year)"
    ])

    if oil_q == "COVID Crash Prices (March-April 2020)":
        df = run_query("SELECT date, price FROM oil_processed_prices WHERE date BETWEEN '2020-03-01' AND '2020-04-30'")
        st.line_chart(df.set_index('date'))
    elif oil_q == "Lowest Price (Last 5 Years)":
        df = run_query("SELECT MIN(price) as min_price FROM oil_processed_prices WHERE date >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR)")
        st.metric("Lowest Oil Price", f"${df.iloc[0,0]:.2f}")
    elif oil_q == "Volatility (Max-Min Difference per Year)":
        df = run_query("SELECT YEAR(date) as year, (MAX(price) - MIN(price)) as volatility FROM oil_processed_prices GROUP BY year")
        st.bar_chart(df.set_index('year'))

elif selected == "Stock Market Analysis":
    st.header("Global Equity Indices")
    stock_q = st.selectbox("Select Analysis:", [
        "Monthly Avg Closing Price per Ticker",
        "Avg Trading Volume NSEI (2024)"
    ])

    if stock_q == "Monthly Avg Closing Price per Ticker":
        df = run_query("SELECT source, DATE_FORMAT(date, '%Y-%m') as month, AVG(close_price) as avg_close FROM stock_processed_data GROUP BY source, month")
        st.dataframe(df)
    elif stock_q == "Avg Trading Volume NSEI (2024)":
        df = run_query("SELECT AVG(volume) FROM stock_processed_data WHERE source = '^NSEI' AND YEAR(date) = 2024")
        st.write(df)

elif selected == "Cross-Market Correlation":
    st.header("Cross-Asset Correlations")
    cross_q = st.selectbox("Select Comparison:", [
        "Bitcoin vs Oil Avg (2025)",
        "Multi-Asset Daily Comparison (Stocks, Oil, Bitcoin)"
    ])

    if cross_q == "Bitcoin vs Oil Avg (2025)":
        df = run_query("""
            SELECT 'Bitcoin' as Asset, AVG(price_inr) as avg_val FROM crypto_historical_prices WHERE coin_id='bitcoin' AND YEAR(date)=2025
            UNION
            SELECT 'Oil' as Asset, AVG(price) as avg_val FROM oil_processed_prices WHERE YEAR(date)=2025
        """)
        st.dataframe(df)
    elif cross_q == "Multi-Asset Daily Comparison (Stocks, Oil, Bitcoin)":
        df = run_query("""
            SELECT 
                CAST(s.date AS DATE) as Trade_Date, 
                s.close_price as SP500_Close, 
                o.price as Oil_Price, 
                c.price_inr as BTC_Price_INR
            FROM stock_processed_data s
            JOIN oil_processed_prices o ON CAST(s.date AS DATE) = CAST(o.date AS DATE)
            JOIN crypto_historical_prices c ON CAST(s.date AS DATE) = CAST(c.date AS DATE)
            WHERE s.source = '^GSPC' AND c.coin_id = 'bitcoin'
            ORDER BY Trade_Date DESC 
            LIMIT 100
        """)
        st.dataframe(df)
