# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import re

# Read input dataset
input_dataset = dataiku.Dataset("YOUR_INPUT_DATASET_NAME")
df = input_dataset.get_dataframe()

# More precise patterns based on the actual text structure
communication_patterns = {
    'email': [
        # Core email communication patterns (within 10 words)
        r'\b(via|through|by|using|with|over)\s+(?:\w+\s+){0,3}email\b',
        r'\bemail\s+(?:\w+\s+){0,2}(notification|alert|message|communication|delivery|transmission)\b',
        r'\b(send|sends|sending|receive|receives|receiving|deliver|delivers|delivering)\s+(?:\w+\s+){0,3}email',
        r'\bemail\s+(?:\w+\s+){0,2}(capability|feature|function|support|service)\b',
        # Technical indicators
        r'\b(smtp|imap|pop3)\s+(server|protocol|service|gateway)\b',
        r'\bemail\s+(server|gateway|relay|client|integration|api|system)\b',
        r'\b(outbound|inbound)\s+email\b',
        r'\bemail-based\s+(notification|communication|alert|system)\b',
        r'\belectronic\s+mail\s+(notification|communication|system|delivery)\b',
        # Action patterns
        r'\btransmit\s+(?:\w+\s+){0,3}email\b',
        r'\bemail\s+(?:\w+\s+){0,2}to\s+(users|customers|clients|recipients|parties)\b',
        r'\b(automated|automatic)\s+email\b',
        r'\bemail\s+distribution\b',
    ],
    
    'sms': [
        # Core SMS patterns (within 10 words)
        r'\b(via|through|by|using|with|over)\s+(?:\w+\s+){0,3}(sms|text\s+message)\b',
        r'\bsms\s+(?:\w+\s+){0,2}(notification|alert|message|communication|delivery|transmission)\b',
        r'\b(send|sends|sending|receive|receives|receiving|deliver|delivers|delivering)\s+(?:\w+\s+){0,3}(sms|text\s+message)',
        r'\bsms\s+(?:\w+\s+){0,2}(capability|feature|function|support|service)\b',
        r'\btext\s+message\s+(?:\w+\s+){0,2}(notification|alert|communication|delivery)\b',
        # Technical indicators  
        r'\b(twilio|nexmo|vonage|plivo|bandwidth)\b',
        r'\bsms\s+(gateway|api|service|integration|platform|system)\b',
        r'\b(outbound|inbound)\s+sms\b',
        r'\bshort\s+message\s+service\b',
        r'\btext\s+messaging\s+(capability|service|feature|platform|system)\b',
        r'\bmobile\s+(?:\w+\s+){0,2}text\s+(notification|message|alert)\b',
    ],
    
    'chat': [
        # Core chat patterns (within 10 words)
        r'\b(via|through|by|using|with|over)\s+(?:\w+\s+){0,3}chat\b',
        r'\bchat\s+(?:\w+\s+){0,2}(notification|message|communication|interface|window)\b',
        r'\b(provide|provides|providing|enable|enables|enabling|support|supports|supporting)\s+(?:\w+\s+){0,3}chat',
        r'\bchat\s+(?:\w+\s+){0,2}(capability|feature|function|functionality|system)\b',
        # Specific chat types
        r'\b(in-app|live|real-time|instant|web-based)\s+chat\b',
        r'\binstant\s+messaging\b',
        r'\bdirect\s+messaging\b',
        r'\bmessaging\s+(?:\w+\s+){0,2}(capability|feature|platform|system|service)\b',
        # Technical indicators
        r'\b(websocket|socket\.io|xmpp|mqtt)\b',
        r'\bchat\s+(platform|system|integration|api|service|client|server)\b',
        r'\b(slack|teams|discord|intercom|zendesk)\s+(integration|chat|messaging)\b',
        r'\bpeer-to-peer\s+(chat|messaging)\b',
        r'\btwo-way\s+(chat|messaging|communication)\b',
    ],
    
    'comments': [
        # Core comment patterns (within 10 words)
        r'\b(via|through|by|using|with)\s+(?:\w+\s+){0,3}comment\b',
        r'\bcomment\s+(?:\w+\s+){0,2}(notification|feature|system|functionality|thread)\b',
        r'\b(post|posts|posting|leave|leaves|leaving|add|adds|adding|submit|submits|submitting|make|makes|making)\s+(?:\w+\s+){0,3}comment',
        r'\bcomment\s+(?:\w+\s+){0,2}(capability|function|support)\b',
        # Commenting features
        r'\buser\s+(?:\w+\s+){0,2}comment\b',
        r'\bcomment(?:ing|s)?\s+(?:\w+\s+){0,2}(section|area|box|field|system|feature)\b',
        r'\bcomment\s+thread\b',
        r'\breply\s+to\s+comment\b',
        r'\bcomment-based\s+(communication|feedback|interaction)\b',
        r'\ballow\s+(?:\w+\s+){0,3}comment\b',
    ]
}

