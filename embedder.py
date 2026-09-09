"""
Embedding logic using sentence-transformers/all-MiniLM-L6-v2.
Converts text chunks into 384-dim vectors for pgvector storage.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import numpy as np


class Embedder:
    """Wrapper around sentence-transformers for batch embedding"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedder with model.
        
        Args:
            model_name: HuggingFace model ID (default: all-MiniLM-L6-v2 = 384 dims)
        """
        print(f"📦 Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f"✅ Model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed multiple texts in batches.
        
        Args:
            texts: List of text strings
            batch_size: How many to embed at once (default 32, adjust for GPU RAM)
        
        Returns:
            numpy array of shape (len(texts), 384)
        """
        print(f"  Embedding {len(texts)} chunks (batch_size={batch_size})...")
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """
        Embed a single text (for query embedding in Streamlit app).
        
        Args:
            text: Single text string
        
        Returns:
            List of floats (length 384)
        """
        embedding = self.model.encode(text)
        return embedding.tolist()


def batch_embed_chunks(embedder: Embedder, chunk_texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Embed a list of chunk texts and return as list of lists (pgvector-friendly).
    
    Args:
        embedder: Embedder instance
        chunk_texts: List of chunk content strings
        batch_size: Batch size for embedding
    
    Returns:
        List of embeddings (each is List[float])
    """
    if not chunk_texts:
        return []
    
    embeddings = embedder.embed_texts(chunk_texts, batch_size=batch_size)
    return embeddings.tolist()
