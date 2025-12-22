# -*- coding: utf-8 -*-
# ================================================================================
# input and output tables - configure these
# ================================================================================

INPUT_TABLE_1 = 'table1'
INPUT_TABLE_2 = 'table2'
INPUT_TABLE_3 = 'table3'
INPUT_TABLE_4 = 'table4'
INPUT_TABLE_5 = 'table5'

OUTPUT_TABLE = 'ecomm_detection_results'

# ================================================================================
# false positives - strings incorrectly flagged (add as you find them)
# ================================================================================

FALSE_POSITIVES = [
]

# ================================================================================
# false negatives - strings that should be flagged (add as you find them)
# ================================================================================

FALSE_NEGATIVES = [
]

# ================================================================================
# end of configuration
# ================================================================================

import dataiku
import pandas as pd
import re
from collections import defaultdict

# ================================================================================
# positive signals - any of these suggest e-comm capability
# these are intentionally broad to catch more
# ================================================================================

POSITIVE_PATTERNS = [
    # sending actions (broad)
    r'sends?\s+(?:an?\s+)?(?:email|e-mail|message|text|sms|mms|notification|alert)',
    r'(?:email|message|text|sms|notification|alert)s?\s+(?:are\s+)?sent',
    r'(?:deliver|transmit|dispatch|push)(?:es|s|ing)?\s+(?:email|message|notification|alert)',
    r'(?:email|message|notification|alert)\s+delivery',
    r'outbound\s+(?:email|message|sms|communication)',
    r'outgoing\s+(?:email|message|call)',
    
    # user communication actions
    r'(?:user|customer|member)s?\s+(?:can\s+)?(?:send|message|contact|reach|chat|call)',
    r'(?:send|compose|write|draft|reply|forward)\s+(?:a\s+)?(?:message|email|text)',
    r'(?:message|email|chat|call)\s+(?:other\s+)?(?:user|customer|member|people)',
    r'(?:contact|reach|message)\s+(?:us|support|customer\s+service)',
    
    # messaging and chat
    r'\bmessaging\b',
    r'\bchat\b',
    r'\bchatting\b',
    r'\bim\b',
    r'\bdirect\s+message',
    r'\binstant\s+message',
    r'\bprivate\s+message',
    r'\bin-app\s+messag',
    r'\breal-time\s+messag',
    r'\blive\s+chat\b',
    
    # calling
    r'\bvideo\s+call',
    r'\bvoice\s+call',
    r'\bphone\s+call',
    r'\baudio\s+call',
    r'\bvideo\s+chat\b',
    r'\bvoip\b',
    r'\bsip\s+call',
    r'\bwebrtc\b',
    r'\bconference\s+call',
    r'\bvideo\s+conference',
    r'\btelephone\b',
    r'\bcaller\b',
    r'\bcalling\s+feature',
    r'\bmake\s+(?:a\s+)?call',
    r'\bplace\s+(?:a\s+)?call',
    
    # inbox/outbox (strong signal)
    r'\binbox\b',
    r'\boutbox\b',
    r'\bsent\s+(?:folder|items|mail|messages)',
    r'\bdrafts?\b',
    r'\bmailbox\b',
    
    # compose/write
    r'\bcompose\b',
    r'\bcomposer\b',
    r'\breply\b',
    r'\bforward\b',
    r'\brespond\b',
    
    # recipients
    r'\brecipient',
    r'\baddressee',
    r'\bto:\s*field',
    r'\bcc:\b',
    r'\bbcc:\b',
    
    # notifications (app sending to users)
    r'push\s+notification',
    r'mobile\s+notification',
    r'app\s+notification',
    r'(?:send|push|deliver).*notification',
    r'notification.*(?:sent|delivered|pushed)',
    r'notifies?\s+(?:user|customer)',
    r'alerts?\s+(?:user|customer)',
    
    # sms/text specific
    r'\bsms\b',
    r'\bmms\b',
    r'\btext\s+message',
    r'\btext\s+alert',
    r'\bsms\s+gateway',
    r'\btwilio\b',
    r'\bsendgrid\b',
    r'\bmailchimp\b',
    r'\bmailgun\b',
    
    # email specific (sending context)
    r'email\s+(?:campaign|blast|newsletter|marketing)',
    r'(?:send|deliver)\s+email',
    r'email\s+(?:notification|alert|reminder)',
    r'transactional\s+email',
    r'automated\s+email',
    r'bulk\s+email',
    r'mass\s+email',
    
    # communication features
    r'(?:communication|messaging|chat|calling)\s+(?:feature|capability|platform|system|module)',
    r'(?:e-?comm(?:unication)?)\b',
    r'electronic\s+communication',
    r'unified\s+communication',
    r'omnichannel',
    r'multi-?channel\s+(?:communication|messaging)',
    
    # conversation/thread
    r'\bconversation\b',
    r'\bthread\b',
    r'\bdialogue\b',
    r'\bcorrespondence\b',
    
    # broadcast
    r'\bbroadcast\b',
    r'\bannouncement\b',
    r'\bbulletin\b',
    
    # customer communication
    r'customer\s+(?:communication|contact|outreach|engagement)',
    r'(?:contact|reach)\s+customer',
    r'user\s+communication',
]

