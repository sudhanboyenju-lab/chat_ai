services = [
    {"name": "Birth Registration", "fee": 100},
    {"name": "Map Approval", "fee": 500},
    {"name": "Tax Payment", "fee": 200}
]

print("=== Old way: regular loop ===")
fees = []
for s in services:
    fees.append(s["fee"])
print(fees)

print("\n=== New way: list comprehension (same result) ===")
fees = [s["fee"] for s in services]
print(fees)

print("\n=== List comprehension with a condition (filtering) ===")
expensive_services = [s["name"] for s in services if s["fee"] > 150]
print(expensive_services)

print("\n=== List comprehension doing a transformation ===")
uppercase_names = [s["name"].upper() for s in services]
print(uppercase_names)

print("\n=== List comprehension on plain numbers ===")
numbers = [1, 2, 3, 4, 5]
squared = [n ** 2 for n in numbers]
print(squared)

even_only = [n for n in numbers if n % 2 == 0]
print(even_only)