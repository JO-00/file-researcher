import re
from models import models

def extract_dates_with_context(text, context_window=100):

    #Extract dates using regex and NER, returning each date with surrounding text.
    try:
        entities = models.ner(text)
        date_entities = [ent for ent in entities if ent['entity_group'] == 'DATE']
        ner_dates = set()
        for ent in date_entities:
            # Get surrounding context
            start = max(0, ent['start'] - context_window)
            end = min(len(text), ent['end'] + context_window)
            context = text[start:end].replace('\n', ' ')
            ner_dates.add((ent['word'], context))
    except:
        ner_dates = set()
    
    
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',                    
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  
        r'\b\d{4}\b',                                              
        r'\b(?:19|20)\d{2}s\b'                                   
    ]
    
    regex_dates = set()
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            date_str = match.group()
            start = max(0, match.start() - context_window)
            end = min(len(text), match.end() + context_window)
            context = text[start:end].replace('\n', ' ')
            regex_dates.add((date_str, context))
    
    
    all_dates = list(ner_dates | regex_dates)
    all_dates.sort(key=lambda x: x[0])  # sort by date string
    return [{'date': date_str, 'context': context} for date_str, context in all_dates]