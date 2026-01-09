# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import re
from collections import Counter

# Read input dataset
input_dataset = dataiku.Dataset("YOUR_INPUT_DATASET_NAME")
df = input_dataset.get_dataframe()

# Define keywords to analyze
keywords = ['email', 'sms', 'text', 'message', 'messages', 'chat', 'comment', 'comments', 'video', 'call', 'calls']

text_column = 'TXT_RSRC_DESC'

def extract_context_phrases(text, keyword):
    """
    Extract phrases with 1 word before and 1 word after the keyword.
    Returns list of tuples: (word_before, keyword, word_after)
    """
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    # Clean and tokenize
    text_lower = text.lower()
    # Replace punctuation with spaces to avoid weird tokens
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
    words = text_clean.split()
    
    phrases = []
    
    for i, word in enumerate(words):
        if word == keyword:
            word_before = words[i-1] if i > 0 else '<START>'
            word_after = words[i+1] if i < len(words) - 1 else '<END>'
            phrases.append((word_before, keyword, word_after))
    
    return phrases

# Analyze each keyword
print("="*80)
print("COMMUNICATION KEYWORD CONTEXT ANALYSIS")
print("="*80)

for keyword in keywords:
    word_before_counts = Counter()
    word_after_counts = Counter()
    full_phrase_counts = Counter()
    
    # Extract all occurrences across all rows
    for text in df[text_column]:
        phrases = extract_context_phrases(text, keyword)
        
        for word_before, kw, word_after in phrases:
            word_before_counts[word_before] += 1
            word_after_counts[word_after] += 1
            full_phrase_counts[f"{word_before} {kw} {word_after}"] += 1
    
    total_occurrences = sum(word_before_counts.values())
    
    if total_occurrences == 0:
        continue
    
    print(f"\n{'='*80}")
    print(f"KEYWORD: '{keyword.upper()}'")
    print(f"Total occurrences: {total_occurrences}")
    print(f"{'='*80}")
    
    # Words BEFORE
    print(f"\nWords appearing BEFORE '{keyword}':")
    print(f"{'-'*80}")
    for word, count in word_before_counts.most_common():
        print(f"  {word:<40} {count:>6} times")
    
    # Words AFTER
    print(f"\nWords appearing AFTER '{keyword}':")
    print(f"{'-'*80}")
    for word, count in word_after_counts.most_common():
        print(f"  {word:<40} {count:>6} times")
    
    # Three-word phrases (most popular to least)
    print(f"\nThree-word phrases containing '{keyword}' (most popular to least):")
    print(f"{'-'*80}")
    for phrase, count in full_phrase_counts.most_common():
        print(f"  {phrase:<60} {count:>6} times")

print(f"\n{'='*80}")
print("Analysis complete!")
print(f"{'='*80}")
