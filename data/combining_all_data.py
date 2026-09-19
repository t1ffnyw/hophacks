import pandas as pd

tiffany_data = pd.read_csv("csa_heat_income_trees.csv")
saanvi_data = pd.read_csv("csa_illness.csv")

combined = tiffany_data.merge(
    saanvi_data[["csa", "illness_pctile"]],
    left_on="csa2010", right_on="csa",
    how="left"
).drop(columns=["csa"])  # drop the now-redundant duplicate key column

combined.to_csv("csa_combined_heat_income_trees_illness.csv", index=False)