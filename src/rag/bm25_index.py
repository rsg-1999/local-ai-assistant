import math
import re
from collections import Counter


def tokenize(text):
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text)
    return tokens


class BM25Index:
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_tokens = []
        self.doc_freqs = {}
        self.idf = {}
        self.avg_doc_len = 0

    def add_document(self, document):
        tokens = tokenize(document["content"])
        self.documents.append(document)
        self.doc_tokens.append(tokens)

        for term in set(tokens):
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

    def _build(self):
        n = len(self.documents)
        self.avg_doc_len = sum(len(tokens) for tokens in self.doc_tokens) / n
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((n - freq + 0.5) / (freq + 0.5) + 1)

    def _score(self, query_tokens, doc_index):
        score = 0
        doc_term_counts = Counter(self.doc_tokens[doc_index])
        doc_len = len(self.doc_tokens[doc_index])

        for term in query_tokens:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            tf = doc_term_counts[term]
            numerator = idf * tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_len / self.avg_doc_len)
            )
            score += numerator / denominator

        return score

    def search(self, query, k=3):
        if not self.documents:
            return []

        self._build()
        query_tokens = tokenize(query)

        scores = []
        for i in range(len(self.documents)):
            score = self._score(query_tokens, i)
            scores.append((score, self.documents[i]))

        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[:k]
