# -*- coding: utf-8 -*-
"""
================================================================================
E-COMMUNICATION CAPABILITY DETECTION - DATAIKU PYTHON RECIPE
================================================================================

SETUP:
    1. Create a Python Recipe in Dataiku
    2. Add the 4 input datasets listed below
    3. Add the 1 output dataset listed below
    4. Paste this script and run

SEMANTIC UNDERSTANDING:
    Uses TF-IDF vectorization with scikit-learn (always available in Dataiku)
    to semantically compare text against 100+ training examples

VERSION: 7.0.0
================================================================================
"""

import dataiku
import pandas as pd
import numpy as np
import re
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ================================================================================
# INPUT AND OUTPUT CONFIGURATION - MODIFY THESE TO MATCH YOUR DATASETS
# ================================================================================

# Input dataset names (must match exactly what's in your Dataiku project)
INPUT_TABLES = [
    'table1',   # First input table
    'table2',   # Second input table  
    'table3',   # Third input table
    'table4',   # Fourth input table
]

# Output dataset name
OUTPUT_TABLE = 'ecomm_detection_results'

# ================================================================================
# DETECTION SETTINGS
# ================================================================================

# Classification threshold (0.0 to 1.0) - Lower = more lenient, Higher = stricter
ECOMM_THRESHOLD = 0.55

# Minimum text length to analyze
MIN_TEXT_LENGTH = 5

# Maximum evidence samples to store per IDN_EON
MAX_EVIDENCE_SAMPLES = 3

# Invalid IDN_EON values to skip
INVALID_IDN_EON_VALUES = {
    'nan', 'none', '', 'null', 'n/a', 'na', 'n.a.', 
    '-', '--', 'unknown', ' ', 'undefined', '#n/a', '#null', '<na>'
}

# ================================================================================
# FALSE POSITIVES - ADD STRINGS THAT INCORRECTLY TRIGGER DETECTION
# When you find text being wrongly flagged as e-comm, add it here
# ================================================================================

FALSE_POSITIVES = [
    # --- ADD YOUR FALSE POSITIVES BELOW THIS LINE ---
    
    # Example: "message queue for batch processing",
    # Example: "call stack trace",
    # Example: "email field varchar",
    
    # --- ADD YOUR FALSE POSITIVES ABOVE THIS LINE ---
]

# ================================================================================
# FALSE NEGATIVES - ADD STRINGS THAT SHOULD TRIGGER BUT DON'T
# When you find text that should be flagged as e-comm but isn't, add it here
# ================================================================================

FALSE_NEGATIVES = [
    # --- ADD YOUR FALSE NEGATIVES BELOW THIS LINE ---
    
    # Example: "proprietary messaging system",
    # Example: "custom notification framework",
    
    # --- ADD YOUR FALSE NEGATIVES ABOVE THIS LINE ---
]

# ================================================================================
# TRAINING DATA: E-COMMUNICATION SENDING EXAMPLES
# Text that indicates the app CAN SEND communications (what we DETECT)
# ================================================================================

