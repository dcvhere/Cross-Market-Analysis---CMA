import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# ==========================================
# 1. SET PAGE CONFIG (Must be the very first Streamlit command)
# ==========================================
st.set_page_config(page_title="Market Analysis", layout="wide")

# ==========================================
# 2. CONFIGURATION: EXTRACTED FROM IPYNB
# ==========================================
DB_USERNAME = "iatXFmXH7cy5Eyv.root"
DB_PASSWORD = "ndGScqvE2B1dpP9p"
DB_NAME     = "market_analysis" 

CRYPTO_TABLE = "api_data"       
OIL_TABLE    = "oil_data"       
TOP3_TABLE   = "top3_crypto"     
STOCK_TABLE  = "nifty_data"      
# ==========================================

st.title("Cross-Market Analysis: Crypto, Oil & Stocks with SQL")
st.subheader("Cross-Market Analysis Dashboard")
st.write("Data Preview")

# Database connection using extracted TiDB details
engine = create_engine(
    f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/{DB_NAME}",
    connect_args={"ssl": {"ssl": True}}
)

# Navigation
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
        btc_avg = pd.read_sql(
            f"""
            SELECT AVG(current_price) AS avg_bitcoin
            FROM {CRYPTO_TABLE}
            WHERE id = 'bitcoin'
              AND DATE(last_updated) BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(btc_avg)

    if st.button("Oil Average Price Analysis"):
        oil_avg = pd.read_sql(
            f"""
            SELECT AVG(price) AS avg_oil_price 
            FROM {OIL_TABLE} 
            WHERE DATE(date) BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(oil_avg)

elif page == "Query Analysis":
    st.title("Query Analysis")
    st.write("Cross-Market comparisons")
    
    if st.button("Crypto Price trend vs Nifty (^NSEI)"):
        sql = """
        SELECT
            DATE(c.last_updated) AS date,
            c.id AS crypto_id,
            avg(c.current_price) AS crypto_price,
            s.close AS nifty_close_price
        FROM top3_crypto c
        LEFT JOIN nifty_data s 
            ON DATE(c.last_updated) = s.Date AND s.source = '^NSEI'
        GROUP BY DATE(c.last_updated), c.id, s.close
        """
        
        # Adding error handling to bypass Streamlit Cloud's redaction
        try:
            df = pd.read_sql(sql, engine)
            st.subheader("Query Result")
            st.dataframe(df)
        except Exception as e:
            st.error("🚨 Database Query Failed!")
            st.error(f"Exact Error: {e}")
            st.write("Check your table and column names in TiDB based on the error above.")


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
        df = pd.read_sql(
            f"""
            SELECT
                DATE(last_updated) AS date,
                current_price
            FROM {CRYPTO_TABLE}
            WHERE id = %s
              AND DATE(last_updated) BETWEEN %s AND %s
            ORDER BY date
            """,
            engine,
            params=(coin, start_date, end_date)
        )
        
        st.subheader("Query Result")
        st.dataframe(df)
        if not df.empty:
            st.line_chart(data=df, x='date', y='current_price')
