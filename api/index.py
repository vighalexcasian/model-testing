
import sys
import math
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Make the existing src folder importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from backtest import download_history, run_backtest

app = FastAPI(
    title="Backtesting API",
    description="Historical weekly MACD long/short backtesting service",
    version="1.0.0"
)


class BacktestRequest(BaseModel):
    ticker: str = Field(default="SPY", min_length=1, max_length=20)
    period: str = "5y"
    fee_bps: float = Field(default=5, ge=0, le=10000)


def clean_number(value):
    value = float(value)
    return value if math.isfinite(value) else None


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Backtesting API"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/backtest")
def backtest(request: BacktestRequest):
    try:
        ticker = request.ticker.strip().upper()

        if request.period not in [
            "1y", "2y", "5y", "10y", "max",
            "1mo", "3mo", "6mo", "ytd"
        ]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported historical period"
            )

        # Download historical prices
        history = download_history(ticker, request.period)

        # Execute your existing strategy
        result, metrics = run_backtest(
            history,
            fee_bps=request.fee_bps
        )

        # Convert performance metrics to JSON-compatible values
        clean_metrics = {}

        for category, values in metrics.items():
            clean_metrics[category] = {
                key: clean_number(value)
                for key, value in values.items()
            }

        # Prepare equity curve for the frontend
        curve = []

        for date, row in result.iterrows():
            curve.append({
                "date": date.isoformat(),
                "close": clean_number(row["Close"]),
                "weekly_macd": clean_number(row["Weekly_MACD"]),
                "weekly_macd_signal": clean_number(row["Weekly_MACD_Signal"]),
                "macd_histogram": clean_number(row["MACD_Histogram"]),
                "position": clean_number(row["Position"]),
                "strategy_return": clean_number(
                    row["Strategy_Return"]
                ),
                "equity": clean_number(row["Equity"]),
                "buy_hold_equity": clean_number(
                    row["Buy_Hold_Equity"]
                )
            })

        return {
            "ticker": ticker,
            "period": request.period,
            "bars": len(history),
            "metrics": clean_metrics,
            "equity_curve": curve
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
