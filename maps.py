import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", css_file="custom.css")

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

    def toggle_active_bin(current, clicked):
        """Toggle: same cell clears, different cell switches."""
        if current == clicked:
            return None
        return clicked

    def active_bin_for_selection(selected_keys, current_bin):
        """Clear active_bin when fewer than two categories are selected."""
        if len(selected_keys) != 2:
            return None
        return current_bin

    return (
        active_bin_for_selection,
        checkbox_disabled_states,
        normalize_category_selection,
        resolve_selected_keys,
        toggle_active_bin,
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
    whatif_model = import_module("data.what_if_regression")
    whatif_widget = import_module("scripts.tree_whatif_widget")
    comparison_module = import_module("scripts.csa_comparison")
    comparison_widget_module = import_module("scripts.csa_map_widget")
    donate_widget_module = import_module("scripts.tree_donate_widget")
    CATEGORY_ORDER = data_module.CATEGORY_ORDER
    CLASS_ORDER = data_module.CLASS_ORDER
    LAYER_SPECS = data_module.LAYER_SPECS
    MAP_EMBED_HEIGHT = render_module.MAP_EMBED_HEIGHT
    PAIR_PALETTES = render_module.PAIR_PALETTES
    load_csa_map_data = data_module.load_csa_map_data
    build_csa_map = render_module.build_csa_map
    build_legend_html = render_module.build_legend_html
    canonicalize_selection = render_module.canonicalize_selection
    comparison_label = render_module.comparison_label
    embed_map_html = render_module.embed_map_html
    format_bivariate_bin_detail = render_module.format_bivariate_bin_detail
    csa_whatif_stats = whatif_model.csa_whatif_stats
    regression_scatter_payload = whatif_model.regression_scatter_payload
    tree_illness_slope = whatif_model.tree_illness_slope
    build_whatif_widget = whatif_widget.build_whatif_widget
    build_selection_widget = comparison_widget_module.build_selection_widget
    build_tree_donate_widget = donate_widget_module.build_tree_donate_widget
    render_comparison = comparison_module.render_comparison

    _ = load_dotenv(Path(__file__).resolve().parent / ".env")
    return (
        CATEGORY_ORDER,
        CLASS_ORDER,
        LAYER_SPECS,
        MAP_EMBED_HEIGHT,
        PAIR_PALETTES,
        Path,
        build_csa_map,
        build_legend_html,
        build_selection_widget,
        build_tree_donate_widget,
        build_whatif_widget,
        canonicalize_selection,
        comparison_label,
        csa_whatif_stats,
        embed_map_html,
        format_bivariate_bin_detail,
        load_csa_map_data,
        mo,
        os,
        regression_scatter_payload,
        render_comparison,
        tree_illness_slope,
    )


@app.cell
def _(Path):
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    return (data_dir,)


@app.cell
def _(data_dir, load_csa_map_data):
    csa_gdf, ics = load_csa_map_data(data_dir)
    return csa_gdf, ics

##########
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Executive Summary
 
    **Imagine it's 100 degrees outside. Is there shade on your block? A working air conditioner? Somewhere cooler to go?** In Baltimore, the answers depend on where you live. Across the city, the neighborhoods that heat up the most tend to be the ones with the fewest trees and the lowest household incomes, and they tend to rank higher for heat-related illness too. Same city, same afternoon, very different experiences.
 
    That divide isn't new. The 2019 investigation [*Code Red: Baltimore's Climate Divide*](https://cnsmaryland.org/interactives/summer-2019/code-red/introduction.html) documented how extreme heat compounds health challenges in communities with fewer resources and less protection. This notebook lets you see the pattern for yourself: pick a layer, or pair two, on the map, then use the what-if tool to add trees and watch what changes.
 
    By making these relationships visible, the project aims to support discussion about equitable heat protection and where further public-health investigation may be warranted.
    """)
    return


@app.cell(hide_code=True)
def _(Path, mo):
    images_dir = Path(__file__).resolve().parent / "images"
    roland_park = mo.image(
        src=images_dir / "roland_park.jpg",
        alt="Tree-lined residential street in Roland Park",
        width="100%",
        rounded=True,
        caption=(
            "Roland Park — a leafy north Baltimore neighborhood where mature "
            "street trees and large lots cast deep shade on quiet residential streets."
        ),
    )
    madison_eastend = mo.image(
        src=images_dir / "madison_eastend.jpg",
        alt="Rowhouses along a street in Madison Eastend",
        width="100%",
        rounded=True,
        caption=(
            "Madison Eastend — a denser east Baltimore rowhouse corridor, where "
            "hardscape dominates and tree canopy is far thinner than in Roland Park."
        ),
    )
    mo.hstack(
        [roland_park, madison_eastend],
        widths="equal",
        gap=1.25,
        align="start",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Problem Statement
 
    **Who gets to stay cool?**
 
    When a heat wave hits, staying safe takes resources: shade, air conditioning, somewhere to go. *Code Red* showed that the places that heat up fastest are often the ones where those resources are scarcest.
 
    We ask that question of the data: **where in Baltimore do hotter conditions, limited tree canopy, lower household incomes, and higher heat-illness rankings overlap?**
 
    We build on earlier reporting in two ways. We put four measures side by side at the same neighborhood scale, and we add a what-if tool that asks what more trees could change. First, the ingredients.
    """)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data Overview
 
    Our analysis brings together five datasets at a common geographic scale: Baltimore's 55 Community Statistical Areas (CSAs).
 
    | Dataset | What it measures | Source |
    |---|---|---|
    | CSA boundaries | Reference boundaries for Baltimore's Community Statistical Areas, used to join everything else | data.baltimorecity.gov |
    | Afternoon temperature | Modeled average afternoon temperature within each CSA | OSF |
    | Tree cover | Percent of each CSA covered by tree canopy | data.baltimorecity.gov |
    | Median household income | Median household income in each CSA | data.baltimorecity.gov |
    | Heat-Related Illness | A percentile rank for each ZIP code (92 means worse than 92% other zip codes nationwide) | ATSDR |
 
    Now, let's look at the map.
    """)
    return
 
 
# ---------------------------------------------------------------------------
# Core visualization
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _(diagnostics, mo):
    mo.md(f"""
    ## Core Visualization
 
    Start with the map. Pick one category to see how a single thing varies across the city, or pick two to see where they overlap. Then compare any two neighborhoods side by side, and finish with the what-if tool: click a neighborhood, add trees, and see how its heat-health ranking might change.
 
    """)
    return
 #############

@app.cell
def _(ics, mo):
    mo.md(f"""
    # Baltimore CSA interactive choropleth

    The map uses {ics.joined_count} named Community Statistical
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
    get_active_bin, set_active_bin = mo.state(
        None,
        allow_self_loops=True,
    )
    return (
        get_active_bin,
        get_category_revision,
        get_category_selection,
        set_active_bin,
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
    return (category_checks,)


@app.cell
def _(
    CATEGORY_ORDER,
    active_bin_for_selection,
    get_active_bin,
    get_category_selection,
    resolve_selected_keys,
    set_active_bin,
):
    selected_keys, selection_message = resolve_selected_keys(
        get_category_selection(),
        CATEGORY_ORDER,
    )
    _cleared = active_bin_for_selection(selected_keys, get_active_bin())
    if _cleared != get_active_bin():
        set_active_bin(_cleared)
    active_bin = _cleared
    return active_bin, selected_keys, selection_message


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
    CLASS_ORDER,
    LAYER_SPECS,
    PAIR_PALETTES,
    active_bin,
    build_legend_html,
    canonicalize_selection,
    comparison_label,
    ics,
    format_bivariate_bin_detail,
    mo,
    selected_keys,
    set_active_bin,
    toggle_active_bin,
):
    """Interactive bivariate color grid; kept separate so clicks update state."""
    selected = canonicalize_selection(selected_keys)
    bin_buttons = {}
    if len(selected) == 2:
        first, second = selected
        palette = PAIR_PALETTES[(first, second)]
        cell_px = 48
        label_font_px = 13
        bin_buttons = {}
        display_bins = {}
        for second_index in reversed(range(3)):
            for first_index in range(3):
                first_class = CLASS_ORDER[first_index]
                second_class = CLASS_ORDER[second_index]
                cell_key = (first_class, second_class)
                color = palette[second_index][first_index]
                is_selected = active_bin == cell_key
                border_style = (
                    "3px solid #111827"
                    if is_selected
                    else "1px solid #6b7280"
                )

                def _make_handler(ck=cell_key):
                    def _on_click(value):
                        set_active_bin(
                            lambda current: toggle_active_bin(current, ck)
                        )
                        # Marimo expects on_click to return the next button value.
                        return (value or 0) + 1

                    return _on_click

                # Keep the raw button so Marimo registers on_click. Styling the
                # button itself with .style() turns it into plain Html and drops
                # the handler (that is why clicks did nothing after the merge).
                button = mo.ui.button(
                    value=0,
                    label="\u00a0",
                    on_click=_make_handler(),
                    full_width=True,
                    tooltip=(
                        f"{comparison_label(first, LAYER_SPECS)}: {first_class}; "
                        f"{comparison_label(second, LAYER_SPECS)}: {second_class}"
                    ),
                )
                bin_buttons[cell_key] = button
                display_bins[cell_key] = mo.vstack([button], gap=0).style(
                    {
                        "--csa-bin-color": color,
                        "background": color,
                        "background-color": color,
                        "border": border_style,
                        "border-radius": "0",
                        "box-shadow": "none",
                        "box-sizing": "border-box",
                        "cursor": "pointer",
                        "display": "block",
                        "flex": f"0 0 {cell_px}px",
                        "height": f"{cell_px}px",
                        "max-width": f"{cell_px}px",
                        "min-height": f"{cell_px}px",
                        "min-width": f"{cell_px}px",
                        "overflow": "hidden",
                        "padding": "0",
                        "position": "relative",
                        "width": f"{cell_px}px",
                    }
                )

        grid_rows = []
        for second_index in reversed(range(3)):
            row_cells = []
            for first_index in range(3):
                first_class = CLASS_ORDER[first_index]
                second_class = CLASS_ORDER[second_index]
                row_cells.append(display_bins[(first_class, second_class)])
            grid_rows.append(
                mo.hstack(row_cells, gap=0, align="center")
            )
        grid_column = mo.vstack(grid_rows, gap=0, align="start")

        row_labels = []
        for second_index in reversed(range(3)):
            row_labels.append(
                mo.Html(
                    f"<div style='height:{cell_px}px;display:flex;align-items:center;"
                    f"font-size:{label_font_px}px;font-weight:600;padding-right:6px'>"
                    f"{CLASS_ORDER[second_index]}</div>"
                )
            )
        row_label_col = mo.vstack(row_labels, gap=0, align="end")

        second_label_html = mo.Html(
            f"<div style='font-size:{label_font_px}px;font-weight:600;"
            f"writing-mode:vertical-rl;text-orientation:mixed;"
            f"transform:rotate(180deg);display:flex;align-items:center;"
            f"justify-content:center;padding-right:6px'>"
            f"{comparison_label(second, LAYER_SPECS)}</div>"
        )

        col_label_cells = [
            mo.Html(
                f"<div style='width:{cell_px}px;text-align:center;"
                f"font-size:{label_font_px}px;font-weight:600;padding-top:4px;"
                f"box-sizing:border-box'>"
                f"{name}</div>"
            )
            for name in CLASS_ORDER
        ]
        col_labels = mo.hstack(col_label_cells, gap=0, align="start")

        first_label_html = mo.Html(
            f"<div style='width:{cell_px * 3}px;text-align:center;"
            f"font-size:{label_font_px}px;font-weight:600;margin-top:4px;"
            f"box-sizing:border-box'>"
            f"{comparison_label(first, LAYER_SPECS)}</div>"
        )

        grid_and_bottom = mo.vstack(
            [grid_column, col_labels, first_label_html],
            gap=0,
            align="start",
        )

        grid_with_row_labels = mo.hstack(
            [second_label_html, row_label_col, grid_and_bottom],
            gap=0.25,
            align="start",
        )

        legend_title = mo.Html(
            "<div style='text-align:center'>"
            "<div style='font-size:16px;font-weight:700;line-height:1.3'>"
            f"{comparison_label(first, LAYER_SPECS)} × "
            f"{comparison_label(second, LAYER_SPECS)}</div>"
            "<div style='font-size:12px;font-weight:400;color:#4b5563;"
            "margin-top:2px;margin-bottom:12px;line-height:1.3'>"
            "Click a square for more info</div>"
            "</div>"
        )

        bin_button_css = mo.Html(
            """
            <style>
            /* Colored square is the wrapper; stretch + hide Marimo's pill. */
            [style*="--csa-bin-color"] {
                padding: 0 !important;
                position: relative !important;
            }
            [style*="--csa-bin-color"] marimo-ui-element,
            [style*="--csa-bin-color"] marimo-button {
                bottom: 0 !important;
                box-sizing: border-box !important;
                display: block !important;
                height: 100% !important;
                inset: 0 !important;
                left: 0 !important;
                margin: 0 !important;
                max-height: none !important;
                max-width: none !important;
                min-height: 100% !important;
                min-width: 100% !important;
                /* Keep clickable; fully transparent still receives events. */
                opacity: 0.01 !important;
                padding: 0 !important;
                position: absolute !important;
                right: 0 !important;
                top: 0 !important;
                width: 100% !important;
                z-index: 2 !important;
            }
            </style>
            """
        )

        legend_items = [
            bin_button_css,
            legend_title,
            grid_with_row_labels,
        ]

        if active_bin is not None:
            detail_html = format_bivariate_bin_detail(
                first,
                second,
                active_bin[0],
                active_bin[1],
                LAYER_SPECS,
                ics.thresholds,
            )
            legend_items.append(
                mo.Html(
                    f"<div style='margin-top:12px'>{detail_html}</div>"
                )
            )

        legend_region = mo.vstack(
            legend_items,
            align="center",
            gap=0.25,
        ).style(
            {
                "background": "rgba(255, 255, 255, 0.96)",
                "border": "1px solid #9ca3af",
                "border-radius": "4px",
                "box-shadow": "0 1px 5px rgba(0,0,0,.35)",
                "color": "#111827",
                "font": "12px/1.35 Arial, sans-serif",
                "padding": "10px",
            }
        )
    else:
        legend_html = build_legend_html(
            selected_keys,
            LAYER_SPECS,
            ics.thresholds,
        )
        legend_region = mo.Html(legend_html)

    # Return buttons so Marimo registers their on_click handlers.
    return (legend_region,)


