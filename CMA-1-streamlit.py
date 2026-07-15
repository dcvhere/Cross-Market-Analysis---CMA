import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. SET_PAGE_CONFIG MUST BE THE VERY FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Market Analysis", layout="wide")

st.title("Cross-Market Analysis: Crypto, Oil & Stocks with SQL")
st.subheader("Cross-Market Analysis Dashboard")
st.write("Data Preview")

# 2. DATABASE CONNECTION
# TODO: Retrieve your exact TiDB connection string from your Jupyter Notebook.
# Update the placeholder below with your actual username, password, and database_name.
engine = create_engine(
    "mysql+pymysql://<username>:<password>@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/<database_name>",
    connect_args={"ssl": {"ssl": True}}
)

# 3. NAVIGATION
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
        # Parameterized queries prevent SQL injection and format errors
        btc_avg = pd.read_sql(
            """
            SELECT AVG(price_usd) AS avg_bitcoin
            FROM crypto_prices
            WHERE coin_id = 'bitcoin'
              AND date BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(btc_avg)

    if st.button("Oil Average Price Analysis"):
        oil_avg = pd.read_sql(
            """
            SELECT AVG(price_usd) AS avg_oil_price 
            FROM oil_prices 
            WHERE date BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(oil_avg)

elif page == "Query Analysis":
    st.title("Query Analysis")
    st.write("Cross-Market comparisons")
    
    if st.button("Crypto Price trend vs Nifty (^NSEI)"):
        # Using LEFT JOIN on the proper tables defined in your schema
        sql = """
        SELECT
            c.date,
            c.coin_id AS crypto_id,
            AVG(c.price_usd) AS crypto_price,
            s.close AS nifty_close_price
        FROM crypto_prices c
        LEFT JOIN stock_prices s 
            ON c.date = s.date AND s.ticker = '^NSEI'
        WHERE c.coin_id IN ('bitcoin', 'ethereum', 'tether')
        GROUP BY c.date, c.coin_id, s.close
        """
        df = pd.read_sql(sql, engine)

        st.subheader("Query Result")
        st.dataframe(df)

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
            """
            SELECT
                date,
                price_usd AS current_price
            FROM crypto_prices
            WHERE coin_id = %s
              AND date BETWEEN %s AND %s
            ORDER BY date
            """,
            engine,
            params=(coin, start_date, end_date)
        )
        
        st.subheader("Query Result")
        st.dataframe(df)
        if not df.empty:
            st.line_chart(data=df, x='date', y='current_price')
