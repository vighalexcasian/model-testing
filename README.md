# Market Backtesting

A reproducible daily backtest of a 200-day EMA long/short strategy,
compared with buy and hold.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python src\backtest.py
```

By default, the script downloads the maximum available SPY history at a daily
(`1d`) interval. It writes the adjusted historical candle fields returned by
Yahoo Finance, the equity curve, and position changes to `data\` with `_1d`
filenames. Existing weekly datasets and outputs are left intact.
The current SPY daily run also includes a static chart at
`data\SPY_1d_equity_chart.svg`; the interactive chart is in the simulator.

Choose another symbol:

```powershell
python src\backtest.py --ticker BTC-USD --fee-bps 5
```

The strategy goes long when the daily close crosses above its 200-day EMA and
short when it crosses below. It holds that direction until the next EMA
crossing reverses the position. MACD is not used. Signals take effect at the
next daily open, and returns are measured between daily opens. A reversal
from long to short (or vice versa) incurs fees on both sides. Metrics are
annualized using 252 trading days.
The model does not include margin interest, stock-borrow fees, taxes,
additional slippage, or dividends not reflected in adjusted prices.

Yahoo Finance availability and historical depth vary by symbol.
The downloaded CSV is the local record of the data used in each run.

## Interactive simulator

Open `interactive_simulator\index.html` in a browser and press **Start
simulation** to animate the strategy against buy and hold. It includes
bundled SPY daily history and needs no install or local server. See
`interactive_simulator\README.md` for controls.
