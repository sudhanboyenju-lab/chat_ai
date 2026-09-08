import numpy as np

print("=== 1. Creating arrays ===")
vector = np.array([1, 2, 3, 4])
print(vector)

print("\n=== 2. Basic math operations ===")
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

print("a + b =", a + b)
print("a - b =", a - b)
print("a * 2 =", a * 2)

print("\n=== 3. Dot product ===")
dot_result = np.dot(a, b)
print("Dot product:", dot_result)

print("\n=== 4. Norm (vector length/magnitude) ===")
norm_a = np.linalg.norm(a)
print("Norm of a:", norm_a)

print("\n=== 5. Cosine similarity ===")
def cosine_similarity(vec1, vec2):
    a = np.array(vec1)
    b = np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

similarity = cosine_similarity(a, b)
print("Cosine similarity:", similarity)

print("\n=== 6. Shape and length ===")
print("Shape:", vector.shape)
print("Length:", len(vector))