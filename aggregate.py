# -*- coding: utf-8 -*-
# ================================================================================
# INPUT AND OUTPUT TABLES - CONFIGURE THESE
# ================================================================================

INPUT_TABLE_1 = 'table1'  # First input table name
INPUT_TABLE_2 = 'table2'  # Second input table name
INPUT_TABLE_3 = 'table3'  # Third input table name
INPUT_TABLE_4 = 'table4'  # Fourth input table name

OUTPUT_TABLE = 'ecomm_detection_results'  # Output table name

# ================================================================================
# DETECTION SETTINGS
# ================================================================================

ECOMM_THRESHOLD = 0.55  # Classification threshold (0.0 to 1.0)
MIN_TEXT_LENGTH = 5     # Minimum text length to analyze

# ================================================================================
# FALSE POSITIVES - Add strings that INCORRECTLY trigger e-comm detection
# ================================================================================

FALSE_POSITIVES = [
    # Example: "message queue for batch processing",
    # Example: "call stack trace",
    
]

# ================================================================================
# FALSE NEGATIVES - Add strings that SHOULD trigger e-comm but DON'T
# ================================================================================

FALSE_NEGATIVES = [
    # Example: "proprietary messaging system",
    # Example: "custom notification framework",
    
]

# ================================================================================
# END OF CONFIGURATION
# ================================================================================

import dataiku
import pandas as pd
import numpy as np
import re
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ================================================================================
# TRAINING DATA: E-COMMUNICATION EXAMPLES (DETECT THESE)
# ================================================================================

ECOMM_SENDING_EXAMPLES = [
    "users can send emails through the app",
    "app sends email notifications to users",
    "email delivery capability enabled",
    "transmits emails to users automatically",
    "send order confirmation emails",
    "sends promotional emails to customers",
    "email sending feature available",
    "users send emails within the platform",
    "automatic email sending system",
    "email alerts sent to users",
    "delivers email communications",
    "sends emails on behalf of users",
    "bulk email delivery system",
    "sends welcome emails",
    "sends reminder emails",
    "email notification delivery",
    "outgoing email functionality",
    "users can send texts through the app",
    "app sends SMS alerts to users",
    "text message delivery system",
    "SMS notification system enabled",
    "send appointment reminder texts",
    "text messaging capability",
    "SMS sending feature",
    "sends text notifications",
    "bulk SMS sending",
    "automated text messages",
    "SMS messaging platform",
    "sends promotional texts",
    "users can make video calls",
    "video calling feature enabled",
    "video conferencing capability",
    "video chat between users",
    "voice calling platform enabled",
    "VoIP capability available",
    "make phone calls through app",
    "real-time video calling",
    "voice calls between users",
    "users can send messages",
    "instant messaging capability",
    "chat feature enabled",
    "messaging between users",
    "direct messaging platform",
    "in-app messaging",
    "real-time messaging",
    "users message each other",
    "send direct messages",
    "chat functionality",
    "real-time chat",
    "sends push notifications to users",
    "delivers push notifications",
    "mobile push alerts enabled",
    "push notification system",
    "sends app notifications",
    "notification delivery system",
    "push notification capability",
    "sends mobile alerts",
    "e-communication enabled",
    "e-communications platform",
    "electronic communication capability",
    "digital communication platform",
]

# ================================================================================
# TRAINING DATA: DATA COLLECTION EXAMPLES (REJECT THESE)
# ================================================================================

DATA_COLLECTION_EXAMPLES = [
    "collects email addresses",
    "gathers email from users",
    "stores email addresses in database",
    "email address collection form",
    "captures email for marketing",
    "collects user email",
    "stores email data",
    "saves email in database",
    "retains email address",
    "email records stored",
    "maintains email addresses",
    "email stored in system",
    "keeps email on record",
    "email required for registration",
    "login with email",
    "email as username",
    "sign in with email",
    "register with email",
    "email for authentication",
    "email field in form",
    "email input field",
    "enter email address",
    "email form field",
    "email text box",
    "email entry field",
    "validates email format",
    "verifies email address",
    "email format validation",
    "email validation check",
    "email field in database",
    "email column in table",
    "varchar email field",
    "email database column",
    "plaintext email field",
    "email, phone",
    "phone, email",
    "email, phone, address",
    "name, email, phone",
    "fields: email, phone",
    "collects phone numbers",
    "stores phone numbers",
    "phone number field",
    "SMS verification code",
    "2FA via SMS",
    "one-time password text",
    "SMS OTP code",
    "verification SMS",
]

# ================================================================================
# HARD PATTERNS
# ================================================================================

