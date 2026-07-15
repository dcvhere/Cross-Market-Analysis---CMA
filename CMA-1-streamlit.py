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
        # Pushed the default start date way back to ensure we catch your data
        start_date = st.date_input("Start date", key="p3_start", value=pd.to_datetime("2020-01-01"))
    with col2:
        end_date = st.date_input("End date", key="p3_end", value=pd.to_datetime("today"))

    if st.button("View Price Trend"):
        try:
            # Format dates to raw strings to guarantee they match TiDB safely
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # We use LEFT(last_updated, 10) to bypass MySQL's strict datetime rules 
            # and safely extract just the 'YYYY-MM-DD' from the API's ISO string.
            df = safe_read_sql(
                """
                SELECT
                    LEFT(last_updated, 10) AS date,
                    current_price
                FROM api_data
                WHERE id = %s
                  AND LEFT(last_updated, 10) BETWEEN %s AND %s
                ORDER BY date
                """,
                engine,
                params=(coin, start_str, end_str)
            )

            if df.empty:
                st.warning("No data found for this coin in the selected timeframe. Try expanding the Date Range.")
            else:
                # Force Streamlit to recognize the extracted string as a proper DateTime index
                df['date'] = pd.to_datetime(df['date'])
                chart_data = df.set_index('date')

                st.subheader(f"Price Trend Chart: {coin.capitalize()}")
                
                # If there's only 1 data point (a snapshot), a line chart will be blank. 
                # We dynamically switch to a scatter or bar chart so it actually displays!
                if len(df) == 1:
                    st.info("💡 Only a single day of data is present in the database. Displaying as a point graph.")
                    st.scatter_chart(data=chart_data, y='current_price')
                else:
                    st.line_chart(data=chart_data, y='current_price')
                
                st.subheader("Daily Price Table")
                # Clean up the output table for better presentation
                st.dataframe(df.assign(date=df['date'].dt.strftime('%Y-%m-%d')), use_container_width=True)

        except Exception as e:
            st.error(f"Failed to fetch insights data: {e}")
