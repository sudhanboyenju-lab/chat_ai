# Text (string)
name = "Dailo"
print(name)

# Number (integer)
age = 5
print(age)

# Decimal number (float)
price = 99.50
print(price)

# True/False (boolean)
is_online = True
print(is_online)

# Combine text and variables
print("System name is:", name)
print("Age is:", age, "years")


# List
documents = ["Citizenship copy", "Hospital letter", "Photo"]
documents.append("Ward recommendation")
print(documents)

# Dictionary
service = {
    "name": "Birth Registration",
    "fee": 100,
    "documents": documents
}
print(service["name"], service["fee"])

class Service:
    def __init__(self, name, fee, office):
        self.name = name
        self.fee = fee
        self.office = office

    def describe(self):
        return f"{self.name} costs Rs.{self.fee}, handled at {self.office}"

birth_reg = Service("Birth Registration", 100, "Ward Office")
print(birth_reg.describe())

# Writing to a file
with open("notes.txt", "w") as file:
    file.write("Birth Registration requires a hospital letter.\n")
    file.write("Map Approval requires a land ownership certificate.\n")

# Reading from a file
with open("notes.txt", "r") as file:
    content = file.read()
    print(content)