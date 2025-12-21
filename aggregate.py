"""
INTELLIGENT E-COMMUNICATION DETECTOR v2.0
==========================================
Key improvements:
1. Linguistic verb-based classification (transmission vs storage verbs)
2. Subject-object awareness (WHO is sending TO WHOM)
3. Contrastive semantic classification 
4. Multi-signal voting system
5. Context-aware negation handling
"""

import dataiku
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

print("="*80)
print("INTELLIGENT E-COMMUNICATION DETECTOR v2.0")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================
CONFIDENCE_THRESHOLD = 0.6
MIN_FINDINGS_REQUIRED = 1

print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
print(f"Min Findings Required: {MIN_FINDINGS_REQUIRED}")

input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# ============================================================================
# LINGUISTIC KNOWLEDGE BASE
# ============================================================================

# Verbs that indicate TRANSMISSION (sending out)
TRANSMISSION_VERBS = {
    'send', 'sends', 'sending', 'sent',
    'deliver', 'delivers', 'delivering', 'delivered',
    'transmit', 'transmits', 'transmitting', 'transmitted',
    'dispatch', 'dispatches', 'dispatching', 'dispatched',
    'push', 'pushes', 'pushing', 'pushed',
    'broadcast', 'broadcasts', 'broadcasting',
    'notify', 'notifies', 'notifying', 'notified',
    'alert', 'alerts', 'alerting', 'alerted',
    'email', 'emails', 'emailing', 'emailed',  # as verb
    'text', 'texts', 'texting', 'texted',  # as verb
    'message', 'messages', 'messaging', 'messaged',  # as verb
    'call', 'calls', 'calling', 'called',
    'contact', 'contacts', 'contacting', 'contacted',
    'reach', 'reaches', 'reaching', 'reached',
    'communicate', 'communicates', 'communicating',
    'post', 'posts', 'posting', 'posted',
    'share', 'shares', 'sharing', 'shared',
    'forward', 'forwards', 'forwarding', 'forwarded',
    'relay', 'relays', 'relaying', 'relayed',
    'issue', 'issues', 'issuing', 'issued',
    'distribute', 'distributes', 'distributing', 'distributed',
}

# Verbs that indicate COLLECTION/STORAGE (not sending)
COLLECTION_VERBS = {
    'collect', 'collects', 'collecting', 'collected',
    'store', 'stores', 'storing', 'stored',
    'save', 'saves', 'saving', 'saved',
    'keep', 'keeps', 'keeping', 'kept',
    'retain', 'retains', 'retaining', 'retained',
    'maintain', 'maintains', 'maintaining', 'maintained',
    'record', 'records', 'recording', 'recorded',
    'log', 'logs', 'logging', 'logged',
    'capture', 'captures', 'capturing', 'captured',
    'gather', 'gathers', 'gathering', 'gathered',
    'obtain', 'obtains', 'obtaining', 'obtained',
    'acquire', 'acquires', 'acquiring', 'acquired',
    'request', 'requests', 'requesting', 'requested',
    'require', 'requires', 'requiring', 'required',
    'need', 'needs', 'needing', 'needed',
    'ask', 'asks', 'asking', 'asked',
    'input', 'inputs', 'inputting',
    'enter', 'enters', 'entering', 'entered',
    'provide', 'provides', 'providing', 'provided',
    'submit', 'submits', 'submitting', 'submitted',
    'register', 'registers', 'registering', 'registered',
    'archive', 'archives', 'archiving', 'archived',
    'backup', 'backups', 'backing',
    'hold', 'holds', 'holding', 'held',
    'contain', 'contains', 'containing', 'contained',
    'include', 'includes', 'including', 'included',
    'have', 'has', 'having', 'had',
    'display', 'displays', 'displaying', 'displayed',
    'show', 'shows', 'showing', 'shown',
    'validate', 'validates', 'validating', 'validated',
    'verify', 'verifies', 'verifying', 'verified',
    'check', 'checks', 'checking', 'checked',
    'update', 'updates', 'updating', 'updated',
    'modify', 'modifies', 'modifying', 'modified',
    'edit', 'edits', 'editing', 'edited',
    'change', 'changes', 'changing', 'changed',
}

