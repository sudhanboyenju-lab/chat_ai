print("=== Basic try/except ===")
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero!")

print("\n=== Catching a different error type ===")
try:
    number = int("not a number")
except ValueError:
    print("That wasn't a valid number.")

print("\n=== Catching multiple possible errors ===")
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        print("Error: division by zero")
        return None
    except TypeError:
        print("Error: invalid types for division")
        return None

print(safe_divide(10, 2))
print(safe_divide(10, 0))
print(safe_divide(10, "a"))

print("\n=== Using else and finally ===")
try:
    value = 5 + 5
except ArithmeticError:
    print("Something went wrong with the math")
else:
    print("No errors — result is:", value)
finally:
    print("This always runs, error or not")

print("\n=== Catching a specific, expected error ===")
try:
    with open("does_not_exist.txt") as f:
        content = f.read()
except FileNotFoundError as e:
    print("File not found:", e)