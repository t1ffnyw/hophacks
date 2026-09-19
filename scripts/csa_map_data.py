"""Load and classify the CSA-level data used by the interactive map."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

import geopandas as gpd
import numpy as np
import pandas as pd


CATEGORY_ORDER = ("heat", "health", "income", "trees")
CLASS_ORDER = ("Low", "Medium", "High")
BOUNDARY_FILENAME = "Community_Statistical_Areas_(CSAs)__Reference_Boundaries.geojson"
COMBINED_FILENAME = "csa_combined_heat_income_trees_illness.csv"


@dataclass(frozen=True)
class LayerSpec:
    """Metadata needed to label and render one map category."""

    key: str
    label: str
    column: str
    units: str
    period: str
    hue: str
    caveat: str = ""


@dataclass(frozen=True)
class TercileThresholds:
    """Fixed value boundaries and edge-case information for one category."""

    low_max: float | None
    medium_max: float | None
    valid_count: int
    unique_values: int
    empty_classes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MapDiagnostics:
    """Join and missing-value diagnostics surfaced by the notebook."""

    boundary_count: int
    table_count: int
    joined_count: int
    boundary_only: tuple[str, ...]
    table_only: tuple[str, ...]
    missing_by_layer: Mapping[str, tuple[str, ...]]
    layer_specs: Mapping[str, LayerSpec]
    thresholds: Mapping[str, TercileThresholds]


LAYER_SPECS: dict[str, LayerSpec] = {
    "heat": LayerSpec(
        key="heat",
        label="Heat",
        column="temp_af_mean",
        units="source-raster units (likely °C)",
        period="Modeled afternoon surface, approximately 3 PM; 2018 source context",
        hue="red",
        caveat="TIFF metadata does not declare a temperature-unit conversion.",
    ),
    "health": LayerSpec(
        key="health",
        label="Heat-health vulnerability",
        column="illness_pctile",
        units="PR_HRI percentile",
        period="2024 HHI source label; derived CSA approximation",
        hue="purple",
        caveat=(
            "Approximate ZIP-to-CSA aggregation; this is not an illness rate "
            "or causal measure."
        ),
    ),
    "income": LayerSpec(
        key="income",
        label="Median household income",
        column="mhhi23",
        units="USD",
        period="2023 income year",
        hue="blue",
    ),
    "trees": LayerSpec(
        key="trees",
        label="Tree canopy coverage",
        column="trees17",
        units="percent of CSA area",
        period="2017",
        hue="green",
    ),
}


def _require_columns(
    frame: pd.DataFrame, required: set[str], source: str
) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {', '.join(missing)}")


def _numeric_values(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _with_empty_classes(
    series: pd.Series, thresholds: TercileThresholds
) -> TercileThresholds:
    classes = assign_tercile_classes(series, thresholds)
    empty = tuple(
        class_name
        for class_name in CLASS_ORDER
        if not bool((classes == class_name).any())
    )
    return replace(thresholds, empty_classes=empty)


def compute_tercile_thresholds(series: pd.Series) -> TercileThresholds:
    """Compute fixed empirical tercile boundaries without splitting ties."""
    values = _numeric_values(series).dropna()
    if values.empty:
        return TercileThresholds(
            low_max=None,
            medium_max=None,
            valid_count=0,
            unique_values=0,
        )

    unique = np.sort(values.unique())
    unique_count = len(unique)
    if unique_count == 1:
        thresholds = TercileThresholds(
            low_max=float(unique[0]),
            medium_max=float(unique[0]),
            valid_count=len(values),
            unique_values=unique_count,
        )
    elif unique_count == 2:
        thresholds = TercileThresholds(
            low_max=float(unique[0]),
            medium_max=float(unique[0]),
            valid_count=len(values),
            unique_values=unique_count,
        )
    else:
        quantiles = values.quantile([1 / 3, 2 / 3], interpolation="linear")
        thresholds = TercileThresholds(
            low_max=float(quantiles.loc[1 / 3]),
            medium_max=float(quantiles.loc[2 / 3]),
            valid_count=len(values),
            unique_values=unique_count,
        )

    return _with_empty_classes(series, thresholds)


def assign_tercile_classes(
    series: pd.Series, thresholds: TercileThresholds
) -> pd.Series:
    """Assign Low/Medium/High while keeping equal values together."""
    values = _numeric_values(series)
    classes = pd.Series(pd.NA, index=series.index, dtype="string")
    valid = values.notna()
    if thresholds.valid_count == 0:
        return classes

    if thresholds.unique_values == 1:
        classes.loc[valid] = "Medium"
        return classes

    if thresholds.unique_values == 2:
        classes.loc[valid & (values <= thresholds.low_max)] = "Low"
        classes.loc[valid & (values > thresholds.low_max)] = "High"
        return classes

    classes.loc[valid & (values <= thresholds.low_max)] = "Low"
    classes.loc[
        valid
        & (values > thresholds.low_max)
        & (values <= thresholds.medium_max)
    ] = "Medium"
    classes.loc[valid & (values > thresholds.medium_max)] = "High"
    return classes


def load_csa_map_data(
    data_dir: Path,
) -> tuple[gpd.GeoDataFrame, MapDiagnostics]:
    """Load the combined table, join it to named CSA boundaries, and classify it."""
    boundary_path = data_dir / BOUNDARY_FILENAME
    combined_path = data_dir / COMBINED_FILENAME

    boundaries = gpd.read_file(boundary_path)
    _require_columns(boundaries, {"Community", "geometry"}, str(boundary_path))
    boundaries = boundaries.loc[
        boundaries["Community"].notna()
        & boundaries["Community"].ne("Unassigned -- Jail")
    ].copy()
    boundaries["Community"] = boundaries["Community"].astype(str).str.strip()

    combined = pd.read_csv(combined_path, encoding="utf-8-sig")
    required_columns = {"csa2010"} | {
        spec.column for spec in LAYER_SPECS.values()
    }
    _require_columns(combined, required_columns, str(combined_path))
    combined["csa2010"] = combined["csa2010"].astype(str).str.strip()

    if boundaries["Community"].duplicated().any():
        raise ValueError("CSA boundaries contain duplicate Community values")
    if combined["csa2010"].duplicated().any():
        raise ValueError("Combined CSA table contains duplicate csa2010 values")

    for spec in LAYER_SPECS.values():
        combined[spec.column] = _numeric_values(combined[spec.column])

    boundary_keys = set(boundaries["Community"])
    table_keys = set(combined["csa2010"])
    boundary_only = tuple(sorted(boundary_keys - table_keys))
    table_only = tuple(sorted(table_keys - boundary_keys))

    joined = boundaries.merge(
        combined,
        left_on="Community",
        right_on="csa2010",
        how="left",
        validate="one_to_one",
    )

    thresholds: dict[str, TercileThresholds] = {}
    missing_by_layer: dict[str, tuple[str, ...]] = {}
    for key, spec in LAYER_SPECS.items():
        category_thresholds = compute_tercile_thresholds(joined[spec.column])
        thresholds[key] = category_thresholds
        joined[f"{key}_class"] = assign_tercile_classes(
            joined[spec.column], category_thresholds
        )
        missing_by_layer[key] = tuple(
            joined.loc[joined[spec.column].isna(), "Community"].tolist()
        )

    diagnostics = MapDiagnostics(
        boundary_count=len(boundaries),
        table_count=len(combined),
        joined_count=len(joined),
        boundary_only=boundary_only,
        table_only=table_only,
        missing_by_layer=missing_by_layer,
        layer_specs=LAYER_SPECS,
        thresholds=thresholds,
    )
    return joined, diagnostics