ECOMM_SENDING_EXAMPLES = [
    # Email sending
    "users can send emails through the app",
    "app sends email notifications to users",
    "email delivery capability enabled",
    "transmits emails to users automatically",
    "email messaging platform for users",
    "send order confirmation emails",
    "sends promotional emails to customers",
    "email sending feature available",
    "users send emails within the platform",
    "application delivers emails",
    "email dispatch functionality",
    "automatic email sending system",
    "email transmission service",
    "send transactional emails",
    "email alerts sent to users",
    "delivers email communications",
    "email outbound capability",
    "sends emails on behalf of users",
    "email broadcast feature",
    "mass email sending capability",
    "bulk email delivery system",
    "email campaign sending",
    "automated email sender",
    "sends welcome emails",
    "sends reminder emails",
    "email notification delivery",
    "users can compose and send emails",
    "in-app email sending",
    "email messaging enabled",
    "sends password reset emails",
    "outgoing email functionality",
    
    # SMS/Text sending
    "users can send texts through the app",
    "app sends SMS alerts to users",
    "text message delivery system",
    "SMS notification system enabled",
    "send appointment reminder texts",
    "text messaging capability",
    "SMS sending feature",
    "sends text notifications",
    "text message alerts",
    "SMS delivery platform",
    "users send text messages",
    "mobile text messaging",
    "SMS communication enabled",
    "text sending functionality",
    "sends SMS reminders",
    "text alert system",
    "SMS broadcast capability",
    "bulk SMS sending",
    "automated text messages",
    "SMS outbound service",
    "text message transmission",
    "sends texts automatically",
    "SMS messaging platform",
    "text notification delivery",
    "sends promotional texts",
    
    # Video calling
    "users can make video calls",
    "video calling feature enabled",
    "video conferencing capability",
    "video chat between users",
    "video call functionality",
    "supports video calling",
    "video communication platform",
    "make video calls in app",
    "video calling service",
    "video chat capability",
    "real-time video calling",
    "video calls between users",
    "video meeting capability",
    "group video calling",
    "video calling enabled",
    
    # Voice calling
    "users can make voice calls",
    "voice calling platform enabled",
    "VoIP capability available",
    "phone call feature in app",
    "voice communication enabled",
    "voice call functionality",
    "make phone calls through app",
    "voice calling service",
    "VoIP calling feature",
    "internet calling enabled",
    "voice calls between users",
    "audio calling capability",
    "voice calling enabled",
    "telephone capability",
    "call users directly",
    
    # Instant messaging
    "users can send messages",
    "instant messaging capability",
    "chat feature enabled",
    "messaging between users",
    "direct messaging platform",
    "in-app messaging",
    "real-time messaging",
    "instant chat feature",
    "message sending capability",
    "users message each other",
    "chat functionality",
    "messaging system enabled",
    "send direct messages",
    "chat platform",
    "messaging service",
    "user-to-user messaging",
    "send chat messages",
    "messaging feature available",
    "chat capability",
    "messaging enabled",
    "real-time chat",
    "messaging platform",
    
    # Push notifications
    "sends push notifications to users",
    "delivers push notifications",
    "mobile push alerts enabled",
    "push notification system",
    "push message delivery",
    "sends app notifications",
    "push alerts to users",
    "notification delivery system",
    "mobile notifications enabled",
    "push notification capability",
    "sends mobile alerts",
    "app push notifications",
    "real-time push alerts",
    "push notification feature",
    "notification sending feature",
    "push notifications enabled",
    
    # E-communications explicit
    "e-communication enabled",
    "e-communications platform",
    "e-communication services",
    "electronic communication capability",
    "e-communication feature",
    "e-communication system",
    "digital communication platform",
    
    # General communication sending
    "sends alerts to users",
    "notification sending capability",
    "delivers communications",
    "communication platform enabled",
    "alert delivery system",
    "sends user notifications",
    "communication capability enabled",
]

# ================================================================================
# TRAINING DATA: DATA COLLECTION EXAMPLES  
# Text that indicates the app only COLLECTS/STORES data (what we REJECT)
# ================================================================================

