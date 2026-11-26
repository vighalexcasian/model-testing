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

## Interactive simulator and API

The HTML frontend is served from `/` on Vercel. Its original bundled-SPY
simulator remains available, and the **Run live backtest** form submits a
same-origin request to `POST /api/backtest`. The legacy `POST /backtest` and
`GET /health` routes are retained; `GET /api` and `GET /api/health` expose API
status checks.

The request body accepts `ticker` (default `SPY`), `period` (default `5y`;
`1y`, `2y`, `5y`, `10y`, `max`, `1mo`, `3mo`, `6mo`, or `ytd`), and `fee_bps`
(default `5`). At least 34 completed weekly candles are needed by the MACD
strategy, so short date ranges may be rejected. The response contains strategy
and buy-and-hold metrics plus the daily equity curve. The same weekly MACD
calculations and annualized metrics are used by the existing backtesting engine.

Vercel deploys the FastAPI app as a Python Function. Its maximum request
execution duration is configured in `vercel.json`; the available ceiling is
plan-dependent. Backtests require outbound access to Yahoo Finance, whose
availability and rate limits are outside this project. The endpoint is public
and unauthenticated, with no per-user quota or rate limit; anyone who can reach
the deployed URL can request a backtest. Add edge rate limiting or a quota
before exposing it to significant public traffic. For Vercel deployment,
connect this repository to a Vercel project
with the repository root as the project root, then deploy the project.

For local simulator controls, see `interactive_simulator\README.md`.
