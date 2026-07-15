import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import textwrap

# ==========================================
# 1. SET PAGE CONFIG (Must be the very first Streamlit command)
# ==========================================
st.set_page_config(page_title="Market Analysis Dashboard", layout="wide")

st.title("Cross-Market Analysis: Crypto, Oil & Stocks with SQL")
st.subheader("Cross-Market Analysis Dashboard")
st.write("Data Preview")

# ==========================================
# 2. DATABASE CONNECTION (Using st.cache_resource for speed)
# ==========================================
@st.cache_resource
def init_connection():
    return create_engine(
        "mysql+pymysql://iatXFmXH7cy5Eyv.root:ndGScqvE2B1dpP9p@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/market_analysis",
        connect_args={"ssl": {"ssl": True}},
        pool_pre_ping=True,  # Automatically checks and resets stale connections
        pool_recycle=3600
    )

engine = init_connection()

# Helper function to execute queries safely and prevent transaction locking
def safe_read_sql(sql, engine, params=None):
    with engine.connect() as conn:
        try:
            # Execute within a localized transaction context
            with conn.begin():
                return pd.read_sql(sql, conn, params=params)
        except Exception as e:
            # The context manager automatically rolls back the transaction here
            raise e

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
page = st.sidebar.radio(
    "Navigation",
    [
        "Data Exploration",
        "Query Analysis",
        "Insights"
    ]
)

# ==========================================
# PAGE 1: DATA EXPLORATION
# ==========================================
if page == "Data Exploration":
    st.title("Data Exploration")
    st.write("Select a date range to filter the market averages.")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", pd.to_datetime("2024-01-01"))
    with col2:
        end_date = st.date_input("End date", pd.to_datetime("today"))

    st.write("---")
    
    if st.button("Calculate Market Averages"):
        col_btc, col_oil, col_sp500, col_nifty = st.columns(4)
        
        try:
            # Bitcoin Avg
            btc_df = safe_read_sql(
                """SELECT AVG(current_price) AS avg_bitcoin FROM api_data 
                   WHERE id = 'bitcoin' AND DATE(last_updated) BETWEEN %s AND %s""",
                engine, params=(start_date, end_date)
            )
            btc_avg = btc_df.iloc[0, 0] if not btc_df.empty else None
            col_btc.metric("Bitcoin Avg Price", f"₹{btc_avg:,.2f}" if pd.notnull(btc_avg) else "N/A")

            # Oil Avg
            oil_df = safe_read_sql(
                """SELECT AVG(Price) AS avg_oil_price FROM oil_data 
                   WHERE DATE(Date) BETWEEN %s AND %s""",
                engine, params=(start_date, end_date)
            )
            oil_avg = oil_df.iloc[0, 0] if not oil_df.empty else None
            col_oil.metric("Crude Oil Avg", f"${oil_avg:,.2f}" if pd.notnull(oil_avg) else "N/A")

            # S&P 500 Avg
            sp500_df = safe_read_sql(
                """SELECT AVG(Close) AS avg_sp500_price FROM stock_data 
                   WHERE source = '^GSPC' AND DATE(Date) BETWEEN %s AND %s""",
                engine, params=(start_date, end_date)
            )
            sp500_avg = sp500_df.iloc[0, 0] if not sp500_df.empty else None
            col_sp500.metric("S&P 500 Avg", f"${sp500_avg:,.2f}" if pd.notnull(sp500_avg) else "N/A")

            # NIFTY Avg
            nifty_df = safe_read_sql(
                """SELECT AVG(Close) AS avg_nifty_price FROM stock_data 
                   WHERE source = '^NSEI' AND DATE(Date) BETWEEN %s AND %s""",
                engine, params=(start_date, end_date)
            )
            nifty_avg = nifty_df.iloc[0, 0] if not nifty_df.empty else None
            col_nifty.metric("NIFTY 50 Avg", f"₹{nifty_avg:,.2f}" if pd.notnull(nifty_avg) else "N/A")
        except Exception as e:
            st.error(f"Error computing averages: {e}")

    st.write("---")
    st.subheader("Daily Market Snapshot Table")
    try:
        snapshot_df = safe_read_sql(
            """
            SELECT
                DATE(c.last_updated) AS date,
                c.current_price AS bitcoin_price,
                o.Price AS oil_price,
                sp.Close AS sp500_close,
                ni.Close AS nifty_close
            FROM api_data c
            LEFT JOIN oil_data o
                ON DATE(c.last_updated) = DATE(o.Date)
            LEFT JOIN stock_data sp
                ON DATE(c.last_updated) = DATE(sp.Date) AND sp.source = '^GSPC'
            LEFT JOIN stock_data ni
                ON DATE(c.last_updated) = DATE(ni.Date) AND ni.source = '^NSEI'
            WHERE c.id = 'bitcoin'
            ORDER BY date DESC
            LIMIT 100
            """,
            engine
        )
        st.dataframe(snapshot_df, use_container_width=True)
    except Exception as e:
        st.error(f"Snapshot Query Failed: {e}")

