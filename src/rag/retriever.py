from src.rag.embeddings import generate_embedding


class Retriever:
    def __init__(self, vector_index, bm25_index):
        self.vector_index = vector_index
        self.bm25_index = bm25_index

    def add_document(self, document):
        vector = generate_embedding(document["content"])
        self.vector_index.add_vector(vector, document)
        self.bm25_index.add_document(document)

    def search(self, query, k=3, k_rrf=60):
        query_vector = generate_embedding(query)

        candidate_pool = k * 20

        vector_results = self.vector_index.search(query_vector, k=candidate_pool)
        bm25_results = self.bm25_index.search(query, k=candidate_pool)

        doc_ranks = {}
        for results in (vector_results, bm25_results):
            for rank, (_, document) in enumerate(results):
                doc_id = id(document)
                if doc_id not in doc_ranks:
                    doc_ranks[doc_id] = {"document": document, "ranks": []}
                doc_ranks[doc_id]["ranks"].append(rank + 1)

        scored = []
        for entry in doc_ranks.values():
            rrf_score = sum(1 / (k_rrf + rank) for rank in entry["ranks"])
            scored.append((rrf_score, entry["document"]))

        scored.sort(key=lambda item: item[0], reverse=True)

        return scored[:k]
