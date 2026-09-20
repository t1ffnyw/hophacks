<<<<<<< HEAD
"""OLS what-if model: tree canopy coverage vs heat-health vulnerability."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import statsmodels.api as sm


COMBINED_FILENAME = "csa_combined_heat_income_trees_illness.csv"
TREE_COLUMN = "trees17"
ILLNESS_COLUMN = "illness_pctile"
CSA_COLUMNS = ("csa2010", "Community")


def default_combined_path() -> Path:
    return Path(__file__).resolve().parent / COMBINED_FILENAME


def load_combined_table(path: Path | None = None) -> pd.DataFrame:
    csv_path = path or default_combined_path()
    return pd.read_csv(csv_path, encoding="utf-8-sig")


def fit_tree_illness_model(df: pd.DataFrame):
    """Fit illness percentile on tree canopy percent, with an intercept."""
    work = pd.DataFrame(
        {
            TREE_COLUMN: pd.to_numeric(df[TREE_COLUMN], errors="coerce"),
            ILLNESS_COLUMN: pd.to_numeric(df[ILLNESS_COLUMN], errors="coerce"),
        }
    ).dropna()
    if work.empty:
        raise ValueError("No overlapping tree cover and illness values to fit")
    design = sm.add_constant(work[TREE_COLUMN])
    return sm.OLS(work[ILLNESS_COLUMN], design).fit()


def tree_illness_slope(df: pd.DataFrame) -> float:
    return float(fit_tree_illness_model(df).params[TREE_COLUMN])


def regression_scatter_payload(df: pd.DataFrame) -> dict[str, Any]:
    """Points and fitted line for the tree canopy vs illness scatterplot."""
    names = (
        df["Community"]
        if "Community" in df.columns
        else df["csa2010"]
        if "csa2010" in df.columns
        else pd.Series(df.index.astype(str), index=df.index)
    )
    work = pd.DataFrame(
        {
            "name": names.astype(str).str.strip(),
            "trees": pd.to_numeric(df[TREE_COLUMN], errors="coerce"),
            "illness": pd.to_numeric(df[ILLNESS_COLUMN], errors="coerce"),
        }
    ).dropna()

    model = fit_tree_illness_model(df)
    intercept = float(model.params["const"])
    slope = float(model.params[TREE_COLUMN])
    points = [
        {
            "name": str(row["name"]),
            "trees": float(row["trees"]),
            "illness": float(row["illness"]),
        }
        for _, row in work.iterrows()
    ]
    x_min = float(work["trees"].min()) if not work.empty else 0.0
    x_max = float(work["trees"].max()) if not work.empty else 100.0
    pad = max(1.0, (x_max - x_min) * 0.05)
    line_x0 = max(0.0, x_min - pad)
    line_x1 = min(100.0, x_max + pad)
    return {
        "points": points,
        "intercept": intercept,
        "slope": slope,
        "r_squared": float(model.rsquared),
        "corr": float(work["trees"].corr(work["illness"])) if len(work) > 1 else 0.0,
        "line": [
            {"trees": line_x0, "illness": intercept + slope * line_x0},
            {"trees": line_x1, "illness": intercept + slope * line_x1},
        ],
        "x_label": "Tree canopy cover (%)",
        "y_label": "Heat-health vulnerability",
    }


def _lookup_csa_row(df: pd.DataFrame, csa_name: str) -> pd.Series:
    target = str(csa_name).strip()
    for column in CSA_COLUMNS:
        if column not in df.columns:
            continue
        matches = df[df[column].astype(str).str.strip() == target]
        if not matches.empty:
            return matches.iloc[0]
    raise KeyError(f"Unknown CSA: {csa_name}")


def predict_whatif(
    df: pd.DataFrame,
    csa_name: str,
    tree_change: float,
    slope: float | None = None,
) -> dict[str, Any]:
    """Project illness percentile after a percentage-point tree-cover change."""
    row = _lookup_csa_row(df, csa_name)
    if slope is None:
        slope = tree_illness_slope(df)

    current_tree = pd.to_numeric(row[TREE_COLUMN], errors="coerce")
    current_illness = pd.to_numeric(row[ILLNESS_COLUMN], errors="coerce")
    if pd.isna(current_tree) or pd.isna(current_illness):
        return {
            "csa_name": str(csa_name),
            "current_tree": None,
            "new_tree": None,
            "actual_change_applied": 0.0,
            "current_illness": None,
            "new_illness": None,
            "slope": float(slope),
            "usable": False,
        }

    current_tree = float(current_tree)
    current_illness = float(current_illness)
    new_tree = max(0.0, min(100.0, current_tree + float(tree_change)))
    actual_change_applied = new_tree - current_tree
    new_illness = current_illness + float(slope) * actual_change_applied
    new_illness = max(0.0, min(100.0, new_illness))
    return {
        "csa_name": str(csa_name),
        "current_tree": current_tree,
        "new_tree": new_tree,
        "actual_change_applied": actual_change_applied,
        "current_illness": current_illness,
        "new_illness": new_illness,
        "slope": float(slope),
        "usable": True,
    }


def csa_whatif_stats(df: pd.DataFrame) -> dict[str, Mapping[str, float | None]]:
    """Per-CSA inputs the map widget needs to project a tree-cover change."""
    stats: dict[str, Mapping[str, float | None]] = {}
    name_series = df["csa2010"] if "csa2010" in df.columns else df["Community"]
    for index, name in name_series.items():
        trees = pd.to_numeric(df.at[index, TREE_COLUMN], errors="coerce")
        illness = pd.to_numeric(df.at[index, ILLNESS_COLUMN], errors="coerce")
        stats[str(name).strip()] = {
            "trees": None if pd.isna(trees) else float(trees),
            "illness": None if pd.isna(illness) else float(illness),
        }
        if "Community" in df.columns:
            community = str(df.at[index, "Community"]).strip()
            stats[community] = stats[str(name).strip()]
    return stats


if __name__ == "__main__":
    df = load_combined_table()
    print(df.shape)
    print(df[["csa2010", TREE_COLUMN, ILLNESS_COLUMN]].head())
    model = fit_tree_illness_model(df)
    print(model.summary())
    slope = model.params[TREE_COLUMN]

    def _predict_whatif(csa_name, tree_change):
        return predict_whatif(df, csa_name, tree_change, slope=slope)

    sample = df["csa2010"].iloc[0]
    print(_predict_whatif(sample, 5))
=======
import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("csa_combined_heat_income_trees_illness.csv")
print(df.shape)
print(df[["csa2010", "trees17", "illness_pctile"]].head())

X = df["trees17"]
y = df["illness_pctile"]
X_with_const = sm.add_constant(X)  # adds intercept term

model = sm.OLS(y, X_with_const).fit()
print(model.summary())

slope = model.params["trees17"]

def predict_whatif(csa_name, tree_change):
    row = df[df["csa2010"] == csa_name].iloc[0]
    current_tree = row["trees17"]
    new_tree = max(0, min(100, current_tree + tree_change))
    actual_change_applied = new_tree - current_tree

    current_illness = row["illness_pctile"]
    new_illness = current_illness + slope * actual_change_applied
    new_illness = max(0, min(100, new_illness))

    return current_illness, new_illness

# sanity checks
print(predict_whatif("Downtown/Seton Hill", 10))
print(predict_whatif("Greater Roland Park/Poplar Hill", -10))
>>>>>>> origin/main