DATA_COLLECTION_EXAMPLES = [
    # Email collection
    "collects email addresses",
    "gathers email from users",
    "stores email addresses in database",
    "email address collection form",
    "captures email for marketing",
    "email captured during signup",
    "collects user email",
    "email collection field",
    "gathers email addresses",
    "stores email data",
    "collects emails for records",
    "email data collection",
    "captures user email address",
    "gathers customer emails",
    "stores user email addresses",
    "collects contact email",
    
    # Storage
    "saves email in database",
    "email on file for records",
    "retains email address",
    "email records stored",
    "maintains email addresses",
    "email stored in system",
    "stores email permanently",
    "email saved for reference",
    "keeps email on record",
    "email archived in database",
    "email data preserved",
    "email address retained",
    
    # Registration/Login
    "email required for registration",
    "email for account creation",
    "login with email",
    "email as username",
    "sign in with email",
    "email needed for signup",
    "register with email",
    "email login required",
    "email for authentication",
    "sign up using email",
    "email address for login",
    "login using email address",
    "email-based login",
    "email required to register",
    
    # Forms and input
    "email field in form",
    "email input field",
    "enter email address",
    "provide email in form",
    "email form field",
    "email text box",
    "input email address",
    "email entry field",
    "fill in email",
    "email input required",
    "email address input",
    "type email address",
    "email field required",
    "enter your email",
    
    # Validation
    "validates email format",
    "verifies email address",
    "checks email syntax",
    "email format validation",
    "email validation check",
    "verify email format",
    "validates user email",
    "email address verification",
    "check email format",
    
    # Database/Technical
    "email field in database",
    "email column in table",
    "email data type",
    "email table column",
    "plaintext email field",
    "text field for email",
    "text column email",
    "varchar email field",
    "email database column",
    "string field email",
    "email varchar column",
    "email stored as text",
    "plaintext email storage",
    
    # List format (strong indicator of collection)
    "email, phone",
    "phone, email",
    "email and phone number",
    "email, phone, address",
    "fields: email, phone",
    "email phone address",
    "contact: email, phone",
    "email, phone collected",
    "stores email, phone",
    "name, email, phone",
    "email phone fields",
    "email, telephone",
    "email, phone required",
    
    # Phone collection
    "collects phone numbers",
    "stores phone numbers",
    "gathers mobile numbers",
    "phone number field",
    "phone number collected",
    "stores mobile numbers",
    "phone field in form",
    "mobile number field",
    "phone number input",
    
    # Profile/Display only
    "email in user profile",
    "profile contains email",
    "account email address",
    "displays email address",
    "shows email to user",
    "email visible in profile",
    "email shown on screen",
    "displays user email",
    
    # 2FA/Verification only (not real messaging)
    "SMS verification code",
    "text verification code",
    "2FA via SMS",
    "one-time password text",
    "SMS OTP code",
    "text-based 2FA",
    "verification SMS",
    "SMS authentication code",
    "verification code text",
    "SMS 2FA code",
    
    # Non-communication text types
    "Japanese text",
    "Chinese text",
    "Korean text",
    "unicode text",
    "rich text field",
    "plain text format",
    "text encoding",
    "multiline text",
    "email optional",
    "email not required",
]

# ================================================================================
# HARD PATTERN MATCHING - AUTOMATIC CLASSIFICATION
# ================================================================================

# Patterns that automatically REJECT (confidence = 0)
HARD_DISQUALIFIER_PATTERNS = [
    # List format
    r'email\s*,\s*phone', r'phone\s*,\s*email',
    r'email\s*,\s*(?:phone|mobile|address|fax)',
    r'(?:phone|mobile)\s*,\s*email',
    r'name\s*,\s*email', r'fields?\s*:\s*email',
    r'contact\s*:\s*email',
    
    # Collection verbs
    r'collects?\s+(?:email|phone|contact)',
    r'gathers?\s+(?:email|phone|contact)',
    r'stores?\s+(?:email|phone|contact)',
    r'captures?\s+(?:email|phone)',
    r'saves?\s+(?:email|phone)',
    
    # Login/Registration
    r'email\s+(?:for|as)\s+(?:login|username|authentication)',
    r'login\s+(?:with|using)\s+email',
    r'sign\s+in\s+(?:with|using)\s+email',
    r'email\s+(?:required|needed)\s+(?:for|to)\s+(?:register|signup)',
    r'(?:register|signup)\s+(?:with|using)\s+email',
    
    # Form fields
    r'email\s+(?:field|input|textbox|entry)',
    r'(?:field|input)\s+(?:for\s+)?email',
    r'enter\s+(?:your\s+)?email',
    r'provide\s+(?:your\s+)?email',
    
    # Database/Technical
    r'email\s+(?:column|field)\s+(?:in\s+)?(?:database|table|db)',
    r'(?:varchar|text|string)\s+(?:field\s+)?(?:for\s+)?email',
    r'plaintext',
    r'(?:stored|saved)\s+as\s+text',
    
    # Validation
    r'validates?\s+email', r'verif(?:y|ies)\s+email',
    r'(?:email|phone)\s+validation',
    
    # 2FA only
    r'(?:sms|text)\s+verification',
    r'2fa\s+(?:via|through)\s+(?:sms|text)',
    r'(?:otp|one[- ]?time\s+password)',
    r'verification\s+(?:code|token)',
    
    # Display only
    r'displays?\s+(?:email|phone)',
    r'shows?\s+(?:email|phone)',
    r'(?:email|phone)\s+(?:visible|shown|displayed)',
    
    # Non-English text
    r'japanese\s+text', r'chinese\s+text', r'korean\s+text',
    
    # Optional
    r'email\s+(?:is\s+)?optional',
    r'email\s+(?:can\s+be|may\s+be)\s+(?:blank|empty)',
]