@app.cell
def _(
    LAYER_SPECS,
    MAP_EMBED_HEIGHT,
    active_bin,
    basemap_message,
    build_csa_map,
    category_checks,
    csa_gdf,
    ics,
    embed_map_html,
    legend_region,
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
        ics.thresholds,
        tile_url,
        tile_attr,
        active_bin=active_bin,
    )
    map_output = mo.Html(
        embed_map_html(map_widget, MAP_EMBED_HEIGHT)
    ).style({"height": MAP_EMBED_HEIGHT})
    category_header = mo.Html(
        "<div style='font-size:18px;font-weight:700;line-height:1.3'>"
        "Categories \N{EM DASH} select up to two</div>"
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

    legend_panel = legend_region.style(
        {
            "flex": "1 1 auto",
            "min-height": "0",
            "overflow-y": "auto",
        }
    )
    sidebar = mo.vstack(
        [category_group, legend_panel],
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
        widths=[6.5, 3.5],
        align="stretch",
        gap=0.5,
    )
    if basemap_message:
        output = mo.vstack([mo.md(basemap_message), map_layout])
    else:
        output = map_layout
    output
    return


@app.cell
def _(mo):
    mo.md("""
    ## Compare two Community Statistical Areas

    Choose two neighborhoods to compare their heat, health, income,
    and tree canopy measurements side by side.
    """)
    return


@app.cell
def _(build_selection_widget, csa_gdf, mo):
    comparison_widget = build_selection_widget(csa_gdf)
    comparison_map = mo.ui.anywidget(comparison_widget)
    comparison_map
    return (comparison_map,)


@app.cell
def _(comparison_map, csa_gdf, mo, render_comparison):
    selected_regions = list(
        comparison_map.value.get("selected_ids", [None, None])
    )
    comparison_panel = mo.Html(render_comparison(csa_gdf, selected_regions))
    comparison_panel
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
    ics,
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
            ics.thresholds,
            whatif_slope,
            whatif_stats,
            tile_url,
            tile_attr,
            scatter_payload=whatif_scatter,
        )
    )
    whatif_explorer
    return

