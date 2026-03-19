from models import models
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def answer_broad(question, node, threshold=0.2, best_so_far=None, is_root=True):
    """
    Recursively searches ALL nodes, and at leaf level checks overlapping windows.
    """
    query_vec = models.embedder.encode([question])
    
    if best_so_far is None:
        best_so_far = (-1.0, None, "node")  # (score, node/text, type)
    
    if isinstance(best_so_far, str):
        return best_so_far
    
    # Score current node (using node.text, not summary)
    try:
        current_vec = models.embedder.encode([node.text])  # Use node.text!
        current_score = float(cosine_similarity(query_vec, current_vec)[0][0])
    except Exception as e:
        print(f"Error scoring node: {e}")
        current_score = -1.0
    
    # Update best if current is better
    if isinstance(best_so_far, tuple) and current_score > best_so_far[0]:
        best_so_far = (current_score, node, "node")
        if current_score > 0.15:
            preview = node.text[:80] + "..." if len(node.text) > 80 else node.text
            print(f"   New best node: {current_score:.4f} - {preview}")
    
    # If this is a leaf node (no children), check overlapping windows with next leaf?
    # This is tricky in recursion - better to handle at parent level
    
    # Recursively search children
    if hasattr(node, 'children') and node.children:
        # Before diving into children, if this is a parent of leaves, check overlapping windows
        if node.children and not node.children[0].children:  # Children are leaves
            print(f"   📚 Checking overlapping windows at parent level...")
            for i in range(len(node.children) - 1):
                # Concatenate two consecutive leaves
                window_text = node.children[i].text + " " + node.children[i+1].text
                try:
                    window_vec = models.embedder.encode([window_text])
                    window_score = float(cosine_similarity(query_vec, window_vec)[0][0])
                    
                    if window_score > best_so_far[0]:
                        best_so_far = (window_score, window_text, "window")
                        if window_score > 0.15:
                            preview = window_text[:80] + "..." if len(window_text) > 80 else window_text
                            print(f"      ✨ New best window: {window_score:.4f} - {preview}")
                except Exception as e:
                    print(f"Error scoring window: {e}")
        
        # Now search children normally
        for child in node.children:
            result = answer_broad(question, child, threshold, best_so_far, is_root=False)
            if isinstance(result, str):
                return result
            elif isinstance(result, tuple):
                best_so_far = result
    
    # If this is the root, return formatted answer
    if is_root and isinstance(best_so_far, tuple) and best_so_far[1] is not None:
        best_score, best_content, content_type = best_so_far
        print(f"\n📊 Best score overall: {best_score:.4f} ({content_type})")
        
        # Extract the text to return
        if content_type == "node":
            answer_text = best_content.text
        else:  # window
            answer_text = best_content
        
        if best_score >= threshold:
            return f"the answer : {answer_text}"
        else:
            return f"only found: {answer_text}\n\n(Confidence: {best_score:.2f} - below threshold. Please verify this information.)"
    
    return best_so_far



