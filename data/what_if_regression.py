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