#########
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Insight Synthesis
 
    1. **Lower-income neighborhoods tend to have fewer trees.**
 
    2. **Fewer trees tend to mean hotter afternoons.**
 
    3. **The hotter, less shaded places tend to rank higher for heat-related illnesses.**
 
    **Putting it all together.** Some neighborhoods are hot, short on trees, low on income, and high on the illness ranking. If shade is added somewhere, these are natural places to look at first.
    """)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Discussion
 
    **What the what-if tool is.** It lets you click a neighborhood, add tree cover with the slider, and see how its heat-health vulnerability ranking might change. It borrows the pattern we found across Baltimore, where neighborhoods with more trees tend to rank lower for heat-related illness, and applies it to estimate the effect. Think of it as a way to feel the pattern, not a forecast for any particular block.
 
    **What we can and cannot conclude.**
 
    - **Correlation is not causation.** Neighborhoods with more trees may also differ in other ways that affect heat, such as housing age, the amount of pavement and buildings, industrial land, nearby highways, and access to air conditioning.
    - **The what-if estimate is simple.** It applies a single average relationship to every neighborhood. In practice, the benefit of new trees depends on where they are planted, how large they grow, and what surrounds them, and young trees take years to provide shade.
    - **Our illness measure is coarse.** It's a percentile rank by ZIP code, so it can't tell us how many people were affected, and matching ZIPs to CSAs is approximate. The what-if result is a rough guide to direction, not a count of illnesses avoided.
 
    **Where we'd go next**
 
    1. **Get neighborhood-level illness counts,** ideally from the city or state health department, to test whether these patterns hold up in actual cases.
    2. **Account for other factors.** Replace our simple comparison with a model that includes income, pavement and building coverage, and housing age, to separate the effect of trees from everything that travels with them.
    3. **Make the what-if tool more realistic.** Add where trees can physically be planted, what it costs, and how long trees take to grow, and check the projections against neighborhoods that have actually gained trees.
    4. **Involve residents.** Communities know where people go to cool off and where shade is missing. Their input should shape where any planting happens.
 
    Trees are one tool among many, but they matter for health as well as comfort. Shade and cooler air can lower the heat people are exposed to, and heat is hardest on those with heart, kidney, and lung conditions. Cooling centers, help paying for air conditioning, and outreach to older and isolated neighbors matter too. But whether there's shade on your block shouldn't depend on where you live.
    """)
    return


