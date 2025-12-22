# -*- coding: utf-8 -*-
# ================================================================================
# INPUT AND OUTPUT TABLES - CONFIGURE THESE
# ================================================================================

INPUT_TABLE_1 = 'table1'
INPUT_TABLE_2 = 'table2'
INPUT_TABLE_3 = 'table3'
INPUT_TABLE_4 = 'table4'
INPUT_TABLE_5 = 'table5'

OUTPUT_TABLE = 'ecomm_detection_results'

# ================================================================================
# FALSE POSITIVES - Strings incorrectly flagged (add as you find them)
# ================================================================================

FALSE_POSITIVES = [
]

# ================================================================================
# FALSE NEGATIVES - Strings that should be flagged (add as you find them)
# ================================================================================

FALSE_NEGATIVES = [
]

# ================================================================================
# END OF CONFIGURATION
# ================================================================================

import dataiku
import pandas as pd
import re
from collections import defaultdict

"""
DETECTION STRATEGY:

The key question: Can users ACTIVELY COMMUNICATE through this app?

TRUE E-COMM indicators (action-oriented):
- Sending: send, compose, write, reply, forward, broadcast
- Receiving: inbox, receive, incoming
- UI elements: send button, compose window, message box, chat window
- Recipients: to:, recipient, addressee
- Conversations: thread, conversation, chat history, correspondence
- Real-time: live chat, video call, voice call, conference
- Features: messaging feature, chat capability, calling enabled

FALSE indicators (passive/storage):
- Storage: stored, saved, collected, database, field, column
- Display: displayed, shown, view, profile
- Input: enter email, email field, form
- Validation: validate, verify, format check
- Settings: preferences, settings, enable/disable notifications
- Auth: login, register, 2FA, OTP, verification code
- Lists: email, phone (comma-separated = data fields)
"""

# ================================================================================
# STRONG POSITIVE SIGNALS - These strongly indicate real e-comm capability
# ================================================================================

