# Interactive SPY Simulator

Open `index.html` in a modern browser and press **Start simulation**. The
historical, adjusted SPY daily price data is bundled into the page, so no
server, dependencies, or internet connection are needed.

The simulator uses a daily EMA-only long/short strategy. It goes long when
the close crosses above its 200-day EMA and short when it crosses below.
Positions reverse on the next EMA crossing. MACD is not used. The EMA has a
200-day warmup, and signals are acted on at the next daily open, with returns
measured between daily opens. Reversals incur fees on both sides.

Set starting capital and trading fee before starting. Use **Pause**,
**Resume**, **Step**, and **Reset** to control playback. The residual return
card shows the strategy's dollar-value difference from buy and hold. The
performance table shows Sharpe ratio,
information ratio versus buy and hold, maximum drawdown, and CAGR; ratios and
CAGR are annualized from daily returns using 252 trading days per year. Hover
over the chart to inspect portfolio values and the strategy's long/short/cash
position.

The simulation uses the same next-bar-open execution assumption as
`src\backtest.py`; it does not include margin interest or stock-borrow fees.
Results are historical and are not investment advice.
