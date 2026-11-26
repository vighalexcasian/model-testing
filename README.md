# Market Backtesting

A reproducible daily backtest of a weekly MACD long/short strategy, compared
with buy and hold.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python src\backtest.py
```

By default, the script downloads the maximum available SPY history at a daily
(`1d`) interval. It writes adjusted daily candles, the equity curve, and
position changes to `data\` with `_1d` filenames.

Choose another symbol:

```powershell
python src\backtest.py --ticker BTC-USD --fee-bps 5
```

The strategy calculates MACD(12, 26, 9) from weekly closing prices. A positive
MACD histogram holds a long position; a negative histogram holds a short
position. Only completed weekly candles are used, and each weekly reading
becomes active at the next daily open. Daily-open returns are used for both
the strategy and benchmark. A reversal incurs fees on both sides. Metrics are
annualized using 252 trading days.
The model does not include margin interest, stock-borrow fees, taxes,
additional slippage, or dividends not reflected in adjusted prices.

Yahoo Finance availability and historical depth vary by symbol. The downloaded
CSV is the local record of the data used in each run.

## Interactive simulator

Open `interactive_simulator\index.html` in a browser and press **Start
simulation** to animate the strategy against buy and hold. It includes
bundled SPY daily history and needs no install or local server. See
`interactive_simulator\README.md` for controls.
