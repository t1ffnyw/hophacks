import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    def checkbox_disabled_states(selected_keys, category_order):
        selected = set(selected_keys)
        at_limit = len(selected) >= 2
        return {
            key: at_limit and key not in selected
            for key in category_order
        }

    def normalize_category_selection(selected_keys, category_order):
        selected = set(selected_keys)
        unknown = selected.difference(category_order)
        if unknown:
            raise ValueError(f"Unknown map categories: {sorted(unknown)}")
        if len(selected) > 2:
            raise ValueError("Select one or two map categories")
        return tuple(key for key in category_order if key in selected)

    def transition_category_selection(
        selected_keys,
        key,
        checked,
        category_order,
    ):
        selection = list(selected_keys)
        if checked and key not in selection and len(selection) < 2:
            selection.append(key)
        elif not checked and key in selection:
            selection.remove(key)
        return normalize_category_selection(selection, category_order)

    def resolve_selected_keys(selected_keys, category_order):
        normalized = normalize_category_selection(selected_keys, category_order)
        if not normalized:
            return ("heat",), "At least one category is required; showing Heat."
        return normalized, ""

    return (
        checkbox_disabled_states,
        normalize_category_selection,
        resolve_selected_keys,
        transition_category_selection,
    )


@app.cell
def _():
    import os
    from pathlib import Path
    from importlib import import_module

    from dotenv import load_dotenv
    import marimo as mo

    data_module = import_module("scripts.csa_map_data")
    render_module = import_module("scripts.csa_map_render")
    CATEGORY_ORDER = data_module.CATEGORY_ORDER
    LAYER_SPECS = data_module.LAYER_SPECS
    MAP_EMBED_HEIGHT = render_module.MAP_EMBED_HEIGHT
    load_csa_map_data = data_module.load_csa_map_data
    build_csa_map = render_module.build_csa_map
    build_legend_html = render_module.build_legend_html
    canonicalize_selection = render_module.canonicalize_selection
    embed_map_html = render_module.embed_map_html

    _ = load_dotenv(Path(__file__).resolve().parent / ".env")
    return (
        CATEGORY_ORDER,
        LAYER_SPECS,
        MAP_EMBED_HEIGHT,
        Path,
        build_csa_map,
        build_legend_html,
        canonicalize_selection,
        embed_map_html,
        load_csa_map_data,
        mo,
        os,
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
    mo.md(f"""
# Baltimore CSA interactive choropleth

The map uses {diagnostics.joined_count} named Community Statistical
Areas.
""")
    return


@app.cell
def _(mo):
    get_category_selection, set_category_selection = mo.state(
        ("heat",),
        allow_self_loops=True,
    )
    get_category_revision, set_category_revision = mo.state(
        0,
        allow_self_loops=True,
    )
    return (
        get_category_revision,
        get_category_selection,
        set_category_revision,
        set_category_selection,
    )


@app.cell
def _(
    CATEGORY_ORDER,
    LAYER_SPECS,
    checkbox_disabled_states,
    get_category_revision,
    get_category_selection,
    mo,
    normalize_category_selection,
    set_category_revision,
    set_category_selection,
    transition_category_selection,
):
    _ = get_category_revision()
    category_options = {
        LAYER_SPECS[key].label: key for key in CATEGORY_ORDER
    }
    current_selection = normalize_category_selection(
        get_category_selection(),
        CATEGORY_ORDER,
    )
    disabled_states = checkbox_disabled_states(
        current_selection,
        CATEGORY_ORDER,
    )

    def _on_category_change(key):
        def _update(checked):
            set_category_selection(
                lambda current: transition_category_selection(
                    current,
                    key,
                    checked,
                    CATEGORY_ORDER,
                )
            )
            set_category_revision(lambda revision: revision + 1)

        return _update

    category_checks = {
        label: mo.ui.checkbox(
            value=(key in current_selection),
            label=label,
            disabled=disabled_states[key],
            on_change=_on_category_change(key),
        )
        for label, key in category_options.items()
    }
    return category_checks, category_options


@app.cell
def _(CATEGORY_ORDER, get_category_selection, resolve_selected_keys):
    selected_keys, selection_message = resolve_selected_keys(
        get_category_selection(),
        CATEGORY_ORDER,
    )
    return selected_keys, selection_message


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
    MAP_EMBED_HEIGHT,
    basemap_message,
    build_csa_map,
    build_legend_html,
    category_checks,
    csa_gdf,
    diagnostics,
    embed_map_html,
    mo,
    selected_keys,
    selection_message,
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
    legend_html = build_legend_html(
        selected_keys,
        LAYER_SPECS,
        diagnostics.thresholds,
    )
    map_output = mo.Html(
        embed_map_html(map_widget, MAP_EMBED_HEIGHT)
    ).style({"height": MAP_EMBED_HEIGHT})
    category_header = mo.md(
        "**Categories** \N{EM DASH} select up to two"
    )
    checkbox_group = mo.vstack(
        list(category_checks.values()),
        align="start",
        gap=0.25,
    )
    category_items = [category_header, checkbox_group]
    if selection_message:
        category_items.append(mo.md(selection_message))
    category_group = mo.vstack(category_items, align="stretch", gap=0.5)
    legend_region = mo.Html(legend_html).style(
        {
            "flex": "1 1 auto",
            "min-height": "0",
            "overflow-y": "auto",
        }
    )
    sidebar = mo.vstack(
        [category_group, legend_region],
        align="stretch",
        gap=0.5,
    ).style(
        {
            "box-sizing": "border-box",
            "height": MAP_EMBED_HEIGHT,
            "min-height": "0",
            "overflow": "hidden",
            "padding-right": "4px",
        }
    )
    map_layout = mo.hstack(
        [map_output, sidebar],
        widths=[7, 3],
        align="stretch",
        gap=0.5,
    )
    if basemap_message:
        output = mo.vstack([mo.md(basemap_message), map_layout])
    else:
        output = map_layout
    output
    return legend_html, map_layout


if __name__ == "__main__":
    app.run()
