# Embeddings wrapper
# Uses sentence-transformers to convert text to vector embeddings
"""
Embeddings wrapper.
Uses sentence-transformers to convert text to vector embeddings.
Model: all-MiniLM-L6-v2 (384 dimensions, fast, great for local CPU/Metal).
"""

from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once at startup (takes ~2 seconds, then stays in memory)
print("🧠 Loading embedding model (all-MiniLM-L6-v2)...")
_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✓ Embedding model ready")

# Dimension of the vectors produced by this model
EMBEDDING_DIM = 384


def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    Convert a list of strings into a numpy array of vectors.
    
    Args:
        texts: List of strings to embed.
        
    Returns:
        Numpy array of shape (len(texts), 384) with float32 precision.
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, EMBEDDING_DIM)
        
    # encode returns a numpy array, we ensure it's float32 for FAISS
    vectors = _model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(vectors, dtype=np.float32)