import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# CRITICAL: set_page_config MUST be the very first Streamlit command!
st.set_page_config(page_title="Market Analysis", layout="wide")

st.title("Cross-Market Analysis: Crypto, Oil & Stocks with SQL")
st.subheader("Cross-Market Analysis Dashboard")

# Secure Database connection reading from Streamlit Secrets
# Local fallback is provided if you want to run it locally with secrets
try:
    db_username = st.secrets["connections"]["tidb"]["username"]
    db_password = st.secrets["connections"]["tidb"]["password"]
    db_host = st.secrets["connections"]["tidb"]["host"]
    db_port = st.secrets["connections"]["tidb"]["port"]
    db_name = st.secrets["connections"]["tidb"]["database"]
except KeyError:
    # Local fallback/hardcoded backup for testing (highly recommended to use Secrets!)
    db_username = "db_username"
    db_password = "db_password"
    db_host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    db_port = 4000
    db_name = "literacy_gdp_analysis"

# Build engine with SSL requirements for secure TiDB Cloud handshake
connection_uri = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(
    connection_uri,
    connect_args={"ssl": {"ssl": True}}
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Data Exploration",
        "Query Analysis",
        "Insights"
    ]
)

if page == "Data Exploration":
    st.title("Data Exploration")
    st.write("Select Date Range")

    start_date = st.date_input("Start date")
    end_date = st.date_input("End date")

    if st.button("Bitcoin Average Price Analysis"):
        # Fix: Wrap query in text() and use dict mapping parameters to prevent SQL syntax crashes
        query = text("""
            SELECT AVG(current_price) AS avg_bitcoin
            FROM api_data
            WHERE id = 'bitcoin'
              AND DATE(last_updated) BETWEEN :start_date AND :end_date
        """)
        
        try:
            with engine.connect() as conn:
                btc_avg = pd.read_sql(
                    query,
                    conn,
                    params={"start_date": start_date, "end_date": end_date}
                )
            st.dataframe(btc_avg)
        except Exception as e:
            st.error(f"Database Error: {e}")

    if st.button("Oil Average Price Analysis"):
        query = text("""
            SELECT AVG(price) AS avg_oil
            FROM stock_data
            WHERE source = 'CL=F'
              AND Date BETWEEN :start_date AND :end_date
        """)
        try:
            with engine.connect() as conn:
                oil_avg = pd.read_sql(
                    query,
                    conn,
                    params={"start_date": start_date, "end_date": end_date}
                )
            st.dataframe(oil_avg)
        except Exception as e:
            st.error(f"Database Error: {e}")

elif page == "Query Analysis":
    st.title("Query Analysis Insights")
    
    query_option = st.selectbox(
        "Select a Pre-defined Analysis Query",
        [
            "1. Crypto price trend vs Oil Price",
            "2. S&P 500 Performance vs Crypto",
            "3. Gold/Nifty Correlation Analysis",
            "4. Compare Bitcoin vs Ethereum Volatility",
            "5. Crypto performance against Stock indices"
        ]
    )

    # Let's map queries to matching database structures
    if query_option == "1. Crypto price trend vs Oil Price":
        sql = text("""
            SELECT 
                DATE(c.last_updated) AS date,
                c.id AS crypto_id,
                AVG(c.current_price) AS crypto_price,
                AVG(o.price) AS oil_price
            FROM 
                top_3_coin c
            LEFT JOIN 
                stock_data o ON DATE(c.last_updated) = o.Date AND o.source = 'CL=F'
            GROUP BY 
                DATE(c.last_updated), c.id
        """)
    elif query_option == "2. S&P 500 Performance vs Crypto":
        sql = text("""
            SELECT 
                DATE(c.last_updated) AS date,
                c.id AS crypto_id,
                AVG(c.current_price) AS crypto_price,
                s.close AS sp500_price
            FROM 
                top_3_coin c
            LEFT JOIN 
                stock_data s ON DATE(c.last_updated) = s.Date AND s.source = '^GSPC'
            GROUP BY 
                DATE(c.last_updated), c.id, s.close
        """)
    elif query_option == "3. Gold/Nifty Correlation Analysis":
        sql = text("""
            SELECT 
                DATE(c.last_updated) AS date,
                c.id AS crypto_id,
                AVG(c.current_price) AS crypto_price,
                s.close AS nifty_close_price
            FROM 
                top_3_coin c
            LEFT JOIN 
                stock_data s ON DATE(c.last_updated) = s.Date AND s.source = '^NSEI'
            GROUP BY 
                DATE(c.last_updated), c.id, s.close
        """)
    else:
        # Fallback queries matching table architectures
        sql = text("""
            SELECT DATE(last_updated) AS date, id, AVG(current_price) as avg_price 
            FROM top_3_coin 
            GROUP BY DATE(last_updated), id 
            LIMIT 100
        """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        st.subheader("Query Result")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Database Query Failed: {e}")

elif page == "Insights":
    st.title("Insights on Top 3 Cryptocurrencies")
    st.write("Select a coin and date range to view price trends")

    coin = st.selectbox(
        "Select Coin",
        ("bitcoin", "ethereum", "tether")
    )

    start_date = st.date_input("Start date", key="p3_start")
    end_date = st.date_input("End date", key="p3_end")

    if st.button("View Price Trend"):
        query = text("""
            SELECT
                DATE(last_updated) AS date,
                current_price
            FROM api_data
            WHERE id = :coin
              AND DATE(last_updated) BETWEEN :start_date AND :end_date
            ORDER BY date
        """)
        
        try:
            with engine.connect() as conn:
                df = pd.read_sql(
                    query,
                    conn,
                    params={"coin": coin, "start_date": start_date, "end_date": end_date}
                )
            
            if not df.empty:
                st.write(f"### Price Trend for {coin.capitalize()}")
                st.line_chart(df.set_index("date"))
                st.dataframe(df)
            else:
                st.warning("No data found for this specific asset or date range.")
        except Exception as e:
            st.error(f"Database query failed: {e}")
