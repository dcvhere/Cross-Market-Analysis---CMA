
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from sqlalchemy import create_engine, text
import pymysql # Required by sqlalchemy for mysql+pymysql

# Database connection details (re-using from the main notebook)
DB_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
DB_USER = "iatXFmXH7cy5Eyv.root"
DB_PASSWORD = "ndGScqvE2B1dpP9p"
DB_PORT = 4000
DB_NAME = "market_data_db" # Centralized database name

# Create a SQLAlchemy engine for persistent connections to the specific database
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, connect_args={"ssl": {"ssl": True}})

st.set_page_config(layout="wide")
st.title("Cross-Market Analysis: Crypto, Oil & Stocks")
st.subheader("Interactive Dashboard")

with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["Home", "Cryptocurrency", "Oil Prices", "Stock Market"],
        icons=["house", "currency-bitcoin", "graph-up-arrow", "building-columns"],
        default_index=0
    )

if selected == "Home":
    st.write("Welcome to the Cross-Market Analysis Dashboard!")
    st.write("Use the sidebar to navigate through different market data.")
    st.image("https://www.tidb.cloud/blog/tidb-vs-mysql-database/images/MySQL%20to%20TiDB.png", use_column_width=True)

elif selected == "Cryptocurrency":
    st.header("Cryptocurrency Data")
    crypto_option = st.selectbox(
        "Select data view:",
        (
            "Current Market Data",
            "Top 5 by Market Cap",
            "Circulating Supply Ratio (>90%)"
        )
    )

    if crypto_option == "Current Market Data":
        st.subheader("All Current Cryptocurrency Market Data")
        try:
            df_crypto_current = pd.read_sql(text("SELECT * FROM crypto_current_market LIMIT 100"), engine)
            st.dataframe(df_crypto_current)
        except Exception as e:
            st.error(f"Error loading current crypto data: {e}")

    elif crypto_option == "Top 5 by Market Cap":
        st.subheader("Top 5 Cryptocurrencies by Market Cap")
        try:
            df_top_5_crypto = pd.read_sql(text("SELECT name, symbol, current_price, market_cap FROM crypto_processed_current ORDER BY market_cap DESC LIMIT 5"), engine)
            st.dataframe(df_top_5_crypto)
        except Exception as e:
            st.error(f"Error loading top 5 crypto by market cap: {e}")

    elif crypto_option == "Circulating Supply Ratio (>90%)":
        st.subheader("Cryptocurrencies with >90% Circulating Supply Ratio")
        try:
            df_high_supply_ratio = pd.read_sql(text("SELECT name, symbol, circulating_supply, total_supply FROM crypto_processed_current WHERE (circulating_supply * 100 / total_supply) > 90 LIMIT 10"), engine)
            st.dataframe(df_high_supply_ratio)
        except Exception as e:
            st.error(f"Error loading high circulating supply crypto: {e}")

elif selected == "Oil Prices":
    st.header("Crude Oil Prices (WTI)")
    oil_option = st.selectbox(
        "Select data view:",
        (
            "Raw Oil Prices",
            "Highest Price in Last 5 Years",
            "Average Annual Price"
        )
    )

    if oil_option == "Raw Oil Prices":
        st.subheader("Recent Raw Oil Prices")
        try:
            df_oil_raw = pd.read_sql(text("SELECT date, price FROM oil_prices ORDER BY date DESC LIMIT 100"), engine)
            st.dataframe(df_oil_raw)
        except Exception as e:
            st.error(f"Error loading raw oil prices: {e}")

    elif oil_option == "Highest Price in Last 5 Years":
        st.subheader("Highest Oil Price in the Last 5 Years")
        try:
            df_highest_oil = pd.read_sql(text("SELECT MAX(price) AS highest_oil_price_5y FROM oil_processed_prices WHERE date >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR)"), engine)
            st.dataframe(df_highest_oil)
        except Exception as e:
            st.error(f"Error loading highest oil price: {e}")

    elif oil_option == "Average Annual Price":
        st.subheader("Average Annual Oil Price (Last 5 Years)")
        try:
            df_avg_annual_oil = pd.read_sql(text("SELECT YEAR(date) AS year, AVG(price) AS average_price FROM oil_processed_prices GROUP BY year ORDER BY year DESC LIMIT 5"), engine)
            st.dataframe(df_avg_annual_oil)
        except Exception as e:
            st.error(f"Error loading average annual oil price: {e}")

elif selected == "Stock Market":
    st.header("Stock Market Data")
    stock_option = st.selectbox(
        "Select data view:",
        (
            "Recent Stock Prices",
            "Highest NASDAQ Close",
            "Top 5 S&P 500 Price Differences"
        )
    )

    if stock_option == "Recent Stock Prices":
        st.subheader("Recent Stock Prices")
        try:
            df_stocks_raw = pd.read_sql(text("SELECT date, source, close_price FROM stock_prices ORDER BY date DESC LIMIT 100"), engine)
            st.dataframe(df_stocks_raw)
        except Exception as e:
            st.error(f"Error loading raw stock prices: {e}")

    elif stock_option == "Highest NASDAQ Close":
        st.subheader("Highest Closing Price for NASDAQ")
        try:
            df_highest_nasdaq = pd.read_sql(text("SELECT MAX(close_price) AS highest_close_price_NASDAQ FROM stock_processed_data WHERE source = '^IXIC'"), engine)
            st.dataframe(df_highest_nasdaq)
        except Exception as e:
            st.error(f"Error loading highest NASDAQ close: {e}")

    elif stock_option == "Top 5 S&P 500 Price Differences":
        st.subheader("Top 5 Days with Highest Price Difference for S&P 500")
        try:
            df_sp500_diff = pd.read_sql(text("SELECT date, (high_price - low_price) AS price_difference FROM stock_processed_data WHERE source = '^GSPC' ORDER BY price_difference DESC LIMIT 5"), engine)
            st.dataframe(df_sp500_diff)
        except Exception as e:
            st.error(f"Error loading S&P 500 price differences: {e}")
