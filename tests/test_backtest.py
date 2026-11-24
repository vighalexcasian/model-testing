import unittest

import pandas as pd

from src.backtest import run_backtest


class BacktestTests(unittest.TestCase):
    def setUp(self):
        closes = [100.0] * 210 + [90.0, 110.0, 110.0, 90.0, 90.0, 90.0]
        self.history = pd.DataFrame(
            {
                "Open": closes,
                "High": [price + 1 for price in closes],
                "Low": [price - 1 for price in closes],
                "Close": closes,
            },
            index=pd.date_range("2020-01-03", periods=len(closes), freq="B"),
        )

    def test_long_and_short_signals_follow_daily_ema_crosses(self):
        result, _ = run_backtest(self.history, fee_bps=0)

        self.assertEqual(
            result.index[result["Long_Signal"]].tolist(),
            [self.history.index[211]],
        )
        self.assertEqual(
            result.index[result["Short_Signal"]].tolist(),
            [self.history.index[210], self.history.index[213]],
        )
        self.assertEqual(result["Position"].iloc[211], -1.0)
        self.assertEqual(result["Position"].iloc[212], 1.0)
        self.assertEqual(result["Position"].iloc[214], -1.0)

    def test_reversals_charge_two_sides_and_short_returns_are_signed(self):
        history = self.history.copy()
        history.iloc[215, history.columns.get_loc("Open")] = 80.0
        result, _ = run_backtest(history, fee_bps=100)

        self.assertAlmostEqual(result["Turnover"].iloc[211], 1.0)
        self.assertAlmostEqual(
            result["Strategy_Return"].iloc[211], -0.01
        )
        self.assertAlmostEqual(result["Turnover"].iloc[212], 2.0)
        self.assertAlmostEqual(
            result["Strategy_Return"].iloc[212], (90 / 110 - 1) - 0.02
        )
        self.assertAlmostEqual(result["Turnover"].iloc[214], 2.0)
        self.assertAlmostEqual(
            result["Strategy_Return"].iloc[214], (1 - 80 / 90) - 0.02
        )

    def test_ema_requires_200_day_warmup(self):
        result, _ = run_backtest(self.history, fee_bps=0)

        self.assertTrue(result["EMA200"].iloc[:199].isna().all())
        self.assertTrue(pd.notna(result["EMA200"].iloc[199]))
        self.assertFalse(result["Long_Signal"].iloc[:199].any())
        self.assertFalse(result["Short_Signal"].iloc[:199].any())

    def test_price_crossing_above_ema_enters_long_without_macd_confirmation(self):
        closes = [100.0] * 210 + [50.0]
        closes.extend(closes[-1] + 0.1 * step for step in range(1, 301))
        history = pd.DataFrame(
            {
                "Open": closes,
                "High": [price + 1 for price in closes],
                "Low": [price - 1 for price in closes],
                "Close": closes,
            },
            index=pd.date_range("2020-01-03", periods=len(closes), freq="B"),
        )
        result, _ = run_backtest(history, fee_bps=0)

        self.assertTrue(result["Close"].iloc[389] > result["EMA200"].iloc[389])
        self.assertTrue(result["Long_Signal"].iloc[239])
        self.assertEqual(result["Position"].iloc[240], 1.0)

    def test_price_crossing_below_ema_enters_short_without_macd_confirmation(self):
        closes = [100.0] * 210 + [50.0, 50.0, 50.0]
        history = pd.DataFrame(
            {
                "Open": closes,
                "High": [price + 1 for price in closes],
                "Low": [price - 1 for price in closes],
                "Close": closes,
            },
            index=pd.date_range("2020-01-03", periods=len(closes), freq="B"),
        )
        result, _ = run_backtest(history, fee_bps=0)

        self.assertTrue(result["Short_Signal"].iloc[210])
        self.assertLess(result["Close"].iloc[210], result["EMA200"].iloc[210])
        self.assertEqual(result["Position"].iloc[211], -1.0)

    def test_daily_candles_and_at_least_201_bars_are_required(self):
        with self.assertRaises(ValueError):
            run_backtest(self.history, interval="1wk")
        with self.assertRaises(ValueError):
            run_backtest(self.history.iloc[:200])

    def test_metrics_annualize_daily_returns_using_252_sessions(self):
        closes = [100.0]
        for step in range(1, 260):
            closes.append(closes[-1] * (1.001 if step % 2 else 0.999))
        history = pd.DataFrame(
            {
                "Open": closes,
                "High": [price + 1 for price in closes],
                "Low": [price - 1 for price in closes],
                "Close": closes,
            },
            index=pd.date_range("2020-01-03", periods=len(closes), freq="B"),
        )

        result, metrics = run_backtest(history)
        returns = result["Buy_Hold_Return"]
        expected_sharpe = returns.mean() / returns.std() * (252 ** 0.5)

        self.assertAlmostEqual(metrics["buy_hold"]["sharpe"], expected_sharpe)


if __name__ == "__main__":
    unittest.main()
