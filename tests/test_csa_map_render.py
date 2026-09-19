import itertools
import unittest
from pathlib import Path

import pandas as pd

from scripts.csa_map_data import load_csa_map_data
from scripts.csa_map_render import (
    MISSING_COLOR,
    PAIR_PALETTES,
    SINGLE_PALETTES,
    build_csa_map,
    canonicalize_selection,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


class CsaMapRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gdf, cls.diagnostics = load_csa_map_data(DATA_DIR)

    def test_canonicalizes_selections_in_fixed_order(self):
        self.assertEqual(
            canonicalize_selection(["trees", "heat"]),
            ("heat", "trees"),
        )
        with self.assertRaises(ValueError):
            canonicalize_selection(["heat", "health", "income"])

    def test_has_six_pair_palettes_with_nine_colors_each(self):
        expected_pairs = set(itertools.combinations(("heat", "health", "income", "trees"), 2))

        self.assertEqual(set(PAIR_PALETTES), expected_pairs)
        for palette in PAIR_PALETTES.values():
            self.assertEqual(len(palette), 3)
            self.assertTrue(all(len(row) == 3 for row in palette))

    def test_renders_all_single_and_pair_modes(self):
        for key in SINGLE_PALETTES:
            rendered = build_csa_map(
                self.gdf,
                [key],
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
                tile_url=None,
                tile_attr=None,
            ).get_root().render()
            self.assertIn("Reset to Baltimore", rendered)
            self.assertIn(self.diagnostics.layer_specs[key].label, rendered)

        for first, second in PAIR_PALETTES:
            rendered = build_csa_map(
                self.gdf,
                [first, second],
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
                tile_url=None,
                tile_attr=None,
            ).get_root().render()
            self.assertIn("Low", rendered)
            self.assertIn("High", rendered)
            self.assertIn(self.diagnostics.layer_specs[first].label, rendered)
            self.assertIn(self.diagnostics.layer_specs[second].label, rendered)

    def test_single_legend_contains_units_period_and_thresholds(self):
        rendered = build_csa_map(
            self.gdf,
            ["income"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn("USD", rendered)
        self.assertIn("2023 income year", rendered)
        self.assertIn("Darker means a higher value", rendered)
        self.assertIn("≤ $", rendered)

    def test_legend_layout_places_card_beside_map(self):
        rendered = build_csa_map(
            self.gdf,
            ["heat"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn("csa-map-layout", rendered)
        self.assertIn("flex-direction: row", rendered)
        self.assertIn("csa-map-legend", rendered)

    def test_map_limits_minimum_zoom(self):
        map_widget = build_csa_map(
            self.gdf,
            ["heat"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        )

        self.assertEqual(map_widget.options["minZoom"], 10)
        self.assertIn('"minZoom": 10', map_widget.get_root().render())

    def test_bivariate_legend_contains_axes_and_numeric_ranges(self):
        rendered = build_csa_map(
            self.gdf,
            ["heat", "income"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn("Low → High", rendered)
        self.assertIn("Modeled afternoon surface", rendered)
        self.assertIn("Median household income", rendered)
        self.assertIn("2023 income year", rendered)

    def test_missing_values_use_neutral_opaque_styling(self):
        missing_gdf = self.gdf.copy()
        first_index = missing_gdf.index[0]
        missing_gdf.loc[first_index, "mhhi23"] = pd.NA
        missing_gdf.loc[first_index, "income_class"] = pd.NA
        rendered = build_csa_map(
            missing_gdf,
            ["income", "trees"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn(MISSING_COLOR, rendered)
        self.assertIn('"Missing"', rendered)
        self.assertIn('"fillOpacity": 1.0', rendered)
        self.assertIn("_tooltip_class_income", rendered)


if __name__ == "__main__":
    unittest.main()
