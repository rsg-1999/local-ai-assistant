from ddgs import DDGS

def search(query, max_results = 10):
    results = DDGS().text(query,max_results = max_results)
    return results

def format_context(results):
    lines = []
    for i, r in enumerate(results, start=1):
        lines.append(f"[{i}] {r['title']}\n{r['href']}\n{r['body']}\n")
    return "\n".join(lines)