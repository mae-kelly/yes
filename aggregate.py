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
        'message', 'messages', 'messaging', 'messaged', 'messenger', 'messengers',
        'msg', 'msgs', 'mssg', 'mssgs', 'mesg', 'mesgs',
        'dm', 'dms', 'direct_message', 'direct_messages', 'directmessage', 'directmessages',
        'pm', 'pms', 'private_message', 'private_messages', 'privatemessage', 'privatemessages',
        'inbox', 'outbox', 'sent', 'received', 'unread'
    ],
    'comments': [
        'comment', 'comments', 'commented', 'commenting', 'commenter', 'commenters',
        'cmt', 'cmts', 'cmnt', 'cmnts',
        'reply', 'replies', 'replied', 'replying', 'replyto',
        'feedback', 'feedbacks',
        'response', 'responses', 'respond', 'responded',
        'remark', 'remarks', 'annotation', 'annotations'
    ],
    'text': [
        'text', 'texts', 'texting', 'texted', 'textual', 'txt', 'txts',
        'content', 'contents', 'body', 'bodies',
        'description', 'descriptions', 'desc', 'descr',
        'note', 'notes', 'notation', 'notations',
        'caption', 'captions', 'subtitle', 'subtitles',
        'transcript', 'transcripts', 'transcription'
    ],
    'videos': [
        'video', 'videos', 'vid', 'vids', 'vdo', 'vdos',
        'clip', 'clips', 'clipping',
        'stream', 'streams', 'streaming', 'streamed', 'streamer',
        'recording', 'recordings', 'recorded', 'record',
        'footage', 'film', 'films', 'movie', 'movies',
        'watch', 'watching', 'watched', 'view', 'views', 'viewed', 'viewing',
        'play', 'plays', 'played', 'playing', 'player',
        'youtube', 'vimeo', 'video_url', 'videourl'
    ],
    'electronic_communications': [
        'email', 'emails', 'e_mail', 'e_mails', 'mail', 'mails', 'mailing',
        'electronic', 'digital', 'online',
        'communication', 'communications', 'communicate', 'communicated',
        'correspondence', 'correspond',
        'notification', 'notifications', 'notify', 'notified', 'notif', 'notifs',
        'alert', 'alerts', 'alerted', 'alerting',
        'ping', 'pings', 'pinged',
        'newsletter', 'newsletters', 'bulletin', 'bulletins',
        'broadcast', 'broadcasts', 'broadcasting'
    ],
    'sms': [
        'sms', 'text_message', 'text_messages', 'textmessage', 'textmessages',
        'mms', 'mobile_message', 'mobile_messages', 'mobilemessage', 'mobilemessages',
        'phone_message', 'phone_messages', 'phonemessage', 'phonemessages',
        'cellular', 'mobile', 'cell',
        'short_message', 'shortmessage'
    ],
    'social_media': [
        'social', 'social_media', 'socialmedia', 'social_network', 'socialnetwork',
        'post', 'posts', 'posting', 'posted', 'poster',
        'tweet', 'tweets', 'tweeted', 'tweeting', 'twitter', 'retweet', 'retweets',
        'facebook', 'fb', 'instagram', 'insta', 'ig',
        'linkedin', 'tiktok', 'snapchat', 'snap', 'pinterest', 'reddit',
        'share', 'shares', 'shared', 'sharing', 'reshare',
        'like', 'likes', 'liked', 'liking', 'favorite', 'fav',
        'follow', 'follows', 'follower', 'followers', 'following', 'followed', 'unfollow',
        'friend', 'friends', 'friendship', 'unfriend',
        'status', 'update', 'updates', 'updated', 'updating',
        'feed', 'feeds', 'timeline', 'wall',
        'mention', 'mentions', 'mentioned', 'tag', 'tags', 'tagged', 'tagging',
        'hashtag', 'hashtags', 'trend', 'trending', 'viral'
    ],
    'chat': [
        'chat', 'chats', 'chatting', 'chatted', 'chatter', 'chatroom', 'chatrooms',
        'conversation', 'conversations', 'conversational', 'convo', 'convos',
        'dialogue', 'dialog', 'discussion', 'discussions',
        'thread', 'threads', 'threaded', 'threading',
        'channel', 'channels', 'room', 'rooms',
        'slack', 'discord', 'whatsapp', 'telegram', 'wechat', 'teams', 'skype',
        'instant_message', 'instant_messages', 'instantmessage', 'im', 'ims',
        'group_chat', 'groupchat', 'group_message', 'groupmessage'
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
    Also returns the matching patterns found.
    """
    normalized_col = normalize_column_name(col_name)
    matches = {}
    match_details = {}
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        matched_keywords = []
        
        for keyword in keywords:
            found = False
            
            # Method 1: Check if keyword appears as a complete segment (word boundary match)
            pattern = r'(^|_)' + re.escape(keyword) + r'($|_)'
            if re.search(pattern, normalized_col):
                matched_keywords.append(keyword)
                found = True
            
            # Method 2: Check if keyword appears anywhere in the string (substring match)
            elif keyword in normalized_col:
                matched_keywords.append(keyword)
                found = True
            
            # Method 3: Check in original column name (case-insensitive)
            elif keyword in col_name.lower():
                matched_keywords.append(keyword)
                found = True
        
        if matched_keywords:
            matches[category] = sorted(set(matched_keywords))
            match_details[category] = {
                'keywords': sorted(set(matched_keywords)),
                'original_column': col_name,
                'normalized_column': normalized_col
            }
    
    return matches, match_details


def analyze_dataset_columns(input_dataset_name, output_dataset_name):
    """
    Main function to analyze columns in the input dataset and create
    a summary table in the output dataset.
    
    This function scans both column names AND cell content for keywords.
    Shows ALL matched cell values sorted by frequency.
    
    Parameters:
    - input_dataset_name: Name of the input dataset to analyze
    - output_dataset_name: Name of the output dataset to create
    """
    
    # Read the input dataset
    print(f"Reading dataset: {input_dataset_name}")
    input_dataset = dataiku.Dataset(input_dataset_name)
    df = input_dataset.get_dataframe()
    
    print(f"Found {len(df.columns)} columns to analyze")
    print(f"Dataset has {len(df)} rows")
    print("Will show ALL matched cell values (not limited)")
    
    # Analyze each column
    results = []
    
    for col_name in df.columns:
        print(f"Analyzing column: {col_name}")
        
        # Check column name for matches
        column_name_matches, _ = find_keywords_in_column(col_name)
        
        # Check cell content for matches
        cell_content_matches = {}
        matched_cell_values = {}
        cell_value_counts = {}
        
        # Get all non-null values from this column
        non_null_values = df[col_name].dropna()
        
        # Only analyze string columns or columns that can be converted to string
        if len(non_null_values) > 0:
            # Convert to string and get unique values
            try:
                unique_values = non_null_values.astype(str).unique()
                
                # For each unique value, check if it contains keywords
                for cell_value in unique_values:
                    if cell_value and str(cell_value).strip():  # Skip empty strings
                        value_matches, _ = find_keywords_in_column(str(cell_value))
                        
                        if value_matches:
                            # Count how many times this value appears
                            value_count = (df[col_name].astype(str) == cell_value).sum()
                            
                            for category, keywords in value_matches.items():
                                if category not in cell_content_matches:
                                    cell_content_matches[category] = []
                                    matched_cell_values[category] = []
                                    cell_value_counts[category] = []
                                
                                # Store the matched keywords
                                cell_content_matches[category].extend(keywords)
                                
                                # Store the actual cell value and its count
                                matched_cell_values[category].append(cell_value)
                                cell_value_counts[category].append(value_count)
            except Exception as e:
                print(f"  Could not analyze content for column {col_name}: {e}")
        
        # Combine column name matches and cell content matches
        all_matches = {}
        for category in KEYWORD_CATEGORIES.keys():
            if category in column_name_matches or category in cell_content_matches:
                all_matches[category] = {
                    'column_name_keywords': column_name_matches.get(category, []),
                    'cell_content_keywords': list(set(cell_content_matches.get(category, []))),
                    'matched_cell_values': matched_cell_values.get(category, []),
                    'cell_value_counts': cell_value_counts.get(category, [])
                }
        
        if all_matches:  # Only include columns with matches
            # Calculate total occurrences across all cells
            total_cell_occurrences = sum(
                sum(all_matches[cat]['cell_value_counts']) 
                for cat in all_matches 
                if all_matches[cat]['cell_value_counts']
            )
            
            # Create a row for this column
            row = {
                'column_name': col_name,
                'normalized_column_name': normalize_column_name(col_name),
                'total_categories_matched': len(all_matches),
                'total_keywords_matched_in_column_name': sum(len(column_name_matches.get(cat, [])) for cat in column_name_matches),
                'total_keywords_matched_in_cells': sum(len(all_matches[cat]['cell_content_keywords']) for cat in all_matches),
                'total_cell_value_occurrences': total_cell_occurrences,
                'unique_matched_cell_values': sum(len(all_matches[cat]['matched_cell_values']) for cat in all_matches)
            }
            
            # Add category-specific information
            for category in KEYWORD_CATEGORIES.keys():
                if category in all_matches:
                    cat_data = all_matches[category]
                    
                    row[f'{category}_matched'] = 'Yes'
                    
                    # Column name keywords
                    row[f'{category}_column_keywords'] = ', '.join(cat_data['column_name_keywords']) if cat_data['column_name_keywords'] else ''
                    
                    # Cell content keywords
                    row[f'{category}_cell_keywords'] = ', '.join(cat_data['cell_content_keywords']) if cat_data['cell_content_keywords'] else ''
                    
                    # Matched cell values sorted by frequency (most common first)
                    if cat_data['matched_cell_values']:
                        # Sort by count (descending)
                        sorted_pairs = sorted(
                            zip(cat_data['matched_cell_values'], cat_data['cell_value_counts']),
                            key=lambda x: x[1],
                            reverse=True
                        )
                        
                        # Show ALL values sorted by frequency (most common first)
                        num_values = len(sorted_pairs)
                        
                        # Format as "value (count)"
                        cell_values_formatted = []
                        for val, count in sorted_pairs:  # Use all pairs, not limited
                            # Truncate very long cell values to 100 characters
                            truncated_val = val[:100] + '...' if len(val) > 100 else val
                            cell_values_formatted.append(f"{truncated_val} ({count})")
                        
                        row[f'{category}_matched_cell_values'] = ' | '.join(cell_values_formatted)
                        row[f'{category}_total_cell_occurrences'] = sum(cat_data['cell_value_counts'])
                        row[f'{category}_unique_values_count'] = num_values
                    else:
                        row[f'{category}_matched_cell_values'] = ''
                        row[f'{category}_total_cell_occurrences'] = 0
                        row[f'{category}_unique_values_count'] = 0
                        
                else:
                    row[f'{category}_matched'] = 'No'
                    row[f'{category}_column_keywords'] = ''
                    row[f'{category}_cell_keywords'] = ''
                    row[f'{category}_matched_cell_values'] = ''
                    row[f'{category}_total_cell_occurrences'] = 0
                    row[f'{category}_unique_values_count'] = 0
            
            # Add all matched keywords combined
            all_column_keywords = []
            all_cell_keywords = []
            for cat in all_matches:
                all_column_keywords.extend(all_matches[cat]['column_name_keywords'])
                all_cell_keywords.extend(all_matches[cat]['cell_content_keywords'])
            
            row['all_column_keywords'] = ', '.join(sorted(set(all_column_keywords)))
            row['all_cell_keywords'] = ', '.join(sorted(set(all_cell_keywords)))
            
            results.append(row)
    
    # Create results dataframe
    if results:
        results_df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        column_order = [
            'column_name', 
            'normalized_column_name',
            'total_categories_matched', 
            'total_cell_value_occurrences',  # Sort by this - most important
            'unique_matched_cell_values',
            'total_keywords_matched_in_column_name',
            'total_keywords_matched_in_cells',
            'all_column_keywords',
            'all_cell_keywords'
        ]
        
        for category in KEYWORD_CATEGORIES.keys():
            column_order.extend([
                f'{category}_matched', 
                f'{category}_total_cell_occurrences',
                f'{category}_unique_values_count',
                f'{category}_matched_cell_values',
                f'{category}_column_keywords', 
                f'{category}_cell_keywords'
            ])
        
        results_df = results_df[column_order]
        
        # Sort by total cell occurrences (most to least), then by column name
        results_df = results_df.sort_values(
            ['total_cell_value_occurrences', 'unique_matched_cell_values', 'column_name'],
            ascending=[False, False, True]
        )
        
    else:
        # Create empty dataframe with correct schema if no matches found
        print("No columns matched any keywords")
        column_order = [
            'column_name', 
            'normalized_column_name',
            'total_categories_matched', 
            'total_cell_value_occurrences',
            'unique_matched_cell_values',
            'total_keywords_matched_in_column_name',
            'total_keywords_matched_in_cells',
            'all_column_keywords',
            'all_cell_keywords'
        ]
        
        for category in KEYWORD_CATEGORIES.keys():
            column_order.extend([
                f'{category}_matched', 
                f'{category}_total_cell_occurrences',
                f'{category}_unique_values_count',
                f'{category}_matched_cell_values',
                f'{category}_column_keywords', 
                f'{category}_cell_keywords'
            ])
        
        results_df = pd.DataFrame(columns=column_order)
    
    # Write to output dataset
    print(f"Writing results to dataset: {output_dataset_name}")
    output_dataset = dataiku.Dataset(output_dataset_name)
    output_dataset.write_with_schema(results_df)
    
    print(f"Analysis complete! Found {len(results_df)} columns with matching keywords")
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total columns in dataset: {len(df.columns)}")
    print(f"Columns with matches: {len(results_df)}")
    
    if len(results_df) > 0:
        total_cell_matches = results_df['total_cell_value_occurrences'].sum()
        print(f"Total cell value occurrences containing keywords: {total_cell_matches}")
        
        print("\nTop 10 columns by cell content occurrences (most to least):")
        top_cols = results_df[['column_name', 'total_cell_value_occurrences', 'unique_matched_cell_values', 'all_cell_keywords']].head(10)
        print(top_cols.to_string(index=False))
        
        print("\nCategory breakdown:")
        for category in KEYWORD_CATEGORIES.keys():
            col_count = (results_df[f'{category}_matched'] == 'Yes').sum()
            if col_count > 0:
                total_occurrences = results_df[f'{category}_total_cell_occurrences'].sum()
                print(f"  {category}: {col_count} columns, {total_occurrences} total cell occurrences")
    
    return results_df


# Main execution
if __name__ == "__main__":
    # Configuration - modify these values as needed
    INPUT_DATASET = "your_input_dataset_name"  # Replace with your input dataset name
    OUTPUT_DATASET = "communication_columns_analysis"  # Replace with desired output name
    
    # Run the analysis
    results = analyze_dataset_columns(INPUT_DATASET, OUTPUT_DATASET)
