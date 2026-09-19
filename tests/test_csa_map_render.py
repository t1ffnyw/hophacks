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
    comparison_label,
    embed_map_html,
    format_bivariate_bin_detail,
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
            self.assertIn(
                comparison_label(first, self.diagnostics.layer_specs),
                legend,
            )
            self.assertIn(
                comparison_label(second, self.diagnostics.layer_specs),
                legend,
            )

    def test_single_legend_contains_units_period_and_thresholds(self):
        legend = build_legend_html(
            ("income",),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )

        self.assertIn("USD", legend)
        self.assertIn("csa-legend-units", legend)
        self.assertIn("≤ $", legend)
        self.assertIn("font-size: 18px", legend)
        self.assertNotIn("2023 income year", legend)
        self.assertNotIn("Darker means a higher value", legend)

    def test_single_legend_unit_descriptions(self):
        cases = {
            "heat": "Degrees Celsius",
            "health": "Heat-health risk index (percentile)",
            "income": "USD",
            "trees": "Percent of neighborhood area",
        }
        for key, description in cases.items():
            legend = build_legend_html(
                (key,),
                self.diagnostics.layer_specs,
                self.diagnostics.thresholds,
            )
            self.assertIn(description, legend)

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
            "Heat-Health Vulnerability",
            "Median Household Income",
            "Tree Canopy Coverage",
        ):
            self.assertIn(label, rendered)

        self.assertIn("_tooltip_value_heat", rendered)
        self.assertNotIn("_tooltip_value_health", rendered)
        self.assertNotIn("_tooltip_value_income", rendered)
        self.assertNotIn("_tooltip_value_trees", rendered)

    def test_map_popup_chrome_matches_tooltip_style(self):
        rendered = build_csa_map(
            self.gdf,
            ["heat"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
        ).get_root().render()

        self.assertIn('"closeButton": false', rendered)
        self.assertIn(".leaflet-popup-content-wrapper", rendered)
        self.assertIn(".leaflet-popup-close-button", rendered)
        self.assertIn("background: transparent", rendered)
        self.assertIn("rgba(255, 255, 255, 0.85)", rendered)
        self.assertIn(".foliumpopup", rendered)
        self.assertIn("border-radius: 3px", rendered)

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

    def test_bivariate_legend_title_and_grid_size(self):
        first, second = "heat", "income"
        legend = build_legend_html(
            (first, second),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )

        self.assertIn("Heat × Household Income", legend)
        self.assertNotIn("Bivariate choropleth", legend)
        self.assertIn("height: 48px", legend)
        self.assertIn("width: 48px", legend)

    def test_bivariate_legend_has_left_row_labels(self):
        legend = build_legend_html(
            ("heat", "income"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        for class_name in ("Low", "Medium", "High"):
            self.assertIn(f"<th scope='row'>{class_name}</th>", legend)
        self.assertIn("csa-axis-y-label", legend)
        self.assertIn("Household Income", legend)

    def test_bivariate_legend_has_bottom_column_labels(self):
        legend = build_legend_html(
            ("heat", "income"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        for class_name in ("Low", "Medium", "High"):
            self.assertIn(
                f"<td class='csa-bivariate-col-label'>{class_name}</td>",
                legend,
            )
        self.assertIn("csa-axis-x-label", legend)
        self.assertIn("Heat", legend)

    def test_bivariate_legend_column_labels_after_grid_rows(self):
        legend = build_legend_html(
            ("heat", "income"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        last_color_cell = legend.rfind("cursor:pointer'></td>")
        col_label_td = legend.find("<td class='csa-bivariate-col-label'>Low</td>")
        self.assertGreater(col_label_td, last_color_cell)

    def test_bivariate_legend_no_range_notes(self):
        legend = build_legend_html(
            ("heat", "income"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        self.assertNotIn("Low → High", legend)
        self.assertNotIn("— Low:", legend)
        self.assertNotIn("(Low → High, rows)", legend)
        self.assertNotIn("(Low → High, columns)", legend)
        first_spec = self.diagnostics.layer_specs["heat"]
        self.assertNotIn(
            f"({first_spec.units}; {first_spec.period})",
            legend,
        )

    def test_bivariate_legend_contains_both_category_labels(self):
        legend = build_legend_html(
            ("heat", "income"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        self.assertIn("Heat", legend)
        self.assertIn("Household Income", legend)
        self.assertNotIn("Median Household Income", legend)

    def test_format_bivariate_bin_detail(self):
        detail = format_bivariate_bin_detail(
            "heat",
            "income",
            "Low",
            "High",
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        self.assertIn("Heat", detail)
        self.assertIn("Low", detail)
        self.assertIn("Household Income", detail)
        self.assertIn("High", detail)
        self.assertIn("≤", detail)
        self.assertIn(">", detail)

    def test_bivariate_short_labels_for_trees(self):
        legend = build_legend_html(
            ("income", "trees"),
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
        )
        self.assertIn("Household Income", legend)
        self.assertIn("Tree Canopy", legend)
        self.assertNotIn("Tree Canopy Coverage", legend)
        self.assertNotIn("Median Household Income", legend)

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


    def test_active_bin_filter_keeps_matching_features_colored(self):
        """With active_bin set, matching features keep palette color."""
        from scripts.csa_map_render import _style_function, CLASS_INDEX

        selected = ("heat", "income")
        active_bin = ("Low", "High")
        style_fn = _style_function(selected, active_bin=active_bin)

        feature = {
            "properties": {"heat_class": "Low", "income_class": "High"}
        }
        result = style_fn(feature)
        palette_color = PAIR_PALETTES[("heat", "income")][
            CLASS_INDEX["High"]
        ][CLASS_INDEX["Low"]]
        self.assertEqual(result["fillColor"], palette_color)

    def test_active_bin_filter_grays_non_matching_features(self):
        """With active_bin set, non-matching features become gray."""
        from scripts.csa_map_render import _style_function

        selected = ("heat", "income")
        active_bin = ("Low", "High")
        style_fn = _style_function(selected, active_bin=active_bin)

        feature = {
            "properties": {"heat_class": "High", "income_class": "High"}
        }
        result = style_fn(feature)
        self.assertEqual(result["fillColor"], MISSING_COLOR)

    def test_active_bin_none_preserves_bivariate_colors(self):
        """Without active_bin, all features keep normal palette color."""
        from scripts.csa_map_render import _style_function, CLASS_INDEX

        selected = ("heat", "income")
        style_fn = _style_function(selected, active_bin=None)

        for first_class in ("Low", "Medium", "High"):
            for second_class in ("Low", "Medium", "High"):
                feature = {
                    "properties": {
                        "heat_class": first_class,
                        "income_class": second_class,
                    }
                }
                result = style_fn(feature)
                expected = PAIR_PALETTES[("heat", "income")][
                    CLASS_INDEX[second_class]
                ][CLASS_INDEX[first_class]]
                self.assertEqual(result["fillColor"], expected)

    def test_build_csa_map_accepts_active_bin(self):
        """build_csa_map should accept active_bin kwarg without error."""
        map_widget = build_csa_map(
            self.gdf,
            ["heat", "income"],
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            tile_url=None,
            tile_attr=None,
            active_bin=("Low", "High"),
        )
        rendered = map_widget.get_root().render()
        self.assertIn("Reset to Baltimore", rendered)


if __name__ == "__main__":
    unittest.main()
