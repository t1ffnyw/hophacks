import unittest

import maps


class MapsNotebookTests(unittest.TestCase):
    def test_notebook_defaults_to_heat_and_loads_all_csas(self):
        _, definitions = maps.app.run()

        self.assertEqual(definitions["selected_keys"], ("heat",))
        self.assertEqual(len(definitions["csa_gdf"]), 55)
        self.assertEqual(len(definitions["category_options"]), 4)
        self.assertIn("Heat-health vulnerability", definitions["category_options"])
        self.assertEqual(
            definitions["category_selector"]._args.args["max-selections"],
            2,
        )


if __name__ == "__main__":
    unittest.main()
