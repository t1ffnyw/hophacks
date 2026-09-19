"""Folium rendering helpers for the Baltimore CSA choropleth."""

from __future__ import annotations

import html as html_lib
import json
from typing import Mapping, Sequence

import folium
import geopandas as gpd
from branca.element import Figure, MacroElement, Template

from scripts.csa_map_data import (
    CATEGORY_ORDER,
    CLASS_ORDER,
    LayerSpec,
    TercileThresholds,
)


MISSING_COLOR = "#bdbdbd"
MAP_EMBED_HEIGHT = "520px"
_TOOLTIP_STYLE = (
    "background-color: white; color: #111827; "
    "font-family: arial; font-size: 12px; padding: 8px;"
)
_POPUP_PANEL_ALPHA = "rgba(255, 255, 255, 0.85)"
_POPUP_STYLE = (
    f"background-color: {_POPUP_PANEL_ALPHA}; color: #111827; "
    "font-family: arial; font-size: 12px; padding: 8px;"
)
SINGLE_PALETTES: dict[str, tuple[str, str, str]] = {
    "heat": ("#fee5d9", "#fb6a4a", "#a50f15"),
    "health": ("#efedf5", "#bcbddc", "#756bb1"),
    "income": ("#deebf7", "#9ecae1", "#2171b5"),
    "trees": ("#e5f5e0", "#a1d99b", "#238b45"),
}

# Rows run from the second category's Low to High; columns run from the
# first category's Low to High. Each pair is intentionally explicit so that
# the visual meaning is stable across runs and does not depend on alpha layers.
PAIR_PALETTES: dict[tuple[str, str], tuple[tuple[str, str, str], ...]] = {
    (
        "heat",
        "health",
    ): (
        ("#f3f4f6", "#f8c7c2", "#e87870"),
        ("#d9cbe5", "#df9999", "#b84c58"),
        ("#b9a5d0", "#a96887", "#713c68"),
    ),
    (
        "heat",
        "income",
    ): (
        ("#f3f4f6", "#f6c7c0", "#e77c73"),
        ("#c8dceb", "#d99d9b", "#b15b69"),
        ("#86b7d5", "#9a748f", "#624d73"),
    ),
    (
        "heat",
        "trees",
    ): (
        ("#f3f4f6", "#f7c8bf", "#e8796e"),
        ("#cce5c9", "#d99c8d", "#b34e4c"),
        ("#8ec49b", "#9f766d", "#684b4e"),
    ),
    (
        "health",
        "income",
    ): (
        ("#f3f4f6", "#cbddec", "#7faed0"),
        ("#ddd4e7", "#b7b0ce", "#7188af"),
        ("#b69bc9", "#8e7eaf", "#5d5689"),
    ),
    (
        "health",
        "trees",
    ): (
        ("#f3f4f6", "#d2e6cf", "#93c69a"),
        ("#ddd2e7", "#c2b6c9", "#888d91"),
        ("#b598cb", "#987fa2", "#5f5971"),
    ),
    (
        "income",
        "trees",
    ): (
        ("#f3f4f6", "#cfe5d0", "#8ec59b"),
        ("#c8dceb", "#b4d1bd", "#729e9d"),
        ("#87b7d4", "#7fa9ad", "#527b8a"),
    ),
}

CLASS_INDEX = {class_name: index for index, class_name in enumerate(CLASS_ORDER)}


def canonicalize_selection(selected_keys: Sequence[str]) -> tuple[str, ...]:
    """Return one or two selected categories in the project-wide order."""
    selected = set(selected_keys)
    unknown = selected.difference(CATEGORY_ORDER)
    if unknown:
        raise ValueError(f"Unknown map categories: {sorted(unknown)}")

    ordered = tuple(key for key in CATEGORY_ORDER if key in selected)
    if len(ordered) not in (1, 2):
        raise ValueError("Select one or two map categories")
    return ordered


def _format_measurement(value: object, spec: LayerSpec) -> str:
    if value is None or value != value:
        return "Missing"
    numeric = float(value)
    if spec.units == "USD":
        return f"${numeric:,.0f}"
    return f"{numeric:,.1f}"