# ================================================================================
# negative signals - these indicate data storage, not e-comm capability
# only reject if these match AND no strong positive signal
# ================================================================================

NEGATIVE_PATTERNS = [
    # field/data lists (very strong negative)
    r'(?:email|phone|name|address)\s*[,;/&]\s*(?:email|phone|name|address)',
    r'fields?\s*:\s*.*(?:email|phone)',
    r'(?:email|phone)\s*:\s*$',
    
    # storage verbs
    r'(?:collect|gather|capture|store|save|record|retain|log)s?\s+(?:the\s+)?(?:user.?s?\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:is\s+)?(?:stored|saved|collected|recorded|logged)',
    
    # form/input
    r'(?:enter|input|type|provide|fill)\s+(?:your\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:field|input|textbox|form)',
    r'(?:email|phone)\s+(?:is\s+)?(?:required|optional|mandatory)',
    
    # database/schema
    r'(?:varchar|nvarchar|char|text|string|int)\s*\(?\d*\)?\s*(?:email|phone)',
    r'(?:email|phone)\s+(?:column|table|schema|database)',
    r'(?:create|alter|insert|update|select)\s+.*(?:email|phone)',
    
    # auth/login
    r'(?:login|signin|register|signup)\s+(?:with|using)\s+(?:email|phone)',
    r'(?:email|phone)\s+(?:as|for)\s+(?:username|login|account)',
    r'(?:forgot|reset)\s+password',
    
    # 2fa/otp
    r'(?:2fa|two-?factor|mfa|otp|one-?time)',
    r'verification\s+code',
    
    # validation
    r'(?:validate|verify|check)\s+(?:email|phone)',
    r'(?:email|phone)\s+(?:validation|verification|format)',
    r'(?:valid|invalid)\s+(?:email|phone)',
    
    # display only
    r'(?:display|show|view)s?\s+(?:the\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:displayed|shown|visible)',
    
    # settings/preferences
    r'notification\s+(?:setting|preference|option)',
    r'(?:enable|disable)\s+notification',
    r'(?:opt-?in|opt-?out|unsubscribe)',
    
    # templates
    r'(?:email|message)\s+template',
]

# ================================================================================
# simple keyword check - must have at least one
# ================================================================================

KEYWORDS = [
    'email', 'e-mail', 'mail',
    'sms', 'mms', 'text',
    'message', 'messaging',
    'call', 'calling', 'caller', 'phone', 'telephone',
    'video', 'voice', 'voip',
    'chat', 'chatting',
    'notification', 'notify', 'alert',
    'push',
    'communication', 'communicate',
    'inbox', 'outbox', 'compose', 'reply',
    'conversation', 'thread',
    'conference',
    'broadcast',
    'twilio', 'sendgrid', 'mailchimp',
]

INVALID_IDN = {'nan', 'none', '', 'null', 'n/a', 'na', '-', 'unknown', ' ', 'undefined', 'test', 'example'}

# compile patterns
POSITIVE_RE = [re.compile(p, re.IGNORECASE) for p in POSITIVE_PATTERNS]
NEGATIVE_RE = [re.compile(p, re.IGNORECASE) for p in NEGATIVE_PATTERNS]
FALSE_POS_SET = set(x.lower().strip() for x in FALSE_POSITIVES if x and x.strip())
FALSE_NEG_SET = set(x.lower().strip() for x in FALSE_NEGATIVES if x and x.strip())

