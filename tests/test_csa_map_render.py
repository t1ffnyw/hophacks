import itertools
import unittest
from pathlib import Path

import pandas as pd

from scripts.csa_map_data import load_csa_map_data
from scripts.csa_map_render import (
    MAP_EMBED_HEIGHT,
    MISSING_COLOR,
    PAIR_PALETTES,
    SINGLE_PALETTES,
    build_csa_map,
    build_legend_html,
    canonicalize_selection,
    embed_map_html,
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
            self.assertNotIn("csa-map-legend", rendered)

            legend = build_legend_html(
                (key,),
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
            )
            self.assertIn(self.diagnostics.layer_specs[key].label, legend)

        for first, second in PAIR_PALETTES:
            rendered = build_csa_map(
                self.gdf,
                [first, second],
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
                tile_url=None,
                tile_attr=None,
            ).get_root().render()
            self.assertIn("Reset to Baltimore", rendered)
            self.assertNotIn("csa-map-legend", rendered)

            legend = build_legend_html(
                (first, second),
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
            )
            self.assertIn("Low", legend)
            self.assertIn("High", legend)
            self.assertIn(self.diagnostics.layer_specs[first].label, legend)
            self.assertIn(self.diagnostics.layer_specs[second].label, legend)

    def test_single_legend_contains_units_period_and_thresholds(self):
        legend = build_legend_html(
            ("income",),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )

        self.assertIn("USD", legend)
        self.assertIn("2023 income year", legend)
        self.assertIn("Darker means a higher value", legend)
        self.assertIn("≤ $", legend)

    def test_legend_html_includes_sidebar_styles(self):
        legend = build_legend_html(
            ("heat",),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )

        self.assertIn("csa-map-layout", legend)
        self.assertIn("csa-map-legend", legend)
        self.assertIn(
            ".csa-map-layout {\n"
            "        max-width: none;\n"
            "        width: 100%;",
            legend,
        )

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

    def test_map_suppresses_browser_focus_box_on_region_click(self):
        rendered = build_csa_map(
            self.gdf,
            ["heat"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn("path.leaflet-interactive:focus", rendered)
        self.assertIn("outline: none", rendered)
        self.assertIn("stroke: #111827", rendered)
        self.assertIn("stroke-width: 2.5", rendered)

    def test_map_popup_lists_all_four_metrics_while_tooltip_stays_scoped(self):
        rendered = build_csa_map(
            self.gdf,
            ["heat"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn("bindPopup", rendered)
        self.assertIn("_popup_value_heat", rendered)
        self.assertIn("_popup_value_health", rendered)
        self.assertIn("_popup_value_income", rendered)
        self.assertIn("_popup_value_trees", rendered)
        for label in (
            "Heat",
            "Heat-health vulnerability",
            "Median household income",
            "Tree canopy coverage",
        ):
            self.assertIn(label, rendered)

        self.assertIn("_tooltip_value_heat", rendered)
        self.assertNotIn("_tooltip_value_health", rendered)
        self.assertNotIn("_tooltip_value_income", rendered)
        self.assertNotIn("_tooltip_value_trees", rendered)

    def test_embed_map_html_uses_fixed_height(self):
        self.assertEqual(MAP_EMBED_HEIGHT, "520px")
        map_widget = build_csa_map(
            self.gdf,
            ["heat"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        )
        embedded = embed_map_html(map_widget)

        self.assertIn(f'height="{MAP_EMBED_HEIGHT}"', embedded)
        self.assertNotIn("padding-bottom", embedded)

    def test_legends_omit_missing_legend_rows(self):
        for key in SINGLE_PALETTES:
            legend = build_legend_html(
                (key,),
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
            )
            self.assertNotIn(
                "<strong>Missing</strong>: no selected measurement",
                legend,
            )
            self.assertNotIn(">Missing<", legend)
            self.assertNotIn("no selected measurement", legend)
            self.assertNotIn(
                f"background:{MISSING_COLOR}",
                legend,
            )

        for first, second in PAIR_PALETTES:
            legend = build_legend_html(
                (first, second),
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
            )
            self.assertNotIn(
                "<strong>Missing</strong>: either selected measurement missing",
                legend,
            )
            self.assertNotIn(">Missing<", legend)
            self.assertNotIn("either selected measurement missing", legend)
            self.assertNotIn(
                f"background:{MISSING_COLOR}",
                legend,
            )

    def test_bivariate_legend_title_axes_and_grid_size(self):
        first, second = "heat", "income"
        first_label = self.diagnostics.layer_specs[first].label
        second_label = self.diagnostics.layer_specs[second].label
        legend = build_legend_html(
            (first, second),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )

        self.assertIn(
            f"Combined categories: {first_label} × {second_label}",
            legend,
        )
        self.assertNotIn("Bivariate choropleth", legend)
        self.assertIn("height: 36px", legend)
        self.assertIn("width: 36px", legend)
        self.assertIn("csa-bivariate-col-label", legend)
        for class_name in ("Low", "Medium", "High"):
            self.assertIn(
                f"<th class='csa-bivariate-col-label' scope='col'>{class_name}</th>",
                legend,
            )
            self.assertIn(f"<th scope='row'>{class_name}</th>", legend)
        self.assertIn("csa-axis-y-caption", legend)
        self.assertIn(second_label, legend)

    def test_bivariate_legend_contains_axes_and_numeric_ranges(self):
        legend = build_legend_html(
            ("heat", "income"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )

        self.assertIn("Low → High", legend)
        self.assertIn("Modeled afternoon surface", legend)
        self.assertIn("Median household income", legend)
        self.assertIn("2023 income year", legend)

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
