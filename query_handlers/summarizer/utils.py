from collections import deque
from models import models
import asyncio
from concurrent.futures import ThreadPoolExecutor


def split_text(article, n, tolerance=50):
        text = article.strip()
        length = len(text)
        target_size = max(1, length // n)
        split_characters = ".,;!"
        chunks = []
        start = 0

        def seek(text,char,ideal_end,tolerance):
            dot_pos = text.find(char, ideal_end)
            if dot_pos != -1 and (dot_pos - ideal_end) <= tolerance:
                return dot_pos + 1
            return False

        while start < length:
            ideal_end = start + target_size
            if ideal_end >= length:
                chunks.append(text[start:].strip())
                break

            for char in split_characters:
                split_pos = seek(text,char,ideal_end,tolerance)
                if split_pos:
                    break
            else:
                split_pos = ideal_end

            chunk = text[start:split_pos].strip()
            if chunk:
                chunks.append(chunk)
            start = split_pos

        return chunks[:n]


def get_document_domain(root,generate_func=None):
        SPECIAL_PROMPTS = [
            "what's the main topic of the following text, only output a nominal group, be very concise don't mention any dates or numbers:\n",
            "what's the main topic of the following text, only output a noun phrase, be very concise don't mention any dates or numbers:\n",
            "give the main subject of the text as a concise noun phrase, avoid dates or numbers:\n",
            "provide a short noun phrase describing the topic of the text, ignore dates and numbers:\n"
        ]

        prepositions = {
            "of","in","on","at","to","for","with","by","about","as","into","like",
            "through","after","over","between","out","against","during","without","before","under","around","among"
        }
        import re

        def prepare_for_ner(text):
            """
            Clean text to help spaCy's NER do its job better.
            Only removes obfuscations, doesn't try to identify entities.
            """
            if not text:
                return text
            
            # no possessives
            text = re.sub(r"'s\b", "", text)
            
            # no punctuation
            text = re.sub(r"[;,.:!?]$", "", text)
            
            # no brackets or paretheses
            text = re.sub(r'^[\(\[\{]|[\)\]\}]$', '', text)
            
            if '-' in text and not text[0].isupper():  # If not already capitalized
                parts = text.split('-')
                
                for part in parts:
                    if part and part[0].isupper():
                        text = part
                        break
            
            return text.strip()

        

        candidates = []
        for prompt in SPECIAL_PROMPTS:
            topic = models.ollama_generate(prompt + root.summary).strip()
            print(topic)
            if len(topic.split(" "))<=12: # max 12 words
                candidates.append(topic) 

        if not candidates:
            return ""

        scored = []
        root_text_lower = root.summary.lower()

        for c in candidates:
            words = [w.strip(".,;:!?").lower() for w in c.split()]
            score = 0

            for w in words:
                if w in prepositions:
                    score -= 1
                elif re.match(r"\b(1\d{3}|2\d{3})\b", w):
                    score -= 1

            if models.spacy_ner:
                doc = models.spacy_ner(c)
                for ent in doc.ents:
                    ent_text = prepare_for_ner(ent.text.strip())
                    if ent.label_ in {"PERSON","GPE","LOC","NORP","ORG"} or ent.text.istitle():
                        if ent_text.lower() in root_text_lower:
                            score += 5
                        else:
                            score -= 10

            scored.append((score,len(words), c))
        print(scored)
        scored.sort(key=lambda x: (-x[0], -x[1])) # highest score wins, if equal scores we pick longest topic

        return scored[0][2]


def summarize_pdf(root, level_of_precision):
    """Return concatenated summaries of all nodes at the given level."""
    if level_of_precision == 0:
        return root.summary

    queue = deque([(root, 0)])
    summaries = []

    while queue:
        node, lvl = queue.popleft()
        if lvl == level_of_precision:
            summaries.append(node.summary)
        elif lvl < level_of_precision:
            for child in node.children:
                queue.append((child, lvl + 1))

    return "\n".join(summaries)

def create_sync_llm_wrappers():
    """Create synchronous LLM wrapper functions"""
    def safe_generate(prompt):
        return models.ollama_generate(prompt)
    
    def summarize_nodes_limited(nodes, level_type="leaf", summarize_method='summarize', max_concurrent=None):
        """
        Summarize multiple nodes synchronously
        
        Args:
            nodes: List of nodes to summarize
            level_type: 'leaf' or 'parent'
            summarize_method: Which method to call ('summarize' or 'summarize_async')
            max_concurrent: Not used in sync mode, kept for API compatibility
        """
        results = []
        for idx, node in enumerate(nodes):
            # Get the appropriate summarize method
            summarize_func = getattr(node, summarize_method)
            result = summarize_func(level_type=level_type, idx=idx)
            results.append(result)
        return results
    
    return safe_generate, summarize_nodes_limited

def create_async_llm_wrappers(thread_count=1):
    """Create asynchronous LLM wrapper functions with semaphore control"""
    sem = asyncio.Semaphore(thread_count if thread_count > 0 else 1)
    executor = ThreadPoolExecutor(max_workers=thread_count)
    
    async def safe_generate_async(prompt):
        async with sem:
            return await asyncio.to_thread(models.ollama_generate, prompt)
    
    async def summarize_nodes_limited_async(nodes, level_type="leaf", summarize_method='summarize_async', max_concurrent=None):
        """
        Summarize multiple nodes asynchronously with TRUE concurrency
        
        Args:
            nodes: List of nodes to summarize
            level_type: 'leaf' or 'parent'
            summarize_method: Which method to call ('summarize' or 'summarize_async')
            max_concurrent: Maximum concurrent operations (uses thread_count if not specified)
        """
        # Use thread_count as the concurrency limit
        concurrency_limit = max_concurrent or thread_count
        sem = asyncio.Semaphore(concurrency_limit)
        
        async def summarize_with_sem(node, idx):
            async with sem:
                summarize_func = getattr(node, summarize_method)
                return await summarize_func(level_type=level_type, idx=idx)
        
        # Create all tasks first, THEN gather them
        tasks = [summarize_with_sem(node, idx) for idx, node in enumerate(nodes)]
        results = await asyncio.gather(*tasks)
        return results
    
    return safe_generate_async, summarize_nodes_limited_async