# E-communication channels/objects
ECOMM_OBJECTS = {
    'email', 'emails', 'e-mail', 'e-mails',
    'text', 'texts', 'sms', 'mms',
    'message', 'messages', 'msg', 'msgs',
    'notification', 'notifications',
    'alert', 'alerts',
    'push notification', 'push notifications',
    'call', 'calls',
    'video call', 'video calls', 'video chat', 'video chats',
    'voice call', 'voice calls',
    'chat', 'chats', 'im', 'instant message', 'instant messages',
}

# Recipients that indicate outbound communication
RECIPIENT_INDICATORS = {
    'to user', 'to users', 'to customer', 'to customers',
    'to subscriber', 'to subscribers', 'to member', 'to members',
    'to recipient', 'to recipients', 'to contact', 'to contacts',
    'to client', 'to clients', 'to patient', 'to patients',
    'to device', 'to devices', 'to phone', 'to phones',
    'to inbox', 'to inboxes',
}

# Data field indicators (strong signal for collection, not sending)
DATA_FIELD_PATTERNS = [
    r'\bemail\s*,\s*phone\b',
    r'\bphone\s*,\s*email\b',
    r'\bemail\s*,\s*address\b',
    r'\bname\s*,\s*email\b',
    r'\bemail\s*,\s*name\b',
    r'\bemail\s+address\s+field\b',
    r'\bemail\s+field\b',
    r'\bphone\s+field\b',
    r'\brequired\s*:\s*email\b',
    r'\bemail\s+required\b',
    r'\bemail\s+for\s+(registration|login|signin|account|authentication)\b',
    r'\buser\s+provides?\s+email\b',
    r'\bcollects?\s+(user\s+)?email\b',
    r'\bstores?\s+(user\s+)?email\b',
    r'\bemail\s+in\s+(database|profile|account|record)\b',
    r'\bemail\s+data\s+type\b',
    r'\bemail\s+column\b',
    r'\bplaintext\b',
    r'\btext\s+field\b',
    r'\btext\s+column\b',
    r'\bdata\s*:\s*email\b',
    r'\bfields?\s*:\s*email\b',
    r'\b(japanese|chinese|korean|arabic)\s+text\b',
]

# Strong e-comm sending patterns
ECOMM_SENDING_PATTERNS = [
    r'\b(can|will|may|could|should)\s+send\s+(email|text|sms|message|notification)s?\b',
    r'\b(send|deliver|transmit|dispatch)s?\s+(email|text|sms|message|notification)s?\s+(to|for)\b',
    r'\b(email|text|sms|message|notification)s?\s+(are\s+)?(sent|delivered|transmitted|dispatched)\s+to\b',
    r'\bsends?\s+push\s+notification\b',
    r'\bpush\s+notifications?\s+(to|for)\s+(user|customer|device)\b',
    r'\b(app|application|system|platform|service)\s+(send|deliver|transmit)s?\s+(email|text|sms|message|notification)s?\b',
    r'\be-?communication\s+(capability|feature|platform|service)\b',
    r'\belectronic\s+communication\s+(capability|feature|platform|service)\b',
    r'\b(video|voice)\s+(call|calling|chat|chatting)\s+(capability|feature|between|with)\b',
    r'\binstant\s+messag(e|ing)\s+(capability|feature|platform|between|with)\b',
    r'\bmessaging\s+(platform|service|capability|feature)\b',
    r'\b(enable|allow|permit)s?\s+(user|customer)s?\s+to\s+(send|message|email|text|call|chat)\b',
    r'\buser\s+to\s+user\s+(messaging|communication|chat)\b',
    r'\breal-?time\s+(messaging|communication|chat|notification)\b',
    r'\btwo-?way\s+(messaging|communication|chat)\b',
    r'\b(email|sms|text)\s+marketing\s+campaign\b',
    r'\btransactional\s+(email|sms|text)\b',
    r'\bautomated\s+(email|sms|text|notification)\b',
    r'\bscheduled\s+(email|sms|text|notification)\b',
    r'\bbulk\s+(email|sms|text|message)\b',
    r'\bmass\s+(email|sms|text|message)\b',
]