def _format_boundary(value: float | None, spec: LayerSpec) -> str:
    if value is None:
        return "not available"
    if spec.units == "USD":
        return f"${value:,.0f}"
    return f"{value:,.1f}"


def _class_range(
    class_name: str, thresholds: TercileThresholds, spec: LayerSpec
) -> str:
    if thresholds.valid_count == 0:
        return "no valid values"
    if class_name == "Low":
        text = f"≤ {_format_boundary(thresholds.low_max, spec)}"
    elif class_name == "Medium":
        text = (
            f"> {_format_boundary(thresholds.low_max, spec)} and "
            f"≤ {_format_boundary(thresholds.medium_max, spec)}"
        )
    else:
        text = f"> {_format_boundary(thresholds.medium_max, spec)}"
    if class_name in thresholds.empty_classes:
        return f"{text} (no areas)"
    return text


def _prepare_tooltip_columns(
    gdf: gpd.GeoDataFrame,
    selected_keys: tuple[str, ...],
    specs: Mapping[str, LayerSpec],
) -> gpd.GeoDataFrame:
    prepared = gdf.copy()
    for key in selected_keys:
        spec = specs[key]
        value_field = f"_tooltip_value_{key}"
        class_field = f"_tooltip_class_{key}"
        prepared[value_field] = prepared[spec.column].map(
            lambda value, s=spec: _format_measurement(value, s)
        )
        prepared[class_field] = (
            prepared[f"{key}_class"].fillna("Missing").astype(str)
        )
    return prepared


def _prepare_popup_columns(
    gdf: gpd.GeoDataFrame,
    specs: Mapping[str, LayerSpec],
) -> gpd.GeoDataFrame:
    prepared = gdf.copy()
    for key in CATEGORY_ORDER:
        spec = specs[key]
        prepared[f"_popup_value_{key}"] = prepared[spec.column].map(
            lambda value, s=spec: _format_measurement(value, s)
        )
    return prepared


def _style_function(
    selected_keys: tuple[str, ...],
    active_bin: tuple[str, str] | None = None,
) -> callable:
    def style(feature: dict) -> dict[str, object]:
        properties = feature["properties"]
        classes = tuple(
            properties.get(f"{key}_class") for key in selected_keys
        )
        if any(class_name not in CLASS_INDEX for class_name in classes):
            fill_color = MISSING_COLOR
        elif len(selected_keys) == 1:
            fill_color = SINGLE_PALETTES[selected_keys[0]][
                CLASS_INDEX[classes[0]]
            ]
        else:
            first, second = selected_keys
            fill_color = PAIR_PALETTES[(first, second)][
                CLASS_INDEX[classes[1]]
            ][CLASS_INDEX[classes[0]]]
            if active_bin is not None and classes != active_bin:
                fill_color = MISSING_COLOR
        return {
            "color": "#4b5563",
            "fillColor": fill_color,
            "fillOpacity": 1.0,
            "weight": 0.6,
        }

    return style


def _tooltip(
    selected_keys: tuple[str, ...], specs: Mapping[str, LayerSpec]
) -> folium.GeoJsonTooltip:
    fields = ["Community"]
    aliases = ["CSA"]
    for key in selected_keys:
        spec = specs[key]
        fields.append(f"_tooltip_value_{key}")
        aliases.append(spec.label)
        if len(selected_keys) == 2:
            fields.append(f"_tooltip_class_{key}")
            aliases.append(f"{spec.label} class")
    return folium.GeoJsonTooltip(
        fields=fields,
        aliases=aliases,
        labels=True,
        sticky=False,
        localize=True,
        style=_TOOLTIP_STYLE,
    )


def _popup(specs: Mapping[str, LayerSpec]) -> folium.GeoJsonPopup:
    fields = ["Community"]
    aliases = ["CSA"]
    for key in CATEGORY_ORDER:
        fields.append(f"_popup_value_{key}")
        aliases.append(specs[key].label)
    return folium.GeoJsonPopup(
        fields=fields,
        aliases=aliases,
        labels=True,
        localize=True,
        style=_POPUP_STYLE,
        closeButton=False,
    )


# Plain-language unit lines shown under single-category legend titles.
LEGEND_UNIT_DESCRIPTIONS: dict[str, str] = {
    "heat": "Degrees Celsius",
    "health": "Heat-health risk index (percentile)",
    "income": "USD",
    "trees": "Percent of neighborhood area",
}

