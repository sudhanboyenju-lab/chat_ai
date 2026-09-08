import pandas as pd

print("=== 1. Creating a DataFrame ===")
data = {
    "service_name": ["Birth Registration", "Map Approval", "Tax Payment"],
    "fee": [100, 500, 200],
    "office": ["Ward Office", "Planning Office", "Revenue Office"]
}
df = pd.DataFrame(data)
print(df)

print("\n=== 2. Selecting columns ===")
print(df["service_name"])
print(df[["service_name", "fee"]])

print("\n=== 3. Selecting rows ===")
print("First row:")
print(df.iloc[0])
print("\nServices with fee over 150:")
print(df[df["fee"] > 150])

print("\n=== 4. Adding a new column ===")
df["eligibility"] = ["All citizens", "Property owners only", "All citizens"]
print(df)

print("\n=== 5. Looping through rows ===")
for index, row in df.iterrows():
    print(f"{row['service_name']} (Rs.{row['fee']}) - Eligibility: {row['eligibility']}")

print("\n=== 6. Saving and loading CSV ===")
df.to_csv("services.csv", index=False)
loaded_csv = pd.read_csv("services.csv")
print("Loaded from CSV:")
print(loaded_csv)

print("\n=== 7. Saving and loading Excel ===")
df.to_excel("services.xlsx", index=False)
loaded_excel = pd.read_excel("services.xlsx")
print("Loaded from Excel:")
print(loaded_excel)

print("\n=== 8. Handling missing data ===")
df_with_missing = df.copy()
df_with_missing.loc[1, "fee"] = None  # intentionally create a missing value
print("With missing value:")
print(df_with_missing)
print("\nCheck for nulls:")
print(df_with_missing.isnull())
print("\nFilled with default:")
print(df_with_missing.fillna("N/A"))