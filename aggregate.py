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
                        cell_matches, _ = find_keywords_in_column(str(cell_value))
                        
                        if cell_matches:
                            # Count how many times this value appears
                            value_count = (df[col_name].astype(str) == cell_value).sum()
                            
                            # Get all matched keywords across all categories for this cell
                            all_cell_keywords = []
                            matched_categories = []
                            for category, keywords in cell_matches.items():
                                matched_categories.append(category)
                                all_cell_keywords.extend(keywords)
                            
                            # Create a row for this specific cell value
                            row = {
                                'column_name': col_name,
                                'normalized_column_name': normalize_column_name(col_name),
                                'matched_cell_value': cell_value,
                                'cell_value_occurrences': value_count,
                                'matched_categories': ', '.join(matched_categories),
                                'total_categories_matched': len(cell_matches),
                                'all_matched_keywords': ', '.join(sorted(set(all_cell_keywords))),
                                'column_name_has_keywords': 'Yes' if column_name_matches else 'No'
                            }
                            
                            # Add column name keywords if any
                            if column_name_matches:
                                all_column_keywords = []
                                for keywords in column_name_matches.values():
                                    all_column_keywords.extend(keywords)
                                row['column_name_keywords'] = ', '.join(sorted(set(all_column_keywords)))
                            else:
                                row['column_name_keywords'] = ''
                            
                            # Add category-specific information
                            for category in KEYWORD_CATEGORIES.keys():
                                if category in cell_matches:
                                    row[f'{category}_matched'] = 'Yes'
                                    row[f'{category}_keywords'] = ', '.join(sorted(set(cell_matches[category])))
                                else:
                                    row[f'{category}_matched'] = 'No'
                                    row[f'{category}_keywords'] = ''
                            
                            results.append(row)
            except Exception as e:
                print(f"  Could not analyze content for column {col_name}: {e}")
    
    # Create results dataframe
    if results:
        results_df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        column_order = [
            'column_name',
            'matched_cell_value',
            'cell_value_occurrences',
            'matched_categories',
            'total_categories_matched',
            'all_matched_keywords',
            'column_name_has_keywords',
            'column_name_keywords',
            'normalized_column_name'
        ]
        
        for category in KEYWORD_CATEGORIES.keys():
            column_order.extend([
                f'{category}_matched',
                f'{category}_keywords'
            ])
        
        results_df = results_df[column_order]
        
        # Sort by cell value occurrences (most to least), then by column name, then by cell value
        results_df = results_df.sort_values(
            ['cell_value_occurrences', 'column_name', 'matched_cell_value'],
            ascending=[False, True, True]
        )
        
    else:
        # Create empty dataframe with correct schema if no matches found
        print("No columns matched any keywords")
        column_order = [
            'column_name',
            'matched_cell_value',
            'cell_value_occurrences',
            'matched_categories',
            'total_categories_matched',
            'all_matched_keywords',
            'column_name_has_keywords',
            'column_name_keywords',
            'normalized_column_name'
        ]
        
        for category in KEYWORD_CATEGORIES.keys():
            column_order.extend([
                f'{category}_matched',
                f'{category}_keywords'
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
    print(f"Total matched cell values (rows in output): {len(results_df)}")
    print(f"Unique columns with matches: {results_df['column_name'].nunique()}")
    
    if len(results_df) > 0:
        total_cell_occurrences = results_df['cell_value_occurrences'].sum()
        print(f"Total cell occurrences containing keywords: {total_cell_occurrences}")
        
        print("\nTop 10 matched cell values by occurrence count:")
        top_cells = results_df[['column_name', 'matched_cell_value', 'cell_value_occurrences', 'matched_categories']].head(10)
        print(top_cells.to_string(index=False))
        
        print("\nCategory breakdown:")
        for category in KEYWORD_CATEGORIES.keys():
            row_count = (results_df[f'{category}_matched'] == 'Yes').sum()
            if row_count > 0:
                total_occurrences = results_df[results_df[f'{category}_matched'] == 'Yes']['cell_value_occurrences'].sum()
                print(f"  {category}: {row_count} cell values, {total_occurrences} total occurrences")
    
    return results_df


# Main execution
if __name__ == "__main__":
    # Configuration - modify these values as needed
    INPUT_DATASET = "your_input_dataset_name"  # Replace with your input dataset name
    OUTPUT_DATASET = "communication_columns_analysis"  # Replace with desired output name
    
    # Run the analysis
    results = analyze_dataset_columns(INPUT_DATASET, OUTPUT_DATASET)
