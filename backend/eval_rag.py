"""
RAG Evaluation Script for MeetQ (English Domains)
- Loads cleaned chunks from AMI + TED eval_results
- Indexes them in FAISS using Ollama nomic-embed-text (768-dim)
- Runs 12 test queries through retrieval + generation
- Saves results to eval_results/rag_eval/

Usage (backend env):
    python eval_rag.py
"""
import asyncio
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")

# ── Backend imports (uses YOUR production code) ────────────────────
from app.ai.embeddings import get_embeddings, get_single_embedding, EMBEDDING_DIM
from app.services.cleaning import clean_chunks_in_memory

# ── Configuration ──────────────────────────────────────────────────
EVAL_ROOT = Path.home() / "MeetQ/Local meeting agent/LMA_v1/lma/eval_results"
OUTPUT_DIR = EVAL_ROOT / "rag_eval"
FAISS_INDEX_PATH = OUTPUT_DIR / "faiss_index.bin"
RESULTS_PATH = OUTPUT_DIR / "rag_eval_results.json"

TOP_K = 5
EMBED_BATCH_SIZE = 20  # Ollama handles batching; keep requests reasonable

ENGLISH_RUNS = [
    "ami_1", "ami_2", "ami_3",
    "ted_1", "ted_2", "ted_3",
]

TEST_QUERIES = [
    {
        "id": 1, "type": "factual_lookup",
        "query": "What price point was proposed for the remote control in the AMI meeting?",
        "expected": "25 euros, with clarification needed on whether this is wholesale or retail",
        "source": "AMI ES2002a",
    },
    {
        "id": 2, "type": "factual_lookup",
        "query": "According to Patrick Winston, what three factors determine the quality of communication?",
        "expected": "Knowledge (K), Practice (P), and inherent Talent (T), where T is very small compared to K and P",
        "source": "TED Patrick Winston",
    },
    {
        "id": 3, "type": "decision_retrieval",
        "query": "What rule of engagement did Patrick Winston establish at the start of his lecture?",
        "expected": "No laptops and no cell phones, because humans have only one language processor",
        "source": "TED Patrick Winston",
    },
    {
        "id": 4, "type": "multi_hop",
        "query": "How does Patrick Winston's skiing anecdote about Mary Lou Retton relate to the KPT formula?",
        "expected": "Retton had high talent but was a novice skier; Winston was better because he had knowledge and practice. K and P matter more than T alone",
        "source": "TED Patrick Winston",
    },
    {
        "id": 5, "type": "multi_hop",
        "query": "Why does Patrick Winston recommend cycling through topics three times during a talk?",
        "expected": "Because about 20% of the audience will be fogged out at any moment, so repeating ensures everyone receives the message",
        "source": "TED Patrick Winston",
    },
    {
        "id": 6, "type": "speaker_attribution",
        "query": "Who proposed the empowerment promise technique for starting talks?",
        "expected": "Patrick Winston",
        "source": "TED Patrick Winston",
    },
    {
        "id": 7, "type": "speaker_attribution",
        "query": "In the AMI meeting, who led the remote control design project?",
        "expected": "Laura",
        "source": "AMI ES2002a",
    },
    {
        "id": 8, "type": "concept_explanation",
        "query": "What does building a fence around an idea mean according to Patrick Winston?",
        "expected": "Clearly distinguishing your idea from similar ideas by explicitly stating what it is NOT",
        "source": "TED Patrick Winston",
    },
    {
        "id": 9, "type": "negative_unanswerable",
        "query": "What budget was allocated for Q4 marketing in the AMI meeting?",
        "expected": "Not mentioned in the transcript",
        "source": "Should return not mentioned",
    },
    {
        "id": 10, "type": "factual_lookup",
        "query": "What target revenue was mentioned for the remote control project?",
        "expected": "50 million euros",
        "source": "AMI ES2002a",
    },
    {
        "id": 11, "type": "concept_explanation",
        "query": "What is verbal punctuation according to Patrick Winston?",
        "expected": "Providing landmark places in a talk where the speaker announces structure so listeners who fogged out can get back on track",
        "source": "TED Patrick Winston",
    },
    {
        "id": 12, "type": "factual_lookup",
        "query": "How long should a speaker pause when asking the audience a question?",
        "expected": "Seven seconds, which feels like an eternity but is the standard amount of time to wait for an answer",
        "source": "TED Patrick Winston",
    },
]


async def load_and_clean_chunks(run_name: str) -> list[dict]:
    """Load chunks.json for a run, clean them, return enriched chunks."""
    chunks_path = EVAL_ROOT / run_name / "chunks.json"
    if not chunks_path.exists():
        print(f"  ⚠️  {run_name}: chunks.json not found, skipping")
        return []

    raw_chunks = json.loads(chunks_path.read_text())
    chunks_data = [{"chunk_id": c["chunk_id"], "raw_text": c["raw_text"]} for c in raw_chunks]
    cleaned_texts = await clean_chunks_in_memory(chunks_data)

    enriched = []
    for raw, cleaned in zip(raw_chunks, cleaned_texts):
        if not cleaned or not cleaned.strip():
            continue
        enriched.append({
            "run": run_name,
            "chunk_id": raw["chunk_id"],
            "text": cleaned,
            "start_ms": raw.get("start_ms", 0),
            "end_ms": raw.get("end_ms", 0),
        })
    return enriched


