# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import re
from collections import Counter

# Read input dataset
input_dataset = dataiku.Dataset("YOUR_INPUT_DATASET_NAME")
df = input_dataset.get_dataframe()

# Define keywords to analyze
keywords = [
    'message', 
    'comment', 
    'email', 
    'text', 
    'video', 
    'electronic communication',
    'ecomm',
    'e-comm',
    'sms',
    'social media',
    'chat'
]

text_column = 'TXT_RSRC_DESC'

def extract_context_phrases(text, keyword):
    """
    Extract phrases with 1 word before and 1 word after the keyword.
    For multi-word keywords, treats the entire phrase as the keyword.
    Returns list of tuples: (word_before, keyword, word_after)
    """
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    # Clean text
    text_lower = text.lower()
    # Replace punctuation with spaces to avoid weird tokens
    text_clean = re.sub(r'[^\w\s-]', ' ', text_lower)  # Keep hyphens for e-comm
    
    phrases = []
    
    # For multi-word keywords, find the exact phrase
    if ' ' in keyword or '-' in keyword:
        # Find all occurrences of the multi-word keyword
        pattern = r'\b' + re.escape(keyword) + r'\b'
        for match in re.finditer(pattern, text_lower):
            start_pos = match.start()
            end_pos = match.end()
            
            # Get text before and after
            before_text = text_lower[:start_pos].strip()
            after_text = text_lower[end_pos:].strip()
            
            # Get last word before
            before_words = before_text.split()
            word_before = before_words[-1] if before_words else '<START>'
            
            # Get first word after
            after_words = after_text.split()
            word_after = after_words[0] if after_words else '<END>'
            
            phrases.append((word_before, keyword, word_after))
    else:
        # Single word keyword - tokenize normally
        words = text_clean.split()
        
        for i, word in enumerate(words):
            if word == keyword:
                word_before = words[i-1] if i > 0 else '<START>'
                word_after = words[i+1] if i < len(words) - 1 else '<END>'
                phrases.append((word_before, keyword, word_after))
    
    return phrases

# Collect ALL three-word phrases across ALL keywords
all_phrases = Counter()

print("="*80)
print("ANALYZING COMMUNICATION KEYWORDS...")
print("="*80)

for keyword in keywords:
    for text in df[text_column]:
        phrases = extract_context_phrases(text, keyword)
        
        for word_before, kw, word_after in phrases:
            phrase = f"{word_before} {kw} {word_after}"
            all_phrases[phrase] += 1

# Print all phrases from most popular to least
total_phrases = sum(all_phrases.values())

print(f"\nTotal three-word phrases found: {total_phrases}")
print(f"\n{'='*80}")
print("ALL THREE-WORD PHRASES (Most Popular to Least)")
print(f"{'='*80}\n")

for phrase, count in all_phrases.most_common():
    print(f"{phrase:<70} {count:>6} times")

print(f"\n{'='*80}")
print("Analysis complete!")
print(f"{'='*80}")
