import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. SET_PAGE_CONFIG MUST BE THE VERY FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Market Analysis", layout="wide")

# Now you can use other Streamlit commands
st.title("Cross-Market Analysis: Crypto, Oil & Stocks with SQL")
st.subheader("Cross-Market Analysis Dashboard")
st.write("Data Preview")

# 2. DATABASE CONNECTION
# TODO: Replace 'db_username', 'db_password', and 'literacy_gdp_analysis' with your actual TiDB credentials and database name.
engine = create_engine(
    "mysql+pymysql://db_username:db_password@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/literacy_gdp_analysis",
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
        # We use standard parameterized queries here to prevent SQL injection
        btc_avg = pd.read_sql(
            """
            SELECT AVG(current_price) AS avg_bitcoin
            FROM api_data
            WHERE id = 'bitcoin'
              AND DATE(last_updated) BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(btc_avg)

    if st.button("Oil Average Price Analysis"):
        oil_avg = pd.read_sql(
            """
            SELECT AVG(price) AS avg_oil_price 
            FROM oil_data 
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
        FROM top_3_coin c
        LEFT JOIN stock_data s 
            ON DATE(c.last_updated) = s.Date AND s.source = '^NSEI'
        GROUP BY DATE(c.last_updated), c.id, s.close
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
                DATE(last_updated) AS date,
                current_price
            FROM api_data
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
