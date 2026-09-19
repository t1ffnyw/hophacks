import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    from pathlib import Path
    from importlib import import_module

    from dotenv import load_dotenv
    import marimo as mo

    data_module = import_module("scripts.csa_map_data")
    render_module = import_module("scripts.csa_map_render")
    whatif_model = import_module("data.what_if_regression")
    whatif_widget = import_module("scripts.tree_whatif_widget")
    CATEGORY_ORDER = data_module.CATEGORY_ORDER
    LAYER_SPECS = data_module.LAYER_SPECS
    load_csa_map_data = data_module.load_csa_map_data
    build_csa_map = render_module.build_csa_map
    canonicalize_selection = render_module.canonicalize_selection
    csa_whatif_stats = whatif_model.csa_whatif_stats
    regression_scatter_payload = whatif_model.regression_scatter_payload
    tree_illness_slope = whatif_model.tree_illness_slope
    build_whatif_widget = whatif_widget.build_whatif_widget

    _ = load_dotenv(Path(__file__).resolve().parent / ".env")
    return (
        CATEGORY_ORDER,
        LAYER_SPECS,
        Path,
        build_csa_map,
        build_whatif_widget,
        canonicalize_selection,
        csa_whatif_stats,
        load_csa_map_data,
        mo,
        os,
        regression_scatter_payload,
        tree_illness_slope,
    )


@app.cell
def _(Path):
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    return (data_dir,)


@app.cell
def _(data_dir, load_csa_map_data):
    csa_gdf, diagnostics = load_csa_map_data(data_dir)
    return csa_gdf, diagnostics


@app.cell
def _(diagnostics, mo):
    def _names(values):
        return ", ".join(values) if values else "none"

    missing_lines = "\n".join(
        f"- {diagnostics.layer_specs[key].label}: "
        f"{_names(diagnostics.missing_by_layer[key])}"
        for key in diagnostics.layer_specs
    )
    mo.md(f"""
    # Baltimore CSA interactive choropleth

    The map uses {diagnostics.joined_count} named Community Statistical
    Areas. 
    """)
    return


@app.cell
def _(CATEGORY_ORDER, LAYER_SPECS, mo):
    category_options = {
        LAYER_SPECS[key].label: key for key in CATEGORY_ORDER
    }
    category_selector = mo.ui.multiselect(
        options=list(category_options),
        value=[LAYER_SPECS["heat"].label],
        max_selections=2,
        label="Categories",
        full_width=True,
    )
    category_selector
    return category_options, category_selector


@app.cell
def _(canonicalize_selection, category_options, category_selector, mo):
    selected_labels = list(category_selector.value or [])
    selected_keys = tuple(
        category_options[label]
        for label in selected_labels
        if label in category_options
    )
    if not selected_keys:
        selected_keys = ("heat",)
        selection_message = "At least one category is required; showing Heat."
    else:
        selected_keys = canonicalize_selection(selected_keys)
        selection_message = "Choose up to two categories."
    mo.md(selection_message)
    return (selected_keys,)


@app.cell
def _(os):
    carto_key = os.getenv("CARTODB_API_KEY") or os.getenv("CARTO_KEY")
    if carto_key:
        tile_url = (
            "https://{s}.basemaps.cartocdn.com/"
            f"light_all/{{z}}/{{x}}/{{y}}.png?key={carto_key}"
        )
        tile_attr = "&copy; OpenStreetMap contributors &copy; CARTO"
        basemap_message = ""
    else:
        tile_url = None
        tile_attr = None
        basemap_message = (
            "CARTO basemap disabled: set CARTO_KEY or CARTODB_API_KEY "
            "in the environment to enable it."
        )
    return basemap_message, tile_attr, tile_url


@app.cell
def _(
    LAYER_SPECS,
    basemap_message,
    build_csa_map,
    csa_gdf,
    diagnostics,
    mo,
    selected_keys,
    tile_attr,
    tile_url,
):
    map_widget = build_csa_map(
        csa_gdf,
        selected_keys,
        LAYER_SPECS,
        diagnostics.thresholds,
        tile_url,
        tile_attr,
    )
    map_output = mo.Html(map_widget._repr_html_())
    if basemap_message:
        output = mo.vstack([mo.md(basemap_message), map_output])
    else:
        output = map_output
    output
    return


@app.cell
def _(mo):
    mo.md("""
    ## Heat-health vulnerability and tree cover

    This map always shows heat-health vulnerability with tree cover.
    Click a Community Statistical Area, then use the tree slider to
    explore a modeled change in heat-health vulnerability.
    """)
    return


@app.cell
def _(
    LAYER_SPECS,
    build_whatif_widget,
    csa_gdf,
    csa_whatif_stats,
    diagnostics,
    mo,
    regression_scatter_payload,
    tile_attr,
    tile_url,
    tree_illness_slope,
):
    vulnerability_tree_keys = ("health", "trees")
    whatif_slope = tree_illness_slope(csa_gdf)
    whatif_stats = csa_whatif_stats(csa_gdf)
    whatif_scatter = regression_scatter_payload(csa_gdf)
    whatif_explorer = mo.ui.anywidget(
        build_whatif_widget(
            csa_gdf,
            LAYER_SPECS,
            diagnostics.thresholds,
            whatif_slope,
            whatif_stats,
            tile_url,
            tile_attr,
            scatter_payload=whatif_scatter,
        )
    )
    whatif_explorer
    return whatif_explorer, vulnerability_tree_keys


if __name__ == "__main__":
    app.run()
