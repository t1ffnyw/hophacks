import unittest

import pandas as pd

from data.what_if_regression import predict_whatif, tree_illness_slope


class WhatIfRegressionTests(unittest.TestCase):
    def test_applies_slope_and_clamps_tree_cover(self):
        df = pd.DataFrame(
            {
                "csa2010": ["Test CSA"],
                "trees17": [10.0],
                "illness_pctile": [50.0],
            }
        )

        result = predict_whatif(df, "Test CSA", 5, slope=-0.4)

        self.assertTrue(result["usable"])
        self.assertEqual(result["new_tree"], 15.0)
        self.assertEqual(result["actual_change_applied"], 5.0)
        self.assertEqual(result["new_illness"], 48.0)

    def test_clamps_projected_canopy_at_zero(self):
        df = pd.DataFrame(
            {
                "Community": ["Edge CSA"],
                "trees17": [2.0],
                "illness_pctile": [40.0],
            }
        )

        result = predict_whatif(df, "Edge CSA", -10, slope=-0.5)

        self.assertEqual(result["new_tree"], 0.0)
        self.assertEqual(result["actual_change_applied"], -2.0)
        self.assertEqual(result["new_illness"], 41.0)

    def test_fits_a_finite_slope_on_real_csa_table(self):
        from pathlib import Path

        from data.what_if_regression import load_combined_table, regression_scatter_payload

        df = load_combined_table(
            Path(__file__).resolve().parents[1]
            / "data"
            / "csa_combined_heat_income_trees_illness.csv"
        )
        slope = tree_illness_slope(df)
        self.assertTrue(slope == slope)
        self.assertNotEqual(slope, 0.0)

        scatter = regression_scatter_payload(df)
        self.assertGreaterEqual(len(scatter["points"]), 50)
        self.assertEqual(len(scatter["line"]), 2)
        self.assertIn("r_squared", scatter)
        self.assertIn("corr", scatter)
        self.assertAlmostEqual(scatter["slope"], slope)


if __name__ == "__main__":
    unittest.main()