STRONG_POSITIVE_PATTERNS = [
    # === ACTIVE SENDING VERBS WITH CONTEXT ===
    r'(?:can|able to|allow(?:s|ing)?|let(?:s)?|enable(?:s|d)?)\s+(?:user|customer|member|people|you)s?\s+(?:to\s+)?(?:send|compose|write|create|draft)',
    r'(?:user|customer|member|people)s?\s+(?:can|may|could)\s+(?:send|compose|write|reply|forward)',
    r'(?:send|compose|write|draft|reply|forward)\s+(?:a\s+)?(?:message|email|text|sms|chat|response)',
    r'(?:message|email|text|sms)\s+(?:can be|is|are)\s+(?:sent|composed|written|drafted)',
    
    # === INBOX/OUTBOX (implies sending AND receiving) ===
    r'\b(?:inbox|outbox|sent\s*(?:folder|items|messages|mail)|drafts?\s*folder)\b',
    r'(?:message|email|chat)\s+(?:inbox|outbox)',
    r'(?:view|check|open)\s+(?:your\s+)?(?:inbox|messages|emails)',
    
    # === COMPOSE/WRITE ACTIONS ===
    r'\b(?:compose|composing)\s+(?:a\s+)?(?:new\s+)?(?:message|email|text|mail)\b',
    r'(?:new|create)\s+(?:message|email|conversation|chat)',
    r'(?:write|draft)\s+(?:a\s+)?(?:message|email|response|reply)',
    r'(?:message|email)\s+(?:composer|composition|editor)',
    
    # === REPLY/FORWARD/RESPOND ===
    r'\b(?:reply|replying|respond|responding)\s+(?:to\s+)?(?:message|email|sender|user)',
    r'\bforward(?:ing)?\s+(?:message|email|mail)',
    r'(?:can|able to)\s+(?:reply|respond|forward)',
    
    # === RECIPIENT INDICATORS ===
    r'\b(?:recipient|addressee|receiver)s?\b',
    r'\bto:\s*(?:field|line|address)',
    r'(?:select|choose|add|enter)\s+(?:a\s+)?recipient',
    r'(?:send|message)\s+to\s+(?:user|customer|member|contact|friend|recipient)',
    
    # === CONVERSATION/THREAD ===
    r'\b(?:conversation|thread|chat\s*history|message\s*history|correspondence)\b',
    r'(?:start|begin|initiate|open)\s+(?:a\s+)?(?:conversation|chat|dialogue)',
    r'(?:conversation|chat|thread)\s+(?:with|between)\s+(?:user|customer|member)',
    
    # === REAL-TIME COMMUNICATION ===
    r'\b(?:live\s*chat|real[\s-]*time\s+(?:chat|messaging|communication))\b',
    r'\b(?:video\s*call|voice\s*call|phone\s*call|audio\s*call)(?:ing)?\b',
    r'\b(?:video|voice|audio)\s+(?:conference|conferencing|meeting)\b',
    r'(?:make|place|start|initiate|join)\s+(?:a\s+)?(?:call|video|voice)',
    r'(?:call|ring|dial)\s+(?:user|customer|contact|someone)',
    
    # === INSTANT MESSAGING ===
    r'\b(?:instant\s*messag(?:e|ing)|im|direct\s*messag(?:e|ing)|dm|private\s*messag(?:e|ing)|pm)\b',
    r'(?:send|receive)\s+(?:instant|direct|private)\s+message',
    r'(?:chat|message)\s+(?:with|to)\s+(?:other\s+)?(?:user|customer|member|friend)',
    
    # === MESSAGING FEATURES ===
    r'(?:messaging|chat|communication|calling)\s+(?:feature|capability|function(?:ality)?|module)',
    r'(?:built[\s-]*in|integrated|native)\s+(?:messaging|chat|email|calling)',
    r'(?:in[\s-]*app)\s+(?:messaging|chat|email|calling|communication)',
    
    # === PUSH/SEND NOTIFICATIONS (app actively sends) ===
    r'(?:app|system|platform|we)\s+(?:send|push|deliver)s?\s+(?:notification|alert|message)',
    r'(?:push|send)\s+notification\s+to\s+(?:user|device|customer)',
    r'(?:notification|alert|message)\s+(?:is|are)\s+(?:sent|pushed|delivered)\s+to',
    
    # === UI ELEMENTS FOR COMMUNICATION ===
    r'\b(?:send\s*button|compose\s*button|reply\s*button|chat\s*button|call\s*button)\b',
    r'(?:click|tap|press)\s+(?:to\s+)?(?:send|compose|reply|call|chat)',
    r'(?:message|chat|compose)\s+(?:window|box|panel|screen|interface)',
    r'(?:chat|message|call)\s+(?:icon|button|widget)',
    
    # === BROADCAST/BULK SENDING ===
    r'(?:broadcast|mass[\s-]*send|bulk[\s-]*send|send\s+to\s+(?:all|multiple|many))',
    r'(?:send|email|message)\s+(?:campaign|newsletter|announcement|blast)',
    
    # === SPECIFIC COMMUNICATION TYPES ===
    r'\b(?:sms|mms)\s+(?:messaging|sending|capability)\b',
    r'\b(?:voip|sip)\s+(?:call|capability|enabled)\b',
    r'\bwebrtc\b',
    r'(?:toll[\s-]*free|1[\s-]*800|customer\s+service)\s+(?:call|line|number)',
    
    # === EXPLICIT E-COMMUNICATION ===
    r'\be[\s-]*comm(?:unication)?s?\b',
    r'electronic\s+communication',
]

# ================================================================================
# STRONG NEGATIVE SIGNALS - These indicate NOT e-comm (just data/storage)
# ================================================================================

