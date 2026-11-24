"""Download daily history and backtest a 200-day EMA long/short strategy."""

import argparse
import re
from pathlib import Path

import pandas as pd


PERIODS_PER_YEAR = 252
OHLC_COLUMNS = ("Open", "High", "Low", "Close")


def download_history(ticker, period):
    """Fetch adjusted daily OHLC data from Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "yfinance is required to download data; install requirements.txt"
        ) from exc

    history = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if history.empty:
        raise ValueError(
            "Yahoo Finance returned no daily data for {0} (period {1})".format(
                ticker, period
            )
        )

    if isinstance(history.columns, pd.MultiIndex):
        for level in range(history.columns.nlevels):
            if ticker in history.columns.get_level_values(level):
                history = history.droplevel(level, axis=1)
                break

    missing = set(OHLC_COLUMNS) - set(history.columns)
    if missing:
        raise ValueError(
            "Downloaded data is missing required columns: "
            + ", ".join(sorted(missing))
        )

    return history.dropna(subset=list(OHLC_COLUMNS)).sort_index()


def _summarize(returns, equity, active_returns=None):
    years = len(returns) / PERIODS_PER_YEAR
    total_return = equity.iloc[-1] - 1.0
    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0 if years > 0 else float("nan")
    volatility = returns.std()
    sharpe = (
        returns.mean() / volatility * PERIODS_PER_YEAR**0.5
        if pd.notna(volatility) and volatility > 0
        else float("nan")
    )
    drawdown = equity / equity.cummax() - 1.0
    active_volatility = (
        active_returns.std() if active_returns is not None else float("nan")
    )
    information_ratio = (
        active_returns.mean() / active_volatility * PERIODS_PER_YEAR**0.5
        if pd.notna(active_volatility) and active_volatility > 0
        else float("nan")
    )
    return {
        "total_return": total_return,
        "cagr": cagr,
        "max_drawdown": drawdown.min(),
        "sharpe": sharpe,
        "information_ratio": information_ratio,
    }


def run_backtest(history, fee_bps=5, interval="1d"):
    """Trade daily price crossings of the EMA200 at the next open."""
    if interval != "1d":
        raise ValueError("The strategy requires daily (1d) candles")
    if fee_bps < 0 or fee_bps > 10000:
        raise ValueError("fee-bps must be between 0 and 10000")
    if not set(OHLC_COLUMNS).issubset(history.columns):
        raise ValueError("History must contain Open, High, Low, and Close columns")

    frame = history[list(OHLC_COLUMNS)].dropna().sort_index().copy()
    if len(frame) < 201:
        raise ValueError("At least 201 daily candles are required for the EMA200")

    close = frame["Close"]
    ema200 = close.ewm(span=200, adjust=False, min_periods=200).mean()

    price_cross_above = (close > ema200) & (
        close.shift(1) <= ema200.shift(1)
    )
    price_cross_below = (close < ema200) & (
        close.shift(1) >= ema200.shift(1)
    )
    long_signal = price_cross_above.fillna(False)
    short_signal = price_cross_below.fillna(False)

    close_signal_position = pd.Series(0.0, index=frame.index)
    position = 0.0
    for date in frame.index:
        if long_signal.loc[date]:
            position = 1.0
        elif short_signal.loc[date]:
            position = -1.0
        close_signal_position.loc[date] = position

    next_open_return = frame["Open"].shift(-1).div(frame["Open"]).sub(1.0)
    result = frame.copy()
    result["EMA200"] = ema200
    result["Long_Signal"] = long_signal
    result["Short_Signal"] = short_signal
    result["Position"] = close_signal_position.shift(1).fillna(0.0)
    result["Turnover"] = result["Position"].diff().abs().fillna(
        result["Position"].abs()
    )
    result["Strategy_Return"] = (
        result["Position"] * next_open_return
        - result["Turnover"] * (fee_bps / 10000.0)
    )
    result["Buy_Hold_Return"] = next_open_return
    result["Equity"] = (1.0 + result["Strategy_Return"]).cumprod()
    result["Buy_Hold_Equity"] = (1.0 + result["Buy_Hold_Return"]).cumprod()
    result = result.loc[next_open_return.notna()].copy()
    if result.empty:
        raise ValueError("Not enough daily history to calculate returns")
    if result["Equity"].le(0).any() or result["Buy_Hold_Equity"].le(0).any():
        raise ValueError(
            "A portfolio value became non-positive; review short exposure and fees"
        )

    metrics = {
        "strategy": _summarize(
            result["Strategy_Return"],
            result["Equity"],
            result["Strategy_Return"] - result["Buy_Hold_Return"],
        ),
        "buy_hold": _summarize(
            result["Buy_Hold_Return"],
            result["Buy_Hold_Equity"],
        ),
    }
    return result, metrics


def main():
    parser = argparse.ArgumentParser(
        description="Backtest the daily EMA200 long/short strategy."
    )
    parser.add_argument("--ticker", default="SPY", help="Yahoo Finance symbol")
    parser.add_argument("--period", default="max", help="Yahoo Finance history period")
    parser.add_argument(
        "--fee-bps",
        type=float,
        default=5,
        help="Trading cost per position change in basis points (5 = 0.05%%)",
    )
    args = parser.parse_args()

    history = download_history(args.ticker, args.period)
    result, metrics = run_backtest(history, fee_bps=args.fee_bps)

    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    safe_ticker = re.sub(r"[^A-Za-z0-9._-]+", "_", args.ticker)
    name = "{0}_1d".format(safe_ticker)
    history_path = data_dir / (name + "_historical.csv")
    equity_path = data_dir / (name + "_equity_curve.csv")
    trades_path = data_dir / (name + "_position_changes.csv")
    history.to_csv(history_path, index_label="Date")
    result.to_csv(equity_path, index_label="Date")
    result.loc[result["Turnover"] > 0, ["Position", "Turnover"]].to_csv(
        trades_path, index_label="Date"
    )

    print(
        "{0} 1d | {1} bars | EMA 200 long/short | fee {2:g} bps".format(
            args.ticker, len(history), args.fee_bps
        )
    )
    for label, stats in metrics.items():
        sharpe = (
            "n/a"
            if pd.isna(stats["sharpe"])
            else "{0:.2f}".format(stats["sharpe"])
        )
        information_ratio = (
            "n/a"
            if label == "buy_hold" or pd.isna(stats["information_ratio"])
            else "{0:.2f}".format(stats["information_ratio"])
        )
        print(
            "{0}: total {1:.2%}, CAGR {2:.2%}, max drawdown {3:.2%}, "
            "Sharpe {4}, information ratio {5}".format(
                label.replace("_", " "),
                stats["total_return"],
                stats["cagr"],
                stats["max_drawdown"],
                sharpe,
                information_ratio,
            )
        )
    print("Historical data: {0}".format(history_path))
    print("Equity curve:    {0}".format(equity_path))
    print("Position changes:{0}".format(trades_path))


if __name__ == "__main__":
    main()