# Shorter names for bivariate comparison titles and axes.
LEGEND_COMPARISON_LABELS: dict[str, str] = {
    "heat": "Heat",
    "health": "Heat-Health Vulnerability",
    "income": "Household Income",
    "trees": "Tree Canopy",
}


def comparison_label(key: str, specs: Mapping[str, LayerSpec]) -> str:
    """Return the short display label used in two-category legends."""
    return LEGEND_COMPARISON_LABELS.get(key, specs[key].label)


def _single_legend(
    key: str,
    spec: LayerSpec,
    thresholds: TercileThresholds,
) -> str:
    rows = []
    for class_name, color in zip(CLASS_ORDER, SINGLE_PALETTES[key]):
        rows.append(
            "<div class='csa-legend-row'>"
            f"<span class='csa-swatch' style='background:{color}'></span>"
            f"<span><strong>{class_name}</strong>: "
            f"{_class_range(class_name, thresholds, spec)}</span>"
            "</div>"
        )
    caveat = (
        f"<div class='csa-legend-note'>{html_lib.escape(spec.caveat)}</div>"
        if spec.caveat
        else ""
    )
    unit_description = LEGEND_UNIT_DESCRIPTIONS.get(key, spec.units)
    return (
        "<div class='csa-map-legend'>"
        f"<div class='csa-legend-title'>{html_lib.escape(spec.label)}</div>"
        f"<div class='csa-legend-units'>{html_lib.escape(unit_description)}</div>"
        + "".join(rows)
        + caveat
        + "</div>"
    )


def format_bivariate_bin_detail(
    first: str,
    second: str,
    first_class: str,
    second_class: str,
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
) -> str:
    """Return detail HTML for one selected bivariate legend cell."""
    first_spec = specs[first]
    second_spec = specs[second]
    first_range = _class_range(first_class, thresholds[first], first_spec)
    second_range = _class_range(second_class, thresholds[second], second_spec)
    first_name = comparison_label(first, specs)
    second_name = comparison_label(second, specs)
    return (
        "<div class='csa-bin-detail'>"
        f"<div><strong>{html_lib.escape(first_name)}</strong>: "
        f"{html_lib.escape(first_class)} ({html_lib.escape(first_range)})</div>"
        f"<div><strong>{html_lib.escape(second_name)}</strong>: "
        f"{html_lib.escape(second_class)} ({html_lib.escape(second_range)})</div>"
        "</div>"
    )


def _bivariate_legend(
    first: str,
    second: str,
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
) -> str:
    first_spec = specs[first]
    second_spec = specs[second]
    first_name = comparison_label(first, specs)
    second_name = comparison_label(second, specs)
    palette = PAIR_PALETTES[(first, second)]
    grid_rows = []
    for second_index in reversed(range(3)):
        cells = []
        for first_index in range(3):
            first_class = CLASS_ORDER[first_index]
            second_class = CLASS_ORDER[second_index]
            title = (
                f"{first_name}: "
                f"{_class_range(first_class, thresholds[first], first_spec)}; "
                f"{second_name}: "
                f"{_class_range(second_class, thresholds[second], second_spec)}"
            )
            cells.append(
                f"<td title='{html_lib.escape(title, quote=True)}' "
                f"data-first-class='{first_class}' "
                f"data-second-class='{second_class}' "
                f"style='background:{palette[second_index][first_index]}; cursor:pointer'"
                "></td>"
            )
        grid_rows.append(
            f"<tr><th scope='row'>{CLASS_ORDER[second_index]}</th>"
            f"{''.join(cells)}</tr>"
        )
    column_labels = "".join(
        f"<td class='csa-bivariate-col-label'>{name}</td>"
        for name in CLASS_ORDER
    )
    column_label_row = f"<tr><td></td>{column_labels}</tr>"
    caveats = " ".join(
        caveat for caveat in (first_spec.caveat, second_spec.caveat) if caveat
    )
    caveat_html = (
        f"<div class='csa-legend-note'>{html_lib.escape(caveats)}</div>"
        if caveats
        else ""
    )
    return (
        "<div class='csa-map-legend'>"
        "<div class='csa-legend-title'>"
        f"{html_lib.escape(first_name)} × "
        f"{html_lib.escape(second_name)}</div>"
        f"<div class='csa-axis-y-label'>{html_lib.escape(second_name)}</div>"
        "<table class='csa-bivariate-grid'><tbody>"
        + "".join(grid_rows)
        + column_label_row
        + "</tbody></table>"
        f"<div class='csa-axis-x-label'>{html_lib.escape(first_name)}</div>"
        + caveat_html
        + "</div>"
    )