HARD_DISQUALIFIER_PATTERNS = [
    r'email\s*,\s*phone', r'phone\s*,\s*email',
    r'collects?\s+(?:email|phone)', r'gathers?\s+(?:email|phone)',
    r'stores?\s+(?:email|phone)', r'captures?\s+(?:email|phone)',
    r'login\s+(?:with|using)\s+email', r'sign\s+in\s+(?:with|using)\s+email',
    r'email\s+(?:required|needed)\s+for', r'register\s+(?:with|using)\s+email',
    r'email\s+(?:field|input|textbox)', r'enter\s+(?:your\s+)?email',
    r'(?:varchar|text|string)\s+.*email', r'email\s+(?:column|field)\s+in',
    r'plaintext', r'validates?\s+email', r'verif(?:y|ies)\s+email',
    r'(?:sms|text)\s+verification', r'2fa\s+via', r'otp',
    r'displays?\s+(?:email|phone)', r'email\s+optional',
    r'name\s*,\s*email', r'fields?\s*:\s*email',
]

HARD_QUALIFIER_PATTERNS = [
    r'e[-\s]?communication', r'electronic\s+communication',
    r'(?:can|able\s+to)\s+send\s+(?:email|text|message|sms)',
    r'(?:user|app)s?\s+sends?\s+(?:email|notification|text|sms|alert)',
    r'sends?\s+(?:email|text|sms)\s+(?:notification|alert|message)',
    r'video\s+call(?:ing)?', r'voice\s+call(?:ing)?',
    r'video\s+(?:conferencing|chat)', r'voip',
    r'instant\s+messag', r'real[- ]?time\s+(?:messaging|chat)',
    r'(?:direct|in[- ]?app)\s+messag', r'chat\s+(?:feature|capability|enabled)',
    r'users?\s+(?:can\s+)?message\s+each\s+other',
    r'sends?\s+push\s+notification', r'push\s+notification\s+(?:capability|feature)',
]

COMMUNICATION_KEYWORDS = [
    'email', 'e-mail', 'text', 'sms', 'message', 'messaging',
    'call', 'calling', 'phone', 'video', 'voice', 'chat',
    'notification', 'notify', 'alert', 'push', 'communicat', 'voip',
]

INVALID_IDN_EON = {'nan', 'none', '', 'null', 'n/a', 'na', '-', 'unknown', ' '}

# ================================================================================
# CLASSIFIER
# ================================================================================

class ECommClassifier:
    def __init__(self):
        self.disqualifiers = [re.compile(p, re.IGNORECASE) for p in HARD_DISQUALIFIER_PATTERNS]
        self.qualifiers = [re.compile(p, re.IGNORECASE) for p in HARD_QUALIFIER_PATTERNS]
        self.false_pos = set(x.lower().strip() for x in FALSE_POSITIVES if x.strip())
        self.false_neg = set(x.lower().strip() for x in FALSE_NEGATIVES if x.strip())
        
        # Build TF-IDF
        all_examples = ECOMM_SENDING_EXAMPLES + DATA_COLLECTION_EXAMPLES
        self.vectorizer = TfidfVectorizer(ngram_range=(1,3), max_features=5000, stop_words='english')
        self.vectorizer.fit(all_examples)
        self.ecomm_vectors = self.vectorizer.transform(ECOMM_SENDING_EXAMPLES)
        self.datacoll_vectors = self.vectorizer.transform(DATA_COLLECTION_EXAMPLES)
        self.ecomm_centroid = np.asarray(self.ecomm_vectors.mean(axis=0)).flatten()
        self.datacoll_centroid = np.asarray(self.datacoll_vectors.mean(axis=0)).flatten()
    
    def _cosine(self, v1, v2):
        v1, v2 = np.asarray(v1).flatten(), np.asarray(v2).flatten()
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        return float(np.dot(v1, v2) / (n1 * n2)) if n1 > 0 and n2 > 0 else 0.0
    
    def classify(self, text):
        if not text or len(str(text).strip()) < MIN_TEXT_LENGTH:
            return 0.0
        
        text = str(text).strip()
        text_lower = text.lower()
        
        # Check learned patterns
        if any(fp in text_lower for fp in self.false_pos if fp):
            return 0.0
        if any(fn in text_lower for fn in self.false_neg if fn):
            return 0.95
        
        # Must have keyword
        if not any(kw in text_lower for kw in COMMUNICATION_KEYWORDS):
            return 0.0
        
        # Hard patterns
        for p in self.disqualifiers:
            if p.search(text_lower):
                return 0.0
        for p in self.qualifiers:
            if p.search(text_lower):
                return 0.95
        
        # TF-IDF semantic
        vec = self.vectorizer.transform([text])
        arr = np.asarray(vec.toarray()).flatten()
        
        ecomm_sims = cosine_similarity(vec, self.ecomm_vectors).flatten()
        datacoll_sims = cosine_similarity(vec, self.datacoll_vectors).flatten()
        
        avg_ecomm = (self._cosine(arr, self.ecomm_centroid) + np.max(ecomm_sims) + np.percentile(ecomm_sims, 90)) / 3
        avg_datacoll = (self._cosine(arr, self.datacoll_centroid) + np.max(datacoll_sims) + np.percentile(datacoll_sims, 90)) / 3
        
        total = avg_ecomm + avg_datacoll
        return avg_ecomm / total if total > 0 else 0.5

