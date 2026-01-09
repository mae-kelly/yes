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

def extract_two_word_phrases(text, keyword):
    """
    Extract two-word phrases: keyword + word_after OR word_before + keyword
    Returns list of two-word phrases
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
            word_before = before_words[-1] if before_words else None
            
            # Get first word after
            after_words = after_text.split()
            word_after = after_words[0] if after_words else None
            
            # Create two-word phrases
            if word_before:
                phrases.append(f"{word_before} {keyword}")
            if word_after:
                phrases.append(f"{keyword} {word_after}")
    else:
        # Single word keyword - tokenize normally
        words = text_clean.split()
        
        for i, word in enumerate(words):
            if word == keyword:
                # word_before + keyword
                if i > 0:
                    phrases.append(f"{words[i-1]} {keyword}")
                
                # keyword + word_after
                if i < len(words) - 1:
                    phrases.append(f"{keyword} {words[i+1]}")
    
    return phrases

# Collect ALL two-word phrases across ALL keywords
all_two_word_phrases = Counter()

print("="*80)
print("ANALYZING COMMUNICATION KEYWORDS (2-WORD PHRASES)...")
print("="*80)

for keyword in keywords:
    for text in df[text_column]:
        phrases = extract_two_word_phrases(text, keyword)
        
        for phrase in phrases:
            all_two_word_phrases[phrase] += 1

# Print all phrases from most popular to least
total_phrases = sum(all_two_word_phrases.values())

print(f"\nTotal two-word phrases found: {total_phrases}")
print(f"\n{'='*80}")
print("ALL TWO-WORD PHRASES (Most Popular to Least)")
print(f"{'='*80}\n")

for phrase, count in all_two_word_phrases.most_common():
    print(f"{phrase:<70} {count:>6} times")

print(f"\n{'='*80}")
print("Analysis complete!")
print(f"{'='*80}")