# ==========================================
# PAGE 2: QUERY ANALYSIS
# ==========================================
elif page == "Query Analysis":
    st.title("Query Analysis")
    st.write("Select a predefined SQL query and click **Run Query**")
    
    query_option = st.selectbox(
        "Choose a query",
        (
            "Bitcoin Average Price",
            "S&P 500 Average Closing Price",
            "NIFTY Average Closing Price",
            "Compare Bitcoin vs Oil average price in 2025.",
            "Bitcoin vs S&P 500 (Daily)",
            "Find the top 3 cryptocurrencies by market cap",
            "Get coins that are within 10 percent of their all-time-high (ATH).",
            "Find the highest daily price of Bitcoin in the last 365 days.",
            "Show oil prices during COVID crash (March-April 2020).",
            "List all coins where circulating supply exceeds 90 percent of total supply.",
            "Find the average market cap rank of coins with volume above $1B.",
            "Get the most recently updated coin.",
            "Calculate the average daily price of Ethereum in the past 1 year.",
            "Show the daily price trend of Bitcoin in Feb 2026.",
            "Find the coin with the highest average price over 1 year.",
            "Get the percentage change in Bitcoin price during Feb 2026",
            "Find the highest oil price in the last 5 years.",
            "Get the average oil price per year.",
            "Find the lowest price of oil in the last 10 years.",
            "Calculate the volatility of oil prices (max-min difference per year).",
            "Get all stock prices for ^IXIC ticker",
            "Find the highest closing price for NASDAQ (^IXIC)",
            "List top 5 days with highest price difference for S&P 500 (^GSPC)",
            "Get monthly average closing price for each ticker",
            "Get average trading volume of NSEI in 2024",
            "Check if Bitcoin moves with ^GSPC.",
            "Find days when oil price spiked and compare with Bitcoin price change during Feb 2026",
            "Compare stock prices (^GSPC) with crude oil prices on the same dates",
            "Correlate Bitcoin closing price with crude oil closing price (same date)",
            "Compare NASDAQ (^IXIC) with Ethereum price trends",
            "Join top 3 crypto coins with stock indices for 2025",
            "Multi-join: stock prices, oil prices, and Bitcoin prices for daily comparison",
            "Compare top 3 coins daily price trend vs Nifty (^NSEI)."
        )
    )
    
    if st.button("Run Query"):
        sql = ""
        if query_option == "Bitcoin Average Price":
            sql = "SELECT AVG(current_price) AS avg_bitcoin_price FROM api_data WHERE id = 'bitcoin'"
        elif query_option == "S&P 500 Average Closing Price":
            sql = "SELECT AVG(Close) AS avg_sp500_price FROM stock_data WHERE source = '^GSPC'"
        elif query_option == "NIFTY Average Closing Price":
            sql = "SELECT AVG(Close) AS avg_nifty_price FROM stock_data WHERE source = '^NSEI'"
        elif query_option == "Compare Bitcoin vs Oil average price in 2025.":
            sql = "select avg(b.current_price) as avg_bitcoin, avg(o.Price) as avg_oil from api_data b left join oil_data o on o.Price = b.current_price and b.id = 'bitcoin' where year(o.Date) = 2025"
        elif query_option == "Bitcoin vs S&P 500 (Daily)":
            sql = "SELECT DATE(c.last_updated) AS date, c.current_price AS bitcoin_price, s.Close AS sp500_close FROM api_data c LEFT JOIN stock_data s ON DATE(c.last_updated) = DATE(s.Date) AND s.source = '^GSPC' WHERE c.id = 'bitcoin' ORDER BY date"
        elif query_option == "Find the top 3 cryptocurrencies by market cap": 
            sql = "SELECT * FROM api_data order by market_cap desc Limit 3"
        elif query_option == "Get coins that are within 10 percent of their all-time-high (ATH).":
            sql = "select * from api_data where (current_price/ath)*100 > 90 "   
        elif query_option == "Find the highest daily price of Bitcoin in the last 365 days.":
            sql = "select max(current_price) as highest_daily_price from api_data where id = 'bitcoin' and last_updated >=now() - interval 365 day "
        elif query_option == "Show oil prices during COVID crash (March-April 2020).":
            sql = "select Price, Date from oil_data where year(Date) = 2020 AND month(Date) in (3,4)"
        elif query_option == "List all coins where circulating supply exceeds 90 percent of total supply.":    
            sql = "SELECT * from api_data where (circulating_supply * 100 / total_supply) > 90"
        elif query_option == "Find the average market cap rank of coins with volume above $1B.":
            sql = "select avg(market_cap_rank) as Avg_market_cap_rank from api_data where total_volume > 1000000000"
        elif query_option == "Get the most recently updated coin.":
            sql = "select * from api_data order by last_updated desc limit 1"
        elif query_option == "Calculate the average daily price of Ethereum in the past 1 year.":
            sql = "SELECT DATE(last_updated) AS price_date, AVG(current_price) AS daily_avg_price FROM api_data WHERE symbol = 'eth' AND last_updated >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY DATE(last_updated) ORDER BY price_date"
        elif query_option == "Show the daily price trend of Bitcoin in Feb 2026.":
            sql = "select * from api_data where id = 'bitcoin' and year(last_updated) = 2026 and month(last_updated) = 2"    
        elif query_option == "Find the coin with the highest average price over 1 year.":
            sql = "select symbol, name, avg(current_price) as avg_price_1y from api_data where last_updated >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) group by symbol, name order by avg_price_1y DESC"
        elif query_option == "Get the percentage change in Bitcoin price during Feb 2026":
            sql = "select last_updated, current_price, (current_price - LAG(current_price) OVER (ORDER BY last_updated)) / LAG(current_price) OVER (ORDER BY last_updated) * 100 AS percent_change from api_data where id = 'bitcoin'"
        elif query_option == "Find the highest oil price in the last 5 years.":
            sql = "select max(Price) as highest_oil_price from oil_data where Date >= now() - interval 5 year"
        elif query_option == "Get the average oil price per year.":
            sql = "select avg(Price) from oil_data where Date>=now() - interval 1 year"
        elif query_option == "Find the lowest price of oil in the last 10 years.":
            sql = "select min(Price) as lowest_oil_price from oil_data where Date>=now() - interval 10 year"
        elif query_option == "Calculate the volatility of oil prices (max-min difference per year).":     
            sql = "select max(Price) - min(Price) as volatility from oil_data where Date>=now() - interval 1 year"
        elif query_option == "Get all stock prices for ^IXIC ticker":
            sql = "select Close, source from stock_data where source = '^IXIC'" 
        elif query_option == "Find the highest closing price for NASDAQ (^IXIC)":
            sql = "select max(Close) as highest_close_price_NASDAQ from stock_data where source = '^IXIC'"       
        elif query_option == "List top 5 days with highest price difference for S&P 500 (^GSPC)":
            sql = "SELECT Date, (High - Low) AS price_difference FROM stock_data WHERE source = '^GSPC' ORDER BY price_difference DESC LIMIT 5"
        elif query_option == "Get monthly average closing price for each ticker":
            sql = "select source, avg(Close) as avg_close_price from stock_data group by source"
        elif query_option == "Get average trading volume of NSEI in 2024":
            sql = "select avg(Volume) as avg_trading_volume_NSEI from stock_data where source ='^NSEI' and year(Date) = 2024"
        elif query_option == "Check if Bitcoin moves with ^GSPC.":
            sql = "SELECT DATE(b.last_updated) AS date, b.current_price AS bitcoin_price, s.Close AS stock_close_price FROM api_data b JOIN stock_data s ON DATE(b.last_updated) = DATE(s.Date) WHERE b.id = 'bitcoin' AND s.source = '^GSPC' "
        elif query_option == "Find days when oil price spiked and compare with Bitcoin price change during Feb 2026":
            sql = "select date(b.last_updated), o.Price as oil_price, b.current_price as bitcoin_price from oil_data o join api_data b on year(b.last_updated)=year(o.Date) and month(b.last_updated)=month(o.Date) where b.id = 'bitcoin'"
        elif query_option == "Compare stock prices (^GSPC) with crude oil prices on the same dates":
            sql = "select s.Date as date, s.source, s.Close as GSPC_price , o.Price as oil_price from stock_data s join oil_data o on o.Date = s.Date where source = '^GSPC'"
        elif query_option == "Correlate Bitcoin closing price with crude oil closing price (same date)":
            sql = "select o.Date as common_date, o.Price as oil_price, b.current_price as bitcoin_price from oil_data o join api_data b on date(b.last_updated)=o.Date where id='bitcoin'"
        elif query_option == "Compare NASDAQ (^IXIC) with Ethereum price trends":
            sql = "select date(e.last_updated) as date, e.current_price as ethereum_price, s.Close as IXIC_price from api_data e left join stock_data s on date(e.last_updated) = DATE(s.Date) and s.source = '^IXIC' where e.id = 'ethereum'"
        elif query_option == "Join top 3 crypto coins with stock indices for 2025":
            sql = "select date(c.last_updated) as date, c.id as crypto_id, avg(c.current_price) as crypto_price, s.source as source, s.Close as stock_price from api_data c join stock_data s on DATE(s.Date) = date(c.last_updated) where year(c.last_updated) = 2025 group by date(c.last_updated), c.id, s.source, s.Close order by crypto_price desc"
        elif query_option == "Multi-join: stock prices, oil prices, and Bitcoin prices for daily comparison":
            sql = "select c.id, c.current_price, s.source, s.Close, o.Price from api_data c left join stock_data s on DATE(s.Date) = date(c.last_updated) left join oil_data o on o.Date = date(c.last_updated) where c.id = 'bitcoin' "
        elif query_option == "Compare top 3 coins daily price trend vs Nifty (^NSEI).":
            sql = "SELECT DATE(c.last_updated) AS date, c.id AS crypto_id, avg(c.current_price) AS crypto_price, s.Close AS nifty_close_price FROM top_3_coin c LEFT JOIN stock_data s ON DATE(c.last_updated) = DATE(s.Date) AND s.source = '^NSEI' GROUP BY DATE(c.last_updated), c.id, s.Close"

        try:
            df = safe_read_sql(sql, engine)
            st.subheader("Query Result")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            # Displays the real SQL error clearly without bricking the rest of the application
            st.error("🚨 Database Query Execution Failed!")
            st.code(textwrap.dedent(str(e)), language="text")

# ==========================================
# PAGE 3: INSIGHTS
# ==========================================
elif page == "Insights":
    st.title("Insights on Top 3 Cryptocurrencies")
    st.write("Select a coin and date range to view price trends")

    coin = st.selectbox(
        "Select Coin",
        ("bitcoin", "ethereum", "tether")
    )

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", key="p3_start", value=pd.to_datetime("2024-01-01"))
    with col2:
        end_date = st.date_input("End date", key="p3_end", value=pd.to_datetime("today"))

    if st.button("View Price Trend"):
        try:
            df = safe_read_sql(
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

            if df.empty:
                st.warning("No data available for the selected coin and date range.")
            else:
                st.subheader(f"Price Trend Chart: {coin.capitalize()}")
                st.line_chart(data=df.set_index('date'), y='current_price')
                
                st.subheader("Daily Price Table")
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to fetch insights data: {e}")
