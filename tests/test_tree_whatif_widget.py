import json
import unittest
from pathlib import Path

from scripts.csa_map_data import load_csa_map_data
from scripts.tree_whatif_widget import build_whatif_widget, whatif_geojson


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


class TreeWhatIfWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gdf, cls.diagnostics = load_csa_map_data(DATA_DIR)

    def test_geojson_includes_fill_color_and_model_fields(self):
        payload = whatif_geojson(self.gdf)

        self.assertEqual(len(payload["features"]), 55)
        properties = payload["features"][0]["properties"]
        self.assertIn("Community", properties)
        self.assertIn("fillColor", properties)
        self.assertTrue(str(properties["fillColor"]).startswith("#"))
        self.assertIn("trees17", properties)
        self.assertIn("illness_pctile", properties)

    def test_widget_state_includes_legend_and_slope(self):
        from data.what_if_regression import regression_scatter_payload

        scatter = regression_scatter_payload(self.gdf)
        widget = build_whatif_widget(
            self.gdf,
            self.diagnostics.layer_specs,
            self.diagnostics.thresholds,
            slope=-0.25,
            csa_stats={"Example": {"trees": 20.0, "illness": 40.0}},
            tile_url=None,
            tile_attr=None,
            scatter_payload=scatter,
        )

        self.assertIn("Key", widget.legend_html)
        self.assertIn("Heat-health vulnerability", widget.legend_html)
        self.assertIn("Tree canopy cover", widget.legend_html)
        self.assertIn("#756bb1", widget.legend_html)
        self.assertIn("#238b45", widget.legend_html)
        self.assertNotIn("Bivariate choropleth", widget.legend_html)
        rules = json.loads(widget.color_rules)
        self.assertEqual(rules["missing"], "#bdbdbd")
        self.assertEqual(len(rules["palette"]), 3)
        self.assertEqual(len(rules["palette"][0]), 3)
        self.assertIn("low_max", rules["health"])
        self.assertIn("low_max", rules["trees"])
        self.assertEqual(widget.slope, -0.25)
        self.assertEqual(len(json.loads(widget.bounds_json)), 2)
        self.assertEqual(widget.selected_csa, "")
        self.assertEqual(widget.tree_change, 0)
        scatter_state = json.loads(widget.scatter_json)
        self.assertGreaterEqual(len(scatter_state["points"]), 50)
        self.assertEqual(len(scatter_state["line"]), 2)


if __name__ == "__main__":
    unittest.main()
