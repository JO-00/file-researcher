import ollama
import spacy
from transformers import pipeline

class Models:
    def __init__(self):
        try:
            self.spacy_ner = spacy.load("en_core_web_sm")
        except:
            self.spacy_ner = None
        self.qa = pipeline("question-answering", model="deepset/roberta-base-squad2")

    def ollama_generate(self, prompt, model_name='qwen3:0.6b'):
        """Centralized Ollama call to keep handlers light."""
        try:
            response = ollama.generate(
                model=model_name,
                prompt=prompt
            )
            return response['response']
        except Exception as e:
            return f"Ollama Error: {e}"
        
models = Models()