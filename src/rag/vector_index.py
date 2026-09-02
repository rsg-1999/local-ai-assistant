import numpy as np

def cosine_distance(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 1

    similarity = np.dot(vec1, vec2) / (norm1 * norm2)

    return 1-similarity


class VectorIndex:
    def __init__(self):
        self.vectors = []
        self.documents = []

    def add_vector(self, vector, document):
        self.vectors.append(vector)
        self.documents.append(document)

    def search(self, query_vector, k=3):
        distances = []

        for vector, document in zip(self.vectors, self.documents):
            distance = cosine_distance(query_vector, vector)
            distances.append((distance, document))

        distances.sort(key=lambda item: item[0])

        return distances[:k]