import pandas as pd

# Create a small table of municipal services
data = {
    "service_name": ["Birth Registration", "Map Approval", "Tax Payment"],
    "fee": [100, 500, 200],
    "office": ["Ward Office", "Planning Office", "Revenue Office"],
    "processing_days": [3, 15, 1]
}

df = pd.DataFrame(data)

print(df)
print()
print("Just the fee column:")
print(df["fee"])
print()
print("Services with fee over 150:")
print(df[df["fee"] > 150])
print()
print("Average processing time:", df["processing_days"].mean())

# Save to CSV
df.to_csv("services.csv", index=False)
print("\nSaved to services.csv")

# Load it back
loaded_df = pd.read_csv("services.csv")
print("\nLoaded from CSV:")
print(loaded_df)