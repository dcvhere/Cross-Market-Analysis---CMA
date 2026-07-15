import streamlit as st

st.title("Cross-Market Analysis: Crypto, Oil & Stocks with SQL")

import pandas as pd
from sqlalchemy import create_engine

st.subheader("Cross-Market Analysis Dashboard")

st.write("Data Preview")

# Database connection
engine = create_engine(
    "mysql+pymysql://iatXFmXH7cy5Eyv.root:ndGScqvE2B1dpP9p@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/market_analysis",
    connect_args={"ssl": {"ssl": True}}
)

st.set_page_config(page_title="Market Analysis", layout="wide")

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

    if st.button("^GSPC Average Price Analysis"):
        sp500_avg = pd.read_sql(
            """
            SELECT AVG(close) AS avg_sp500_price
            FROM stock_data
            WHERE source = '^GSPC'
              AND DATE(date) BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(sp500_avg)

    if st.button("^NSEI Average Price Analysis"):
        nifty_avg = pd.read_sql(
            """
            SELECT AVG(close) AS avg_nifty_price
            FROM stock_data
            WHERE source = '^NSEI'
              AND DATE(date) BETWEEN %s AND %s
            """,
            engine,
            params=(start_date, end_date)
        )
        st.write(nifty_avg)

    snapshot_df = pd.read_sql(
        """
        SELECT
            DATE(c.last_updated) AS date,
            c.current_price AS bitcoin_price,
            o.price AS oil_price,
            sp.close AS sp500_close,
            ni.close AS nifty_close
        FROM api_data c
        LEFT JOIN oil_data o
            ON DATE(c.last_updated) = o.date
        LEFT JOIN stock_data sp
            ON DATE(c.last_updated) = sp.date
           AND sp.source = '^GSPC'
        LEFT JOIN stock_data ni
            ON DATE(c.last_updated) = ni.date
           AND ni.source = '^NSEI'
        WHERE c.id = 'bitcoin'
        ORDER BY date
        """,
        engine
    )

    st.subheader("Daily market snapshot table")
    st.dataframe(snapshot_df)


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
        if query_option == "Bitcoin Average Price":
            sql = """
                SELECT AVG(current_price) AS avg_bitcoin_price
                FROM api_data
                WHERE id = 'bitcoin'
            """

        elif query_option == "S&P 500 Average Closing Price":
            sql = """
                SELECT AVG(close) AS avg_sp500_price
                FROM stock_data
                WHERE source = '^GSPC'
            """
        elif query_option == "NIFTY Average Closing Price":
            sql = """
                SELECT AVG(close) AS avg_nifty_price
                FROM stock_data
                WHERE source = '^NSEI'
            """

        elif query_option == "Compare Bitcoin vs Oil average price in 2025.":
            sql = "select avg(b.current_price) as avg_bitcoin, avg(o.price) as avg_oil from api_data b left join oil_data o on o.price = b.current_price and b.id = 'bitcoin' where year(o.date) = 2025"

        elif query_option == "Bitcoin vs S&P 500 (Daily)":
            sql = """
                SELECT
                    DATE(c.last_updated) AS date,
                    c.current_price AS bitcoin_price,
                    s.close AS sp500_close
                FROM api_data c
                LEFT JOIN stock_data s
                    ON DATE(c.last_updated) = s.date
                   AND s.source = '^GSPC'
                WHERE c.id = 'bitcoin'
                ORDER BY date
            """
        elif query_option == "Find the top 3 cryptocurrencies by market cap": 
            sql = "SELECT * FROM api_data order by market_cap desc Limit 3"

        elif query_option == "Get coins that are within 10 percent of their all-time-high (ATH).":
            sql = "select * from api_data where (current_price/ath)*100 > 90 "   

        elif query_option == "Find the highest daily price of Bitcoin in the last 365 days.":
            sql = "select max(current_price) as highest_daily_price from api_data where id = 'bitcoin' and last_updated >=now() - interval 365 day "
               
        elif query_option == "Show oil prices during COVID crash (March-April 2020).":
            sql = "select price, date from oil_data where year(date) = 2020 AND month(date) in (3,4)"

        elif query_option == "List all coins where circulating supply exceeds 90 percent of total supply.":    
            sql = "SELECT * from api_data where (circulating_supply * 100 / total_supply) > 90"

        elif query_option == "Find the average market cap rank of coins with volume above $1B.":
            sql = "select avg(market_cap_rank) as Avg_market_cap_rank from api_data where total_volume > 1000000000"

        elif query_option == "Get the most recently updated coin.":
            sql = "select * from api_data order by last_updated desc limit 1"

        elif query_option == "Calculate the average daily price of Ethereum in the past 1 year.":
            sql = """SELECT
                    DATE(last_updated) AS price_date,
                    AVG(current_price) AS daily_avg_price
                    FROM api_data
                    WHERE
                    symblol = 'eth'
                    AND last_updated >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                    GROUP BY DATE(last_updated)
                    ORDER BY price_date"""
            
        elif query_option == "Show the daily price trend of Bitcoin in Feb 2026.":
            sql = "select * from api_data where id = 'bitcoin' and year(last_updated) = 2026 and month(last_updated) = 2"    

        elif query_option == "Find the coin with the highest average price over 1 year.":
            sql = "select symblol, name, avg(current_price) as avg_price_1y from api_data where last_updated >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) group by symblol, name order by avg_price_1y DESC"

        elif query_option == "Get the percentage change in Bitcoin price during Feb 2026":
            sql = "select last_updated, current_price, (current_price - LAG(current_price) OVER (ORDER BY last_updated)) / LAG(current_price) OVER (ORDER BY last_updated) * 100 AS percent_change from api_data where id = 'bitcoin'"

        elif query_option == "Find the highest oil price in the last 5 years.":
            sql = "select max(price) as highest_oil_price from oil_data where date >= now() - interval 5 year"

        elif query_option == "Get the average oil price per year.":
            sql = "select avg(price) from oil_data where date>=now() - interval 1 year"

        elif query_option == "Find the lowest price of oil in the last 10 years.":
            sql = "select avg(price) as oil_avg_price from oil_data where date>=now() - interval 10 year"

        elif query_option == "Calculate the volatility of oil prices (max-min difference per year).":     
            sql = "select max(price) - min(price) as volatility from oil_data where date>=now() - interval 1 year"

        elif query_option == "Get all stock prices for ^IXIC ticker":
            sql = "select close, source from stock_data where source = '^IXIC'" 

        elif query_option == "Find the highest closing price for NASDAQ (^IXIC)":
            sql = "select max(close) as highest_close_price_NASDAQ from stock_data where source = '^IXIC'"       

        elif query_option == "List top 5 days with highest price difference for S&P 500 (^GSPC)":
            sql = "SELECT Date, (High - Low) AS price_difference FROM stock_data WHERE source = '^GSPC' ORDER BY price_difference DESC LIMIT 5"

        elif query_option == "Get monthly average closing price for each ticker":
            sql = "select source, avg(close) as avg_close_price from stock_data group by source"

        elif query_option == "Get average trading volume of NSEI in 2024":
            sql = "select avg(Volume) as avg_trading_volume_NSEI from stock_data where source ='^NSEI' and year(Date) = 2024"

        elif query_option == "Check if Bitcoin moves with ^GSPC.":
            sql = "SELECT DATE(b.last_updated) AS date, b.current_price AS bitcoin_price, s.close AS stock_close_price FROM api_data b JOIN stock_data s ON DATE(b.last_updated) = DATE(s.Date) WHERE b.id = 'bitcoin' AND s.source = '^GSPC' "

        elif query_option == "Find days when oil price spiked and compare with Bitcoin price change during Feb 2026":
            sql = "select date(b.last_updated), o.price as oil_price, b.current_price as bitcoin_price from oil_data o join api_data b on year(b.last_updated)=year(o.date) and month(b.last_updated)=month(o.date) where b.id = 'bitcoin'"
       
        elif query_option == "Compare stock prices (^GSPC) with crude oil prices on the same dates":
            sql = "select s.date as date,s.source, s.close as GSPC_price , o.price as oil_price from stock_data s join oil_data o on o.date = s.date where source = '^GSPC'"

        elif query_option == "Correlate Bitcoin closing price with crude oil closing price (same date)":
            sql = "select o.date as common_date, o.price as oil_price, b.current_price as bitcoin_price from oil_data o join api_data b on date(b.last_updated)=o.date where id='bitcoin'"

        elif query_option == "Compare NASDAQ (^IXIC) with Ethereum price trends":
            sql = "select date(e.last_updated) as date, e.current_price as ethereum_price, s.close as IXIC_price from api_data e left join stock_data s on date(e.last_updated) =s.Date and s.source = '^IXIC' where e.id = 'ethereum'"

        elif query_option == "Join top 3 crypto coins with stock indices for 2025":
            sql = "select date(c.last_updated) as date, c.id as crypto_id, avg(c.current_price) as crypto_price, s.source as source,s.close as stock_price from api_data c join stock_data s on  s.date = date(c.last_updated) where year(c.last_updated) = 2026 group by date(c.last_updated), c.id, s.source, s.close order by crypto_price desc"

        elif query_option == "Multi-join: stock prices, oil prices, and Bitcoin prices for daily comparison":
            sql = "select c.id, c.current_price, s.source, s.close, o.price from api_data c left join stock_data s on s.date = date(c.last_updated) left join oil_data o on o.date = date(c.last_updated) where c.id = 'bitcoin' "

        elif query_option == "Compare top 3 coins daily price trend vs Nifty (^NSEI).":
            sql = """
        SELECT
        DATE(c.last_updated) AS date,
        c.id AS crypto_id,
        avg(c.current_price) AS crypto_price,
        s.close AS nifty_close_price
        FROM
        top_3_coin c
        LEFT JOIN
        stock_data s ON DATE(c.last_updated) = s.Date AND s.source = '^NSEI'
        GROUP BY
        DATE(c.last_updated), c.id, s.close
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

        if df.empty:
            st.warning("No data available for the selected coin and date range.")

        else:

            # --- Table ---
            st.subheader("Daily Price Table")
            st.dataframe(df)    
