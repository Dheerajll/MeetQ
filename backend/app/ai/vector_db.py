# Vector database management using FAISS
# Handles index creation, saving, loading, and similarity search
"""
Vector database management using FAISS.
Handles index creation, saving, loading, and similarity search.

We use IndexFlatIP (Inner Product) because we normalize our vectors 
in embeddings.py, which makes Inner Product equivalent to Cosine Similarity.
"""

import faiss
import numpy as np
from pathlib import Path

from app.ai.embeddings import EMBEDDING_DIM

# Store the FAISS index in the user's cache directory
INDEX_DIR = Path.home() / ".cache" / "meetq" / "faiss"
INDEX_PATH = INDEX_DIR / "meetq.index"


class VectorDB:
    """
    FAISS wrapper.
    Uses Postgres `TranscriptChunk.id` as the FAISS vector ID.
    """

    def __init__(self):
        self.index: faiss.Index | None = None
        self._ensure_dir()
        self._load_or_create()

    def _ensure_dir(self):
        INDEX_DIR.mkdir(parents=True, exist_ok=True)

    def _load_or_create(self):
        """Load existing index from disk, or create a new empty one."""
        if INDEX_PATH.exists():
            print(f"📂 Loading existing FAISS index from {INDEX_PATH}")
            self.index = faiss.read_index(str(INDEX_PATH))
        else:
            print("✨ Creating new FAISS index")
            # IndexFlatIP = Inner Product (Cosine Similarity for normalized vectors)
            self.index = faiss.IndexFlatIP(EMBEDDING_DIM)

    def add(self, chunk_ids: list[int], vectors: np.ndarray) -> None:
        """
        Add vectors to the index.
        
        Args:
            chunk_ids: List of Postgres TranscriptChunk IDs (must be int64).
            vectors: Numpy array of shape (N, 384).
        """
        if len(chunk_ids) == 0:
            return

        # FAISS requires int64 for IDs
        ids_array = np.array(chunk_ids, dtype=np.int64)
        
        # We need an IndexIDMap to support custom IDs (instead of auto-incrementing 0,1,2)
        if not isinstance(self.index, faiss.IndexIDMap):
            print("🔄 Upgrading FAISS index to support custom IDs...")
            self.index = faiss.IndexIDMap(self.index)

        self.index.add_with_ids(vectors, ids_array)
        self._save()
        print(f"✅ Added {len(chunk_ids)} vectors to FAISS (Total: {self.index.ntotal})")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> tuple[list[int], list[float]]:
        """
        Search for the most similar vectors.
        
        Args:
            query_vector: Numpy array of shape (1, 384).
            top_k: Number of results to return.
            
        Returns:
            Tuple of (chunk_ids, similarity_scores).
        """
        if self.index.ntotal == 0:
            return [], []

        # Ensure top_k doesn't exceed total vectors
        k = min(top_k, self.index.ntotal)

        # Search returns (distances, indices)
        scores, indices = self.index.search(query_vector, k)

        # Extract the IDs and scores, filtering out any -1 (empty slots)
        result_ids = []
        result_scores = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1:
                result_ids.append(int(idx))
                result_scores.append(float(score))

        return result_ids, result_scores

    def _save(self):
        """Persist the index to disk."""
        faiss.write_index(self.index, str(INDEX_PATH))

    def clear(self):
        """Delete the index and start fresh."""
        if INDEX_PATH.exists():
            INDEX_PATH.unlink()
        self._load_or_create()


# Global singleton instance
vector_db = VectorDB()