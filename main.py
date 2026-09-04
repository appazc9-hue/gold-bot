import time
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_TOKEN = "8968119957:AAEGdl7tdt05huo7ZGTlvdZ5L-HYN1WM7tQ"
TELEGRAM_CHAT_ID = "6179754311"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error: {e}")

def check_gold_signal():
    live_data = yf.download("GC=F", period="30d", interval="1h", progress=False)
    if isinstance(live_data.columns, pd.MultiIndex):
        live_data.columns = live_data.columns.get_level_values(0)

    df = live_data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna().copy()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df['ATR'] = ranges.max(axis=1).rolling(14).mean()

    df = df.dropna()
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    last_price, last_low = last_row['Close'], last_row['Low']
    last_ema_p, last_ema_t = last_row['EMA_50'], last_row['EMA_200']
    last_rsi, prev_rsi = last_row['RSI'], prev_row['RSI']
    last_atr = last_row['ATR']

    bull_structure = (last_ema_p > last_ema_t) and (last_price > last_ema_t)
    pullback_touch = (last_low <= last_ema_p) and (last_price > last_ema_p)
    rsi_momentum = (last_rsi >= 53.0) and (last_rsi > prev_rsi)

    timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    if bull_structure and pullback_touch and rsi_momentum:
        sl = last_price - (last_atr * 2.5)
        tp = last_price + (last_atr * 2.5 * 3.0)
        msg = (
            f"🚨 *تنبيه شراء حقيقي للذهب (XAUUSD)* 🚨\n\n"
            f"📈 *سعر الدخول:* {last_price:.2f}\n"
            f"🛑 *وقف الخسارة (SL):* {sl:.2f}\n"
            f"🎯 *الهدف (TP):* {tp:.2f}\n\n"
            f"⏰ *التوقيت:* {timestamp}"
        )
        send_telegram_alert(msg)

send_telegram_alert("🤖 تم تشغيل البوت بنجاح على السيرفر السحابي (24/7)!")

while True:
    check_gold_signal()
    time.sleep(300)