# Patterns that automatically ACCEPT (confidence = 0.95)
HARD_QUALIFIER_PATTERNS = [
    # Explicit e-communication
    r'e[-\s]?communication(?:s)?',
    r'electronic\s+communication(?:s)?',
    
    # Sending emails
    r'(?:can|able\s+to)\s+send\s+email',
    r'(?:user|app|system)s?\s+sends?\s+email',
    r'sends?\s+(?:email|e-mail)\s+(?:notification|alert|message)s?',
    r'email\s+(?:sending|delivery)\s+(?:capability|feature|system)',
    r'(?:outbound|outgoing)\s+email',
    r'delivers?\s+email',
    
    # Sending SMS/Text
    r'(?:can|able\s+to)\s+send\s+(?:sms|text)',
    r'(?:user|app|system)s?\s+sends?\s+(?:sms|text)',
    r'sends?\s+(?:sms|text)\s+(?:notification|alert|message)s?',
    r'(?:sms|text)\s+(?:sending|delivery)\s+(?:capability|feature)',
    r'(?:sms|text)\s+messaging\s+(?:capability|feature|enabled)',
    
    # Video/Voice calling
    r'video\s+call(?:ing)?',
    r'voice\s+call(?:ing)?',
    r'(?:can|able\s+to)\s+(?:make|place)\s+(?:video|voice|phone)\s+calls?',
    r'video\s+(?:conferencing|conference|chat)',
    r'voip\s+(?:capability|calling|feature)',
    
    # Instant messaging
    r'instant\s+messag(?:ing|e)',
    r'(?:real[- ]?time|live)\s+(?:messaging|chat)',
    r'(?:direct|in[- ]?app)\s+messag(?:ing|e)',
    r'chat\s+(?:capability|feature|enabled|platform)',
    r'(?:user|users)\s+(?:can\s+)?(?:message|chat)\s+each\s+other',
    r'messag(?:ing|e)\s+(?:capability|feature|enabled|platform)',
    
    # Push notifications
    r'sends?\s+push\s+notification',
    r'delivers?\s+push\s+notification',
    r'push\s+notification\s+(?:capability|feature|system)',
    r'(?:mobile|app)\s+notification(?:s)?\s+(?:enabled|sent)',
    
    # General sending
    r'sends?\s+(?:alert|notification)s?\s+to\s+users?',
    r'delivers?\s+(?:alert|notification)s?\s+to\s+users?',
    r'notification\s+(?:sending|delivery)\s+(?:capability|feature)',
]

# Keywords that must be present for analysis
COMMUNICATION_KEYWORDS = [
    'email', 'e-mail', 'mail', 'text', 'sms', 'mms',
    'message', 'messaging', 'msg', 'call', 'calling', 'phone',
    'video', 'voice', 'audio', 'chat', 'notification', 'notify',
    'alert', 'push', 'communicat', 'voip', 'telephon',
]

# ================================================================================
# CLASSIFIER CLASS
# ================================================================================

