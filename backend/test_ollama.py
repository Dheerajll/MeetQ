import asyncio
from app.ai.ollama_client import ollama
from app.ai.prompts import TRANSLATE_SYSTEM_PROMPT, TRANSLATE_USER_PROMPT

async def test():
    # Simulate 3 chunks with overlap
    chunks = [
        {
            "chunk_id": 1,
            "raw_text": "[Speaker 0] हजुर, त्यो प्रोजेक्ट त भोलि सम्म सकिन्छ, तर अलिकति टेस्टिङ गर्न बाँकी छ"
        },
        {
            "chunk_id": 2,
            "raw_text": "[Speaker 0] टेस्टिङ गर्न बाँकी छ, अनि बल्ल डिप्लोइ गर्ने हो। [Speaker 1] हुन्छ, म भोलि हेर्छु"
        },
        {
            "chunk_id": 3,
            "raw_text": "[Speaker 1] म भोलि हेर्छु। Thanks everyone, let's wrap up here."
        },
    ]
    
    print("=" * 60)
    print("PASS 1: TRANSLATE EACH CHUNK INDEPENDENTLY")
    print("=" * 60)
    
    translated_chunks = []
    
    for chunk in chunks:
        prompt = TRANSLATE_USER_PROMPT.format(raw_text=chunk["raw_text"])
        
        print(f"\n--- Translating Chunk {chunk['chunk_id']} ---")
        print(f"Input:  {chunk['raw_text']}")
        
        result = await ollama.generate(prompt, system_prompt=TRANSLATE_SYSTEM_PROMPT)
        result = result.strip()
        
        print(f"Output: {result}")
        
        translated_chunks.append({
            "chunk_id": chunk["chunk_id"],
            "cleaned_text": result,
        })
    
    print("\n" + "=" * 60)
    print("ALL TRANSLATED CHUNKS:")
    print("=" * 60)
    for tc in translated_chunks:
        print(f"  Chunk {tc['chunk_id']}: {tc['cleaned_text']}")
    
    await ollama.close()

if __name__ == "__main__":
    asyncio.run(test())