def build_legend_html(
    selected_keys: Sequence[str],
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
) -> str:
    """Return standalone legend HTML for the notebook sidebar."""
    selected = canonicalize_selection(selected_keys)
    if len(selected) == 1:
        legend = _single_legend(
            selected[0],
            specs[selected[0]],
            thresholds[selected[0]],
        )
    else:
        legend = _bivariate_legend(
            selected[0],
            selected[1],
            specs,
            thresholds,
        )
    css = """
    <style>
    .csa-map-layout {
        max-width: none;
        width: 100%;
    }
    .csa-map-legend {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid #9ca3af;
        border-radius: 4px;
        box-shadow: 0 1px 5px rgba(0,0,0,.35);
        color: #111827;
        font: 12px/1.35 Arial, sans-serif;
        padding: 10px;
    }
    .csa-legend-title { font-size: 18px; font-weight: 700; margin-bottom: 3px; }
    .csa-legend-units { color: #374151; font-size: 12px; margin-bottom: 2px; }
    .csa-legend-row { align-items: center; display: flex; gap: 5px; margin-top: 4px; }
    .csa-legend-note { color: #374151; font-size: 11px; margin-top: 6px; }
    .csa-swatch { border: 1px solid #6b7280; display: inline-block; flex: 0 0 auto;
        height: 14px; width: 22px; }
    .csa-bivariate-grid { border-collapse: collapse; margin: 5px auto 2px; }
    .csa-bivariate-grid td { border: 1px solid #6b7280; height: 48px; width: 48px; }
    .csa-bivariate-grid th { font-weight: 600; padding: 2px 4px; }
    .csa-bivariate-col-label { font-size: 11px; text-align: center; border: none !important;
        height: auto !important; padding-top: 2px; }
    .csa-bin-selected { outline: 3px solid #111827; outline-offset: -2px; z-index: 1; position: relative; }
    .csa-axis-x-label { font-size: 11px; font-weight: 600; margin-top: 2px; text-align: center; }
    .csa-axis-y-label { font-size: 11px; font-weight: 600; margin-top: 4px; }
    .csa-bin-detail { background: #f9fafb; border: 1px solid #d1d5db; border-radius: 3px;
        font-size: 11px; margin-top: 6px; padding: 6px 8px; }
    @media (max-width: 640px) {
        .csa-map-layout { max-width: none; }
        .csa-map-legend { font-size: 10px; padding: 6px; }
        .csa-legend-title { font-size: 16px; }
        .csa-legend-units { font-size: 11px; }
        .csa-legend-note { font-size: 9px; }
    }
    </style>
    """
    return css + f"<div class='csa-map-layout'>{legend}</div>"


# Match highlight_function so click/keyboard focus outlines the region path
# instead of Chrome's rectangular SVG focus ring around the feature bounds.
_REGION_HIGHLIGHT = {
    "color": "#111827",
    "fillOpacity": 1.0,
    "weight": 2.5,
}