# Receiving (user receives from app) - NOT the same as app sending
RECEIVING_PATTERNS = [
    r'\b(user|customer)s?\s+(receive|get)s?\s+(email|text|sms|notification)s?\s+from\b',
    r'\b(receive|get)s?\s+(verification|authentication|security)\s+(code|token)\b',
    r'\b(sms|text|email)\s+(verification|authentication)\s+code\b',
    r'\b2fa\s+(via|through|using)\s+(sms|text|email)\b',
    r'\btwo-?factor\s+(via|through|using)\s+(sms|text|email)\b',
    r'\bone-?time\s+(password|code)\s+(via|through|using)\s+(sms|text|email)\b',
    r'\botp\s+(via|through|using)\s+(sms|text|email)\b',
]

# ============================================================================
# COMPILED PATTERNS
# ============================================================================

DATA_FIELD_REGEX = [re.compile(p, re.IGNORECASE) for p in DATA_FIELD_PATTERNS]
ECOMM_SENDING_REGEX = [re.compile(p, re.IGNORECASE) for p in ECOMM_SENDING_PATTERNS]
RECEIVING_REGEX = [re.compile(p, re.IGNORECASE) for p in RECEIVING_PATTERNS]

# ============================================================================
# LOAD SEMANTIC MODEL
# ============================================================================
print("\n" + "="*80)
print("LOADING SEMANTIC MODEL")
print("="*80)

MODEL_AVAILABLE = False
model = None

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    
    print("Loading all-MiniLM-L6-v2...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Model loaded")
    MODEL_AVAILABLE = True
except Exception as e:
    print(f"⚠ Could not load model: {e}")
    print("  Falling back to rule-based classification only")

# ============================================================================
# SEMANTIC ANCHORS - Carefully chosen contrastive pairs
# ============================================================================

if MODEL_AVAILABLE:
    # These are IDEAL examples that capture the semantic distinction
    SENDING_ANCHORS = [
        # App/system as sender
        "the app sends email notifications to users",
        "the system delivers text messages to customers",
        "push notifications are sent to user devices",
        "the platform transmits alerts to subscribers",
        "automated emails are dispatched to customers",
        
        # User as sender
        "users can send messages to each other",
        "allows users to email other users",
        "enables users to text their contacts",
        "users can make video calls",
        "users can chat with each other",
        
        # Capability descriptions
        "email sending capability",
        "SMS delivery feature",
        "instant messaging platform",
        "real-time chat functionality",
        "voice calling service",
    ]
    
    COLLECTION_ANCHORS = [
        # Data collection
        "collects email addresses from users",
        "stores user phone numbers in database",
        "email address required for registration",
        "phone number stored in user profile",
        "saves customer contact information",
        
        # Data fields
        "email and phone number fields",
        "user provides email address",
        "email field in registration form",
        "contact information: email, phone, address",
        "required fields include email",
        
        # Data usage (not sending)
        "email used for login authentication",
        "phone number for account verification",
        "email address on file",
        "stores email for future reference",
        "email validation and storage",
    ]
    
    print("Encoding semantic anchors...")
    sending_embeddings = model.encode(SENDING_ANCHORS, normalize_embeddings=True)
    collection_embeddings = model.encode(COLLECTION_ANCHORS, normalize_embeddings=True)
    print("✓ Anchors encoded")

# ============================================================================
# CLASSIFICATION ENGINE
# ============================================================================

def tokenize_simple(text: str) -> List[str]:
    """Simple word tokenization."""
    return re.findall(r'\b\w+\b', text.lower())

def extract_verb_object_pairs(text: str) -> List[Tuple[str, str]]:
    """Extract verb-object pairs from text."""
    text_lower = text.lower()
    tokens = tokenize_simple(text_lower)
    
    pairs = []
    for i, token in enumerate(tokens):
        if token in TRANSMISSION_VERBS or token in COLLECTION_VERBS:
            # Look for nearby ecomm objects
            window = tokens[max(0, i-3):min(len(tokens), i+5)]
            for obj in ECOMM_OBJECTS:
                obj_tokens = obj.split()
                if all(t in window for t in obj_tokens):
                    verb_type = 'transmission' if token in TRANSMISSION_VERBS else 'collection'
                    pairs.append((token, obj, verb_type))
    
    return pairs

def check_pattern_matches(text: str, patterns: List[re.Pattern]) -> List[str]:
    """Check which patterns match the text."""
    matches = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            matches.append(match.group())
    return matches

