import numpy as np

# A vector (just a list of numbers, but NumPy makes math on it easy)
vector1 = np.array([1, 2, 3])
vector2 = np.array([4, 5, 6])

print("Vector 1:", vector1)
print("Vector 2:", vector2)
print("Sum:", vector1 + vector2)
print("Dot product:", np.dot(vector1, vector2))