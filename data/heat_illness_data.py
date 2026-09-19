import pandas as pd

# your heat-illness data (it's actually an Excel file despite the .csv name)
# contains data for the entire country --> must be filtered by Baltimore zipcodes
hhi = pd.read_excel("HHI Data 2024 United States.csv")

# your zip-to-csa crosswalk
xwalk = pd.read_csv("xwalk_zip2csa.csv")  # columns: zip, csa, id

# --- BEFORE: raw HHI data, by ZIP ---
print("=== BEFORE (raw HHI, all US ZIPs) ===")
print(hhi.shape)
print(hhi[["ZCTA", "PR_HRI"]].head())

# filtering US data to Baltimore only
baltimore_zips = xwalk["zip"].unique().tolist()
hhi_baltimore = hhi[hhi["ZCTA"].isin(baltimore_zips)].copy()

# handle -999 sentinel (missing data) values
hhi_baltimore = hhi_baltimore.replace(-999, pd.NA)

print("\n=== Filtered to Baltimore ZIPs ===")
print(hhi_baltimore.shape)
print(hhi_baltimore[["ZCTA", "PR_HRI"]])

# --- Merge with crosswalk (ZIP -> CSA) ---
# matches xwalk's zip column aggainst hhi_baltimore's ZCTA column 
# wherever those values are equal, pandas glues that row's data together
merged = xwalk.merge(
    hhi_baltimore[["ZCTA", "POP", "PR_HRI"]],
    left_on="zip", right_on="ZCTA", how="left"
)

print("\n=== After merge (one row per ZIP-CSA pair) ===")
print(merged.shape)
print(merged.head(10))

# --- Collapse to one row per CSA ---
csa_illness = merged.groupby("csa").agg(
    illness_pctile=("PR_HRI", "mean"),
    population=("POP", "sum")
).reset_index()

print("\n=== AFTER: final CSA-level table ===")
print(csa_illness.shape)
print(csa_illness)

# --- Save so you can open it directly ---
csa_illness.to_csv("csa_illness.csv", index=False)
print("\nSaved to csa_illness.csv")