"""
eval.py - Offline evaluation for the knowledge-base retrieval (RAG).

Additive and read-only: it imports rag.py and calls rag.search(); it does NOT
modify the agent or any existing file. Run it from the project root:

    python eval.py

Needs Ollama running (same as the agent) and the EMBED_MODEL / KB_FOLDER /
VECTOR_STORE_FILE values in .env. Over a labelled question set (eval_set.json)
it reports:

  - Recall@1 / @2 / @3 : is a chunk from the correct document in the top-k?
  - MRR               : how highly the first correct document ranks
  - Retrieval latency : query embedding + similarity search (avg / p50 / p95)
  - Relevance sanity  : avg top similarity for in-KB vs out-of-KB questions

The printed numbers are measured, so they are safe to cite in a resume/report.
"""

import json
import os
import statistics
import time

from rag import search  # read-only: embeds the query and ranks pre-embedded chunks


HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_SET = os.path.join(HERE, "eval_set.json")

EVAL_TOP_K = 5   # how deep we look when scoring the rank of the correct document
AGENT_TOP_K = 2  # what the agent actually retrieves (tools.py search_knowledge_base)


def percentile(values, pct):
    """Nearest-rank percentile over a list of numbers (no numpy needed)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = round((pct / 100) * (len(ordered) - 1))
    return ordered[max(0, min(len(ordered) - 1, idx))]


def first_correct_rank(results, expected_source):
    """1-based rank of the first retrieved chunk from the expected document, else None."""
    for i, r in enumerate(results, start=1):
        if r["source"] == expected_source:
            return i
    return None


def main():
    with open(EVAL_SET, "r", encoding="utf-8") as f:
        data = json.load(f)

    in_kb = data["in_kb"]
    out_of_kb = data.get("out_of_kb", [])

    latencies_ms = []      # retrieval time per question
    ranks = []             # first-correct rank per in-KB question (or None)
    in_kb_top_scores = []  # top similarity per in-KB question
    rows = []              # per-question detail for printing

    print(f"\nEvaluating retrieval on {len(in_kb)} in-KB questions "
          f"(+ {len(out_of_kb)} out-of-KB)...\n")

    for item in in_kb:
        question = item["question"]
        expected = item["source"]

        t0 = time.perf_counter()
        results = search(question, top_k=EVAL_TOP_K)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

        rank = first_correct_rank(results, expected)
        ranks.append(rank)
        in_kb_top_scores.append(results[0]["score"] if results else 0.0)

        got = results[0]["source"] if results else "(none)"
        mark = "OK  " if (rank is not None and rank <= AGENT_TOP_K) else "MISS"
        rows.append((mark, question, expected, got, rank))

    out_top_scores = []
    for item in out_of_kb:
        t0 = time.perf_counter()
        results = search(item["question"], top_k=1)
        latencies_ms.append((time.perf_counter() - t0) * 1000)
        out_top_scores.append(results[0]["score"] if results else 0.0)

    # ---- Metrics ----
    n = len(in_kb)

    def recall_at(k):
        hits = sum(1 for r in ranks if r is not None and r <= k)
        return hits / n if n else 0.0

    mrr = (sum((1.0 / r) if r else 0.0 for r in ranks) / n) if n else 0.0

    # ---- Report ----
    print("Per-question (top retrieved document):")
    for mark, question, expected, got, rank in rows:
        where = f"rank {rank}" if rank else f"not in top {EVAL_TOP_K}"
        print(f"  [{mark}] {question}")
        print(f"         expected: {expected:<20} got: {got:<20} ({where})")

    print("\n" + "=" * 64)
    print("RETRIEVAL METRICS  (knowledge-base RAG)")
    print("=" * 64)
    print(f"  In-KB questions:          {n}")
    print(f"  Recall@1:                 {recall_at(1) * 100:5.1f}%")
    print(f"  Recall@2 (agent top_k):   {recall_at(2) * 100:5.1f}%")
    print(f"  Recall@3:                 {recall_at(3) * 100:5.1f}%")
    print(f"  MRR:                      {mrr:5.3f}")
    print("-" * 64)
    print("  Retrieval latency (query embed + search):")
    print(f"    avg {sum(latencies_ms) / len(latencies_ms):6.1f} ms"
          f"   p50 {percentile(latencies_ms, 50):6.1f} ms"
          f"   p95 {percentile(latencies_ms, 95):6.1f} ms")
    if out_top_scores:
        print("-" * 64)
        print("  Relevance sanity (top cosine similarity, higher = more relevant):")
        print(f"    in-KB avg {statistics.mean(in_kb_top_scores):.3f}"
              f"   out-of-KB avg {statistics.mean(out_top_scores):.3f}")
        print("    (in-KB should score clearly higher than out-of-KB)")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nEval failed: {e}")
        print("Make sure Ollama is running (as for the agent) and that .env has "
              "EMBED_MODEL, KB_FOLDER and VECTOR_STORE_FILE set.\n")
        raise SystemExit(1)
