# query_handlers/broad_qa.py
from models import models
from utils import find_relevant_chunks, chunk_text

def answer_broad(question, full_text):
    """For questions like 'Who is X?' – synthesize from top chunks"""
    chunks = chunk_text(full_text)
    top_indices, scores = find_relevant_chunks(question, chunks, models.embedder, top_k=3)
    context = ' '.join([chunks[i] for i in top_indices])
    # Use summarizer to synthesize
    summary = models.summarizer(context[:1500], max_length=150, min_length=50)[0]['summary_text']
    return summary