STRONG_NEGATIVE_PATTERNS = [
    # === DATA FIELD FORMATS (lists of fields) ===
    r'(?:email|phone|name|address)\s*[,;/&|]\s*(?:email|phone|name|address)',
    r'(?:field|column|attribute|property|data)s?\s*:\s*(?:.*\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:field|column|attribute|property|input|textbox)',
    
    # === COLLECTION/STORAGE VERBS ===
    r'(?:collect|gather|capture|harvest|store|save|record|retain|maintain|keep|hold|log)s?\s+(?:(?:the|user.?s?|customer.?s?)\s+)?(?:email|phone|contact)',
    r'(?:email|phone|contact)\s+(?:is|are|was|were)\s+(?:collected|gathered|captured|stored|saved|recorded|retained|kept|logged)',
    r'(?:email|phone)\s+(?:storage|collection|retention|database|repository)',
    
    # === FORM/INPUT CONTEXTS ===
    r'(?:enter|input|type|provide|fill|submit)\s+(?:your\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:is\s+)?(?:required|optional|mandatory|needed)',
    r'(?:email|phone)\s+(?:form|input|entry|box|field)',
    r'(?:valid|invalid|correct|incorrect)\s+(?:email|phone)',
    r'(?:validate|verify|check)\s+(?:email|phone)',
    
    # === DATABASE/SCHEMA ===
    r'(?:varchar|nvarchar|char|string|text|int|blob)\s*\(?.*\)?\s*(?:email|phone)',
    r'(?:email|phone)\s+(?:varchar|column|table|schema|database|index)',
    r'(?:create|alter|drop|insert|update|delete|select)\s+.*(?:email|phone)',
    r'(?:primary|foreign)\s+key.*(?:email|phone)',
    r'(?:email|phone).*(?:primary|foreign)\s+key',
    
    # === AUTH/LOGIN ===
    r'(?:login|log\s*in|signin|sign\s*in|register|sign\s*up)\s+(?:with|using|via)\s+(?:email|phone)',
    r'(?:email|phone)\s+(?:as|is|for)\s+(?:username|user\s*id|login|account)',
    r'(?:forgot|reset|change|recover)\s+password.*(?:email|phone)',
    r'(?:email|phone)\s+(?:verification|confirmation)\s+(?:for\s+)?(?:account|registration|signup)',
    
    # === 2FA/OTP ===
    r'(?:2fa|two[\s-]*factor|mfa|multi[\s-]*factor|otp|one[\s-]*time)',
    r'(?:verification|security|auth(?:entication)?)\s+(?:code|token|pin)',
    r'(?:code|token|pin)\s+(?:via|by|through)\s+(?:sms|text|email)',
    
    # === DISPLAY ONLY ===
    r'(?:display|show|view|see|present|render)s?\s+(?:(?:the|user.?s?)\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:is\s+)?(?:displayed|shown|visible|hidden|masked)',
    r'(?:email|phone)\s+(?:in|on)\s+(?:profile|account|settings|screen|page)',
    
    # === NOTIFICATION SETTINGS (configuring, not sending) ===
    r'(?:notification|email|sms)\s+(?:setting|preference|option|configuration)',
    r'(?:enable|disable|turn\s+on|turn\s+off)\s+(?:notification|email|sms)',
    r'(?:opt[\s-]*in|opt[\s-]*out|subscribe|unsubscribe)',
    r'(?:manage|configure|customize)\s+(?:notification|email|alert)',
    
    # === CONTACT INFO CONTEXTS ===
    r'(?:contact|personal|user|customer|account)\s+(?:info(?:rmation)?|details?|data)',
    r'(?:email|phone)\s+(?:info(?:rmation)?|details?|address)',
    r'(?:business|work|home|personal|office|mobile)\s+(?:email|phone)',
    
    # === LOGS/HISTORY (records, not capability) ===
    r'(?:email|call|message|notification)\s+(?:log|history|record|audit)',
    r'(?:log|history|record)\s+of\s+(?:email|call|message|notification)',
    
    # === PASSIVE/STATIC ===
    r'(?:email|phone)\s+(?:is\s+)?(?:blank|empty|null|missing|n/?a)',
    r'(?:no|without|missing)\s+(?:email|phone)',
    r'(?:email|phone)\s+(?:not\s+)?(?:provided|available|specified)',
    
    # === TEMPLATES (not actual sending) ===
    r'(?:email|message|notification)\s+template',
    r'template\s+(?:for\s+)?(?:email|message|notification)',
    
    # === ERROR/BOUNCE ===
    r'(?:email|message)\s+(?:bounce|bounced|failed|error|undeliverable)',
    r'(?:invalid|bad|wrong)\s+(?:email|phone)',
    r'(?:spam|junk|block).*(?:email|message)',
    
    # === TECHNICAL/SYSTEM ===
    r'(?:smtp|pop3?|imap|mail\s*server|mx\s*record)',
    r'(?:email|phone)\s+(?:format|regex|pattern|validation)',
    r'(?:plaintext|encrypted)\s+(?:email|password)',
]

# ================================================================================
# CONTEXT KEYWORDS - Must have at least one for consideration
# ================================================================================

CONTEXT_KEYWORDS = [
    'email', 'e-mail', 'mail',
    'sms', 'text message', 'texting', 'mms',
    'message', 'messaging', 'msg',
    'call', 'calling', 'phone', 'telephone',
    'video', 'voice', 'voip', 'sip',
    'chat', 'chatting', 'im',
    'notification', 'notify', 'alert', 'push',
    'communication', 'communicate',
    'inbox', 'outbox', 'compose', 'send', 'reply',
    'conversation', 'thread', 'dialogue',
    'conference', 'conferencing', 'meeting',
    'webrtc', 'telephony',
]

INVALID_IDN = {'nan', 'none', '', 'null', 'n/a', 'na', '-', 'unknown', ' ', 'undefined', 'test', 'example'}

# Compile patterns
POSITIVE_RE = [re.compile(p, re.IGNORECASE) for p in STRONG_POSITIVE_PATTERNS]
NEGATIVE_RE = [re.compile(p, re.IGNORECASE) for p in STRONG_NEGATIVE_PATTERNS]
FALSE_POS_SET = set(x.lower().strip() for x in FALSE_POSITIVES if x and x.strip())
FALSE_NEG_SET = set(x.lower().strip() for x in FALSE_NEGATIVES if x and x.strip())

