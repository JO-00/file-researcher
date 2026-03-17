# utils.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def chunk_text(text, chunk_size=300, overlap=50):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i+chunk_size])
        if len(chunk.split()) > 30:
            chunks.append(chunk)
    return chunks

def find_relevant_chunks(query, chunks, embedder, top_k=5):
    """Return top_k chunk indices and scores"""
    if not chunks:
        return [], []
    q_emb = embedder.encode([query])
    chunk_embs = embedder.encode(chunks)
    similarities = cosine_similarity(q_emb, chunk_embs)[0]
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return top_indices, similarities[top_indices]