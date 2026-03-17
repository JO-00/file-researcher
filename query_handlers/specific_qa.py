# query_handlers/specific_qa.py
from models import models
from utils import find_relevant_chunks, chunk_text

def answer_specific(question, full_text):
    chunks = chunk_text(full_text)
    top_indices, scores = find_relevant_chunks(question, chunks, models.embedder, top_k=3)
    context = ' '.join([chunks[i] for i in top_indices])
    result = models.qa(question=question, context=context)
    return result['answer'], result['score']