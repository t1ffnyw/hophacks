import unittest
from pathlib import Path

import pandas as pd

from scripts.csa_map_data import (
    CATEGORY_ORDER,
    assign_tercile_classes,
    compute_tercile_thresholds,
    load_csa_map_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


class CsaMapDataTests(unittest.TestCase):
    def test_loads_combined_table_for_all_named_csas(self):
        gdf, diagnostics = load_csa_map_data(DATA_DIR)

        self.assertEqual(len(gdf), 55)
        self.assertNotIn("Unassigned -- Jail", gdf["Community"].tolist())
        self.assertEqual(diagnostics.boundary_only, ())
        self.assertEqual(diagnostics.table_only, ())
        self.assertEqual(
            diagnostics.missing_by_layer,
            {"heat": (), "health": (), "income": (), "trees": ()},
        )
        self.assertEqual(
            {spec.key for spec in diagnostics.layer_specs.values()},
            set(CATEGORY_ORDER),
        )

    def test_tied_values_stay_in_the_same_class(self):
        values = pd.Series([1, 1, 1, 2, 2, 3, 3, 4, 4], dtype=float)
        thresholds = compute_tercile_thresholds(values)
        classes = assign_tercile_classes(values, thresholds)

        self.assertEqual(classes.iloc[0], classes.iloc[1])
        self.assertEqual(classes.iloc[3], classes.iloc[4])
        self.assertEqual(set(classes.dropna()), {"Low", "Medium", "High"})

    def test_insufficient_unique_values_are_explicit(self):
        values = pd.Series([5, 5, 5], dtype=float)
        thresholds = compute_tercile_thresholds(values)
        classes = assign_tercile_classes(values, thresholds)

        self.assertEqual(set(classes.dropna()), {"Medium"})
        self.assertEqual(thresholds.unique_values, 1)
        self.assertEqual(thresholds.empty_classes, ("Low", "High"))


if __name__ == "__main__":
    unittest.main()