class ECommClassifier:
    """TF-IDF based semantic classifier for e-communication detection."""
    
    def __init__(self):
        print("\n" + "=" * 60)
        print("INITIALIZING SEMANTIC CLASSIFIER")
        print("=" * 60)
        
        # Compile regex patterns
        self.disqualifier_patterns = [
            re.compile(p, re.IGNORECASE) for p in HARD_DISQUALIFIER_PATTERNS
        ]
        self.qualifier_patterns = [
            re.compile(p, re.IGNORECASE) for p in HARD_QUALIFIER_PATTERNS
        ]
        
        # Normalize false positives/negatives
        self.false_positives = set(
            fp.lower().strip() for fp in FALSE_POSITIVES if fp and fp.strip()
        )
        self.false_negatives = set(
            fn.lower().strip() for fn in FALSE_NEGATIVES if fn and fn.strip()
        )
        
        # Build TF-IDF model
        self._build_tfidf_model()
        
        print(f"\nClassifier ready:")
        print(f"  - {len(self.disqualifier_patterns)} disqualifier patterns")
        print(f"  - {len(self.qualifier_patterns)} qualifier patterns")
        print(f"  - {len(self.false_positives)} learned false positives")
        print(f"  - {len(self.false_negatives)} learned false negatives")
        print(f"  - TF-IDF vocabulary: {len(self.vectorizer.vocabulary_)} terms")
    
    def _build_tfidf_model(self):
        """Build TF-IDF model from training examples."""
        print("Building TF-IDF semantic model...")
        
        all_examples = ECOMM_SENDING_EXAMPLES + DATA_COLLECTION_EXAMPLES
        
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            stop_words='english',
            min_df=1,
            sublinear_tf=True
        )
        self.vectorizer.fit(all_examples)
        
        # Pre-compute vectors for training examples
        self.ecomm_vectors = self.vectorizer.transform(ECOMM_SENDING_EXAMPLES)
        self.datacoll_vectors = self.vectorizer.transform(DATA_COLLECTION_EXAMPLES)
        
        # Compute centroids
        self.ecomm_centroid = np.asarray(self.ecomm_vectors.mean(axis=0)).flatten()
        self.datacoll_centroid = np.asarray(self.datacoll_vectors.mean(axis=0)).flatten()
        
        print(f"  ✓ Trained on {len(ECOMM_SENDING_EXAMPLES)} e-comm examples")
        print(f"  ✓ Trained on {len(DATA_COLLECTION_EXAMPLES)} data-collection examples")
    
    def _cosine_sim(self, vec1, vec2):
        """Compute cosine similarity."""
        vec1 = np.asarray(vec1).flatten()
        vec2 = np.asarray(vec2).flatten()
        norm1, norm2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def _has_comm_keyword(self, text: str) -> bool:
        """Check if text contains communication keywords."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in COMMUNICATION_KEYWORDS)
    
    def _is_false_positive(self, text: str) -> bool:
        """Check if text matches a learned false positive."""
        text_lower = text.lower().strip()
        if text_lower in self.false_positives:
            return True
        return any(fp in text_lower for fp in self.false_positives if fp)
    
    def _is_false_negative(self, text: str) -> bool:
        """Check if text matches a learned false negative."""
        text_lower = text.lower().strip()
        if text_lower in self.false_negatives:
            return True
        return any(fn in text_lower for fn in self.false_negatives if fn)
    
    def _semantic_score(self, text: str) -> float:
        """Calculate semantic similarity score using TF-IDF."""
        text_vec = self.vectorizer.transform([text])
        text_arr = np.asarray(text_vec.toarray()).flatten()
        
        # Centroid similarities
        ecomm_centroid_sim = self._cosine_sim(text_arr, self.ecomm_centroid)
        datacoll_centroid_sim = self._cosine_sim(text_arr, self.datacoll_centroid)
        
        # Max similarity to individual examples
        ecomm_sims = cosine_similarity(text_vec, self.ecomm_vectors).flatten()
        datacoll_sims = cosine_similarity(text_vec, self.datacoll_vectors).flatten()
        
        ecomm_max = np.max(ecomm_sims) if len(ecomm_sims) > 0 else 0
        datacoll_max = np.max(datacoll_sims) if len(datacoll_sims) > 0 else 0
        
        # 90th percentile similarity
        ecomm_p90 = np.percentile(ecomm_sims, 90) if len(ecomm_sims) > 0 else 0
        datacoll_p90 = np.percentile(datacoll_sims, 90) if len(datacoll_sims) > 0 else 0
        
        # Combined score (average of three metrics)
        avg_ecomm = (ecomm_centroid_sim + ecomm_max + ecomm_p90) / 3
        avg_datacoll = (datacoll_centroid_sim + datacoll_max + datacoll_p90) / 3
        
        total = avg_ecomm + avg_datacoll
        if total == 0:
            return 0.5
        
        return avg_ecomm / total
    
    def classify(self, text: str) -> tuple:
        """
        Classify text for e-communication capability.
        
        Returns:
            (confidence: float, method: str)
        """
        if not text or not isinstance(text, str):
            return (0.0, "invalid_input")
        
        text = str(text).strip()
        if len(text) < MIN_TEXT_LENGTH:
            return (0.0, "text_too_short")
        
        text_lower = text.lower()
        
        # 1. Check learned false negatives first (force flag)
        if self._is_false_negative(text):
            return (0.95, "learned_false_negative")
        
        # 2. Check learned false positives (force reject)
        if self._is_false_positive(text):
            return (0.0, "learned_false_positive")
        
        # 3. Must contain communication keyword
        if not self._has_comm_keyword(text):
            return (0.0, "no_comm_keyword")
        
        # 4. Check hard disqualifiers
        for pattern in self.disqualifier_patterns:
            if pattern.search(text_lower):
                return (0.0, "hard_disqualifier")
        
        # 5. Check hard qualifiers
        for pattern in self.qualifier_patterns:
            if pattern.search(text_lower):
                return (0.95, "hard_qualifier")
        
        # 6. Semantic classification with TF-IDF
        confidence = self._semantic_score(text)
        return (confidence, "tfidf_semantic")


# ================================================================================
# HELPER FUNCTIONS
# ================================================================================

def find_idn_eon_column(df):
    """Find the IDN_EON column (case-insensitive)."""
    for col in df.columns:
        col_upper = col.upper().replace(' ', '_').replace('-', '_')
        if col_upper == 'IDN_EON' or 'IDN_EON' in col_upper:
            return col
    return None


def is_valid_idn_eon(value):
    """Check if IDN_EON value is valid."""
    if value is None or pd.isna(value):
        return False
    str_val = str(value).strip().lower()
    return str_val not in INVALID_IDN_EON_VALUES and len(str_val) > 0


def clean_text(value):
    """Clean and convert value to string."""
    if value is None or pd.isna(value):
        return ""
    try:
        text = str(value).strip()
        return re.sub(r'\s+', ' ', text)
    except:
        return ""


# ================================================================================
# MAIN PROCESSING
# ================================================================================

print("\n" + "=" * 60)
print("E-COMMUNICATION CAPABILITY DETECTION")
print("=" * 60)
print(f"Input tables: {INPUT_TABLES}")
print(f"Output table: {OUTPUT_TABLE}")
print(f"Threshold: {ECOMM_THRESHOLD}")

# ----------------------------------------
# LOAD INPUT DATASETS
# ----------------------------------------
print("\n" + "-" * 60)
print("LOADING INPUT DATASETS")
print("-" * 60)

input_datasets = {}
for table_name in INPUT_TABLES:
    print(f"\nLoading '{table_name}'...")
    try:
        ds = dataiku.Dataset(table_name)
        df = ds.get_dataframe()
        # Convert all to string
        for col in df.columns:
            df[col] = df[col].astype(str)
        input_datasets[table_name] = df
        print(f"  ✓ {len(df):,} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"  ✗ Failed to load: {e}")

if not input_datasets:
    raise ValueError("No input datasets could be loaded!")

# ----------------------------------------
# INITIALIZE CLASSIFIER
# ----------------------------------------
classifier = ECommClassifier()

# ----------------------------------------
# STEP 1: COLLECT UNIQUE IDN_EON AND SOURCE TABLES
# ----------------------------------------
print("\n" + "-" * 60)
print("STEP 1: COLLECTING UNIQUE IDN_EON VALUES")
print("-" * 60)

idn_eon_sources = defaultdict(set)

for table_name, df in input_datasets.items():
    idn_col = find_idn_eon_column(df)
    
    if idn_col is None:
        print(f"\n  ⚠ '{table_name}': No IDN_EON column found - SKIPPING")
        continue
    
    valid_count = 0
    for value in df[idn_col].dropna().unique():
        if is_valid_idn_eon(value):
            clean_val = str(value).strip()
            idn_eon_sources[clean_val].add(table_name)
            valid_count += 1
    
    print(f"\n  ✓ '{table_name}':")
    print(f"      Column: {idn_col}")
    print(f"      Valid IDN_EON: {valid_count:,}")

# Build initial dataframe
idn_eon_list = []
for idn_eon, sources in idn_eon_sources.items():
    idn_eon_list.append({
        'IDN_EON': idn_eon,
        'source_tables': ', '.join(sorted(sources))
    })

print(f"\n  TOTAL UNIQUE IDN_EON: {len(idn_eon_list):,}")

# ----------------------------------------
# STEP 2: ANALYZE E-COMMUNICATION CAPABILITIES
# ----------------------------------------
print("\n" + "-" * 60)
print("STEP 2: ANALYZING E-COMMUNICATION CAPABILITIES")
print("-" * 60)

results = []
total = len(idn_eon_list)
ecomm_count = 0

for idx, item in enumerate(idn_eon_list):
    idn_eon = item['IDN_EON']
    source_tables = item['source_tables']
    
    # Progress
    if (idx + 1) % 500 == 0 or (idx + 1) == total:
        pct = (idx + 1) * 100 / total
        print(f"  Progress: {idx+1:,}/{total:,} ({pct:.1f}%) | E-comm found: {ecomm_count:,}")
    
    best_confidence = 0.0
    best_method = "no_evidence"
    evidence_samples = []
    evidence_locations = set()
    
    # Loop through each table to find this IDN_EON
    for table_name, df in input_datasets.items():
        idn_col = find_idn_eon_column(df)
        if idn_col is None:
            continue
        
        # Find matching rows
        mask = df[idn_col].astype(str).str.strip() == idn_eon
        matching_rows = df[mask]
        
        if matching_rows.empty:
            continue
        
        # Analyze each column
        for col in df.columns:
            if col == idn_col:
                continue
            
            for _, cell_value in matching_rows[col].items():
                text = clean_text(cell_value)
                
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                
                # Classify this text
                confidence, method = classifier.classify(text)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_method = method
                
                # Collect evidence if above threshold
                if confidence > ECOMM_THRESHOLD:
                    evidence_locations.add(f"{table_name}.{col}")
                    if len(evidence_samples) < MAX_EVIDENCE_SAMPLES:
                        evidence_samples.append(text[:200])
    
    # Determine final classification
    has_ecomm = best_confidence > ECOMM_THRESHOLD
    if has_ecomm:
        ecomm_count += 1
    
    results.append({
        'IDN_EON': idn_eon,
        'source_tables': source_tables,
        'has_ecomm_capability': 'YES' if has_ecomm else 'NO',
        'ecomm_confidence': round(best_confidence, 4),
        'ecomm_evidence': ' | '.join(evidence_samples) if evidence_samples else '',
        'detection_details': ', '.join(sorted(evidence_locations)) if evidence_locations else best_method,
    })

# Create output dataframe
output_df = pd.DataFrame(results)

# Sort: YES first, then by confidence descending
output_df = output_df.sort_values(
    ['has_ecomm_capability', 'ecomm_confidence'],
    ascending=[False, False]
).reset_index(drop=True)

# ----------------------------------------
# SUMMARY
# ----------------------------------------
print("\n" + "-" * 60)
print("SUMMARY")
print("-" * 60)

total_idn = len(output_df)
yes_count = (output_df['has_ecomm_capability'] == 'YES').sum()
no_count = total_idn - yes_count

print(f"\n  Total unique IDN_EON: {total_idn:,}")
print(f"  E-comm capability YES: {yes_count:,} ({yes_count*100/total_idn:.1f}%)" if total_idn > 0 else "  E-comm capability YES: 0")
print(f"  E-comm capability NO:  {no_count:,} ({no_count*100/total_idn:.1f}%)" if total_idn > 0 else "  E-comm capability NO: 0")

if yes_count > 0:
    print(f"\n  Top 10 E-Comm Capable IDN_EON:")
    top_ecomm = output_df[output_df['has_ecomm_capability'] == 'YES'].head(10)
    for _, row in top_ecomm.iterrows():
        print(f"    • {row['IDN_EON']}")
        print(f"      Confidence: {row['ecomm_confidence']:.3f} | Sources: {row['source_tables']}")

# ----------------------------------------
# WRITE OUTPUT
# ----------------------------------------
print("\n" + "-" * 60)
print("WRITING OUTPUT")
print("-" * 60)

output_ds = dataiku.Dataset(OUTPUT_TABLE)
output_ds.write_with_schema(output_df)

print(f"\n  ✓ Wrote {len(output_df):,} rows to '{OUTPUT_TABLE}'")

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
