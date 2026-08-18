import asyncio
from app.ai.ollama_client import ollama

async def test():
    system_prompt = """You are a professional meeting transcript translator.

STRICT RULES:
1. Translate ALL Nepali text to English faithfully and accurately.
2. Do NOT summarize, paraphrase, or omit any information.
3. Preserve ALL temporal references (tomorrow, next week, etc.).
4. Preserve ALL sequential meaning (first this, then that).
5. Remove only pure filler words that add zero meaning.
6. Output ONLY the translated text. No commentary.

Nepali to English reference for common meeting words:
- हजुर = Yes/Sure
- भोलि = tomorrow  
- अलिकति = a little bit
- बाँकी = remaining/pending
- अनि बल्ल = and then only / only after that
- नि त = (filler, can be removed)
"""
    
    user_prompt = "हजुर त्यो प्रोजेक्ट त भोलि सम्म सकिन्छ तर अलिकति टेस्टिङ गर्न बाँकी छ अनि बल्ल डिप्लोइ गरने हो नि त"
    
    print(f"Input: {user_prompt}\n")
    
    result = await ollama.generate(user_prompt, system_prompt=system_prompt)
    print(f"Ollama Output:\n{result}")
    
    await ollama.close()

if __name__ == "__main__":
    asyncio.run(test())