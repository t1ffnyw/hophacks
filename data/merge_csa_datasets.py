"""Merge Baltimore CSA heat, income, and tree coverage data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping, Sequence

import geopandas as gpd
import pandas as pd
import rasterio
from rasterstats import zonal_stats


OUTPUT_COLUMNS = [
    "csa2010",
    "csa2020",
    "temp_am_mean",
    "temp_af_mean",
    "temp_pm_mean",
    "mhhi17",
    "mhhi23",
    "trees11",
    "trees17",
]

HEAT_RASTERS = {
    "temp_am_mean": "bal_am.tif",
    "temp_af_mean": "bal_af.tif",
    "temp_pm_mean": "bal_pm.tif",
}


def _require_columns(frame: pd.DataFrame, required: set[str], source: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {', '.join(missing)}")


def load_boundaries(path: Path) -> gpd.GeoDataFrame:
    """Load CSA polygons and retain the 55 named CSAs with data attributes."""
    boundaries = gpd.read_file(path)
    _require_columns(boundaries, {"Community", "geometry"}, str(path))

    boundaries = boundaries.loc[
        boundaries["Community"].notna()
        & boundaries["Community"].ne("Unassigned -- Jail")
    ].copy()
    boundaries["Community"] = boundaries["Community"].astype(str).str.strip()

    if boundaries["Community"].duplicated().any():
        raise ValueError("CSA boundary file contains duplicate Community values")
    if boundaries.crs is None:
        raise ValueError(f"{path} does not define a coordinate reference system")

    return boundaries


def load_attribute_tables(
    income_path: Path, trees_path: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and select the income and tree columns used in the output."""
    income = pd.read_csv(income_path, encoding="utf-8-sig")
    trees = pd.read_csv(trees_path, encoding="utf-8-sig")

    _require_columns(
        income,
        {"CSA2010", "CSA2020", "mhhi17", "mhhi23"},
        str(income_path),
    )
    _require_columns(trees, {"CSA2010", "trees11", "trees17"}, str(trees_path))

    income = income[["CSA2010", "CSA2020", "mhhi17", "mhhi23"]].copy()
    trees = trees[["CSA2010", "trees11", "trees17"]].copy()

    for frame in (income, trees):
        frame["CSA2010"] = frame["CSA2010"].astype(str).str.strip()
    for column in ("mhhi17", "mhhi23"):
        income[column] = pd.to_numeric(income[column], errors="coerce")
    for column in ("trees11", "trees17"):
        trees[column] = pd.to_numeric(trees[column], errors="coerce")

    return income, trees


def calculate_raster_means(
    boundaries: gpd.GeoDataFrame, raster_path: Path
) -> list[float | None]:
    """Calculate the mean non-nodata raster value for each CSA polygon."""
    with rasterio.open(raster_path) as raster:
        if raster.crs is None:
            raise ValueError(f"{raster_path} does not define a coordinate reference system")

        projected_boundaries = boundaries.to_crs(raster.crs)
        stats = zonal_stats(
            projected_boundaries.geometry,
            raster_path,
            stats=["mean"],
            nodata=raster.nodata,
            all_touched=False,
        )

    return [stat["mean"] for stat in stats]


def calculate_heat_table(
    boundaries: gpd.GeoDataFrame, raster_paths: Mapping[str, Path]
) -> pd.DataFrame:
    """Return one mean-temperature row per CSA for the configured rasters."""
    heat = boundaries[["Community"]].copy()
    for column, raster_path in raster_paths.items():
        heat[column] = calculate_raster_means(boundaries, raster_path)
    return heat


def merge_attribute_tables(
    boundaries: pd.DataFrame,
    heat: pd.DataFrame,
    income: pd.DataFrame,
    trees: pd.DataFrame,
) -> pd.DataFrame:
    """Join heat, income, and trees using the 2010 CSA names."""
    _require_columns(boundaries, {"Community"}, "CSA boundaries")
    _require_columns(
        heat,
        {"Community", "temp_am_mean", "temp_af_mean", "temp_pm_mean"},
        "heat table",
    )
    _require_columns(income, {"CSA2010", "CSA2020", "mhhi17", "mhhi23"}, "income table")
    _require_columns(trees, {"CSA2010", "trees11", "trees17"}, "tree table")

    for frame, key, source in (
        (boundaries, "Community", "CSA boundaries"),
        (heat, "Community", "heat table"),
        (income, "CSA2010", "income table"),
        (trees, "CSA2010", "tree table"),
    ):
        if frame[key].duplicated().any():
            raise ValueError(f"{source} contains duplicate {key} values")

    income_keys = set(income["CSA2010"])
    tree_keys = set(trees["CSA2010"])
    if income_keys != tree_keys:
        raise ValueError(
            "Income and tree CSA2010 keys do not match: "
            f"income-only={sorted(income_keys - tree_keys)}, "
            f"tree-only={sorted(tree_keys - income_keys)}"
        )

    attributes = income.merge(
        trees,
        on="CSA2010",
        how="inner",
        validate="one_to_one",
    ).rename(columns={"CSA2020": "csa2020"})
    result = (
        boundaries[["Community"]]
        .rename(columns={"Community": "csa2010"})
        .merge(
            heat.rename(columns={"Community": "csa2010"}),
            on="csa2010",
            how="left",
            validate="one_to_one",
        )
        .merge(
            attributes,
            left_on="csa2010",
            right_on="CSA2010",
            how="left",
            validate="one_to_one",
        )
        .drop(columns=["CSA2010"])
    )

    return result[OUTPUT_COLUMNS]


def build_dataset(
    boundary_path: Path,
    raster_paths: Mapping[str, Path],
    income_path: Path,
    trees_path: Path,
) -> pd.DataFrame:
    """Build the final analysis-ready CSA table."""
    boundaries = load_boundaries(boundary_path)
    income, trees = load_attribute_tables(income_path, trees_path)
    heat = calculate_heat_table(boundaries, raster_paths)
    return merge_attribute_tables(boundaries, heat, income, trees)


def report_missing_values(dataset: pd.DataFrame) -> None:
    """Print row count and CSA names with missing merge values."""
    print(f"Rows: {len(dataset)}")
    for label, columns in {
        "heat": ["temp_am_mean", "temp_af_mean", "temp_pm_mean"],
        "income": ["mhhi17", "mhhi23"],
        "trees": ["trees11", "trees17"],
    }.items():
        missing = dataset.loc[dataset[columns].isna().any(axis=1), "csa2010"].tolist()
        print(f"Missing {label}: {missing or 'none'}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    parser = argparse.ArgumentParser(
        description="Merge Baltimore CSA heat, income, and tree coverage data."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=data_dir,
        help=f"Root data directory (default: {data_dir})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=data_dir / "csa_heat_income_trees.csv",
        help="Output CSV path.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    data_dir = args.data_dir
    heat_dir = data_dir / "baltimore" / "temperature surfaces"
    raster_paths = {
        column: heat_dir / filename
        for column, filename in HEAT_RASTERS.items()
    }

    dataset = build_dataset(
        boundary_path=data_dir
        / "Community_Statistical_Areas_(CSAs)__Reference_Boundaries.geojson",
        raster_paths=raster_paths,
        income_path=data_dir / "Median_Household_Income_-_Community_Statistical_Area.csv",
        trees_path=data_dir / "Percent_of_Area_Covered_by_Trees.csv",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(args.output, index=False)
    report_missing_values(dataset)
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
