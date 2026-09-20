"""Anywidget for CSA tree-cover what-if exploration."""

from __future__ import annotations

import json
import html as html_lib
from pathlib import Path
from typing import Mapping

import anywidget
import geopandas as gpd
import pandas as pd
import traitlets

from scripts.csa_map_data import LayerSpec, TercileThresholds
from scripts.csa_map_render import (
    MISSING_COLOR,
    PAIR_PALETTES,
    SINGLE_PALETTES,
    fill_color_for_properties,
)


WIDGET_DIR = Path(__file__).resolve().parent
WHATIF_KEYS = ("health", "trees")
KEEP_PROPERTIES = (
    "Community",
    "csa2010",
    "trees17",
    "illness_pctile",
    "health_class",
    "trees_class",
    "fillColor",
)


def _threshold_payload(thresholds: TercileThresholds) -> dict[str, float | int | None]:
    return {
        "low_max": thresholds.low_max,
        "medium_max": thresholds.medium_max,
        "valid_count": thresholds.valid_count,
        "unique_values": thresholds.unique_values,
    }


def build_color_rules(
    thresholds: Mapping[str, TercileThresholds],
) -> dict[str, object]:
    """Rules the browser needs to recolor a CSA as the slider moves."""
    return {
        "missing": MISSING_COLOR,
        "class_order": ["Low", "Medium", "High"],
        "palette": [list(row) for row in PAIR_PALETTES[WHATIF_KEYS]],
        "health": _threshold_payload(thresholds["health"]),
        "trees": _threshold_payload(thresholds["trees"]),
    }


def build_whatif_legend_html(specs: Mapping[str, LayerSpec]) -> str:
    """Simple key using the same purple/green as the single-category map."""
    health = specs["health"]
    health_color = SINGLE_PALETTES["health"][2]
    trees_color = SINGLE_PALETTES["trees"][2]
    return (
        "<div class='csa-map-legend whatif-simple-legend'>"
        "<div class='csa-legend-title'>Key</div>"
        "<div class='csa-legend-row'>"
        f"<span class='csa-swatch' style='background:{health_color}'></span>"
        f"<span>{html_lib.escape(health.label)}</span>"
        "</div>"
        "<div class='csa-legend-row'>"
        f"<span class='csa-swatch' style='background:{trees_color}'></span>"
        "<span>Tree canopy cover</span>"
        "</div>"
        "<div class='csa-legend-note'>Darker areas indicate higher values.</div>"
        "</div>"
    )


def _json_safe(value: object) -> object:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, str):
        return value
    return value


def whatif_geojson(
    gdf: gpd.GeoDataFrame,
    selected_keys: tuple[str, ...] = WHATIF_KEYS,
) -> dict[str, object]:
    """Serialize CSA polygons with choropleth fill colors and model inputs."""
    render_gdf = gdf.copy()
    if render_gdf.crs is not None and render_gdf.crs.to_epsg() != 4326:
        render_gdf = render_gdf.to_crs("EPSG:4326")
    # Shrink the anywidget trait payload; full CSA boundaries are ~2MB raw.
    render_gdf["geometry"] = render_gdf.geometry.simplify(
        0.00015, preserve_topology=True
    )

    payload = json.loads(render_gdf.to_json(drop_id=True))
    for feature in payload["features"]:
        properties = feature.get("properties") or {}
        properties["fillColor"] = fill_color_for_properties(selected_keys, properties)
        feature["properties"] = {
            key: _json_safe(properties.get(key))
            for key in KEEP_PROPERTIES
            if key in properties or key == "fillColor"
        }
    return payload


def whatif_bounds(gdf: gpd.GeoDataFrame) -> list[list[float]]:
    render_gdf = gdf
    if render_gdf.crs is not None and render_gdf.crs.to_epsg() != 4326:
        render_gdf = render_gdf.to_crs("EPSG:4326")
    min_x, min_y, max_x, max_y = render_gdf.total_bounds
    return [[float(min_y), float(min_x)], [float(max_y), float(max_x)]]


class TreeCoverWhatIfWidget(anywidget.AnyWidget):
    """Click a CSA, then use a tree-cover slider to project illness change."""

    _esm = WIDGET_DIR / "tree_whatif_widget.js"
    _css = WIDGET_DIR / "tree_whatif_widget.css"

    geojson = traitlets.Unicode("{}").tag(sync=True)
    legend_html = traitlets.Unicode("").tag(sync=True)
    csa_stats = traitlets.Unicode("{}").tag(sync=True)
    bounds_json = traitlets.Unicode("[]").tag(sync=True)
    tile_url = traitlets.Unicode("").tag(sync=True)
    tile_attr = traitlets.Unicode("").tag(sync=True)
    slope = traitlets.Float(0.0).tag(sync=True)
    selected_csa = traitlets.Unicode("").tag(sync=True)
    tree_change = traitlets.Int(0).tag(sync=True)
    color_rules = traitlets.Unicode("{}").tag(sync=True)
    scatter_json = traitlets.Unicode("{}").tag(sync=True)


def build_whatif_widget(
    gdf: gpd.GeoDataFrame,
    specs: Mapping[str, LayerSpec],
    thresholds: Mapping[str, TercileThresholds],
    slope: float,
    csa_stats: Mapping[str, Mapping[str, float | None]],
    tile_url: str | None,
    tile_attr: str | None,
    scatter_payload: Mapping[str, object] | None = None,
) -> TreeCoverWhatIfWidget:
    return TreeCoverWhatIfWidget(
        geojson=json.dumps(whatif_geojson(gdf)),
        legend_html=build_whatif_legend_html(specs),
        csa_stats=json.dumps(csa_stats),
        bounds_json=json.dumps(whatif_bounds(gdf)),
        tile_url=tile_url or "",
        tile_attr=tile_attr or "",
        slope=float(slope),
        selected_csa="",
        tree_change=0,
        color_rules=json.dumps(build_color_rules(thresholds)),
        scatter_json=json.dumps(scatter_payload or {}),
    )
