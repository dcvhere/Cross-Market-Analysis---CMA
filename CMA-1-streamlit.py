
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# Database connection setup
DB_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
DB_USER = "iatXFmXH7cy5Eyv.root"
DB_PASSWORD = "ndGScqvE2B1dpP9p"
DB_PORT = 4000
DB_NAME = "market_data_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, connect_args={"ssl": {"ssl": True}})

st.set_page_config(layout="wide", page_title="Market Analysis Pro Dashboard")
st.title("📊 Comprehensive Market Analysis Dashboard")

with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["Home", "Cryptocurrency", "Crude Oil", "Stock Market", "Cross-Asset Correlation"],
        icons=["house", "currency-bitcoin", "droplet-fill", "graph-up-arrow", "diagram-3"],
        menu_icon="cast", default_index=0,
    )

def run_query(query):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

if selected == "Home":
    st.subheader("🏠 Multi-Asset Market Overview")
    col1, col2, col3 = st.columns(3)
    
    # Fetch latest overview metrics
    btc = run_query("SELECT price_inr FROM crypto_historical_prices WHERE coin_id='bitcoin' ORDER BY date DESC LIMIT 1")
    oil = run_query("SELECT price FROM oil_processed_prices ORDER BY date DESC LIMIT 1")
    stocks = run_query("SELECT AVG(close_price) as avg_p FROM stock_processed_data")
    
    col1.metric("Bitcoin (Latest)", f"₹{btc.iloc[0,0]:,.0f}")
    col2.metric("WTI Crude Oil", f"${oil.iloc[0,0]:.2f}")
    col3.metric("Stock Index Avg", f"{stocks.iloc[0,0]:,.2f}")
    
    st.markdown("--- updates based on the processed tables in TiDB database.")

elif selected == "Cryptocurrency":
    st.header("🪙 Cryptocurrency Insights")
    choice = st.selectbox("Select Requirement", [
        "Coins within 10% of All-Time High",
        "Market Cap Rank (Volume > $1B)",
        "Bitcoin Price Trend (Feb 2026)",
        "Bitcoin % Change (Feb 2026)"
    ])
    
    if "10%" in choice:
        df = run_query("SELECT name, symbol, current_price, ath FROM crypto_current_market WHERE (current_price / ath) >= 0.9")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.write("### Visualization")
        st.plotly_chart(px.bar(df, x='symbol', y=['current_price', 'ath'], barmode='group'))

    elif "$1B" in choice:
        df = run_query("SELECT name, market_cap_rank, total_volume FROM crypto_current_market WHERE total_volume > 1000000000 ORDER BY market_cap_rank")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.write("### Visualization")
        st.plotly_chart(px.scatter(df, x='market_cap_rank', y='total_volume', size='total_volume', color='name'))

    elif "Trend" in choice:
        df = run_query("SELECT date, price_inr FROM crypto_historical_prices WHERE coin_id='bitcoin' AND date LIKE '2026-02%'")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.write("### Visualization")
        st.line_chart(df.set_index('date'))

elif selected == "Crude Oil":
    st.header("🛢️ Crude Oil Analysis")
    choice = st.selectbox("Select Metric", ["COVID Crash 2020", "Annual Volatility", "Historical Lows"])
    
    if "COVID" in choice:
        df = run_query("SELECT date, price FROM oil_processed_prices WHERE date BETWEEN '2020-03-01' AND '2020-04-30'")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.write("### Visualization")
        st.line_chart(df.set_index('date'))

    elif "Volatility" in choice:
        df = run_query("SELECT YEAR(date) as Year, (MAX(price) - MIN(price)) as Range_Vol FROM oil_processed_prices GROUP BY Year")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.write("### Visualization")
        st.bar_chart(df.set_index('Year'))

elif selected == "Stock Market":
    st.header("📈 Stock Market Analysis")
    choice = st.selectbox("Select View", ["Monthly Avg Close", "NSEI Volume 2024"])
    
    if "Monthly" in choice:
        df = run_query("SELECT source, DATE_FORMAT(date, '%Y-%m') as Month, AVG(close_price) as Avg_Close FROM stock_processed_data GROUP BY source, Month")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.write("### Visualization")
        st.plotly_chart(px.line(df, x='Month', y='Avg_Close', color='source'))

    elif "NSEI" in choice:
        df = run_query("SELECT date, volume FROM stock_processed_data WHERE source='^NSEI' AND YEAR(date)=2024")
        st.write("### Data Table")
        st.dataframe(df, use_container_width=True)
        st.area_chart(df.set_index('date'))

elif selected == "Cross-Asset Correlation":
    st.header("🔗 Multi-Asset Correlations")
    df = run_query("""
        SELECT 
            CAST(s.date AS DATE) as Date, 
            s.close_price as SP500, 
            o.price as Oil_Price, 
            c.price_inr/100000 as BTC_Lakhs
        FROM stock_processed_data s
        JOIN oil_processed_prices o ON DATE(s.date) = DATE(o.date)
        JOIN crypto_historical_prices c ON DATE(s.date) = DATE(c.date)
        WHERE s.source = '^GSPC' AND c.coin_id = 'bitcoin'
        ORDER BY Date DESC LIMIT 50""")
    st.write("### Comparison Table")
    st.dataframe(df, use_container_width=True)
    st.write("### Normalized Trend Correlation")
    st.plotly_chart(px.line(df, x='Date', y=['SP500', 'Oil_Price', 'BTC_Lakhs']))