# Strict exclusion patterns
exclusion_patterns = {
    'email': [
        # Registration/input related
        r'\b(enter|entering|provide|providing|input|inputting|type|typing|specify|specifying|submit|submitting)\s+(?:\w+\s+){0,5}email',
        r'\bemail\s+(?:\w+\s+){0,2}(address|field|input|box|form)\b',
        r'\bemail\s+(?:\w+\s+){0,2}(required|optional|mandatory|needed)\b',
        r'\brequire(?:s|d)?\s+(?:\w+\s+){0,3}email\s+address\b',
        r'\buser(?:\'s|s)?\s+email\s+address\b',
        r'\bvalid\s+email\s+address\b',
        # Authentication related
        r'\bemail\s+(?:\w+\s+){0,2}(login|signup|registration|account|credential|authentication)\b',
        r'\bverify\s+(?:\w+\s+){0,3}email\b',
        r'\bemail\s+verification\b',
        r'\b(register|login|sign\s+in)\s+(?:\w+\s+){0,3}email\b',
    ],
    
    'sms': [
        # Verification codes
        r'\bsms\s+(?:\w+\s+){0,2}(code|verification|authentication|2fa|otp|pin)\b',
        r'\bverification\s+(?:\w+\s+){0,2}(via|through|by)\s+sms\b',
        r'\breceive\s+(?:\w+\s+){0,3}verification\s+(?:\w+\s+){0,2}(code|sms)\b',
        r'\benter\s+(?:\w+\s+){0,3}sms\s+code\b',
        r'\bsms-based\s+(verification|authentication)\b',
    ],
    
    'chat': [
        # AI assistants
        r'\bchat\s*gpt\b',
        r'\bchatgpt\b',
        r'\bai\s+chat(?:bot)?\b',
        r'\bchat\s+(?:bot|assistant)\s+(?:named|called)\b',
        r'\bvirtual\s+(?:assistant|agent)\s+chat\b',
    ],
    
    'comments': [
        # Code comments
        r'\bcomment\s+out\b',
        r'\bcode\s+comment\b',
        r'\bcommented\s+(?:code|line|section)\b',
        r'\binline\s+comment\b',
        r'\b(source\s+)?code\s+(?:\w+\s+){0,2}comment\b',
    ]
}

def detect_communication_type(text):
    """
    Detect if text contains true e-communication capability indicators.
    Uses proximity-based matching optimized for long descriptive paragraphs.
    """
    if pd.isna(text) or not isinstance(text, str):
        return {
            'has_email': False,
            'has_sms': False,
            'has_chat': False,
            'has_comments': False,
            'has_any_ecomm': False,
            'matched_email_pattern': '',
            'matched_sms_pattern': '',
            'matched_chat_pattern': '',
            'matched_comments_pattern': ''
        }
    
    text_lower = text.lower()
    results = {}
    
    for comm_type, patterns in communication_patterns.items():
        # Find which patterns match
        matched_pattern = None
        has_match = False
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                has_match = True
                matched_pattern = match.group()
                break
        
        # Check exclusions
        has_exclusion = False
        if has_match:
            for excl_pattern in exclusion_patterns.get(comm_type, []):
                if re.search(excl_pattern, text_lower, re.IGNORECASE):
                    has_exclusion = True
                    break
        
        # Determine if detected
        is_detected = has_match and not has_exclusion
        results[f'has_{comm_type}'] = is_detected
        results[f'matched_{comm_type}_pattern'] = matched_pattern if is_detected else ''
    
    # Overall flag
    results['has_any_ecomm'] = any([
        results['has_email'],
        results['has_sms'],
        results['has_chat'],
        results['has_comments']
    ])
    
    return results

# Apply detection
text_column = 'TXT_RSRC_DESC'

print("Starting e-communication detection on long-form text...")
detection_results = df[text_column].apply(detect_communication_type)
detection_df = pd.DataFrame(detection_results.tolist())

# Combine with original dataframe
output_df = pd.concat([df, detection_df], axis=1)

# Create summary column
def get_comm_types(row):
    types = []
    if row['has_email']:
        types.append('email')
    if row['has_sms']:
        types.append('sms')
    if row['has_chat']:
        types.append('chat')
    if row['has_comments']:
        types.append('comments')
    return ', '.join(types) if types else 'none'

output_df['detected_comm_types'] = output_df.apply(get_comm_types, axis=1)

# Write output
output_dataset = dataiku.Dataset("YOUR_OUTPUT_DATASET_NAME")
output_dataset.write_with_schema(output_df)

# Print detailed summary
print(f"\n{'='*70}")
print(f"E-COMMUNICATION DETECTION SUMMARY")
print(f"{'='*70}")
print(f"Total rows processed: {len(output_df):,}")
print(f"Rows with e-communication: {output_df['has_any_ecomm'].sum():,} ({output_df['has_any_ecomm'].sum()/len(output_df)*100:.1f}%)")
print(f"\nDetection breakdown:")
print(f"  Email:    {output_df['has_email'].sum():5,} ({output_df['has_email'].sum()/len(output_df)*100:.1f}%)")
print(f"  SMS:      {output_df['has_sms'].sum():5,} ({output_df['has_sms'].sum()/len(output_df)*100:.1f}%)")
print(f"  Chat:     {output_df['has_chat'].sum():5,} ({output_df['has_chat'].sum()/len(output_df)*100:.1f}%)")
print(f"  Comments: {output_df['has_comments'].sum():5,} ({output_df['has_comments'].sum()/len(output_df)*100:.1f}%)")
print(f"{'='*70}\n")

# Show examples
if output_df['has_any_ecomm'].sum() > 0:
    print("Sample detections (first 5):")
    samples = output_df[output_df['has_any_ecomm']].head(5)
    for idx, row in samples.iterrows():
        print(f"\n  [{row['detected_comm_types'].upper()}]")
        if row['matched_email_pattern']:
            print(f"    Email match: '{row['matched_email_pattern']}'")
        if row['matched_sms_pattern']:
            print(f"    SMS match: '{row['matched_sms_pattern']}'")
        if row['matched_chat_pattern']:
            print(f"    Chat match: '{row['matched_chat_pattern']}'")
        if row['matched_comments_pattern']:
            print(f"    Comments match: '{row['matched_comments_pattern']}'")
        print(f"    Text preview: {row[text_column][:150]}...")