# ================================================================================
# HELPER FUNCTIONS
# ================================================================================

def find_idn_col(df):
    for col in df.columns:
        if 'IDN_EON' in col.upper().replace(' ','_').replace('-','_'):
            return col
    return None

def is_valid(val):
    if val is None or pd.isna(val):
        return False
    return str(val).strip().lower() not in INVALID_IDN_EON

# ================================================================================
# MAIN EXECUTION
# ================================================================================

print("=" * 60)
print("E-COMMUNICATION CAPABILITY DETECTION")
print("=" * 60)
print(f"Inputs: {INPUT_TABLE_1}, {INPUT_TABLE_2}, {INPUT_TABLE_3}, {INPUT_TABLE_4}")
print(f"Output: {OUTPUT_TABLE}")
print(f"Threshold: {ECOMM_THRESHOLD}")

# Load tables
tables = {}
for name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4]:
    try:
        df = dataiku.Dataset(name).get_dataframe()
        for c in df.columns:
            df[c] = df[c].astype(str)
        tables[name] = df
        print(f"✓ Loaded {name}: {len(df):,} rows")
    except Exception as e:
        print(f"✗ Failed {name}: {e}")

if not tables:
    raise ValueError("No tables loaded!")

# Initialize classifier
print("\nBuilding semantic classifier...")
classifier = ECommClassifier()
print("✓ Classifier ready")

# Step 1: Collect unique IDN_EON and their source tables
print("\n" + "-" * 60)
print("STEP 1: Collecting unique IDN_EON")
print("-" * 60)

idn_sources = defaultdict(set)
for tname, df in tables.items():
    col = find_idn_col(df)
    if not col:
        print(f"  ⚠ {tname}: No IDN_EON column")
        continue
    count = 0
    for v in df[col].dropna().unique():
        if is_valid(v):
            idn_sources[str(v).strip()].add(tname)
            count += 1
    print(f"  ✓ {tname}: {count:,} IDN_EON found")

print(f"\nTotal unique IDN_EON: {len(idn_sources):,}")

# Step 2: Find e-comm strings for each IDN_EON
print("\n" + "-" * 60)
print("STEP 2: Finding e-communication strings")
print("-" * 60)

results = []
total = len(idn_sources)
ecomm_count = 0

for idx, (idn_eon, sources) in enumerate(idn_sources.items()):
    if (idx + 1) % 500 == 0 or (idx + 1) == total:
        print(f"  Progress: {idx+1:,}/{total:,} | E-comm found: {ecomm_count:,}")
    
    ecomm_strings = []  # List of (string, table.column)
    
    # Search all tables for this IDN_EON
    for tname, df in tables.items():
        col = find_idn_col(df)
        if not col:
            continue
        rows = df[df[col].astype(str).str.strip() == idn_eon]
        if rows.empty:
            continue
        
        # Check each column
        for c in df.columns:
            if c == col:
                continue
            for _, val in rows[c].items():
                txt = str(val).strip() if val else ""
                if len(txt) < MIN_TEXT_LENGTH:
                    continue
                
                confidence = classifier.classify(txt)
                if confidence > ECOMM_THRESHOLD:
                    ecomm_strings.append((txt, f"{tname}.{c}"))
    
    # Add to results
    if ecomm_strings:
        ecomm_count += 1
        # Combine all e-comm strings and their locations
        strings = ' | '.join([s[0] for s in ecomm_strings])
        locations = ' | '.join([s[1] for s in ecomm_strings])
    else:
        strings = ''
        locations = ''
    
    results.append({
        'IDN_EON': idn_eon,
        'source_tables': ', '.join(sorted(sources)),
        'ecomm_string': strings,
        'string_location': locations,
    })

# Create output
output_df = pd.DataFrame(results)

# Sort: those with e-comm strings first
output_df['has_ecomm'] = output_df['ecomm_string'].apply(lambda x: 1 if x else 0)
output_df = output_df.sort_values('has_ecomm', ascending=False).drop(columns=['has_ecomm'])
output_df = output_df.reset_index(drop=True)

# Summary
print("\n" + "-" * 60)
print("SUMMARY")
print("-" * 60)
has_ecomm = (output_df['ecomm_string'] != '').sum()
print(f"Total IDN_EON: {len(output_df):,}")
print(f"With e-comm capability: {has_ecomm:,}")
print(f"Without e-comm: {len(output_df) - has_ecomm:,}")

# Write output
print("\n" + "-" * 60)
print("WRITING OUTPUT")
print("-" * 60)
dataiku.Dataset(OUTPUT_TABLE).write_with_schema(output_df)
print(f"✓ Wrote {len(output_df):,} rows to {OUTPUT_TABLE}")

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
