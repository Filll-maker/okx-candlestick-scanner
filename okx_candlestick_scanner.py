
import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="OKX Candlestick Scanner", layout="wide")

st.title("🕯️ OKX Candlestick Pattern Scanner (pandas-ta version)")

# Выбор таймфрейма и паттерна
interval = st.selectbox("Выберите таймфрейм", ["1h", "4h", "1d"])
pattern = st.selectbox("Выберите свечной паттерн", ["hammer", "doji", "engulfing", "morning_star", "evening_star"])

def get_symbols():
    """Получает все USDT торговые пары с OKX."""
    url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    res = requests.get(url).json()
    return [
        t["instId"] for t in res["data"]
        if t["instId"].endswith("USDT")
    ]

@st.cache_data(ttl=3600)
def fetch_ohlcv(symbol, interval, limit=100):
    """Получает исторические данные по свечам."""
    granularity = {"1h": 3600, "4h": 14400, "1d": 86400}[interval]
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json().get("data", [])

    if not data:
        return None

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "_", "__"
    ])
    df = df.iloc[::-1]  # В обратном порядке (от старых к новым)
    df = df.astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df[["open", "high", "low", "close", "volume"]]

def detect_pattern(df, pattern_name):
    """Применяет распознавание паттерна из pandas-ta."""
    func = {
        "hammer": ta.hammer,
        "doji": ta.doji,
        "engulfing": ta.engulfing,
        "morning_star": ta.morningstar,
        "evening_star": ta.eveningstar,
    }.get(pattern_name)

    if func:
        result = func(df["open"], df["high"], df["low"], df["close"])
        return result.iloc[-1]  # Последняя свеча

    return None

if st.button("🔍 Начать сканирование"):
    symbols = get_symbols()
    matches = []

    with st.spinner("Сканирование..."):
        for sym in symbols:
            df = fetch_ohlcv(sym, interval)
            if df is None or len(df) < 10:
                continue

            result = detect_pattern(df, pattern)
            if result and result != 0:
                matches.append((sym, result))

    if matches:
        st.success(f"✅ Найдено {len(matches)} монет с паттерном '{pattern}':")
        for sym, res in matches:
            st.write(f"- {sym} ({'Bullish' if res > 0 else 'Bearish'})")
    else:
        st.warning("Ничего не найдено.")
