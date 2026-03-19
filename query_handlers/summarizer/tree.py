from models import models
import asyncio
from query_handlers.summarizer.utils import split_text



LEAF_PROMPTS = ["Summarize the following text in one clear sentence:\n"]
PARENT_PROMPTS = ["Summarize the following text in one clear sentence:\n"]
SUFFIX = " Return exactly one sentence and nothing else."
NUMBER_CHILDREN_PER_PARENT = 4

class Node:
    def __init__(self, text="", safe_generate_func=None):
        self.text = text
        self.summary = None
        self.children = []
        self.safe_generate = safe_generate_func

    def summarize(self, level_type="leaf", idx=None):
        """Synchronous summarize method"""
        if idx is not None:
            print(f"Summarizing {level_type} node {idx}")

        if self.children:
            self._gather_text()

        prompts_to_use = LEAF_PROMPTS if level_type == "leaf" else PARENT_PROMPTS
        self.summary = self._best_summary(self.text, prompts_to_use)

        if idx is not None:
            print(f"{level_type.capitalize()} node {idx} done summarizing")

        return self.summary

    async def summarize_async(self, level_type="leaf", idx=None):
        """Asynchronous summarize method"""
        if idx is not None:
            print(f"Summarizing {level_type} node {idx}")

        if self.children:
            self._gather_text()

        prompts_to_use = LEAF_PROMPTS if level_type == "leaf" else PARENT_PROMPTS
        self.summary = await self._best_summary_async(self.text, prompts_to_use)

        if idx is not None:
            print(f"{level_type.capitalize()} node {idx} done summarizing")

        return self.summary

    def _best_summary(self, text, prompts):
        """Synchronous best summary - calls safe_generate directly"""
        results = []
        for prompt in prompts:
            full_prompt = prompt + text + SUFFIX
            results.append(self.safe_generate(full_prompt))

        candidates = [r.strip() for r in results if r.strip()]
        if not candidates:
            return text[:100]

        return min(candidates, key=lambda x: len(x.split()))

    async def _best_summary_async(self, text, prompts):
        """Asynchronous best summary - awaits safe_generate results"""
        tasks = []
        for prompt in prompts:
            full_prompt = prompt + text + SUFFIX
            tasks.append(self.safe_generate(full_prompt))
        
        results = await asyncio.gather(*tasks)

        candidates = [r.strip() for r in results if r.strip()]
        if not candidates:
            return text[:100]

        return min(candidates, key=lambda x: len(x.split()))

    def _gather_text(self):
        """Combine children summaries into this node's text"""
        self.text = " ".join(child.summary for child in self.children if child.summary)


# ======================
# Only two exposed functions
# ======================

async def create_tree_async(article, safe_generate_async, summarize_nodes_async,NUMBER_CHUNKS_PER_ARTICLE=4):
    """Asynchronous tree builder"""
    node_method = 'summarize_async'
    
    # --- Leaves ---
    chunks = split_text(article, NUMBER_CHUNKS_PER_ARTICLE)
    leaves = [Node(text=chunk, safe_generate_func=safe_generate_async) for chunk in chunks]
    await summarize_nodes_async(leaves, level_type="leaf", summarize_method=node_method)
    print("All leaves summarized ✅")

    current_level = leaves

    # --- Build tree ---
    while len(current_level) > 1:
        next_level = []
        parents = []
        for i in range(0, len(current_level), NUMBER_CHILDREN_PER_PARENT):
            parent = Node(safe_generate_func=safe_generate_async)
            parent.children = current_level[i:i+NUMBER_CHILDREN_PER_PARENT]
            parents.append(parent)

        await summarize_nodes_async(parents, level_type="parent", summarize_method=node_method)
        next_level.extend(parents)
        current_level = next_level

    root = current_level[0]
    print("Tree fully summarized. Root ready ✅")
    return root


def create_tree_sync(article, safe_generate_sync, summarize_nodes_sync,NUMBER_CHUNKS_PER_ARTICLE=4):
    """Synchronous tree builder"""
    node_method = 'summarize'
    
    # --- Leaves ---
    chunks = split_text(article, NUMBER_CHUNKS_PER_ARTICLE)
    leaves = [Node(text=chunk, safe_generate_func=safe_generate_sync) for chunk in chunks]
    summarize_nodes_sync(leaves, level_type="leaf", summarize_method=node_method)
    print("All leaves summarized ✅")

    current_level = leaves

    # --- Build tree ---
    while len(current_level) > 1:
        next_level = []
        parents = []
        for i in range(0, len(current_level), NUMBER_CHILDREN_PER_PARENT):
            parent = Node(safe_generate_func=safe_generate_sync)
            parent.children = current_level[i:i+NUMBER_CHILDREN_PER_PARENT]
            parents.append(parent)

        summarize_nodes_sync(parents, level_type="parent", summarize_method=node_method)
        next_level.extend(parents)
        current_level = next_level

    root = current_level[0]
    print("Tree fully summarized. Root ready ✅")
    return root