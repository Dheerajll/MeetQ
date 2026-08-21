"""
Embeddings via Ollama.

Uses Ollama's /api/embed endpoint to generate vector embeddings.
No model loading in the FastAPI process — Ollama manages the model lifecycle.

Model: nomic-embed-text (768 dimensions)
Pull it with: ollama pull nomic-embed-text
"""

import httpx

from app.core.config import get_settings

settings = get_settings()

# Ollama embedding model (separate from the LLM model used for generation)
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of strings into vector embeddings using Ollama.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (each is a list of 768 floats).
    """
    if not texts:
        return []

    async with httpx.AsyncClient(
        base_url=settings.ollama_base_url,
        timeout=60.0,
    ) as client:
        response = await client.post(
            "/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": texts,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Ollama returns {"embeddings": [[...], [...], ...]}
        return data.get("embeddings", [])


async def get_single_embedding(text: str) -> list[float]:
    """Embed a single string. Convenience wrapper."""
    results = await get_embeddings([text])
    return results[0] if results else []