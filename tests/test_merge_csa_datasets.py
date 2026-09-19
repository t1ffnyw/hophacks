import unittest

import pandas as pd

from data.merge_csa_datasets import merge_attribute_tables


class MergeAttributeTablesTests(unittest.TestCase):
    def test_joins_community_boundaries_to_2010_income_and_tree_keys(self):
        boundaries = pd.DataFrame(
            {"Community": ["Area A", "Area B"]}
        )
        heat = pd.DataFrame(
            {
                "Community": ["Area A", "Area B"],
                "temp_am_mean": [20.0, 21.0],
                "temp_af_mean": [28.0, 29.0],
                "temp_pm_mean": [24.0, 25.0],
            }
        )
        income = pd.DataFrame(
            {
                "CSA2010": ["Area A", "Area B"],
                "CSA2020": ["Area A 2020", "Area B 2020"],
                "mhhi17": [40000, 50000],
                "mhhi23": [45000, 55000],
            }
        )
        trees = pd.DataFrame(
            {
                "CSA2010": ["Area A", "Area B"],
                "trees11": [10.0, 20.0],
                "trees17": [11.0, 21.0],
            }
        )

        result = merge_attribute_tables(boundaries, heat, income, trees)

        self.assertEqual(
            list(result.columns),
            [
                "csa2010",
                "csa2020",
                "temp_am_mean",
                "temp_af_mean",
                "temp_pm_mean",
                "mhhi17",
                "mhhi23",
                "trees11",
                "trees17",
            ],
        )
        self.assertEqual(result.loc[0, "csa2010"], "Area A")
        self.assertEqual(result.loc[1, "csa2020"], "Area B 2020")
        self.assertEqual(result["mhhi23"].tolist(), [45000, 55000])
        self.assertEqual(result["trees17"].tolist(), [11.0, 21.0])


if __name__ == "__main__":
    unittest.main()
