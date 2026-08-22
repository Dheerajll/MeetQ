"""
Test RAG search step by step.
Usage: python test_rag_search.py
"""
import asyncio
import sys

sys.path.insert(0, ".")


async def main():
    query = "What role does GTM have?"
    user_id = 1  # Adjust if your user ID is different

    print(f"\n{'=' * 60}")
    print(f"🔍 RAG SEARCH DEBUG")
    print(f"{'=' * 60}")
    print(f"Query: {query}")
    print(f"User ID: {user_id}")

    # ──────────────────────────────────────────────
    # Step 1: Test query parser
    # ──────────────────────────────────────────────
    print(f"\n[1/4] Testing query parser...")
    from app.services.query_parser import parse_query
    parsed = parse_query(query)
    print(f"  start_date: {parsed.start_date}")
    print(f"  end_date: {parsed.end_date}")

    if parsed.start_date:
        print(f"  ⚠️ Time filter IS being applied!")
    else:
        print(f"  ✓ No time filter")

    # ──────────────────────────────────────────────
    # Step 2: Test embedding generation
    # ──────────────────────────────────────────────
    print(f"\n[2/4] Testing embedding generation...")
    from app.ai.embeddings import get_single_embedding
    try:
        vector = await get_single_embedding(query)
        if vector:
            print(f"  ✓ Embedding generated: {len(vector)} dimensions")
            print(f"  First 5 values: {vector[:5]}")
        else:
            print(f"  ❌ Embedding is EMPTY!")
            return
    except Exception as e:
        print(f"  ❌ Embedding failed: {e}")
        return

    # ──────────────────────────────────────────────
    # Step 3: Test search WITHOUT time filters
    # ──────────────────────────────────────────────
    print(f"\n[3/4] Testing search (no time filters)...")
    from app.core.database import AsyncSessionLocal
    from app.services.rag_service import search_similar_chunks

    async with AsyncSessionLocal() as db:
        chunks = await search_similar_chunks(
            query=query,
            user_id=user_id,
            db=db,
            top_k=5,
            start_date=None,  # No time filter
            end_date=None,
            meeting_id=None,
        )

    print(f"  Found {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        text_preview = (chunk.cleaned_text or chunk.raw_text)[:80]
        print(f"  [{i+1}] meeting={chunk.meeting_id}, chunk={chunk.chunk_id}: {text_preview}...")

    # ──────────────────────────────────────────────
    # Step 4: Test search WITH parsed time filters
    # ──────────────────────────────────────────────
    if parsed.start_date:
        print(f"\n[4/4] Testing search WITH time filters...")
        async with AsyncSessionLocal() as db:
            chunks_filtered = await search_similar_chunks(
                query=query,
                user_id=user_id,
                db=db,
                top_k=5,
                start_date=parsed.start_date,
                end_date=parsed.end_date,
                meeting_id=None,
            )
        print(f"  Found {len(chunks_filtered)} chunks (with time filter)")
    else:
        print(f"\n[4/4] Skipped (no time filter to test)")

    print(f"\n{'=' * 60}")
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())