"""
Test: Context-aware cleaning with raw-text overlap detection.
"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.services.cleaning_service import clean_chunks_in_memory


TEST_CHUNKS = [
    {
        "chunk_id": 1,
        "raw_text": (
            "[Speaker 0] हजुर, त्यो प्रोजेक्ट को बारे मा कुरा गरौं। "
            "मलाई लाग्छ कि हामीले भोलि सम्म डेडलाइन "
        ),
    },
    {
        "chunk_id": 2,
        "raw_text": (
            "[Speaker 0] भोलि सम्म डेडलाइन राख्नु पर्छ। "
            "तर testing गर्न बाँकी छ। "
            "[Speaker 1] हजुर, म सहमत छु। "
            "QA ले first pass गर्नु पर्छ।"
        ),
    },
    {
        "chunk_id": 3,
        "raw_text": (
            "[Speaker 1] Ani deployment ko plan k cha? "
            "Hami le Friday samma finish garna parcha. "
            "[Speaker 0] Huncha, tara QA team le "
            "sign off garna parcha first."
        ),
    },
    {
        "chunk_id": 4,
        "raw_text": (
            "[Speaker 0] Huncha, tara QA team le sign off garna parcha first. "
            "Ani matra production ma jane. "
            "[Speaker 1] Thik cha, ma QA team lai "
        ),
    },
    {
        "chunk_id": 5,
        "raw_text": (
            "[Speaker 1] ma QA team lai message garnechu aaja. "
            "[Speaker 0] Great, let's wrap up here. "
            "Thanks everyone for joining today."
        ),
    },
]


async def main():
    print("🧪 TESTING RAW-TEXT OVERLAP DETECTION + TRANSLATION")
    print(f"   Chunks: {len(TEST_CHUNKS)}")
    print(f"   Strategy: Detect overlap on RAW → Trim → Translate only NEW")
    
    cleaned = await clean_chunks_in_memory(TEST_CHUNKS)
    
    # Print final combined transcript
    print("\n" + "=" * 70)
    print("FINAL COMBINED TRANSCRIPT")
    print("=" * 70)
    
    # Filter out empty chunks
    non_empty = [c for c in cleaned if c.strip()]
    full_text = "\n".join(non_empty)
    print(f"\n{full_text}\n")
    
    print("=" * 70)
    print("CHUNK BY CHUNK:")
    print("=" * 70)
    for i, text in enumerate(cleaned):
        if text.strip():
            print(f"\n  [Chunk {i+1}]: {text}")
        else:
            print(f"\n  [Chunk {i+1}]: (empty — was overlap)")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())