import json

services = [
    {"name": "Birth Registration", "fee": 100},
    {"name": "Map Approval", "fee": 500},
    {"name": "Tax Payment", "fee": 200}
]

# List comprehension: get just the names
service_names = [s["name"] for s in services]
print("Service names:", service_names)

# Save full list to JSON
with open("services_combined.json", "w") as f:
    json.dump(services, f, indent=2)
print("Saved to services_combined.json")

# Try loading it back, with error handling in case the file is missing
try:
    with open("services_combined.json", "r") as f:
        loaded = json.load(f)
        print("Loaded successfully:", loaded)
except FileNotFoundError:
    print("File not found — nothing to load.")
except json.JSONDecodeError:
    print("File exists but isn't valid JSON.")