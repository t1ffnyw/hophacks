"""Folium rendering helpers for the Baltimore CSA choropleth."""

from __future__ import annotations

import html as html_lib
import json
from typing import Mapping, Sequence

import folium
import geopandas as gpd
from branca.element import Element, MacroElement, Template

from scripts.csa_map_data import (
    CATEGORY_ORDER,
    CLASS_ORDER,
    LayerSpec,
    TercileThresholds,
)


MISSING_COLOR = "#bdbdbd"
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
            lambda value: _format_measurement(value, spec)
        )
        prepared[class_field] = (
            prepared[f"{key}_class"].fillna("Missing").astype(str)
        )
    return prepared


def _style_function(
    selected_keys: tuple[str, ...],
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
        aliases.append(f"{spec.label} ({spec.units}; {spec.period})")
        if len(selected_keys) == 2:
            fields.append(f"_tooltip_class_{key}")
            aliases.append(f"{spec.label} class")
    return folium.GeoJsonTooltip(
        fields=fields,
        aliases=aliases,
        labels=True,
        sticky=False,
        localize=True,
        style=(
            "background-color: white; color: #111827; "
            "font-family: arial; font-size: 12px; padding: 8px;"
        ),
    )


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
    return (
        "<div class='csa-map-legend'>"
        f"<div class='csa-legend-title'>{html_lib.escape(spec.label)}</div>"
        f"<div>{html_lib.escape(spec.units)}</div>"
        f"<div>{html_lib.escape(spec.period)}</div>"
        "<div class='csa-legend-note'>Darker means a higher value; "
        "this is not inherently better or worse.</div>"
        + "".join(rows)
        + caveat
        + "<div class='csa-legend-row'>"
        f"<span class='csa-swatch' style='background:{MISSING_COLOR}'></span>"
        "<span><strong>Missing</strong>: no selected measurement</span>"
        "</div></div>"
    )


def _bivariate_legend(
    first: str,
    second: str,
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
) -> str:
    first_spec = specs[first]
    second_spec = specs[second]
    palette = PAIR_PALETTES[(first, second)]
    grid_rows = []
    for second_index in reversed(range(3)):
        cells = []
        for first_index in range(3):
            first_class = CLASS_ORDER[first_index]
            second_class = CLASS_ORDER[second_index]
            title = (
                f"{first_spec.label}: "
                f"{_class_range(first_class, thresholds[first], first_spec)}; "
                f"{second_spec.label}: "
                f"{_class_range(second_class, thresholds[second], second_spec)}"
            )
            cells.append(
                f"<td title='{html_lib.escape(title, quote=True)}' "
                f"style='background:{palette[second_index][first_index]}'"
                "></td>"
            )
        grid_rows.append(
            f"<tr><th>{CLASS_ORDER[second_index]}</th>{''.join(cells)}</tr>"
        )
    first_ranges = "; ".join(
        f"{name}: {_class_range(name, thresholds[first], first_spec)}"
        for name in CLASS_ORDER
    )
    second_ranges = "; ".join(
        f"{name}: {_class_range(name, thresholds[second], second_spec)}"
        for name in CLASS_ORDER
    )
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
        "<div class='csa-legend-title'>Bivariate choropleth</div>"
        f"<div class='csa-axis-y'>{html_lib.escape(second_spec.label)} "
        "Low → High</div>"
        "<table class='csa-bivariate-grid'><tbody>"
        + "".join(grid_rows)
        + "</tbody></table>"
        f"<div class='csa-axis-x'>Low → High: "
        f"{html_lib.escape(first_spec.label)}</div>"
        f"<div class='csa-legend-note'><strong>{html_lib.escape(first_spec.label)}"
        f"</strong> ({html_lib.escape(first_spec.units)}; "
        f"{html_lib.escape(first_spec.period)}) — "
        f"{html_lib.escape(first_ranges)}</div>"
        f"<div class='csa-legend-note'><strong>{html_lib.escape(second_spec.label)}"
        f"</strong> ({html_lib.escape(second_spec.units)}; "
        f"{html_lib.escape(second_spec.period)}) — "
        f"{html_lib.escape(second_ranges)}</div>"
        "<div class='csa-legend-row'>"
        f"<span class='csa-swatch' style='background:{MISSING_COLOR}'></span>"
        "<span><strong>Missing</strong>: either selected measurement missing</span>"
        "</div>"
        + caveat_html
        + "</div>"
    )


def _add_legend(
    map_widget: folium.Map,
    selected_keys: tuple[str, ...],
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
) -> None:
    if len(selected_keys) == 1:
        legend = _single_legend(
            selected_keys[0],
            specs[selected_keys[0]],
            thresholds[selected_keys[0]],
        )
    else:
        legend = _bivariate_legend(
            selected_keys[0],
            selected_keys[1],
            specs,
            thresholds,
        )
    css = """
    <style>
    html, body {
        box-sizing: border-box;
        height: 100%;
        margin: 0;
        width: 100%;
    }
    body {
        align-items: stretch;
        display: flex;
        flex-direction: row;
        gap: 12px;
        padding: 8px;
    }
    .folium-map {
        flex: 1 1 auto;
        height: 100% !important;
        min-width: 0;
        order: 1;
    }
    .csa-map-layout {
        align-self: flex-start;
        flex: 0 0 310px;
        max-height: 100%;
        order: 2;
        overflow-y: auto;
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
    .csa-legend-title { font-size: 14px; font-weight: 700; margin-bottom: 3px; }
    .csa-legend-row { align-items: center; display: flex; gap: 5px; margin-top: 4px; }
    .csa-legend-note { color: #374151; font-size: 11px; margin-top: 6px; }
    .csa-swatch { border: 1px solid #6b7280; display: inline-block; flex: 0 0 auto;
        height: 14px; width: 22px; }
    .csa-bivariate-grid { border-collapse: collapse; margin: 5px auto 2px; }
    .csa-bivariate-grid td { border: 1px solid #6b7280; height: 25px; width: 25px; }
    .csa-bivariate-grid th { font-weight: 600; padding: 2px 4px; }
    .csa-axis-x { font-size: 11px; text-align: center; }
    .csa-axis-y { font-size: 11px; margin-top: 4px; }
    @media (max-width: 640px) {
        body { flex-direction: column; }
        .folium-map { flex: 1 1 auto; height: 55vh !important; order: 1; }
        .csa-map-layout { flex: 0 0 auto; max-width: none; order: 2; width: 100%; }
        .csa-map-legend { font-size: 10px; padding: 6px; }
        .csa-legend-title { font-size: 12px; }
        .csa-legend-note { font-size: 9px; }
    }
    </style>
    """
    map_widget.get_root().html.add_child(
        Element(css + f"<div class='csa-map-layout'>{legend}</div>")
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
) -> folium.Map:
    """Build one opaque GeoJson map for one or two selected categories."""
    selected = canonicalize_selection(selected_keys)
    render_gdf = _prepare_tooltip_columns(gdf, selected, specs)
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
        style_function=_style_function(selected),
        highlight_function=lambda feature: {
            "color": "#111827",
            "fillOpacity": 1.0,
            "weight": 2.5,
        },
        tooltip=_tooltip(selected, specs),
        show=True,
    ).add_to(map_widget)
    map_widget.fit_bounds(bounds)
    map_widget.add_child(_ResetToBaltimore(bounds))
    _add_legend(map_widget, selected, specs, thresholds)
    return map_widget
