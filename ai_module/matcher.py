from difflib import SequenceMatcher
import re

def clean_text(text):
    """Normalize text by removing punctuation and lowering case."""
    return re.sub(r'[^a-z0-9\s]', '', text.lower().strip())

def text_similarity(a, b):
    """Return similarity between two strings using SequenceMatcher"""
    a, b = clean_text(a), clean_text(b)
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()

def score_pair(lost, found):
    """
    Compute a weighted similarity score between a lost item and a found item.
    Returns a float between 0 and 1.
    """
    score = 0.0

    NAME_WEIGHT = 0.45
    CATEGORY_WEIGHT = 0.2
    LOCATION_WEIGHT = 0.2
    DESC_WEIGHT = 0.15

    # Compute weighted fields
    name_score = text_similarity(lost.get("name", ""), found.get("name", ""))
    score += name_score * NAME_WEIGHT

    category_score = text_similarity(lost.get("category", ""), found.get("category", ""))
    score += category_score * CATEGORY_WEIGHT

    location_score = text_similarity(lost.get("location", ""), found.get("location", ""))
    score += location_score * LOCATION_WEIGHT

    desc_score = text_similarity(lost.get("description", ""), found.get("description", ""))
    score += desc_score * DESC_WEIGHT

    return round(score, 3)
