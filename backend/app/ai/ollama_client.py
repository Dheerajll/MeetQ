# Ollama client wrapper
# Provides async interface for chat, summarization, and text cleaning via Ollama API
"""
Async client for interacting with the local Ollama API.
"""
import httpx
from app.core.config import get_settings

settings = get_settings()

class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: float = 120.0):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Sends a prompt to Ollama and returns the generated text.
        Uses non-streaming mode for easier parsing in background tasks.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  # Low temperature for strict translation/cleaning       # Use top-p sampling
                "num_predict": 2048, # Max tokens to generate
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Ollama returns the text in the 'response' key
            return data.get("response", "")
            
        except httpx.TimeoutException:
            print(f"⚠️ Ollama request timed out (>{self.client.timeout}s)")
            raise
        except httpx.HTTPStatusError as e:
            print(f"❌ Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(self.model) for m in models)
        except Exception:
            return False

# Global instance
ollama = OllamaClient(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model
)