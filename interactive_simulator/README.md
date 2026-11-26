# Interactive SPY Simulator

Open `index.html` in a modern browser and press **Start simulation**. The
historical, adjusted SPY daily price data is bundled into the page, so no
server, dependencies, or internet connection are needed.

The simulator calculates MACD(12, 26, 9) from completed weekly closing prices.
A positive MACD histogram holds long; a negative histogram holds short. Weekly
signals are acted on at the next daily open, with returns measured between
daily opens. Reversals incur fees on both sides.

Set starting capital and trading fee before starting. Use **Pause**,
**Resume**, **Step**, and **Reset** to control playback. The residual return
card shows the strategy's dollar-value difference from buy and hold. The
performance table shows Sharpe ratio, information ratio versus buy and hold,
maximum drawdown, and CAGR; ratios and CAGR are annualized from daily returns
using 252 trading days per year. Hover over the chart to inspect portfolio
values and the strategy's long/short/cash position.

The simulation uses the same next-bar-open execution assumption as
`src\backtest.py`; it does not include margin interest or stock-borrow fees.
Results are historical and are not investment advice.