def has_context_keyword(text_lower):
    """Check if text has any communication-related keyword."""
    for kw in CONTEXT_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def is_ecomm(text):
    """
    Determine if text indicates ACTUAL e-communication capability.
    
    Logic:
    1. Check learned patterns (false pos/neg)
    2. Must have context keyword
    3. Check strong negative patterns - if match, return False
    4. Check strong positive patterns - if match, return True
    5. Default: return False (conservative)
    """
    if not text or len(text) < 15:  # Need enough context
        return False
    
    text_lower = text.lower()
    
    # Learned false positives - always reject
    for fp in FALSE_POS_SET:
        if fp and fp in text_lower:
            return False
    
    # Learned false negatives - always accept
    for fn in FALSE_NEG_SET:
        if fn and fn in text_lower:
            return True
    
    # Must have at least one context keyword
    if not has_context_keyword(text_lower):
        return False
    
    # Check strong negative patterns first (reject if any match)
    for pattern in NEGATIVE_RE:
        if pattern.search(text_lower):
            return False
    
    # Check strong positive patterns (accept if any match)
    for pattern in POSITIVE_RE:
        if pattern.search(text_lower):
            return True
    
    # Default: not e-comm (be conservative to reduce false positives)
    return False

def find_idn_col(df):
    """Find IDN_EON column (case-insensitive)."""
    for col in df.columns:
        normalized = col.upper().replace(' ', '_').replace('-', '_')
        if 'IDN_EON' in normalized:
            return col
    return None

# ================================================================================
# MAIN
# ================================================================================

print("=" * 60)
print("E-COMMUNICATION CAPABILITY DETECTION")
print("=" * 60)
print(f"Positive patterns: {len(STRONG_POSITIVE_PATTERNS)}")
print(f"Negative patterns: {len(STRONG_NEGATIVE_PATTERNS)}")

# Load tables
tables = {}
for name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4, INPUT_TABLE_5]:
    try:
        df = dataiku.Dataset(name).get_dataframe()
        for c in df.columns:
            df[c] = df[c].astype(str)
        tables[name] = df
        print(f"✓ {name}: {len(df):,} rows")
    except Exception as e:
        print(f"✗ {name}: {e}")

if not tables:
    raise ValueError("No tables loaded!")

# Process
print("\nProcessing...")

idn_sources = defaultdict(set)
idn_ecomm = defaultdict(list)
total_rows = 0

for tname, df in tables.items():
    idn_col = find_idn_col(df)
    if not idn_col:
        print(f"  ⚠ {tname}: No IDN_EON column")
        continue
    
    other_cols = [c for c in df.columns if c != idn_col]
    ecomm_count = 0
    
    for idx, row in df.iterrows():
        total_rows += 1
        if total_rows % 5000 == 0:
            print(f"  {total_rows:,} rows...")
        
        idn_val = str(row[idn_col]).strip()
        if idn_val.lower() in INVALID_IDN:
            continue
        
        idn_sources[idn_val].add(tname)
        
        for col in other_cols:
            txt = str(row[col]).strip()
            if is_ecomm(txt):
                loc = f"{tname}.{col}"
                if (txt, loc) not in idn_ecomm[idn_val]:
                    idn_ecomm[idn_val].append((txt, loc))
                    ecomm_count += 1
    
    print(f"  ✓ {tname}: {ecomm_count:,} e-comm capabilities")

# Build output - only IDN_EON with e-comm
print("\nBuilding output...")

results = []
for idn, ecomm_list in idn_ecomm.items():
    if ecomm_list:
        sources = idn_sources.get(idn, set())
        results.append({
            'IDN_EON': idn,
            'source_tables': ', '.join(sorted(sources)),
            'ecomm_string': ' | '.join([s[0] for s in ecomm_list]),
            'string_location': ' | '.join([s[1] for s in ecomm_list]),
        })

output_df = pd.DataFrame(results)

print(f"\nTotal IDN_EON with e-comm capability: {len(output_df):,}")

if len(output_df) > 0:
    print("\nSample detections:")
    for idx, row in output_df.head(5).iterrows():
        idn_short = row['IDN_EON'][:30] + "..." if len(row['IDN_EON']) > 30 else row['IDN_EON']
        ecomm_short = row['ecomm_string'][:70] + "..." if len(row['ecomm_string']) > 70 else row['ecomm_string']
        print(f"  • {idn_short}")
        print(f"    \"{ecomm_short}\"")

print(f"\nWriting to {OUTPUT_TABLE}...")
dataiku.Dataset(OUTPUT_TABLE).write_with_schema(output_df)
print("✓ Done!")