def has_recipient_indicator(text: str) -> bool:
    """Check if text contains recipient indicators (to users, to customers, etc.)."""
    text_lower = text.lower()
    return any(ind in text_lower for ind in RECIPIENT_INDICATORS)

def compute_semantic_scores(text: str) -> Tuple[float, float]:
    """Compute semantic similarity to sending vs collection anchors."""
    if not MODEL_AVAILABLE or model is None:
        return 0.5, 0.5
    
    try:
        text_embedding = model.encode([text], normalize_embeddings=True)[0]
        
        # Compute max similarity to each anchor set
        sending_sims = cosine_similarity(
            text_embedding.reshape(1, -1), 
            sending_embeddings
        )[0]
        collection_sims = cosine_similarity(
            text_embedding.reshape(1, -1), 
            collection_embeddings
        )[0]
        
        # Use top-3 average for robustness
        top_sending = np.mean(sorted(sending_sims, reverse=True)[:3])
        top_collection = np.mean(sorted(collection_sims, reverse=True)[:3])
        
        return float(top_sending), float(top_collection)
    except Exception as e:
        print(f"Semantic error: {e}")
        return 0.5, 0.5

def classify_ecomm(text: str) -> Dict:
    """
    Classify text as e-communication (sending) or not.
    
    Uses a multi-signal voting system:
    1. Pattern matching (strong signals)
    2. Verb-object analysis (linguistic)
    3. Semantic similarity (contextual)
    4. Recipient indicators (directional)
    """
    if not text or pd.isna(text):
        return {'is_ecomm': False, 'confidence': 0.0, 'method': 'empty', 'signals': {}}
    
    text_str = str(text).strip()
    if not text_str or text_str.lower() in ['nan', 'none', '']:
        return {'is_ecomm': False, 'confidence': 0.0, 'method': 'empty', 'signals': {}}
    
    text_lower = text_str.lower()
    signals = {}
    
    # ========== SIGNAL 1: Data field patterns (strong disqualifier) ==========
    data_field_matches = []
    for pattern in DATA_FIELD_REGEX:
        match = pattern.search(text_str)
        if match:
            data_field_matches.append(match.group())
    
    if data_field_matches:
        signals['data_field'] = data_field_matches
        return {
            'is_ecomm': False, 
            'confidence': 0.95, 
            'method': 'data_field_pattern',
            'signals': signals,
            'matched': data_field_matches
        }
    
    # ========== SIGNAL 2: Receiving patterns (disqualifier) ==========
    receiving_matches = check_pattern_matches(text_str, RECEIVING_REGEX)
    if receiving_matches:
        signals['receiving'] = receiving_matches
        return {
            'is_ecomm': False, 
            'confidence': 0.85, 
            'method': 'receiving_pattern',
            'signals': signals,
            'matched': receiving_matches
        }
    
    # ========== SIGNAL 3: Strong e-comm sending patterns (qualifier) ==========
    ecomm_matches = check_pattern_matches(text_str, ECOMM_SENDING_REGEX)
    if ecomm_matches:
        signals['ecomm_pattern'] = ecomm_matches
        return {
            'is_ecomm': True, 
            'confidence': 0.95, 
            'method': 'ecomm_pattern',
            'signals': signals,
            'matched': ecomm_matches
        }
    
    # ========== SIGNAL 4: Verb-object analysis ==========
    verb_object_pairs = extract_verb_object_pairs(text_str)
    transmission_pairs = [p for p in verb_object_pairs if len(p) >= 3 and p[2] == 'transmission']
    collection_pairs = [p for p in verb_object_pairs if len(p) >= 3 and p[2] == 'collection']
    
    signals['transmission_verbs'] = [(p[0], p[1]) for p in transmission_pairs]
    signals['collection_verbs'] = [(p[0], p[1]) for p in collection_pairs]
    
    # ========== SIGNAL 5: Recipient indicators ==========
    has_recipient = has_recipient_indicator(text_str)
    signals['has_recipient'] = has_recipient
    
    # ========== SIGNAL 6: Semantic similarity ==========
    sem_sending, sem_collection = compute_semantic_scores(text_str)
    signals['semantic_sending'] = round(sem_sending, 3)
    signals['semantic_collection'] = round(sem_collection, 3)
    
    # ========== VOTING SYSTEM ==========
    sending_score = 0.0
    collection_score = 0.0
    
    # Verb-object pairs (weight: 0.35)
    if transmission_pairs and not collection_pairs:
        sending_score += 0.35
    elif collection_pairs and not transmission_pairs:
        collection_score += 0.35
    elif transmission_pairs and collection_pairs:
        # Both present - use ratio
        t_count = len(transmission_pairs)
        c_count = len(collection_pairs)
        sending_score += 0.35 * (t_count / (t_count + c_count))
        collection_score += 0.35 * (c_count / (t_count + c_count))
    
    # Recipient indicators (weight: 0.2)
    if has_recipient:
        sending_score += 0.2
    
    # Semantic similarity (weight: 0.45)
    if sem_sending + sem_collection > 0:
        sem_ratio_sending = sem_sending / (sem_sending + sem_collection)
        sem_ratio_collection = sem_collection / (sem_sending + sem_collection)
        sending_score += 0.45 * sem_ratio_sending
        collection_score += 0.45 * sem_ratio_collection
    else:
        # Default to slight collection bias if no semantic signal
        collection_score += 0.225
    
    # Normalize scores
    total = sending_score + collection_score
    if total > 0:
        sending_score /= total
        collection_score /= total
    else:
        sending_score = 0.3
        collection_score = 0.7
    
    # Final decision
    is_ecomm = sending_score > CONFIDENCE_THRESHOLD
    confidence = sending_score if is_ecomm else (1 - sending_score)
    
    return {
        'is_ecomm': is_ecomm,
        'confidence': round(confidence, 3),
        'method': 'multi_signal',
        'sending_score': round(sending_score, 3),
        'collection_score': round(collection_score, 3),
        'signals': signals
    }

