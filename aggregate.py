# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import re

# Read input dataset
input_dataset = dataiku.Dataset("YOUR_INPUT_DATASET_NAME")
df = input_dataset.get_dataframe()

# EXTREMELY restrictive patterns - must explicitly mention the communication type
communication_patterns = {
    'email': [
        # Must have "email" + clear sending/receiving action (within 3 words)
        r'\bsend(?:s|ing)?\s+(?:\w+\s+){0,2}emails?\b',
        r'\breceive(?:s|d|ing)?\s+(?:\w+\s+){0,2}emails?\b',
        r'\bdeliver(?:s|y|ing|ed)?\s+(?:\w+\s+){0,2}emails?\b',
        r'\btransmit(?:s|ting|ted)?\s+(?:\w+\s+){0,2}emails?\b',
        # Via/through email (within 2 words)
        r'\b(via|through)\s+(?:\w+\s+)?emails?\b',
        # Email + notification/alert/message (must be adjacent or 1 word apart)
        r'\bemail\s+(notification|alert|message)s?\b',
        r'\bemail\s+\w+\s+(notification|alert|message)s?\b',
        r'\b(notification|alert|message)s?\s+(via|through)\s+email\b',
        # Technical infrastructure (very specific)
        r'\bsmtp\s+(server|gateway|relay)\b',
        r'\bemail\s+(server|gateway|relay|api)\b',
    ],
    
    'sms': [
        # Must have "sms" or "text message" + clear sending/receiving action (within 3 words)
        r'\bsend(?:s|ing)?\s+(?:\w+\s+){0,2}(sms|text\s+messages?)\b',
        r'\breceive(?:s|d|ing)?\s+(?:\w+\s+){0,2}(sms|text\s+messages?)\b',
        r'\bdeliver(?:s|y|ing|ed)?\s+(?:\w+\s+){0,2}(sms|text\s+messages?)\b',
        # Via/through SMS (within 2 words)
        r'\b(via|through)\s+(?:\w+\s+)?(sms|text)\b',
        # SMS + notification/alert (must be adjacent or 1 word apart)
        r'\bsms\s+(notification|alert|message)s?\b',
        r'\bsms\s+\w+\s+(notification|alert|message)s?\b',
        r'\btext\s+message\s+(notification|alert)s?\b',
        r'\b(notification|alert)s?\s+(via|through)\s+(sms|text)\b',
        # Technical infrastructure
        r'\b(twilio|nexmo|vonage|plivo)\b',
        r'\bsms\s+(gateway|api)\b',
    ],
    
    'chat': [
        # Must have "chat" + clear feature/functionality words (within 2 words max)
        # NOT AI/bot related
        r'\bin-app\s+chat\b',
        r'\blive\s+chat\b',
        r'\breal-?time\s+chat\b',
        r'\binstant\s+chat\b',
        r'\bchat\s+feature\b',
        r'\bchat\s+functionality\b',
        r'\bchat\s+capability\b',
        r'\bchat\s+messaging\b',
        r'\bchat\s+interface\b',
        r'\bchat\s+system\b',
        # Messaging (must be clear it's a feature)
        r'\binstant\s+messaging\b',
        r'\bdirect\s+messaging\b',
        r'\bin-app\s+messaging\b',
        # User-to-user chat
        r'\buser(?:-to-user)?\s+chat\b',
        r'\bpeer-to-peer\s+chat\b',
        r'\btwo-way\s+chat\b',
    ],
    
    'comments': [
        # Must have "comment" + clear action/feature words (within 2 words max)
        r'\bpost(?:s|ing|ed)?\s+(?:\w+\s+)?comments?\b',
        r'\bleave(?:s|ing)?\s+(?:\w+\s+)?comments?\b',
        r'\bsubmit(?:s|ting|ted)?\s+(?:\w+\s+)?comments?\b',
        r'\badd(?:s|ing)?\s+(?:\w+\s+)?comments?\b',
        # Comment features
        r'\bcomment\s+feature\b',
        r'\bcomment\s+functionality\b',
        r'\bcomment\s+section\b',
        r'\bcomment\s+thread\b',
        r'\bcomment\s+system\b',
        r'\buser\s+comments?\b',
        r'\ballow(?:s|ing)?\s+(?:users?\s+to\s+)?comments?\b',
    ]
}