def has_keyword(text_lower):
    for kw in KEYWORDS:
        if kw in text_lower:
            return True
    return False

def count_positive_matches(text_lower):
    count = 0
    for pattern in POSITIVE_RE:
        if pattern.search(text_lower):
            count += 1
    return count

def count_negative_matches(text_lower):
    count = 0
    for pattern in NEGATIVE_RE:
        if pattern.search(text_lower):
            count += 1
    return count

def is_ecomm(text):
    """
    determine if text indicates e-communication capability.
    
    logic:
    1. check learned patterns first
    2. must have at least one keyword
    3. count positive and negative matches
    4. if more positive than negative, or any strong positive -> e-comm
    5. if only negative matches -> not e-comm
    """
    if not text or len(text) < 10:
        return False
    
    text_lower = text.lower()
    
    # learned false positives - always reject
    for fp in FALSE_POS_SET:
        if fp and fp in text_lower:
            return False
    
    # learned false negatives - always accept
    for fn in FALSE_NEG_SET:
        if fn and fn in text_lower:
            return True
    
    # must have keyword
    if not has_keyword(text_lower):
        return False
    
    # count matches
    pos_count = count_positive_matches(text_lower)
    neg_count = count_negative_matches(text_lower)
    
    # if any positive match and not overwhelmed by negatives -> e-comm
    if pos_count > 0 and pos_count >= neg_count:
        return True
    
    # if only negatives -> not e-comm
    if neg_count > 0 and pos_count == 0:
        return False
    
    # edge case: has keyword but no pattern matches
    # check for very simple signals that patterns might miss
    simple_signals = [
        'sends email', 'sends text', 'sends sms', 'sends message',
        'send email', 'send text', 'send sms', 'send message',
        'email sent', 'text sent', 'sms sent', 'message sent',
        'can email', 'can text', 'can message', 'can call',
        'video call', 'voice call', 'phone call',
        'live chat', 'chat with', 'message to',
        'inbox', 'outbox', 'compose',
    ]
    for signal in simple_signals:
        if signal in text_lower:
            return True
    
    return False

def find_idn_col(df):
    for col in df.columns:
        normalized = col.upper().replace(' ', '_').replace('-', '_')
        if 'IDN_EON' in normalized:
            return col
    return None

# ================================================================================
# main
# ================================================================================

print("=" * 60)
print("e-communication capability detection")
print("=" * 60)
print(f"positive patterns: {len(POSITIVE_PATTERNS)}")
print(f"negative patterns: {len(NEGATIVE_PATTERNS)}")

# load tables
tables = {}
for name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4, INPUT_TABLE_5]:
    try:
        df = dataiku.Dataset(name).get_dataframe()
        for c in df.columns:
            df[c] = df[c].astype(str)
        tables[name] = df
        print(f"[ok] {name}: {len(df):,} rows")
    except Exception as e:
        print(f"[fail] {name}: {e}")

if not tables:
    raise ValueError("no tables loaded")

# process
print("\nprocessing...")

idn_sources = defaultdict(set)
idn_ecomm = defaultdict(list)
total_rows = 0

for tname, df in tables.items():
    idn_col = find_idn_col(df)
    if not idn_col:
        print(f"  [warn] {tname}: no idn_eon column")
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
    
    print(f"  [ok] {tname}: {ecomm_count:,} e-comm found")

# build output
print("\nbuilding output...")

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

print(f"\ntotal idn_eon with e-comm capability: {len(output_df):,}")

if len(output_df) > 0:
    print("\nsample detections:")
    for idx, row in output_df.head(5).iterrows():
        idn_short = row['IDN_EON'][:30] + "..." if len(row['IDN_EON']) > 30 else row['IDN_EON']
        ecomm_short = row['ecomm_string'][:70] + "..." if len(row['ecomm_string']) > 70 else row['ecomm_string']
        print(f"  - {idn_short}")
        print(f"    \"{ecomm_short}\"")

print(f"\nwriting to {OUTPUT_TABLE}...")
dataiku.Dataset(OUTPUT_TABLE).write_with_schema(output_df)
print("[ok] done")
