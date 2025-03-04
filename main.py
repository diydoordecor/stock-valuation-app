from fastapi import FastAPI, HTTPException
import requests
import os
import numpy as np

app = FastAPI()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

@app.post("/api/analyze")
async def analyze_stock(data: dict):
    ticker = data.get("ticker")
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    
    # Fetch EPS & Price Data from Alpha Vantage
    alpha_url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    alpha_response = requests.get(alpha_url).json()
    
    if "quarterlyEarnings" not in alpha_response:
        raise HTTPException(status_code=404, detail="Earnings data not found")
    
    earnings_data = alpha_response["quarterlyEarnings"][:12]  # Last 3 years (quarterly data)
    eps_values = [float(eps["reportedEPS"]) for eps in earnings_data]
    growth_rate = np.mean([(eps_values[i] / eps_values[i-1] - 1) * 100 for i in range(1, len(eps_values))])
    
    # Fetch stock price data
    price_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    price_response = requests.get(price_url).json()
    
    if "Time Series (Daily)" not in price_response:
        raise HTTPException(status_code=404, detail="Stock price data not found")
    
    price_data = price_response["Time Series (Daily)"]
    dates = list(price_data.keys())[:100]
    prices = [float(price_data[date]["5. adjusted close"]) for date in dates]
    
    chart_data = {
        "labels": dates[::-1],
        "datasets": [
            {
                "label": "Stock Price",
                "data": prices[::-1],
                "borderColor": "blue",
                "fill": False
            },
            {
                "label": "EPS Trend",
                "data": eps_values[::-1] + [eps_values[-1] * (1 + growth_rate / 100) for _ in range(4)],
                "borderColor": "green",
                "fill": False
            }
        ]
    }
    
    # Fetch strategic insights from Claude API
    claude_response = requests.post(
        "https://api.anthropic.com/v1/complete",
        json={"prompt": f"Summarize {ticker}'s strategic growth objectives based on recent earnings calls and filings.",
              "max_tokens": 200},
        headers={"Authorization": f"Bearer {CLAUDE_API_KEY}"}
    ).json()
    
    strategy_summary = claude_response.get("completion", "No strategy data available.")
    
    # Discounted Cash Flow (DCF) Valuation
    future_eps = eps_values[-1] * (1 + growth_rate / 100) ** 5  # Project 5 years ahead
    discount_rate = 0.10  # 10% discount rate
    intrinsic_value = sum([future_eps / (1 + discount_rate) ** i for i in range(1, 6)])
    
    # Adjust earnings multiple based on growth rate
    if growth_rate < 15:
        earnings_multiple = 15
    elif 15 <= growth_rate < 30:
        earnings_multiple = growth_rate
    else:
        earnings_multiple = 30
    
    fair_value = intrinsic_value * earnings_multiple  
    
    return {
        "chartData": chart_data,
        "valuation": {
            "fairValue": fair_value,
            "growthRate": round(growth_rate, 2),
            "strategy": strategy_summary
        }
    }

