import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    from pathlib import Path

    from dotenv import load_dotenv
    import geopandas as gpd
    import marimo as mo
    import pandas as pd

    load_dotenv(Path(__file__).resolve().parent / ".env")

    return Path, gpd, mo, os, pd


@app.cell
def _(Path):
    data_dir = Path(__file__).resolve().parent / "data"
    boundary_path = (
        data_dir / "Community_Statistical_Areas_(CSAs)__Reference_Boundaries.geojson"
    )
    dataset_path = data_dir / "csa_heat_income_trees.csv"
    return boundary_path, dataset_path


@app.cell
def _(boundary_path, dataset_path, gpd, pd):
    boundaries = gpd.read_file(boundary_path)
    metrics = pd.read_csv(dataset_path)

    metric_columns = ["temp_af_mean", "mhhi23", "trees17"]
    csa_gdf = (
        boundaries.merge(
            metrics,
            left_on="Community",
            right_on="csa2010",
            how="inner",
            validate="one_to_one",
        )
        .dropna(subset=metric_columns)
        .copy()
    )
    return (csa_gdf,)


@app.cell
def _(mo):
    mo.md("""
    # Baltimore CSA heat, income, and tree coverage

    Explore how modeled afternoon temperature, median household income,
    and tree coverage vary across Baltimore's Community Statistical Areas.
    """)
    return


@app.cell
def _(mo):
    layer_options = {
        "Afternoon heat": {
            "column": "temp_af_mean",
            "cmap": "YlOrRd",
            "caption": "Modeled afternoon temperature",
        },
        "Median income (2023)": {
            "column": "mhhi23",
            "cmap": "YlGnBu",
            "caption": "Median household income (2023)",
        },
        "Tree cover (2017)": {
            "column": "trees17",
            "cmap": "Greens",
            "caption": "Tree cover (2017, percent)",
        },
    }
    selected_layer = mo.ui.dropdown(
        options=list(layer_options),
        value="Afternoon heat",
        label="Map layer",
    )
    selected_layer
    return layer_options, selected_layer


@app.cell
def _(csa_gdf, layer_options, mo, os, selected_layer):
    layer = layer_options[selected_layer.value]
    carto_key = os.getenv("CARTODB_API_KEY") or os.getenv("CARTO_KEY")
    if not carto_key:
        raise RuntimeError(
            "CARTODB_API_KEY or CARTO_KEY is missing from the project's .env file"
        )

    tile_url = (
        "https://{s}.basemaps.cartocdn.com/"
        f"light_all/{{z}}/{{x}}/{{y}}.png?key={carto_key}"
    )
    map_widget = csa_gdf.explore(
        column=layer["column"],
        cmap=layer["cmap"],
        tooltip=["Community", layer["column"]],
        legend=True,
        legend_kwds={"caption": layer["caption"]},
        highlight=True,
        style_kwds={"fillOpacity": 0.7},
        tiles=tile_url,
        attr="&copy; OpenStreetMap contributors &copy; CARTO",
    )

    mo.Html(map_widget._repr_html_())
    return


if __name__ == "__main__":
    app.run()
