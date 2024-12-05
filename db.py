import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import ta


# PART 1: Define Functions for Pulling, Processing, and Adding Technical Indicators
def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    return data


def process_data(data):
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data


def calculate_metrics(data):
    last_close = float(data['Close'].iloc[-1])
    prev_close = float(data['Close'].iloc[0])
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = float(data['High'].max())
    low = float(data['Low'].min())
    volume = int(data['Volume'].sum())
    return last_close, change, pct_change, high, low, volume


def add_technical_indicators(data):
    close_series = data['Close'].squeeze()
    data['SMA_20'] = ta.trend.sma_indicator(close=close_series, window=20)
    data['EMA_20'] = ta.trend.ema_indicator(close=close_series, window=20)
    return data


# PART 2: Enhanced Dashboard Layout
st.set_page_config(page_title="📈 Stock Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("📊 **Real-Time Stock Analysis Dashboard**")

# Sidebar Parameters
with st.sidebar:
    st.header("⚙️ **Settings**")
    ticker = st.text_input('🔍 Ticker', 'AAPL', help="Enter the stock symbol (e.g., AAPL, GOOGL).")
    time_period = st.selectbox('⏳ Time Period', ['1d', '1wk', '1mo', '1y', 'max'],
                               help="Select the time period for analysis.")
    chart_type = st.selectbox('📈 Chart Type', ['Candlestick', 'Line'], help="Choose the type of chart to display.")
    indicators = st.multiselect('📊 Technical Indicators', ['SMA 20', 'EMA 20'],
                                help="Add moving averages to the chart.")

    st.header("📡 **Real-Time Stock Prices**")
    stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT']
    for symbol in stock_symbols:
        real_time_data = fetch_stock_data(symbol, '1d', '1m')
        if not real_time_data.empty:
            real_time_data = process_data(real_time_data)
            last_price = float(real_time_data['Close'].iloc[-1])
            change = float(real_time_data['Close'].iloc[-1] - real_time_data['Open'].iloc[0])
            pct_change = (change / float(real_time_data['Open'].iloc[0])) * 100
            st.metric(f"{symbol}", f"{last_price:.2f} USD", f"{change:.2f} ({pct_change:.2f}%)")

# Main Content
tab1, tab2, tab3 = st.tabs(["📊 **Overview**", "📉 **Historical Data**", "🔬 **Technical Indicators**"])

if st.sidebar.button("Update Dashboard"):
    data = fetch_stock_data(ticker, time_period,
                            {'1d': '1m', '1wk': '30m', '1mo': '1d', '1y': '1wk', 'max': '1wk'}[time_period])
    if not data.empty:
        data = process_data(data)
        data = add_technical_indicators(data)
        last_close, change, pct_change, high, low, volume = calculate_metrics(data)

        with tab1:
            st.subheader(f"📈 {ticker} Overview")
            st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD",
                      delta=f"{change:.2f} ({pct_change:.2f}%)")
            col1, col2, col3 = st.columns(3)
            col1.metric("🔼 High", f"{high:.2f} USD")
            col2.metric("🔽 Low", f"{low:.2f} USD")
            col3.metric("📊 Volume", f"{volume:,}")

            fig = go.Figure()
            if chart_type == 'Candlestick':
                fig.add_trace(go.Candlestick(x=data['Datetime'], open=data['Open'], high=data['High'], low=data['Low'],
                                             close=data['Close']))
            else:
                fig = px.line(data, x='Datetime', y='Close')

            for indicator in indicators:
                if indicator == 'SMA 20':
                    fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
                elif indicator == 'EMA 20':
                    fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))

            fig.update_layout(title=f'{ticker} {time_period.upper()} Chart', xaxis_title='Time',
                              yaxis_title='Price (USD)', height=600)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("📜 Historical Data")
            st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']], use_container_width=True)

        with tab3:
            st.subheader("📊 Technical Indicators")
            st.dataframe(data[['Datetime', 'SMA_20', 'EMA_20']], use_container_width=True)

    else:
        st.warning("⚠️ No data available. Please check the ticker or adjust the parameters.")

st.sidebar.info("🛠️ **Customize your view and explore stock trends in real time!**")
