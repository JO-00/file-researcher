from ddgs import DDGS

def search_and_summarize_entity(entity_name, context=""):
    anchors = [word.lower() for word in context.split() if len(word) > 3]
    
    with DDGS() as ddgs:
        try:
            #  get 10 results so we have a 'pool' to pick from!!
            query = f'"{entity_name}" {context}'
            results = list(ddgs.text(query, max_results=10))
            
            if not results:
                return "No results found."

            scored_results = []
            for r in results:
                score = 0
                text_to_check = (r['title'] + " " + r['body']).lower()
                
                # Boost score if anchor words appear in the result
                for word in anchors:
                    if word in text_to_check:
                        score += 2
                
                # Penalty for irrelevance (if it's clearly a different person)
                if "performer" in text_to_check or "born 1981" in text_to_check:
                    score -= 5
                
                scored_results.append((score, r))

            # 3. Sort by score and take the best one
            scored_results.sort(key=lambda x: x[0], reverse=True)
            best_match = scored_results[0][1]

            return f"🌐 Relevant Result: {best_match['title']}\n\n{best_match['body']}"

        except Exception as e:
            return f"Relevance engine failed: {e}"