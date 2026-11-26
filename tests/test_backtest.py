import unittest

import pandas as pd

from src.backtest import run_backtest


class BacktestTests(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range("2020-01-06", periods=100 * 5, freq="B")
        weekly_closes = [
            100 + week if week < 45 else 145 - (week - 45) * 1.2
            for week in range(100)
        ]
        closes = [weekly_closes[index // 5] for index in range(len(dates))]
        self.history = pd.DataFrame(
            {
                "Open": closes,
                "High": [price + 1 for price in closes],
                "Low": [price - 1 for price in closes],
                "Close": closes,
            },
            index=dates,
        )

    def test_signals_follow_weekly_macd_histogram_sign(self):
        result, _ = run_backtest(self.history, fee_bps=0)

        self.assertTrue(result["Long_Signal"].any())
        self.assertTrue(result["Short_Signal"].any())
        self.assertTrue((result.loc[result["Long_Signal"], "MACD_Histogram"] > 0).all())
        self.assertTrue((result.loc[result["Short_Signal"], "MACD_Histogram"] < 0).all())
        self.assertTrue((result["Position"] == 1.0).any())
        self.assertTrue((result["Position"] == -1.0).any())
        first_ready = result["Weekly_MACD_Signal"].first_valid_index()
        self.assertIsNotNone(first_ready)
        self.assertTrue(result.loc[first_ready:, "Weekly_MACD"].notna().all())
        self.assertTrue(result.loc[first_ready:, "Weekly_MACD_Signal"].notna().all())

    def test_weekly_signal_takes_effect_from_the_following_daily_open(self):
        result, _ = run_backtest(self.history, fee_bps=0)
        first_long_position = result.index[result["Position"] == 1.0][0]
        position_index = result.index.get_loc(first_long_position)

        self.assertGreater(position_index, 0)
        self.assertTrue(result["Long_Signal"].iloc[position_index - 1])

    def test_reversals_charge_two_sides_and_short_returns_are_signed(self):
        history = self.history.copy()
        result, _ = run_backtest(history, fee_bps=100)
        reversal_index = next(
            index
            for index in range(1, len(result))
            if result["Position"].iloc[index - 1] == 1.0
            and result["Position"].iloc[index] == -1.0
        )

        self.assertAlmostEqual(result["Turnover"].iloc[reversal_index], 2.0)
        self.assertAlmostEqual(
            result["Strategy_Return"].iloc[reversal_index],
            -result["Buy_Hold_Return"].iloc[reversal_index] - 0.02,
        )

    def test_incomplete_current_week_is_not_used(self):
        history = self.history.iloc[:-2]
        result, _ = run_backtest(history, fee_bps=0)

        self.assertEqual(result.index[-1], history.index[-2])

    def test_requires_34_completed_weekly_candles(self):
        with self.assertRaisesRegex(ValueError, "34 completed weekly candles"):
            run_backtest(self.history.iloc[:150])
        with self.assertRaises(ValueError):
            run_backtest(self.history, interval="1wk")

    def test_metrics_annualize_daily_returns_using_252_sessions(self):
        history = self.history.copy()
        result, metrics = run_backtest(history)
        returns = result["Buy_Hold_Return"]
        expected_sharpe = returns.mean() / returns.std() * (252 ** 0.5)

        self.assertAlmostEqual(metrics["buy_hold"]["sharpe"], expected_sharpe)


if __name__ == "__main__":
    unittest.main()
