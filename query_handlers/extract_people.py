import re
from models import models

# Common OCR/non‑name tokens that appear in PDFs
UNWANTED_SUBSTRINGS = {
    'scan', 'download', 'book', 'check', 'summary', 'audiobook',
    'unlock', 'full', 'text', 'part', 'legacy', 'icon', 'spot',
    'beneath', 'behind', 'under', 'above', 'inside', 'outside',
    'during', 'before', 'after', 'while', 'without', 'between',
    'through', 'via', 'per', 'among', 'despite', 'throughout',
    'within', 'across', 'against', 'along', 'around', 'by', 'for',
    'from', 'in', 'into', 'of', 'off', 'on', 'to', 'with', 'as',
    'like', 'including', 'such', 'these', 'those', 'this', 'that',
    'its', 'their', 'our', 'your', 'her', 'his', 'my', 'was', 'were',
    'is', 'are', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'shall', 'should', 'may', 'might', 'must',
    'can', 'could'
}

def clean_name(name):
    name = name.replace('’', "'").replace('‘', "'")
    name = re.sub(r"'s$|s'$", '', name).strip()
    name = name.strip('.,;:!?"\'')
    return name

def extract_people(text):
    """
    Extract person names using spaCy NER, clean, filter OCR artifacts,
    and deduplicate (keep longest unique names).
    """
    doc = models.spacy_ner(text)

    candidates = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            raw_name = ent.text.strip()
            if len(raw_name) < 2:
                continue
            # Clean and filter
            cleaned = clean_name(raw_name)
            if not cleaned:
                continue
            if any(sub in cleaned.lower() for sub in UNWANTED_SUBSTRINGS):
                continue
            candidates.append(cleaned)

    unique = []
    for name in sorted(candidates, key=len, reverse=True):
        # If this name is not a substring of any already kept name, add it
        if not any(name in other for other in unique):
            unique.append(name)

    return sorted(unique)