@app.cell(hide_code=True)
def _(build_tree_donate_widget, mo):
    tree_donate = mo.ui.anywidget(build_tree_donate_widget())
    treebaltimore_blurb = mo.md(
        """
        ### About TreeBaltimore

        The TreeBaltimore partnership, housed within the Baltimore City Department of
        Recreation and Parks’ Forestry Division, is a citywide coalition of nonprofits,
        city agencies, community groups and individuals working together to grow a
        healthy tree canopy for all residents to enjoy.

        It takes a community of people to grow a community of trees! 
        Your donation will increase our capacity to plant​, care for, and protect our tree canopy.  
        
        Support our future urban forest today by making a donation or by volunteering. 
        More information at treebaltimore.org

        """
    )
    mo.hstack(
        [tree_donate, treebaltimore_blurb],
        widths=[1, 1.4],
        gap=1.5,
        align="center",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reflection
 
    ### Feedback on marimo
 
    **What worked well.** Reactivity was the best part. When a dropdown or slider changes, the map updates with no callback code, which made the what-if tool much easier to build than it would have been in a traditional notebook. Notebooks being plain `.py` files also let us collaborate with git as a team and mirror our GitHub repo in molab for sharing.
 
    **What was hard.** Setting up the environment in VS Code took us a while, and errors in VS Code's notebook view were also confusing, since it wasn't always clear that the problem wasn't our code.
 
    ### Working with AI tools
 
    We used Claude to plan the notebook and divide the work, and Grok through Cursor to build many of the visuals, including the map and slider code.
 
    **What it sped up.** It turned our idea of a single map where you pick up to two variables into working code much faster than we could have alone.
 
    **What it got wrong.** Sometimes it didn't execute our vision properly, and the interface it produced could be difficult to follow. We decided to redesign the map legends so the data was easier to read at a glance. We had to read the errors, fix the code, or go back and re-prompt.
 
    **What we learned about prompting.** Specific prompts worked much better than vague ones. Our habits were to ask for one change at a time, state marimo's rules up front, check every result against our real data, and paste the exact error message when something broke. The tools were fast at drafts, but knowing our data and catching mistakes stayed our job.
    """)
    return


if __name__ == "__main__":
    app.run()
