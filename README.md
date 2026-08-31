# ⚡ Live Market & Forex Alert System (TradingView Style)

A real-time financial market alerting engine and interactive dashboard supporting Forex pairs (`EUR/USD`, `GBP/USD`, `USD/JPY`, `AUD/USD`, `USD/CAD`, `XAU/USD Gold`) and Crypto pairs (`BTC/USDT`, `ETH/USDT`, `SOL/USDT`).

---

## 🌟 Key Features

- **TradingView Parity Alert Conditions**:
  - **Price Crossing Up / Down**: Trigger when price crosses above or below a specific level.
  - **Price Greater / Less Than**: Immediate threshold checks.
  - **Price Crosses Indicator**: e.g., Price crosses above 50 EMA or breaches upper Bollinger Band.
  - **Indicator Crosses Indicator**: e.g., Golden Cross (50 EMA crosses 200 EMA), MACD line crosses Signal.
  - **Indicator Thresholds**: e.g., RSI crosses above 70 (Overbought) or below 30 (Oversold).
  - **Price Channel**: Trigger on channel exit or entry.
- **Configurable Firing Modes**:
  - *Only Once* (deactivates alert after firing)
  - *Once Per Bar*
  - *Once Per Bar Close* (waits for confirmed candlestick bar close)
  - *Every Time* (with custom cooldown period)
- **Multi-Channel Instant Notifications**:
  - 📱 **Native Browser Web Push Notifications** (via VAPID/Service Worker)
  - ✉️ **HTML Email Alerts** (via SMTP / Gmail App Passwords with clean dark-mode card)
  - 🔊 **In-App Dual-Tone Audio Chime & Real-Time Toasts**
  - 🔗 **Discord / Telegram / Webhook HTTP POST Integration**
- **Interactive TradingView Candlestick Chart**:
  - Real-time candle streaming with 1m, 5m, 15m, 1h, 4h, 1D timeframes.
  - Visual indicator overlay toggles (EMA 20, EMA 50, EMA 200, Bollinger Bands).
  - Visual dashed horizontal alert lines displayed directly on chart for active alerts.
  - Quick Price Cross Simulator to inject custom price ticks and test triggers in 1 click.

---

## 🚀 Quick Start Guide

### 1. Launch the Server
```powershell
.\venv\Scripts\python run.py
```

### 2. Open the Dashboard
Navigate to: **[http://localhost:8000](http://localhost:8000)** in your browser (Google Chrome, Edge, Firefox, Brave).

### 3. Enable Browser Push Notifications
Click the **"📱 Enable Push Alerts"** button at the top header and grant notification permissions.

### 4. Create an Alert
1. Click **"+ Create Alert"**.
2. Select your instrument (e.g. `EURUSD`), timeframe (`1m`), and condition (e.g. `Price Crossing Up`).
3. Set your target price or indicator rules.
4. Select your notification channels (`Web Push`, `Email`, `In-App Toast & Audio`).
5. Click **"Save & Activate Alert"**.

---

## ⚙️ Configuring Email Alerts (Gmail SMTP)

To send email alerts using Gmail:
1. Go to your Google Account > **Security** > **2-Step Verification** > **App Passwords**.
2. Generate an App Password for "Mail".
3. Open the **Settings (⚙️)** modal in the dashboard or configure `.env`:
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: `your_email@gmail.com`
   - `SMTP_PASSWORD`: `your_16_char_app_password`
4. Click **"Send Test"** to verify delivery.

---

## 🧪 Running Automated Tests
```powershell
.\venv\Scripts\python -m pytest -v
```
