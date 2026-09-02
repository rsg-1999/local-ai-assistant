from src.rag.store import load_chunks

TEST_SET = [
    {"question": "What happened with INC-2023-Q4-011?", "keyword": "INC-2023-Q4-011"},
]


def precision_at_k(retriever, question, keyword, k=3):
    results = retriever.search(question, k=k)
    relevant = sum(1 for _, doc in results if keyword in doc["content"])
    return relevant / k


def recall_at_k(retriever, question, keyword, k=3):
    all_chunks = load_chunks()
    total_relevant = sum(1 for chunk in all_chunks if keyword in chunk["content"])
    if total_relevant == 0:
        return 0.0

    results = retriever.search(question, k=k)
    found_relevant = sum(1 for _, doc in results if keyword in doc["content"])
    return found_relevant / total_relevant


def mrr(retriever, question, keyword, k=3):
    results = retriever.search(question, k=k)
    for rank, (_, doc) in enumerate(results, start=1):
        if keyword in doc["content"]:
            return 1 / rank
    return 0.0


def run_evaluation(retriever, k=3):
    precision_scores = []
    recall_scores = []
    mrr_scores = []

    for case in TEST_SET:
        question = case["question"]
        keyword = case["keyword"]

        precision_scores.append(precision_at_k(retriever, question, keyword, k))
        recall_scores.append(recall_at_k(retriever, question, keyword, k))
        mrr_scores.append(mrr(retriever, question, keyword, k))

    print("Precision@k:", sum(precision_scores) / len(precision_scores))
    print("Recall@k:", sum(recall_scores) / len(recall_scores))
    print("MRR:", sum(mrr_scores) / len(mrr_scores))
