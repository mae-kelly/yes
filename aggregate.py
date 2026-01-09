# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import re

# Read input dataset
input_dataset = dataiku.Dataset("YOUR_INPUT_DATASET_NAME")
df = input_dataset.get_dataframe()

def detect_email_communication(text):
    """
    Only returns True if text clearly describes email as a communication/notification feature.
    Uses WHITELIST approach - must match specific phrases.
    """
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    # HARD STOP words - if these appear ANYWHERE, immediately return False
    hard_stops = [
        'enter your email', 'enter an email', 'enter email',
        'provide your email', 'provide an email', 'provide email',
        'input your email', 'input email',
        'email address required', 'email required', 'valid email address',
        'email login', 'login with email', 'sign up with email',
        'email verification', 'verify your email', 'verify email',
        'email and password', 'email credential'
    ]
    
    if any(stop in text_lower for stop in hard_stops):
        return False
    
    # WHITELIST - Only these specific phrases indicate email communication
    whitelist = [
        'send email notification',
        'send email alert',
        'sends email notification',
        'sends email alert',
        'email notifications to',
        'email alerts to',
        'notify via email',
        'notifies via email',
        'alert via email',
        'alerts via email',
        'communicate via email',
        'communicates via email',
        'notification via email',
        'notifications via email',
        'send automated email',
        'sends automated email',
        'email delivery system',
        'email notification system',
        'smtp server',
        'smtp gateway',
        'outbound email',
        'inbound email'
    ]
    
    return any(phrase in text_lower for phrase in whitelist)

def detect_sms_communication(text):
    """
    Only returns True if text clearly describes SMS as a communication/notification feature.
    Excludes ALL 2FA/verification use cases.
    """
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    # HARD STOP words
    hard_stops = [
        'sms code', 'sms verification', 'verification code',
        'sms authentication', '2fa', 'two factor', 'two-factor',
        'otp', 'one time password', 'one-time password',
        'verification via sms', 'authenticate via sms',
        'sms to verify', 'confirm via sms'
    ]
    
    if any(stop in text_lower for stop in hard_stops):
        return False
    
    # WHITELIST
    whitelist = [
        'send sms notification',
        'send sms alert',
        'sends sms notification',
        'sends sms alert',
        'sms notifications to',
        'sms alerts to',
        'notify via sms',
        'notifies via sms',
        'alert via sms',
        'alerts via sms',
        'communicate via sms',
        'communicates via sms',
        'notification via sms',
        'notifications via sms',
        'text message notification',
        'text message alert',
        'send text message notification',
        'sends text message notification',
        'sms delivery system',
        'sms notification system',
        'sms gateway',
        'twilio integration',
        'outbound sms',
        'inbound sms'
    ]
    
    return any(phrase in text_lower for phrase in whitelist)

def detect_chat_communication(text):
    """
    Only returns True if text describes user-to-user chat feature.
    Excludes ALL AI/bot/assistant chat.
    """
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    # HARD STOP words
    hard_stops = [
        'chatgpt', 'chat gpt', 'gpt',
        'chatbot', 'chat bot',
        'ai chat', 'ai assistant', 'ai-powered chat',
        'virtual assistant', 'virtual agent',
        'conversational ai', 'conversational agent',
        'automated chat', 'bot chat'
    ]
    
    if any(stop in text_lower for stop in hard_stops):
        return False
    
    # WHITELIST
    whitelist = [
        'live chat feature',
        'live chat functionality',
        'in-app chat',
        'in app chat',
        'real-time chat',
        'real time chat',
        'instant messaging feature',
        'instant messaging functionality',
        'direct messaging feature',
        'direct messaging functionality',
        'user to user chat',
        'user-to-user chat',
        'peer to peer chat',
        'peer-to-peer chat',
        'two-way chat',
        'two way chat',
        'chat between users',
        'users can chat',
        'enables chat between',
        'chat capability for users',
        'chat interface for users',
        'messaging between users',
        'user messaging feature',
        'user chat feature'
    ]
    
    return any(phrase in text_lower for phrase in whitelist)

def detect_comment_communication(text):
    """
    Only returns True if text describes user comment/feedback feature.
    Excludes ALL code-related comments.
    """
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    # HARD STOP words
    hard_stops = [
        'comment out',
        'code comment',
        'inline comment',
        'source code comment',
        'commented code',
        'javascript comment',
        'html comment',
        '//', '/*', '*/'
    ]
    
    if any(stop in text_lower for stop in hard_stops):
        return False
    
    # WHITELIST
    whitelist = [
        'post comment',
        'post comments',
        'leave comment',
        'leave comments',
        'submit comment',
        'submit comments',
        'add comment',
        'add comments',
        'user comment',
        'user comments',
        'users can comment',
        'allow users to comment',
        'allows users to comment',
        'comment feature',
        'comment functionality',
        'commenting feature',
        'commenting functionality',
        'comment section',
        'comments section',
        'comment thread',
        'comment system',
        'commenting system'
    ]
    
    return any(phrase in text_lower for phrase in whitelist)

# Apply detection
text_column = 'TXT_RSRC_DESC'

print("Starting WHITELIST-BASED detection...")
print("Only matching exact phrases that indicate e-communication\n")

output_df = df.copy()
output_df['has_email'] = df[text_column].apply(detect_email_communication)
output_df['has_sms'] = df[text_column].apply(detect_sms_communication)
output_df['has_chat'] = df[text_column].apply(detect_chat_communication)
output_df['has_comments'] = df[text_column].apply(detect_comment_communication)

output_df['has_any_ecomm'] = (
    output_df['has_email'] | 
    output_df['has_sms'] | 
    output_df['has_chat'] | 
    output_df['has_comments']
)

def get_comm_types(row):
    types = []
    if row['has_email']: types.append('email')
    if row['has_sms']: types.append('sms')
    if row['has_chat']: types.append('chat')
    if row['has_comments']: types.append('comments')
    return ', '.join(types) if types else 'none'

output_df['detected_comm_types'] = output_df.apply(get_comm_types, axis=1)

# Write output
output_dataset = dataiku.Dataset("YOUR_OUTPUT_DATASET_NAME")
output_dataset.write_with_schema(output_df)

# Print results
total = len(output_df)
detected = output_df['has_any_ecomm'].sum()

print(f"{'='*70}")
print(f"WHITELIST DETECTION RESULTS")
print(f"{'='*70}")
print(f"Total rows: {total:,}")
print(f"Detected e-communication: {detected:,} ({detected/total*100:.1f}%)")
print(f"\nBreakdown:")
print(f"  Email:    {output_df['has_email'].sum():,}")
print(f"  SMS:      {output_df['has_sms'].sum():,}")
print(f"  Chat:     {output_df['has_chat'].sum():,}")
print(f"  Comments: {output_df['has_comments'].sum():,}")
print(f"{'='*70}")

# Show samples if any detected
if detected > 0:
    print(f"\nSample detections:")
    samples = output_df[output_df['has_any_ecomm']].head(5)
    for idx, row in samples.iterrows():
        print(f"\n[{row['detected_comm_types'].upper()}]")
        print(f"{row[text_column][:300]}...")
