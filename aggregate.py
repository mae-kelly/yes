"""
Dataiku E-Communication Capabilities Analyzer
Finds the most common cell values related to e-communication, messaging, 
video, and email capabilities across all columns in a dataset.
"""

import dataiku
import pandas as pd
import re
from collections import defaultdict

# Define comprehensive keyword lists for e-communication capabilities
KEYWORD_CATEGORIES = {
    'messages': [
        'message', 'messages', 'messaging', 'messaged', 'messenger', 'messengers',
        'msg', 'msgs', 'mssg', 'mssgs', 'mesg', 'mesgs',
        'dm', 'dms', 'direct_message', 'direct_messages', 'directmessage', 'directmessages',
        'pm', 'pms', 'private_message', 'private_messages', 'privatemessage', 'privatemessages',
        'inbox', 'outbox', 'sent', 'received', 'unread',
        'chat', 'chats', 'chatting', 'chatted', 'chatter', 'chatroom', 'chatrooms',
        'conversation', 'conversations', 'conversational', 'convo', 'convos',
        'thread', 'threads', 'threaded', 'threading',
        'instant_message', 'instant_messages', 'instantmessage', 'im', 'ims',
        'sms', 'text_message', 'text_messages', 'textmessage', 'textmessages',
        'mms', 'mobile_message', 'mobile_messages', 'mobilemessage', 'mobilemessages',
        'slack', 'discord', 'whatsapp', 'telegram', 'wechat', 'teams', 'skype'
    ],
    'email': [
        'email', 'emails', 'e_mail', 'e_mails', 'mail', 'mails', 'mailing',
        'electronic_mail', 'electronicmail',
        'notification', 'notifications', 'notify', 'notified', 'notif', 'notifs',
        'alert', 'alerts', 'alerted', 'alerting',
        'newsletter', 'newsletters', 'bulletin', 'bulletins',
        'correspondence', 'correspond'
    ],
    'video': [
        'video', 'videos', 'vid', 'vids', 'vdo', 'vdos',
        'videocall', 'videocalls', 'video_call', 'video_calls',
        'videoconference', 'videoconferencing', 'video_conference',
        'stream', 'streams', 'streaming', 'streamed', 'streamer',
        'recording', 'recordings', 'recorded', 'record',
        'webcam', 'camera', 'zoom', 'meet', 'facetime', 
        'skype', 'teams', 'webex', 'gotomeeting'
    ],
    'communication': [
        'communication', 'communications', 'communicate', 'communicated',
        'contact', 'contacts', 'contactable',
        'call', 'calls', 'calling', 'called', 'caller',
        'voice', 'voicemail', 'audio',
        'share', 'shares', 'shared', 'sharing',
        'post', 'posts', 'posting', 'posted',
        'comment', 'comments', 'reply', 'replies',
        'social', 'social_media', 'socialmedia'
    ]
}


def normalize_text(text):
    """Normalize text for matching - lowercase and replace separators"""
    normalized = str(text).lower()
    normalized = re.sub(r'[.\-\s/\\]+', '_', normalized)
    normalized = re.sub(r'[^\w_]', '', normalized)
    return normalized


def contains_ecommunication_keywords(text):
    """
    Check if text contains any e-communication keywords.
    Returns matched categories and keywords.
    """
    if not text or pd.isna(text):
        return False, [], []
    
    normalized = normalize_text(text)
    original_lower = str(text).lower()
    
    matched_categories = []
    matched_keywords = []
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        for keyword in keywords:
            # Check both normalized and original versions
            if keyword in normalized or keyword in original_lower:
                if category not in matched_categories:
                    matched_categories.append(category)
                matched_keywords.append(keyword)
    
    has_match = len(matched_categories) > 0
    return has_match, matched_categories, matched_keywords


def analyze_ecommunication_capabilities(input_dataset_name, output_dataset_name):
    """
    Analyze dataset for e-communication capabilities.
    Returns a table of the most common cell values with e-communication keywords.
    """
    
    # Read the input dataset
    print(f"Reading dataset: {input_dataset_name}")
    input_dataset = dataiku.Dataset(input_dataset_name)
    df = input_dataset.get_dataframe()
    
    print(f"Analyzing {len(df.columns)} columns and {len(df)} rows")
    
    # Dictionary to store: {cell_value: {'count': X, 'columns': [col1, col2], 'categories': [...], 'keywords': [...]}}
    cell_value_data = defaultdict(lambda: {
        'count': 0, 
        'columns': set(), 
        'categories': set(),
        'keywords': set()
    })
    
    # Analyze each column
    for col_name in df.columns:
        print(f"Analyzing column: {col_name}")
        
        # Get value counts for this column
        value_counts = df[col_name].value_counts()
        
        # Check each unique value
        for cell_value, count in value_counts.items():
            has_match, categories, keywords = contains_ecommunication_keywords(cell_value)
            
            if has_match:
                # Convert to string for consistent storage
                cell_str = str(cell_value)
                
                # Update the data for this cell value
                cell_value_data[cell_str]['count'] += count
                cell_value_data[cell_str]['columns'].add(col_name)
                cell_value_data[cell_str]['categories'].update(categories)
                cell_value_data[cell_str]['keywords'].update(keywords)
    
    # Convert to list of rows for dataframe
    results = []
    for cell_value, data in cell_value_data.items():
        row = {
            'cell_value': cell_value,
            'total_occurrences': data['count'],
            'num_columns_found_in': len(data['columns']),
            'columns_found_in': ' | '.join(sorted(data['columns'])),
            'matched_categories': ', '.join(sorted(data['categories'])),
            'matched_keywords': ', '.join(sorted(data['keywords']))
        }
        results.append(row)
    
    # Create dataframe
    if results:
        results_df = pd.DataFrame(results)
        
        # Sort by total occurrences (most to least)
        results_df = results_df.sort_values('total_occurrences', ascending=False)
        
        # Reset index
        results_df = results_df.reset_index(drop=True)
    else:
        print("No e-communication related cell values found")
        results_df = pd.DataFrame(columns=[
            'cell_value',
            'total_occurrences',
            'num_columns_found_in',
            'columns_found_in',
            'matched_categories',
            'matched_keywords'
        ])
    
    # Write to output dataset
    print(f"Writing results to dataset: {output_dataset_name}")
    output_dataset = dataiku.Dataset(output_dataset_name)
    output_dataset.write_with_schema(results_df)
    
    # Print summary
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    print(f"Total unique e-communication cell values found: {len(results_df)}")
    if len(results_df) > 0:
        print(f"Total occurrences across all columns: {results_df['total_occurrences'].sum()}")
        print(f"Columns analyzed: {len(df.columns)}")
        
        print("\nTop 20 most common e-communication cell values:")
        top_20 = results_df[['cell_value', 'total_occurrences', 'num_columns_found_in', 'matched_categories']].head(20)
        print(top_20.to_string(index=False))
        
        print("\nCategory breakdown:")
        category_counts = defaultdict(int)
        for categories in results_df['matched_categories']:
            for cat in categories.split(', '):
                category_counts[cat] += 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} unique cell values")
    
    return results_df


# Main execution
if __name__ == "__main__":
    # Configuration
    INPUT_DATASET = "your_input_dataset_name"  # Replace with your input dataset name
    OUTPUT_DATASET = "ecommunication_analysis"  # Replace with desired output name
    
    # Run the analysis
    results = analyze_ecommunication_capabilities(INPUT_DATASET, OUTPUT_DATASET)
    
    print("\nAnalysis complete!")
    print(f"Results saved to: {OUTPUT_DATASET}")
