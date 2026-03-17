from models import models

def get_document_domain(text):
    # Use a structural prompt that discourages full sentences
    snippet = text[:4000] if len(text) > 4000 else text
    prompt = (
        "Identify the primary topic of this text in a few words. Focus on the specific topic or domain it belongs to.\n"
        "Do not use full sentences. Do not use the word 'Topic'.\n\n"
        f"TEXT: {snippet}\n\n" 
        "TOPIC:"
    )
    
    try:
        print("Identifying document domain with Qwen3:0.6b via models.py...")
        
        # Calling the new method from models.py
        response_text = models.ollama_generate(prompt)
        
        print("Raw domain response:", response_text)
        clean_domain = response_text.strip()
        
        # Simple cleanup for any stray quotes or periods
        clean_domain = clean_domain.replace('"', '').replace('.', '').strip()
        
        return clean_domain.title() if clean_domain else "General Topic"
        
    except Exception as e:
        print(f"Domain Detection Error: {e}")
        return "General Topic"

def summarize_pdf(text):
    if not text: 
        return "No text found."
    
    snippet = text[:4000] if len(text) > 4000 else text
    prompt = f"Summarize this biography into 3 bullet points:\n\n{snippet}\n\nSUMMARY:"

    try:
        # Using the centralized model caller
        response_text = models.ollama_generate(prompt)
        return response_text
    except Exception as e:
        return f"Error: {e}"