async def embed_in_batches(texts: list[str], batch_size: int = EMBED_BATCH_SIZE) -> np.ndarray:
    """Embed texts using Ollama nomic-embed-text in batches."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"    Embedding batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size} "
              f"({len(batch)} chunks)...")
        embs = await get_embeddings(batch)
        all_embeddings.extend(embs)
    return np.array(all_embeddings, dtype=np.float32)


def build_faiss_index(embeddings: np.ndarray):
    """Build FAISS index from pre-computed embeddings."""
    import faiss
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product (cosine sim since normalized)
    index.add(embeddings)
    return index


def search_faiss(index, query_embedding: np.ndarray, top_k: int) -> list[tuple[int, float]]:
    """Search FAISS index, return (chunk_index, score) pairs."""
    scores, indices = index.search(query_embedding.reshape(1, -1), top_k)
    return list(zip(indices[0].tolist(), scores[0].tolist()))


async def generate_answer_via_ollama(query: str, context: str) -> str:
    """Generate answer using Ollama LLM (same as production RAG)."""
    import httpx
    from app.core.config import get_settings
    settings = get_settings()

    prompt = (
        f"Answer the following question based ONLY on the provided context. "
        f"If the answer is not in the context, say 'Not mentioned in the transcript.'\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    )

    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
        response = await client.post("/api/generate", json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        })
        response.raise_for_status()
        return response.json().get("response", "")


async def evaluate_single_query(query_item: dict, index, chunks: list[dict]) -> dict:
    """Run one query through retrieval + generation."""
    q = query_item["query"]

    # Retrieve
    t0 = time.time()
    q_emb = await get_single_embedding(q)
    q_emb_np = np.array(q_emb, dtype=np.float32)
    hits = search_faiss(index, q_emb_np, TOP_K)
    retrieval_time = round(time.time() - t0, 3)

    retrieved_chunks = []
    for idx, score in hits:
        if idx < 0 or idx >= len(chunks):
            continue
        retrieved_chunks.append({
            "run": chunks[idx]["run"],
            "chunk_id": chunks[idx]["chunk_id"],
            "score": round(float(score), 4),
            "text_preview": chunks[idx]["text"][:200],
        })

    # Generate answer
    context = "\n\n".join(
        f"[{chunks[idx]['run']} chunk {chunks[idx]['chunk_id']}]: {chunks[idx]['text']}"
        for idx, _ in hits
        if 0 <= idx < len(chunks)
    )

    t0 = time.time()
    try:
        answer = await generate_answer_via_ollama(q, context)
    except Exception as e:
        answer = f"GENERATION ERROR: {str(e)}"
    generation_time = round(time.time() - t0, 3)

    return {
        "query_id": query_item["id"],
        "query_type": query_item["type"],
        "query": q,
        "expected": query_item["expected"],
        "source": query_item["source"],
        "retrieved_chunks": retrieved_chunks,
        "generated_answer": answer,
        "retrieval_time_s": retrieval_time,
        "generation_time_s": generation_time,
    }


async def main():
    import faiss
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Load and clean chunks ──────────────────────────────
    print("=" * 60)
    print("STEP 1: Loading and cleaning English eval chunks")
    print("=" * 60)

    all_chunks = []
    for run in ENGLISH_RUNS:
        print(f"\n📂 Loading {run}...")
        chunks = await load_and_clean_chunks(run)
        print(f"   ✓ {len(chunks)} cleaned chunks")
        all_chunks.extend(chunks)

    print(f"\n✅ Total chunks: {len(all_chunks)}")

    # ── Step 2: Embed and build FAISS index ────────────────────────
    print("\n" + "=" * 60)
    print(f"STEP 2: Embedding {len(all_chunks)} chunks via Ollama nomic-embed-text")
    print("=" * 60)

    texts = [c["text"] for c in all_chunks]
    embeddings = await embed_in_batches(texts)
    print(f"   Embeddings shape: {embeddings.shape}")

    index = build_faiss_index(embeddings)
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    print(f"✅ FAISS index saved to {FAISS_INDEX_PATH}")

    # ── Step 3: Run queries ────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"STEP 3: Evaluating {len(TEST_QUERIES)} RAG queries")
    print("=" * 60)

    results = []
    for i, query_item in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] {query_item['type']}: {query_item['query'][:60]}...")
        result = await evaluate_single_query(query_item, index, all_chunks)
        results.append(result)
        print(f"   Retrieved {len(result['retrieved_chunks'])} chunks | "
              f"Retrieval: {result['retrieval_time_s']}s | "
              f"Generation: {result['generation_time_s']}s")
        print(f"   Answer: {result['generated_answer'][:120]}...")

    # ── Step 4: Summary stats ──────────────────────────────────────
    avg_retrieval = round(np.mean([r["retrieval_time_s"] for r in results]), 3)
    avg_generation = round(np.mean([r["generation_time_s"] for r in results]), 3)

    summary = {
        "total_queries": len(results),
        "total_chunks_indexed": len(all_chunks),
        "embedding_model": "nomic-embed-text (768-dim)",
        "runs_indexed": ENGLISH_RUNS,
        "top_k": TOP_K,
        "avg_retrieval_time_s": avg_retrieval,
        "avg_generation_time_s": avg_generation,
        "results": results,
    }

    RESULTS_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("RAG EVALUATION COMPLETE")
    print("=" * 60)
    print(f"Queries evaluated:     {len(results)}")
    print(f"Chunks indexed:        {len(all_chunks)}")
    print(f"Embedding model:       nomic-embed-text (768-dim)")
    print(f"Avg retrieval time:    {avg_retrieval}s")
    print(f"Avg generation time:   {avg_generation}s")
    print(f"\n💾 Results: {RESULTS_PATH}")
    print(f"💾 FAISS index: {FAISS_INDEX_PATH}")


if __name__ == "__main__":
    asyncio.run(main())