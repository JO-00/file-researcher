# this is the summarizer brain, it calls the other summmary APIs !
import asyncio
from models import models
from query_handlers.summarizer.utils import (
    get_document_domain, 
    summarize_pdf,
    create_sync_llm_wrappers,
    create_async_llm_wrappers
)
from query_handlers.summarizer.tree import create_tree_async, create_tree_sync


def create_summarizer(async_mode=False, thread_count=1,NUMBER_CHUNKS_PER_ARTICLE=4):
    
    if async_mode:
        
        safe_generate, summarize_nodes_limited = create_async_llm_wrappers(thread_count)
        
        return {
            'createTree': lambda article: asyncio.run(create_tree_async(
                article, 
                safe_generate, 
                summarize_nodes_limited,
                NUMBER_CHUNKS_PER_ARTICLE
            )),
            'get_document_domain': lambda root: get_document_domain(root, models.ollama_generate),
            'summarize_pdf': summarize_pdf,
            'async_mode': True,
            'thread_count': thread_count
        }
    
    else:

        safe_generate, summarize_nodes_limited = create_sync_llm_wrappers()

        
        # Return configured sync functions
        return {
            'createTree': lambda article: create_tree_sync(
                article, 
                safe_generate, 
                summarize_nodes_limited,
                NUMBER_CHUNKS_PER_ARTICLE
            ),
            'get_document_domain': lambda root: get_document_domain(root, generate_func = models.ollama_generate),
            'summarize_pdf': summarize_pdf,
            'async_mode': False,
            'thread_count': 1
        }