# VERY aggressive exclusion patterns
exclusion_patterns = {
    'email': [
        # Registration/input - ANY mention of entering/providing email
        r'\benter(?:s|ing|ed)?\s+(?:\w+\s+){0,10}email',
        r'\bprovide(?:s|d|ing)?\s+(?:\w+\s+){0,10}email',
        r'\binput(?:s|ting|ted)?\s+(?:\w+\s+){0,10}email',
        r'\btype(?:s|d|ing)?\s+(?:\w+\s+){0,10}email',
        r'\bspecify(?:ing|ied)?\s+(?:\w+\s+){0,10}email',
        r'\bsubmit(?:s|ting|ted)?\s+(?:\w+\s+){0,10}email',
        r'\bsupply(?:ing|ied)?\s+(?:\w+\s+){0,10}email',
        r'\binclude(?:s|d|ing)?\s+(?:\w+\s+){0,10}email',
        # Email address/field mentions
        r'\bemail\s+address\b',
        r'\bemail\s+field\b',
        r'\bemail\s+(?:\w+\s+){0,2}(input|form|box|information|data|details)\b',
        r'\bvalid\s+email\b',
        r'\bemail\s+format\b',
        # Authentication/verification
        r'\bemail\s+(?:\w+\s+){0,5}(login|signup|sign-up|registration|register|account|credential|authentication|password|verify|verification|confirm|confirmation)\b',
        r'\b(login|signup|sign-up|register|authenticate|verify|confirmation)\s+(?:\w+\s+){0,10}email',
        r'\bemail\s+verification\b',
        r'\bverify\s+(?:\w+\s+){0,5}email',
        # Requirements
        r'\brequire(?:s|d|ment)?\s+(?:\w+\s+){0,10}email',
        r'\bemail\s+(?:is\s+)?(required|optional|mandatory|needed|necessary)\b',
        # Contact information
        r'\bcontact\s+(?:\w+\s+){0,5}email\b',
        r'\bemail\s+contact\b',
        r'\b(personal|business|work|company)\s+email\b',
        r'\buser\'?s?\s+email\b',
    ],
    
    'sms': [
        # Verification/2FA - ANY mention of codes or authentication
        r'\bsms\s+(?:\w+\s+){0,5}(code|verification|verify|authenticate|authentication|2fa|two-factor|otp|one-time|pin|confirm|confirmation)\b',
        r'\b(verification|verify|authenticate|authentication|2fa|two-factor|otp|one-time|confirm|confirmation)\s+(?:\w+\s+){0,10}(sms|text)',
        r'\breceive(?:s|d|ing)?\s+(?:\w+\s+){0,10}(verification|authentication|confirmation)\s+(?:\w+\s+){0,5}(code|sms|text)',
        r'\benter(?:s|ing|ed)?\s+(?:\w+\s+){0,5}sms\s+code\b',
        r'\bsms-based\s+(verification|authentication)\b',
    ],
    
    'chat': [
        # AI/Bot related - exclude ALL AI chat
        r'\bchat\s*gpt\b',
        r'\bchatgpt\b',
        r'\bai\s+(?:\w+\s+){0,3}chat\b',
        r'\bchat\s+(?:\w+\s+){0,2}(bot|assistant|agent|ai)\b',
        r'\b(bot|assistant|agent)\s+(?:\w+\s+){0,3}chat\b',
        r'\bvirtual\s+(?:assistant|agent)\b',
        r'\bconversational\s+ai\b',
        r'\b(automated|automatic)\s+chat\b',
        r'\bchatbot\b',
        r'\bartificial\s+intelligence\s+(?:\w+\s+){0,3}chat\b',
    ],
    
    'comments': [
        # Code comments - exclude ALL code-related
        r'\bcomment\s+out\b',
        r'\bcode\s+(?:\w+\s+){0,3}comment',
        r'\bcomment(?:s|ing|ed)?\s+(?:\w+\s+){0,3}(code|line|section|block)\b',
        r'\binline\s+comment\b',
        r'\bsource\s+code\s+comment\b',
        r'\bprogramming\s+comment\b',
        r'\bjavascript\s+comment\b',
        r'\bhtml\s+comment\b',
        r'\b(//|/\*|\*/|<!--)\b',
    ]
}

def detect_communication_type(text):
    """
    ULTRA STRICT detection - only matches explicit e-communication capabilities.
    """
    if pd.isna(text) or not isinstance(text, str):
        return {
            'has_email': False,
            'has_sms': False,
            'has_chat': False,
            'has_comments': False,
            'has_any_ecomm': False,
            'match_details': ''
        }
    
    text_lower = text.lower()
    results = {}
    match_details = []
    
    for comm_type, patterns in communication_patterns.items():
        # Find matches
        matched = False
        matched_text = None
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                matched = True
                matched_text = match.group()
                break
        
        # If we have a match, check ALL exclusions
        is_excluded = False
        if matched:
            for excl_pattern in exclusion_patterns.get(comm_type, []):
                if re.search(excl_pattern, text_lower, re.IGNORECASE):
                    is_excluded = True
                    break
        
        # Only mark as detected if we have a match AND no exclusions
        is_detected = matched and not is_excluded
        results[f'has_{comm_type}'] = is_detected
        
        if is_detected and matched_text:
            match_details.append(f"{comm_type}:{matched_text}")
    
    results['has_any_ecomm'] = any([
        results['has_email'],
        results['has_sms'],
        results['has_chat'],
        results['has_comments']
    ])
    
    results['match_details'] = ' | '.join(match_details) if match_details else ''
    
    return results

# Apply detection
text_column = 'TXT_RSRC_DESC'

print("Starting ULTRA STRICT e-communication detection...")
print("Only detecting explicit mentions of email/sms/chat/comment features\n")

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

# Print summary
total = len(output_df)
detected = output_df['has_any_ecomm'].sum()
print(f"\n{'='*70}")
print(f"ULTRA STRICT DETECTION RESULTS")
print(f"{'='*70}")
print(f"Total rows: {total:,}")
print(f"Detected e-comm: {detected:,} ({detected/total*100:.2f}%)")
print(f"\nBy type:")
print(f"  Email:    {output_df['has_email'].sum():,}")
print(f"  SMS:      {output_df['has_sms'].sum():,}")
print(f"  Chat:     {output_df['has_chat'].sum():,}")
print(f"  Comments: {output_df['has_comments'].sum():,}")
print(f"{'='*70}\n")

# Show examples if any detected
if detected > 0:
    print(f"First {min(10, detected)} TRUE POSITIVES:\n")
    samples = output_df[output_df['has_any_ecomm']].head(10)
    for i, (idx, row) in enumerate(samples.iterrows(), 1):
        print(f"{i}. [{row['detected_comm_types'].upper()}]")
        print(f"   Match: {row['match_details']}")
        print(f"   Text: {row[text_column][:250]}...")
        print()