class _RegionFocusStyle(MacroElement):
    """Focus stroke + popup chrome styled like Leaflet tooltips."""

    def __init__(self) -> None:
        super().__init__()
        self._name = "RegionFocusStyle"
        color = _REGION_HIGHLIGHT["color"]
        weight = _REGION_HIGHLIGHT["weight"]
        panel = _POPUP_PANEL_ALPHA
        self._template = Template(
            f"""
            {{% macro header(this, kwargs) %}}
            <style>
            .leaflet-container path.leaflet-interactive:focus {{
                outline: none;
                stroke: {color};
                stroke-width: {weight};
            }}
            /* Transparent outer Leaflet shell; semi-opaque inner Folium panel. */
            .leaflet-popup-content-wrapper {{
                background: transparent;
                color: #111827;
                border: none;
                border-radius: 3px;
                box-shadow: none;
                padding: 0;
            }}
            .leaflet-popup-content {{
                margin: 0;
                line-height: 1.35;
                font: 12px/1.35 Arial, sans-serif;
            }}
            .leaflet-popup-tip {{
                background: {panel};
                box-shadow: 0 1px 3px rgba(0,0,0,0.4);
                width: 12px;
                height: 12px;
                margin: -6px auto 0;
                padding: 0;
            }}
            .leaflet-popup-close-button {{
                display: none;
            }}
            .foliumpopup {{
                background-color: {panel};
                color: #111827;
                font-family: arial;
                font-size: 12px;
                padding: 8px;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.4);
            }}
            </style>
            {{% endmacro %}}
            """
        )


class _ResetToBaltimore(MacroElement):
    """A small Leaflet control that returns to the initial CSA bounds."""

    def __init__(self, bounds: list[list[float]]) -> None:
        super().__init__()
        self._name = "ResetToBaltimore"
        self.bounds_json = json.dumps(bounds)
        self._template = Template(
            """
            {% macro script(this, kwargs) %}
            var resetControl = L.control({position: 'topright'});
            resetControl.onAdd = function(map) {
                var container = L.DomUtil.create(
                    'div', 'leaflet-bar leaflet-control csa-reset-control'
                );
                var button = L.DomUtil.create('button', '', container);
                button.type = 'button';
                button.innerHTML = 'Reset to Baltimore';
                button.title = 'Reset to Baltimore';
                button.style.cssText =
                    'background:#fff;border:0;cursor:pointer;padding:5px 7px;'
                    + 'font:12px Arial,sans-serif;white-space:nowrap;';
                L.DomEvent.disableClickPropagation(container);
                button.onclick = function() {
                    {{ this._parent.get_name() }}.fitBounds(
                        {{ this.bounds_json }}
                    );
                };
                return container;
            };
            resetControl.addTo({{ this._parent.get_name() }});
            {% endmacro %}
            """
        )


def build_csa_map(
    gdf: gpd.GeoDataFrame,
    selected_keys: Sequence[str],
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
    tile_url: str | None,
    tile_attr: str | None,
    active_bin: tuple[str, str] | None = None,
) -> folium.Map:
    """Build one opaque GeoJson map for one or two selected categories."""
    selected = canonicalize_selection(selected_keys)
    render_gdf = _prepare_tooltip_columns(gdf, selected, specs)
    render_gdf = _prepare_popup_columns(render_gdf, specs)
    if render_gdf.crs is not None and render_gdf.crs.to_epsg() != 4326:
        render_gdf = render_gdf.to_crs("EPSG:4326")

    min_x, min_y, max_x, max_y = render_gdf.total_bounds
    bounds = [[float(min_y), float(min_x)], [float(max_y), float(max_x)]]
    center = [(min_y + max_y) / 2, (min_x + max_x) / 2]
    map_kwargs = {
        "location": center,
        "zoom_start": 11,
        "min_zoom": 10,
        "minZoom": 10,
        "control_scale": True,
        "zoom_control": True,
        "tiles": None,
    }
    if tile_url:
        map_kwargs["tiles"] = tile_url
        map_kwargs["attr"] = tile_attr or ""

    map_widget = folium.Map(**map_kwargs)
    folium.GeoJson(
        data=render_gdf.to_json(drop_id=True),
        name="Baltimore CSA choropleth",
        style_function=_style_function(selected, active_bin=active_bin),
        highlight_function=lambda feature: dict(_REGION_HIGHLIGHT),
        tooltip=_tooltip(selected, specs),
        popup=_popup(specs),
        show=True,
    ).add_to(map_widget)
    map_widget.fit_bounds(bounds)
    map_widget.add_child(_RegionFocusStyle())
    map_widget.add_child(_ResetToBaltimore(bounds))
    return map_widget

def embed_map_html(
    map_widget: folium.Map,
    height: str = MAP_EMBED_HEIGHT,
) -> str:
    """Embed a Folium map in a fixed-height iframe for stable notebook layout."""
    figure = Figure(width="100%", height=height)
    figure.add_child(map_widget)
    return figure._repr_html_()
