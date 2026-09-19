import unittest

import maps


class MapsNotebookTests(unittest.TestCase):
    def test_notebook_defaults_to_heat_and_loads_all_csas(self):
        _, definitions = maps.app.run()

        self.assertEqual(definitions["selected_keys"], ("heat",))
        self.assertEqual(len(definitions["csa_gdf"]), 55)
        self.assertEqual(len(definitions["category_options"]), 4)
        self.assertIn("Heat-health vulnerability", definitions["category_options"])
        self.assertEqual(len(definitions["category_checks"]), 4)
        self.assertTrue(
            definitions["category_checks"][definitions["LAYER_SPECS"]["heat"].label].value
        )
        self.assertIn("csa-map-legend", definitions["legend_html"])
        self.assertIsNotNone(definitions["map_layout"])
        self.assertIn(
            f'height="{definitions["MAP_EMBED_HEIGHT"]}"',
            definitions["map_layout"].text
            if hasattr(definitions["map_layout"], "text")
            else str(definitions["map_layout"]),
        )

    def test_map_and_sidebar_have_fixed_height_parity(self):
        _, definitions = maps.app.run()
        map_region, sidebar_region = definitions["map_layout"]._live_children
        expected_height = f"height:{definitions['MAP_EMBED_HEIGHT']}"

        self.assertIn(expected_height, map_region.text)
        self.assertIn(expected_height, sidebar_region.text)

    def test_map_and_sidebar_use_seventy_thirty_widths(self):
        _, definitions = maps.app.run()
        layout_text = definitions["map_layout"].text

        self.assertIn("<div style='flex: 7'>", layout_text)
        self.assertIn("<div style='flex: 3'>", layout_text)

    def test_categories_and_checkboxes_render_before_scrollable_legend(self):
        _, definitions = maps.app.run()
        layout_text = definitions["map_layout"].text

        categories_position = layout_text.index("Categories")
        first_checkbox_position = layout_text.index("<marimo-checkbox")
        legend_position = layout_text.index("csa-map-legend")
        self.assertLess(categories_position, first_checkbox_position)
        self.assertLess(first_checkbox_position, legend_position)
        self.assertIn("overflow-y:auto", layout_text)
        self.assertIn("Categories", layout_text)
        self.assertIn("select up to two", layout_text)
        self.assertIn(chr(0x2014), layout_text)
        self.assertEqual(layout_text.count("<marimo-checkbox"), 4)
        self.assertNotIn("Select up to two categories.", layout_text)

    def test_two_selections_disable_only_unchecked_categories(self):
        _, definitions = maps.app.run()
        disabled = definitions["checkbox_disabled_states"](
            ("heat", "health"),
            ("heat", "health", "income", "trees"),
        )

        self.assertEqual(
            disabled,
            {
                "heat": False,
                "health": False,
                "income": True,
                "trees": True,
            },
        )

    def test_fewer_than_two_selections_enable_all_categories(self):
        _, definitions = maps.app.run()
        disabled = definitions["checkbox_disabled_states"](
            ("heat",),
            ("heat", "health", "income", "trees"),
        )

        self.assertEqual(
            disabled,
            {
                "heat": False,
                "health": False,
                "income": False,
                "trees": False,
            },
        )

    def test_third_selection_is_ignored_by_callback_transition_logic(self):
        _, definitions = maps.app.run()

        transitioned = definitions["transition_category_selection"](
            ("heat", "health"),
            "income",
            True,
            definitions["CATEGORY_ORDER"],
        )

        self.assertEqual(transitioned, ("heat", "health"))

    def test_category_state_allows_self_loops_for_checkbox_refresh(self):
        _, definitions = maps.app.run()

        self.assertTrue(definitions["get_category_selection"].allow_self_loops)
        self.assertTrue(definitions["get_category_revision"].allow_self_loops)

    def test_third_checkbox_event_preserves_selection_and_refreshes_widgets(self):
        _, definitions = maps.app.run()

        definitions["set_category_selection"](("heat", "health"))
        self.assertIn("get_category_revision", definitions)
        self.assertIn("set_category_revision", definitions)
        revision = definitions["get_category_revision"]()
        third_checkbox = definitions["category_checks"][
            definitions["LAYER_SPECS"]["income"].label
        ]

        third_checkbox._args.on_change(True)

        self.assertEqual(
            definitions["get_category_selection"](),
            ("heat", "health"),
        )
        self.assertGreater(definitions["get_category_revision"](), revision)

    def test_unchecking_selected_category_leaves_one_selection(self):
        _, definitions = maps.app.run()

        transitioned = definitions["transition_category_selection"](
            ("heat", "health"),
            "health",
            False,
            definitions["CATEGORY_ORDER"],
        )

        self.assertEqual(transitioned, ("heat",))

    def test_empty_selection_uses_heat_fallback(self):
        _, definitions = maps.app.run()

        self.assertIn("normalize_category_selection", definitions)
        self.assertIn("resolve_selected_keys", definitions)
        normalized = definitions["normalize_category_selection"](
            (),
            definitions["CATEGORY_ORDER"],
        )
        selected_keys, message = definitions["resolve_selected_keys"](
            normalized,
            definitions["CATEGORY_ORDER"],
        )

        self.assertEqual(normalized, ())
        self.assertEqual(selected_keys, ("heat",))
        self.assertEqual(
            message,
            "At least one category is required; showing Heat.",
        )


if __name__ == "__main__":
    unittest.main()
