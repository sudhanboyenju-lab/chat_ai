import json

print("=== Python dict to JSON string ===")
service = {
    "name": "Birth Registration",
    "fee": 100,
    "documents": ["Hospital letter", "Citizenship copy"]
}

json_string = json.dumps(service, indent=2)
print(json_string)

print("\n=== JSON string back to Python dict ===")
loaded_service = json.loads(json_string)
print(loaded_service["name"])
print(loaded_service["documents"])

print("\n=== Saving a dict to a JSON file ===")
with open("service.json", "w") as f:
    json.dump(service, f, indent=2)
print("Saved to service.json")

print("\n=== Loading a JSON file back ===")
with open("service.json", "r") as f:
    loaded = json.load(f)
    print(loaded)

print("\n=== Saving a LIST of dicts (common for service catalogues) ===")
services = [
    {"name": "Birth Registration", "fee": 100},
    {"name": "Map Approval", "fee": 500},
    {"name": "Tax Payment", "fee": 200}
]

with open("services_list.json", "w") as f:
    json.dump(services, f, indent=2)

with open("services_list.json", "r") as f:
    loaded_services = json.load(f)
    for s in loaded_services:
        print(s["name"], "-", s["fee"])