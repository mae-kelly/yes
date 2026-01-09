# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import re
from collections import Counter

# Read input dataset
input_dataset = dataiku.Dataset("YOUR_INPUT_DATASET_NAME")
df = input_dataset.get_dataframe()

# Define keywords to search for
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

def extract_two_word_phrases_from_text(text, keyword):
    """
    Extract two-word phrases: keyword + word_after OR word_before + keyword
    Returns list of two-word phrases found in this text
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

def extract_sentences(text):
    """
    Split text into sentences.
    """
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    # Simple sentence splitting on period, exclamation, question mark
    sentences = re.split(r'[.!?]+', text)
    # Clean up whitespace
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def find_sentence_with_phrase(text, phrase):
    """
    Find the sentence(s) containing the given phrase.
    Returns list of sentences.
    """
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    sentences = extract_sentences(text)
    matching_sentences = []
    
    phrase_lower = phrase.lower()
    
    for sentence in sentences:
        if phrase_lower in sentence.lower():
            matching_sentences.append(sentence)
    
    return matching_sentences

def process_row(text):
    """
    Process a single row to find all 2-word keyword phrases and their sentences.
    Returns: (matched_keywords_str, matched_sentences_str)
    """
    if pd.isna(text) or not isinstance(text, str):
        return ('', '')
    
    all_matched_phrases = []
    all_matched_sentences = []
    
    # Check each keyword
    for keyword in keywords:
        # Get all 2-word phrases for this keyword in this text
        two_word_phrases = extract_two_word_phrases_from_text(text, keyword)
        
        # For each 2-word phrase found, get the sentence(s) containing it
        for phrase in two_word_phrases:
            if phrase not in all_matched_phrases:
                all_matched_phrases.append(phrase)
                
                # Get sentences containing this phrase
                sentences = find_sentence_with_phrase(text, phrase)
                for sentence in sentences:
                    if sentence not in all_matched_sentences:
                        all_matched_sentences.append(sentence)
    
    # Join multiple matches with separator
    keywords_str = ' | '.join(all_matched_phrases) if all_matched_phrases else ''
    sentences_str = ' | '.join(all_matched_sentences) if all_matched_sentences else ''
    
    return (keywords_str, sentences_str)

print("Processing text for 2-word keyword matches...")

# Apply the function to create new columns
results = df[text_column].apply(process_row)

# Unpack the results into two columns
output_df = df.copy()
output_df['matched_2word_keywords'] = results.apply(lambda x: x[0])
output_df['matched_sentences'] = results.apply(lambda x: x[1])

# Write output dataset
output_dataset = dataiku.Dataset("YOUR_OUTPUT_DATASET_NAME")
output_dataset.write_with_schema(output_df)

# Print summary
total_rows = len(output_df)
matched_rows = len(output_df[output_df['matched_2word_keywords'] != ''])

print(f"\n{'='*70}")
print(f"PROCESSING COMPLETE")
print(f"{'='*70}")
print(f"Total rows processed: {total_rows:,}")
print(f"Rows with keyword matches: {matched_rows:,}")
print(f"Match rate: {matched_rows/total_rows*100:.1f}%")
print(f"{'='*70}")

# Show sample matches
if matched_rows > 0:
    print(f"\nSample matches (first 5):\n")
    samples = output_df[output_df['matched_2word_keywords'] != ''].head(5)
    for idx, row in samples.iterrows():
        print(f"Row {idx}:")
        print(f"  Keywords: {row['matched_2word_keywords']}")
        print(f"  Sentences: {row['matched_sentences'][:300]}...")
        print()