def safe_str(value) -> str:
    """Safely convert value to string."""
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

# ============================================================================
# TESTING
# ============================================================================
print("\n" + "="*80)
print("TESTING CLASSIFIER")
print("="*80)

test_cases = [
    # Clear e-comm sending
    ("users can send emails through the app", True),
    ("application allows transmitting electronic messages", True),
    ("sends push notifications to users", True),
    ("video calling between users", True),
    ("instant messaging capability", True),
    ("app delivers text messages to customers", True),
    ("real-time chat feature", True),
    ("enables users to message each other", True),
    ("SMS marketing campaigns", True),
    ("automated email notifications", True),
    
    # Clear NOT e-comm (data collection)
    ("collects email addresses", False),
    ("email address for registration", False),
    ("stores phone numbers", False),
    ("email, phone, address collected", False),
    ("login with email", False),
    ("email field required", False),
    ("user provides email and phone", False),
    ("email stored in database", False),
    ("requires email for account creation", False),
    ("email and password for login", False),
    
    # Tricky cases
    ("receives verification SMS", False),  # User receives, not app sending outbound
    ("2FA via text message", False),  # Authentication, not communication
    ("OTP sent to phone", False),  # Still auth, single direction
    ("email marketing platform capabilities", True),  # Platform can send
    ("contact information: email, phone", False),  # Data listing
    ("Japanese text support", False),  # Text = language, not SMS
    ("plaintext format", False),  # Technical term
]

print("\nTest Results:")
print("-" * 80)

correct = 0
for text, expected in test_cases:
    result = classify_ecomm(text)
    is_correct = result['is_ecomm'] == expected
    correct += is_correct
    
    status = "✓" if is_correct else "✗"
    conf = result.get('sending_score', result['confidence'])
    print(f"{status} [{conf:.3f}] Expected={expected}, Got={result['is_ecomm']}")
    print(f"    Text: {text[:60]}")
    print(f"    Method: {result['method']}")
    if not is_correct:
        print(f"    Signals: {result.get('signals', {})}")
    print()

accuracy = correct / len(test_cases)
print("-" * 80)
print(f"Accuracy: {accuracy*100:.1f}% ({correct}/{len(test_cases)})")

# ============================================================================
# PROCESS DATA
# ============================================================================
print("\n" + "="*80)
print("PROCESSING DATA")
print("="*80)

all_idn_eons = set()

