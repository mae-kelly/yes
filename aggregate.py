"""
Dataiku Column Keyword Analyzer
Analyzes columns in a Dataiku dataset and identifies those containing
keywords related to messages, comments, text, videos, electronic communications,
SMS, social media, and chat.
"""

import dataiku
import pandas as pd
import re

# Define comprehensive keyword lists for each category
KEYWORD_CATEGORIES = {
    'messages': [
        'message', 'messages', 'messaging', 'messaged', 'messenger',
        'msg', 'msgs', 'dm', 'dms', 'direct_message', 'direct_messages',
        'pm', 'pms', 'private_message', 'private_messages'
    ],
    'comments': [
        'comment', 'comments', 'commented', 'commenting', 'commenter',
        'reply', 'replies', 'replied', 'replying',
        'feedback', 'response', 'responses'
    ],
    'text': [
        'text', 'texts', 'texting', 'texted', 'textual',
        'content', 'body', 'description', 'note', 'notes'
    ],
    'videos': [
        'video', 'videos', 'vid', 'vids', 'clip', 'clips',
        'stream', 'streams', 'streaming', 'streamed',
        'recording', 'recordings', 'footage'
    ],
    'electronic_communications': [
        'email', 'emails', 'e_mail', 'e_mails', 'mail', 'mails',
        'electronic', 'digital', 'online',
        'communication', 'communications', 'communicate',
        'correspondence', 'notification', 'notifications',
        'alert', 'alerts', 'ping', 'pings'
    ],
    'sms': [
        'sms', 'text_message', 'text_messages',
        'mms', 'mobile_message', 'mobile_messages',
        'phone_message', 'cellular', 'mobile'
    ],
    'social_media': [
        'social', 'social_media', 'socialmedia',
        'post', 'posts', 'posting', 'posted',
        'tweet', 'tweets', 'tweeted', 'twitter',
        'facebook', 'instagram', 'linkedin', 'tiktok', 'snapchat',
        'share', 'shares', 'shared', 'sharing',
        'like', 'likes', 'liked', 'liking',
        'follow', 'follows', 'follower', 'followers', 'following',
        'friend', 'friends', 'friendship',
        'status', 'update', 'updates'
    ],
    'chat': [
        'chat', 'chats', 'chatting', 'chatted', 'chatter',
        'conversation', 'conversations', 'convo', 'convos',
        'dialogue', 'discussion', 'discussions',
        'thread', 'threads', 'threaded',
        'channel', 'channels', 'room', 'rooms',
        'slack', 'discord', 'whatsapp', 'telegram', 'wechat'
    ]
}


def normalize_column_name(col_name):
    """
    Normalize column name for matching:
    - Convert to lowercase
    - Replace common separators with underscores
    - Remove special characters
    """
    normalized = col_name.lower()
    normalized = re.sub(r'[.\-\s/\\]+', '_', normalized)
    normalized = re.sub(r'[^\w_]', '', normalized)
    return normalized


def find_keywords_in_column(col_name):
    """
    Check if column name contains any keywords from our categories.
    Returns a dict with categories as keys and lists of matched keywords as values.
    """
    normalized_col = normalize_column_name(col_name)
    matches = {}
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        matched_keywords = []
        
        for keyword in keywords:
            # Create pattern that matches whole words or parts separated by underscores
            pattern = r'(^|_)' + re.escape(keyword) + r'($|_)'
            
            # Also check for partial matches (keyword appears anywhere in the column name)
            if re.search(pattern, normalized_col) or keyword in normalized_col:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            matches[category] = matched_keywords
    
    return matches


def analyze_dataset_columns(input_dataset_name, output_dataset_name):
    """
    Main function to analyze columns in the input dataset and create
    a summary table in the output dataset.
    
    Parameters:
    - input_dataset_name: Name of the input dataset to analyze
    - output_dataset_name: Name of the output dataset to create
    """
    
    # Read the input dataset
    print(f"Reading dataset: {input_dataset_name}")
    input_dataset = dataiku.Dataset(input_dataset_name)
    df = input_dataset.get_dataframe()
    
    print(f"Found {len(df.columns)} columns to analyze")
    
    # Analyze each column
    results = []
    
    for col_name in df.columns:
        matches = find_keywords_in_column(col_name)
        
        if matches:  # Only include columns with matches
            # Create a row for this column
            row = {
                'column_name': col_name,
                'normalized_column_name': normalize_column_name(col_name),
                'total_categories_matched': len(matches),
                'total_keywords_matched': sum(len(kw_list) for kw_list in matches.values())
            }
            
            # Add category-specific information
            for category in KEYWORD_CATEGORIES.keys():
                if category in matches:
                    row[f'{category}_matched'] = 'Yes'
                    row[f'{category}_keywords'] = ', '.join(sorted(set(matches[category])))
                else:
                    row[f'{category}_matched'] = 'No'
                    row[f'{category}_keywords'] = ''
            
            # Add all matched keywords combined
            all_keywords = []
            for kw_list in matches.values():
                all_keywords.extend(kw_list)
            row['all_matched_keywords'] = ', '.join(sorted(set(all_keywords)))
            
            results.append(row)
    
    # Create results dataframe
    if results:
        results_df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        column_order = ['column_name', 'normalized_column_name', 
                       'total_categories_matched', 'total_keywords_matched',
                       'all_matched_keywords']
        
        for category in KEYWORD_CATEGORIES.keys():
            column_order.extend([f'{category}_matched', f'{category}_keywords'])
        
        results_df = results_df[column_order]
        
        # Sort by number of categories matched (descending) and column name
        results_df = results_df.sort_values(
            ['total_categories_matched', 'total_keywords_matched', 'column_name'],
            ascending=[False, False, True]
        )
        
    else:
        # Create empty dataframe with correct schema if no matches found
        print("No columns matched any keywords")
        column_order = ['column_name', 'normalized_column_name', 
                       'total_categories_matched', 'total_keywords_matched',
                       'all_matched_keywords']
        
        for category in KEYWORD_CATEGORIES.keys():
            column_order.extend([f'{category}_matched', f'{category}_keywords'])
        
        results_df = pd.DataFrame(columns=column_order)
    
    # Write to output dataset
    print(f"Writing results to dataset: {output_dataset_name}")
    output_dataset = dataiku.Dataset(output_dataset_name)
    output_dataset.write_with_schema(results_df)
    
    print(f"Analysis complete! Found {len(results_df)} columns with matching keywords")
    
    return results_df


# Main execution
if __name__ == "__main__":
    # Configuration - modify these values as needed
    INPUT_DATASET = "your_input_dataset_name"  # Replace with your input dataset name
    OUTPUT_DATASET = "communication_columns_analysis"  # Replace with desired output name
    
    # Run the analysis
    results = analyze_dataset_columns(INPUT_DATASET, OUTPUT_DATASET)
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total columns analyzed: {len(results) + sum(1 for _ in KEYWORD_CATEGORIES.keys())}")
    print(f"Columns with matches: {len(results)}")
    
    if len(results) > 0:
        print("\nTop 10 columns by keyword matches:")
        print(results[['column_name', 'total_keywords_matched', 'all_matched_keywords']].head(10).to_string(index=False))
        
        print("\nCategory breakdown:")
        for category in KEYWORD_CATEGORIES.keys():
            matched_count = (results[f'{category}_matched'] == 'Yes').sum()
            print(f"  {category}: {matched_count} columns")