for dataset_name in input_dataset_names:
    print(f"\n[{dataset_name}]")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None)
        for col in df.columns:
            df[col] = df[col].astype(str)
        print(f"  Loaded {len(df):,} rows")
    except Exception as e:
        print(f"  Error: {e}")
        continue
    
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        print(f"  No IDN_EON column")
        continue
    
    unique_vals = [str(v).strip() for v in df[idn_col].unique()
                   if str(v).strip() and str(v).lower() not in ['nan', 'none', '']]
    
    print(f"  Found {len(unique_vals):,} unique IDN_EON")
    all_idn_eons.update(unique_vals)

print(f"\nTotal unique IDN_EON: {len(all_idn_eons):,}")

# Build inventory
inventory = {idn: {
    'IDN_EON': idn,
    'sources': set(),
    'ecomm_findings': []
} for idn in all_idn_eons}

processed = 0

for dataset_name in input_dataset_names:
    print(f"\n[{dataset_name}]")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None)
        for col in df.columns:
            df[col] = df[col].astype(str)
    except:
        continue
    
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        continue
    
    unique_idns = [str(v).strip() for v in df[idn_col].unique()
                   if str(v).strip() and str(v).lower() not in ['nan', 'none', '']]
    
    for IDN_EON_str in unique_idns:
        processed += 1
        if processed % 500 == 0:
            print(f"  Progress: {processed:,}/{len(all_idn_eons):,}")
        
        inventory[IDN_EON_str]['sources'].add(dataset_name)
        idn_rows = df[df[idn_col] == IDN_EON_str]
        
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            for val in idn_rows[col]:
                val_str = safe_str(val)
                if not val_str or val_str.lower() in ['nan', 'none', '']:
                    continue
                
                val_lower = val_str.lower()
                
                # Pre-filter: only process potentially relevant text
                relevant_keywords = [
                    'email', 'text', 'sms', 'message', 'call', 'video', 'voice',
                    'chat', 'communication', 'notify', 'notification', 'alert',
                    'send', 'deliver', 'transmit', 'push', 'broadcast'
                ]
                
                if not any(kw in val_lower for kw in relevant_keywords):
                    continue
                
                result = classify_ecomm(val_str)
                
                if result['is_ecomm']:
                    inventory[IDN_EON_str]['ecomm_findings'].append({
                        'location': f"{col} [{dataset_name}]",
                        'confidence': result['confidence'],
                        'sending_score': result.get('sending_score', result['confidence']),
                        'method': result['method'],
                        'content': val_str[:500],
                        'signals': result.get('signals', {}),
                        'matched': result.get('matched', [])
                    })

# Build output
output_data = []

for idn, data in inventory.items():
    if len(data['ecomm_findings']) >= MIN_FINDINGS_REQUIRED:
        max_conf = max([f['sending_score'] for f in data['ecomm_findings']])
        methods = list(set([f['method'] for f in data['ecomm_findings']]))
        locations = list(set([f['location'] for f in data['ecomm_findings']]))
        contents = list(set([f['content'] for f in data['ecomm_findings']]))[:5]
        
        # Collect matched patterns
        all_matches = []
        for f in data['ecomm_findings']:
            all_matches.extend(f.get('matched', []))
        unique_matches = list(set(all_matches))[:5]
        
        output_data.append({
            'IDN_EON': idn,
            'sort_conf': max_conf,
            'data_source': ', '.join(sorted(data['sources'])),
            'ecomm_confidence': round(max_conf, 3),
            'detection_method': ', '.join(methods),
            'pattern_matches': ' | '.join(unique_matches) if unique_matches else 'semantic',
            'found_in': ', '.join(sorted(locations)),
            'sample_content': ' | '.join(contents),
            'total_findings': len(data['ecomm_findings'])
        })

output_df = pd.DataFrame(output_data).sort_values('sort_conf', ascending=False).reset_index(drop=True)
output_df = output_df.drop('sort_conf', axis=1)

output_dataset.write_with_schema(output_df)

print(f"\n{'='*80}")
print(f"RESULTS")
print(f"{'='*80}")
print(f"Total IDN_EON: {len(all_idn_eons):,}")
print(f"With e-communication: {len(output_df):,} ({len(output_df)/len(all_idn_eons)*100:.1f}% if all_idn_eons else 0)")
print(f"{'='*80}")
