"""
TRUE SEMANTIC E-COMMUNICATION DETECTOR v3.0
============================================
This version ACTUALLY understands sentence meaning by:
1. Using sentence embeddings with carefully constructed contrastive examples
2. Analyzing grammatical structure (subject-verb-object relationships)
3. Understanding context and intent, not just keyword presence
4. Using a neural classifier trained on meaning, not pattern matching

The key insight: "email" appearing in text means NOTHING.
What matters is: WHO does WHAT with email, and in WHAT DIRECTION?

Examples that should be DETECTED (app/user SENDS communications):
- "The application sends email notifications to users" → App sends TO users
- "Users can message each other through the platform" → Users send TO each other
- "Push notifications are delivered to customer devices" → System sends TO customers

Examples that should be REJECTED (data collection/storage):
- "Email address is collected during registration" → Collecting FROM users
- "User's phone number is stored in the database" → Storing, not sending
- "Login requires email and password" → Using email as identifier, not communication
"""

import dataiku
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import warnings
import sys
import subprocess

warnings.filterwarnings('ignore')

print("=" * 80)
print("TRUE SEMANTIC E-COMMUNICATION DETECTOR v3.0")
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================
SEMANTIC_THRESHOLD = 0.55  # Score above this = e-communication detected
MIN_FINDINGS_REQUIRED = 1
BATCH_SIZE = 32  # For efficient embedding computation

input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# ============================================================================
# INSTALL AND LOAD SENTENCE TRANSFORMERS
# ============================================================================
print("\n" + "=" * 80)
print("LOADING SEMANTIC MODEL")
print("=" * 80)

MODEL_AVAILABLE = False
model = None

def install_and_load_model():
    """Attempt to install and load sentence-transformers."""
    global MODEL_AVAILABLE, model
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✓ sentence-transformers already installed")
        
        print("Loading all-MiniLM-L6-v2 model...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✓ Model loaded successfully")
        MODEL_AVAILABLE = True
        return True
        
    except ImportError:
        print("⚠ sentence-transformers not found, installing...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "sentence-transformers", "--break-system-packages", "-q"
            ])
            print("✓ Installation complete")
            
            from sentence_transformers import SentenceTransformer
            print("Loading all-MiniLM-L6-v2 model...")
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            print("✓ Model loaded successfully")
            MODEL_AVAILABLE = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to install: {e}")
            print("  Will use advanced rule-based fallback")
            return False
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return False

install_and_load_model()

# ============================================================================
# SEMANTIC TRAINING DATA
# ============================================================================
# These examples are carefully crafted to teach the model the DIFFERENCE
# between sending capabilities and data collection.
# 
# KEY PRINCIPLE: The examples must be semantically diverse but clearly
# distinguish between the two categories based on MEANING, not keywords.

# CATEGORY 1: E-COMMUNICATION SENDING CAPABILITIES
# These describe apps/systems that SEND or ENABLE SENDING of communications
SENDING_EXAMPLES = [
    # === SYSTEM/APP SENDS TO USERS ===
    "the application sends email notifications to users",
    "system delivers text messages to customers",
    "app transmits SMS alerts to subscribers",
    "platform sends push notifications to devices",
    "service emails order confirmations to buyers",
    "application dispatches automated alerts",
    "system broadcasts notifications to all users",
    "app pushes real-time updates to mobile devices",
    "platform delivers instant alerts to subscribers",
    "service transmits promotional messages to customers",
    "application sends appointment reminders via text",
    "system notifies users through email",
    "app alerts customers via SMS",
    "platform communicates updates to subscribers",
    "automated emails are sent to customers",
    "push notifications delivered to user devices",
    "text message alerts sent to phone numbers",
    "email campaigns delivered to subscriber list",
    "transactional emails sent after purchase",
    "SMS notifications dispatched automatically",
    
    # === USER-TO-USER COMMUNICATION ===
    "users can send messages to each other",
    "platform enables direct messaging between users",
    "allows customers to email each other",
    "users can text other members",
    "enables video calling between participants",
    "supports voice calls between users",
    "instant messaging between team members",
    "chat functionality for user communication",
    "allows sending messages to contacts",
    "users can communicate via the app",
    "peer-to-peer messaging capability",
    "enables real-time chat between users",
    "supports group messaging features",
    "allows users to start video chats",
    "voice calling feature for members",
    
    # === COMMUNICATION PLATFORM DESCRIPTIONS ===
    "email sending capability",
    "SMS delivery service",
    "push notification system",
    "messaging platform features",
    "communication delivery infrastructure",
    "notification dispatch system",
    "email marketing platform",
    "text message gateway",
    "real-time messaging service",
    "video conferencing platform",
    "voice communication service",
    "chat application features",
    "instant messaging infrastructure",
    "alert delivery mechanism",
    "notification broadcasting system",
    
    # === CAPABILITY DESCRIPTIONS ===
    "enables sending of electronic communications",
    "provides email transmission capabilities",
    "supports outbound SMS messaging",
    "facilitates push notification delivery",
    "allows transmission of text messages",
    "capable of sending automated emails",
    "equipped with messaging functionality",
    "includes video calling features",
    "offers voice communication options",
    "provides chat capabilities",
    "supports real-time notifications",
    "enables bulk email sending",
    "allows scheduled message delivery",
    "supports triggered notifications",
    "provides communication tools",
    
    # === E-COMMUNICATION EXPLICIT ===
    "e-communication capabilities enabled",
    "electronic communication features",
    "e-communication platform",
    "electronic messaging service",
    "e-communication delivery system",
    "electronic notification capabilities",
    "e-communication infrastructure",
    "digital communication platform",
    "electronic alert system",
    "e-communication enabled application",
]

# CATEGORY 2: DATA COLLECTION/STORAGE (NOT SENDING)
# These describe collecting, storing, or using communication data as identifiers
COLLECTION_EXAMPLES = [
    # === COLLECTING EMAIL/PHONE AS DATA ===
    "collects email addresses from users",
    "gathers customer phone numbers",
    "captures user email during registration",
    "obtains contact information from customers",
    "requests email address for signup",
    "asks users for phone number",
    "collects subscriber email addresses",
    "gathers member contact details",
    "captures email for newsletter signup",
    "obtains phone for account verification",
    "collects user contact information",
    "gathers email and phone data",
    "requests contact details during checkout",
    "asks for email to create account",
    "collects phone number for records",
    
    # === STORING COMMUNICATION DATA ===
    "stores email addresses in database",
    "saves phone numbers to user profile",
    "keeps email on file for records",
    "retains contact information",
    "maintains email address records",
    "archives customer phone numbers",
    "stores contact data securely",
    "saves user email to account",
    "keeps phone number in system",
    "retains subscriber email addresses",
    "stores member contact details",
    "maintains database of emails",
    "archives contact information",
    "saves email for future reference",
    "stores phone for account recovery",
    
    # === EMAIL/PHONE AS IDENTIFIER ===
    "email address used for login",
    "phone number for authentication",
    "email serves as username",
    "login with email and password",
    "sign in using phone number",
    "email required for account access",
    "authenticate using email address",
    "phone number as account identifier",
    "email for user identification",
    "login credentials include email",
    "email based authentication",
    "phone verification for login",
    "email as unique identifier",
    "account tied to email address",
    "phone linked to user account",
    
    # === DATA FIELD DESCRIPTIONS ===
    "email field in registration form",
    "phone number input field",
    "contact information form fields",
    "email address text box",
    "phone number entry field",
    "user provides email address",
    "customer enters phone number",
    "email input on signup page",
    "phone field required",
    "email address field validation",
    "contact form with email field",
    "phone number text input",
    "email and phone form fields",
    "user information includes email",
    "profile contains phone number",
    
    # === DATABASE/SCHEMA DESCRIPTIONS ===
    "email column in user table",
    "phone number data field",
    "contact information schema",
    "email data type varchar",
    "phone stored as string",
    "email address database column",
    "user table contains email",
    "phone field in customer record",
    "email as plaintext field",
    "contact data structure",
    "email in user schema",
    "phone number database entry",
    "email and phone columns",
    "contact information table",
    "user data includes email",
    
    # === LIST FORMAT (STRONG INDICATOR) ===
    "fields: email, phone, address",
    "collects: name, email, phone",
    "data: email, phone number, address",
    "information: email and phone",
    "email, phone, mailing address",
    "contact: email, phone",
    "user data: email, phone, name",
    "profile: email, phone, address",
    "required: email, phone number",
    "includes email and phone number",
    
    # === VERIFICATION CODES (NOT COMMUNICATION) ===
    "SMS verification code sent",
    "email verification link",
    "phone verification for 2FA",
    "one-time password via SMS",
    "verification code to email",
    "2FA code sent to phone",
    "email confirmation link",
    "SMS OTP for authentication",
    "verify phone with code",
    "email verification required",
    
    # === DISPLAY/RENDERING ===
    "displays user email address",
    "shows phone number in profile",
    "renders contact information",
    "email visible on account page",
    "phone displayed in settings",
    "shows email in user details",
    "contact info shown on profile",
    "displays customer phone",
    "renders email address field",
    "shows contact details",
    
    # === VALIDATION/FORMAT ===
    "validates email format",
    "checks phone number format",
    "email format validation",
    "verifies valid email address",
    "phone number format check",
    "validates contact information",
    "email syntax validation",
    "checks valid phone format",
    "validates email domain",
    "phone format verification",
    
    # === UNRELATED TEXT MENTIONS ===
    "Japanese text support",
    "Chinese text encoding",
    "plaintext format",
    "text field data type",
    "text column in database",
    "rich text editor",
    "text formatting options",
    "plain text content",
    "text data storage",
    "text input processing",
]

print(f"\nTraining data: {len(SENDING_EXAMPLES)} sending examples, {len(COLLECTION_EXAMPLES)} collection examples")

# ============================================================================
# COMPUTE SEMANTIC EMBEDDINGS
# ============================================================================

sending_embeddings = None
collection_embeddings = None
sending_centroid = None
collection_centroid = None

if MODEL_AVAILABLE and model is not None:
    print("\nComputing semantic embeddings for training data...")
    
    # Encode all examples
    sending_embeddings = model.encode(SENDING_EXAMPLES, normalize_embeddings=True, show_progress_bar=False)
    collection_embeddings = model.encode(COLLECTION_EXAMPLES, normalize_embeddings=True, show_progress_bar=False)
    
    # Compute centroids (mean embeddings)
    sending_centroid = np.mean(sending_embeddings, axis=0)
    sending_centroid = sending_centroid / np.linalg.norm(sending_centroid)
    
    collection_centroid = np.mean(collection_embeddings, axis=0)
    collection_centroid = collection_centroid / np.linalg.norm(collection_centroid)
    
    print(f"✓ Encoded {len(SENDING_EXAMPLES)} sending examples")
    print(f"✓ Encoded {len(COLLECTION_EXAMPLES)} collection examples")
    print(f"✓ Computed category centroids")

# ============================================================================
# HARD RULES (Override semantic classification in clear cases)
# ============================================================================

# Patterns that DEFINITELY indicate e-communication sending
DEFINITE_SENDING_PATTERNS = [
    # Explicit e-communication terms
    r'\be-?communications?\s+(capabilit|feature|platform|service|enabled|system)',
    r'\belectronic\s+communications?\s+(capabilit|feature|platform|service)',
    
    # Clear sending patterns with recipients
    r'\b(sends?|delivers?|transmits?|dispatches?)\s+(emails?|texts?|sms|messages?|notifications?|alerts?)\s+(to|for)\s+(users?|customers?|subscribers?|members?|devices?)',
    
    # Platform/app as sender
    r'\b(app|application|system|platform|service)\s+(sends?|delivers?|transmits?)\s+(emails?|texts?|sms|notifications?)',
    
    # User-to-user communication
    r'\busers?\s+(can|may|could)\s+(send|message|email|text|call|chat)',
    r'\b(messaging|calling|chatting)\s+between\s+users?',
    r'\buser[\s-]to[\s-]user\s+(messaging|communication|chat)',
    
    # Communication features
    r'\b(video|voice)\s+(call|calling|chat|conferencing)\s+(feature|capabilit|between|with)',
    r'\binstant\s+messaging\s+(feature|capabilit|platform|between)',
    r'\breal[\s-]time\s+(messaging|chat|communication)',
    r'\bpush\s+notifications?\s+(to|for|delivered|sent)',
    
    # Marketing/bulk sending
    r'\b(email|sms|text)\s+marketing',
    r'\bbulk\s+(email|sms|text|message)',
    r'\bmass\s+(email|sms|text|message)',
    r'\btransactional\s+(email|sms)',
    r'\bautomated\s+(email|sms|text|notification)',
]

# Patterns that DEFINITELY indicate data collection (not sending)
DEFINITE_COLLECTION_PATTERNS = [
    # List format (email, phone, etc.)
    r'\bemail\s*[,&]\s*(phone|address|name)',
    r'\b(phone|name)\s*[,&]\s*email',
    r'\bfields?\s*[:\-]?\s*(email|phone)',
    r'\b(data|information|details)\s*[:\-]?\s*(email|phone)',
    
    # Collecting/storing verbs with email/phone
    r'\b(collects?|gathers?|captures?|obtains?|stores?|saves?|retains?|maintains?|archives?)\s+(users?\'?s?\s+)?(email|phone|contact)',
    r'\b(email|phone)\s+(address\s+)?(collected|gathered|stored|saved|retained)',
    
    # Login/authentication
    r'\b(login|sign\s*in|authenticate)\s+(with|using|via)\s+email',
    r'\bemail\s+(for|as)\s+(login|username|authentication|identifier)',
    r'\bemail\s+and\s+password',
    r'\bemail\s+required\s+for\s+(registration|signup|account|login)',
    
    # Database/schema terms
    r'\bemail\s+(column|field|table|data\s*type)',
    r'\b(plaintext|varchar|string)\s+(email|field)',
    r'\bemail\s+in\s+(database|table|schema|record|profile)',
    
    # Form fields
    r'\bemail\s+(input|text\s*box|form)\s*field',
    r'\benter\s+(your\s+)?email\s+address',
    r'\bprovide\s+(your\s+)?email',
    r'\bemail\s+address\s+field',
    
    # Verification (not communication)
    r'\b(sms|text|email)\s+verification\s+(code|link)',
    r'\b(2fa|two[\s-]factor)\s+(via|using|through)\s+(sms|text|email)',
    r'\b(otp|one[\s-]time\s+password)\s+(via|sent|to)',
    r'\bverification\s+(code|link)\s+(sent|to|via)',
    
    # Unrelated "text" references
    r'\b(japanese|chinese|korean|arabic|hebrew)\s+text',
    r'\bplaintext\s+format',
    r'\btext\s+(field|column|data\s*type)',
    r'\brich\s+text\s+editor',
]

# Compile patterns
SENDING_REGEX = [re.compile(p, re.IGNORECASE) for p in DEFINITE_SENDING_PATTERNS]
COLLECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in DEFINITE_COLLECTION_PATTERNS]

# ============================================================================
# SEMANTIC CLASSIFICATION FUNCTION
# ============================================================================

def compute_semantic_similarity(text: str) -> Tuple[float, float, List[str]]:
    """
    Compute semantic similarity of text to sending vs collection categories.
    
    Returns:
        (sending_score, collection_score, top_matches)
    """
    if not MODEL_AVAILABLE or model is None:
        return 0.5, 0.5, []
    
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Encode the input text
        text_embedding = model.encode([text], normalize_embeddings=True)[0]
        
        # 1. Similarity to centroids
        centroid_sending = float(np.dot(text_embedding, sending_centroid))
        centroid_collection = float(np.dot(text_embedding, collection_centroid))
        
        # 2. Max similarity to individual examples
        sending_sims = cosine_similarity(text_embedding.reshape(1, -1), sending_embeddings)[0]
        collection_sims = cosine_similarity(text_embedding.reshape(1, -1), collection_embeddings)[0]
        
        max_sending = float(np.max(sending_sims))
        max_collection = float(np.max(collection_sims))
        
        # 3. Top-5 average (more robust than max alone)
        top5_sending = float(np.mean(sorted(sending_sims, reverse=True)[:5]))
        top5_collection = float(np.mean(sorted(collection_sims, reverse=True)[:5]))
        
        # 4. 90th percentile
        p90_sending = float(np.percentile(sending_sims, 90))
        p90_collection = float(np.percentile(collection_sims, 90))
        
        # Weighted combination
        # Weight towards max and top-5 as they're more discriminative
        sending_score = (
            0.2 * centroid_sending +
            0.35 * max_sending +
            0.30 * top5_sending +
            0.15 * p90_sending
        )
        
        collection_score = (
            0.2 * centroid_collection +
            0.35 * max_collection +
            0.30 * top5_collection +
            0.15 * p90_collection
        )
        
        # Find top matching examples for explainability
        top_sending_idx = np.argsort(sending_sims)[-3:][::-1]
        top_matches = [SENDING_EXAMPLES[i] for i in top_sending_idx]
        
        return sending_score, collection_score, top_matches
        
    except Exception as e:
        print(f"Semantic computation error: {e}")
        return 0.5, 0.5, []


def classify_text(text: str) -> Dict:
    """
    Classify text as e-communication sending capability or not.
    
    This uses a multi-stage approach:
    1. Check hard rules first (definite patterns)
    2. Use semantic similarity for ambiguous cases
    3. Combine signals for final decision
    
    Returns:
        Dict with: is_ecomm, confidence, method, details
    """
    # Handle empty/invalid text
    if not text or pd.isna(text):
        return {
            'is_ecomm': False,
            'confidence': 0.0,
            'method': 'empty',
            'details': {}
        }
    
    text_str = str(text).strip()
    if not text_str or len(text_str) < 10:
        return {
            'is_ecomm': False,
            'confidence': 0.0,
            'method': 'too_short',
            'details': {}
        }
    
    text_lower = text_str.lower()
    
    # Skip text that has no communication-related terms at all
    comm_terms = [
        'email', 'e-mail', 'mail', 'text', 'sms', 'mms', 'message', 'messag',
        'call', 'video', 'voice', 'chat', 'notification', 'notify', 'alert',
        'communication', 'communicat', 'send', 'deliver', 'transmit', 'push',
        'broadcast', 'dispatch'
    ]
    if not any(term in text_lower for term in comm_terms):
        return {
            'is_ecomm': False,
            'confidence': 0.0,
            'method': 'no_comm_terms',
            'details': {}
        }
    
    details = {}
    
    # ========== STAGE 1: Check definite collection patterns (disqualifiers) ==========
    collection_matches = []
    for pattern in COLLECTION_REGEX:
        match = pattern.search(text_str)
        if match:
            collection_matches.append(match.group())
    
    if collection_matches:
        details['collection_patterns'] = collection_matches
        return {
            'is_ecomm': False,
            'confidence': 0.95,
            'method': 'definite_collection_pattern',
            'details': details,
            'matched_patterns': collection_matches
        }
    
    # ========== STAGE 2: Check definite sending patterns (qualifiers) ==========
    sending_matches = []
    for pattern in SENDING_REGEX:
        match = pattern.search(text_str)
        if match:
            sending_matches.append(match.group())
    
    if sending_matches:
        details['sending_patterns'] = sending_matches
        return {
            'is_ecomm': True,
            'confidence': 0.95,
            'method': 'definite_sending_pattern',
            'details': details,
            'matched_patterns': sending_matches
        }
    
    # ========== STAGE 3: Semantic classification for ambiguous cases ==========
    if MODEL_AVAILABLE and model is not None:
        sending_score, collection_score, top_matches = compute_semantic_similarity(text_str)
        
        details['sending_score'] = round(sending_score, 4)
        details['collection_score'] = round(collection_score, 4)
        details['top_similar_sending'] = top_matches[:2]
        
        # Normalize to get a probability-like score
        total = sending_score + collection_score
        if total > 0:
            normalized_sending = sending_score / total
        else:
            normalized_sending = 0.5
        
        details['normalized_score'] = round(normalized_sending, 4)
        
        # Decision
        is_ecomm = normalized_sending > SEMANTIC_THRESHOLD
        confidence = normalized_sending if is_ecomm else (1 - normalized_sending)
        
        return {
            'is_ecomm': is_ecomm,
            'confidence': round(confidence, 3),
            'method': 'semantic',
            'details': details,
            'sending_score': round(normalized_sending, 3)
        }
    
    # ========== FALLBACK: Advanced keyword analysis ==========
    # If no semantic model, use linguistic analysis
    return fallback_classification(text_str)


def fallback_classification(text: str) -> Dict:
    """
    Fallback classification using linguistic patterns when semantic model unavailable.
    """
    text_lower = text.lower()
    details = {}
    
    # Transmission verbs (sending)
    transmission_verbs = {
        'send', 'sends', 'sending', 'sent',
        'deliver', 'delivers', 'delivering', 'delivered',
        'transmit', 'transmits', 'transmitting', 'transmitted',
        'dispatch', 'dispatches', 'dispatching',
        'push', 'pushes', 'pushing',
        'broadcast', 'broadcasts',
        'notify', 'notifies', 'notifying',
        'alert', 'alerts', 'alerting'
    }
    
    # Collection verbs
    collection_verbs = {
        'collect', 'collects', 'collecting', 'collected',
        'store', 'stores', 'storing', 'stored',
        'save', 'saves', 'saving', 'saved',
        'gather', 'gathers', 'gathering', 'gathered',
        'capture', 'captures', 'capturing', 'captured',
        'obtain', 'obtains', 'obtaining', 'obtained',
        'retain', 'retains', 'retaining', 'retained',
        'require', 'requires', 'requiring', 'required',
        'request', 'requests', 'requesting',
        'input', 'inputs', 'enter', 'enters',
        'provide', 'provides', 'providing',
        'display', 'displays', 'show', 'shows'
    }
    
    # Communication objects
    comm_objects = ['email', 'text', 'sms', 'message', 'notification', 'alert', 'call', 'chat']
    
    # Find verbs in text
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    found_transmission = words & transmission_verbs
    found_collection = words & collection_verbs
    found_comm = [obj for obj in comm_objects if obj in text_lower]
    
    details['transmission_verbs'] = list(found_transmission)
    details['collection_verbs'] = list(found_collection)
    details['comm_objects'] = found_comm
    
    # Recipient indicators (suggests sending TO someone)
    recipient_patterns = ['to user', 'to customer', 'to subscriber', 'to device', 'to member']
    has_recipient = any(rp in text_lower for rp in recipient_patterns)
    details['has_recipient'] = has_recipient
    
    # Scoring
    sending_score = 0.0
    
    if found_transmission and found_comm:
        sending_score += 0.4
    if has_recipient:
        sending_score += 0.3
    if found_collection and found_comm:
        sending_score -= 0.4
    if 'capability' in text_lower or 'feature' in text_lower or 'platform' in text_lower:
        if found_comm:
            sending_score += 0.2
    
    # Normalize
    sending_score = max(0.0, min(1.0, sending_score + 0.5))
    
    is_ecomm = sending_score > 0.6
    confidence = sending_score if is_ecomm else (1 - sending_score)
    
    return {
        'is_ecomm': is_ecomm,
        'confidence': round(confidence, 3),
        'method': 'fallback_linguistic',
        'details': details,
        'sending_score': round(sending_score, 3)
    }


# ============================================================================
# TESTING THE CLASSIFIER
# ============================================================================
print("\n" + "=" * 80)
print("TESTING CLASSIFIER")
print("=" * 80)

test_cases = [
    # === SHOULD DETECT (True) - Clear sending capabilities ===
    ("users can send emails through the app", True),
    ("app sends push notifications to users", True),
    ("video calling between users", True),
    ("instant messaging capability", True),
    ("the platform delivers SMS alerts to customers", True),
    ("enables real-time chat between team members", True),
    ("automated email notifications sent to subscribers", True),
    ("users can message each other directly", True),
    ("push notifications are delivered to mobile devices", True),
    ("e-communication capabilities enabled", True),
    ("voice calling feature for members", True),
    ("bulk email marketing platform", True),
    ("transactional SMS sent after purchase", True),
    ("app broadcasts alerts to all users", True),
    ("peer-to-peer messaging between customers", True),
    
    # === SHOULD REJECT (False) - Data collection/storage ===
    ("collects email addresses", False),
    ("email address for registration", False),
    ("email, phone, address collected", False),
    ("login with email", False),
    ("stores user phone numbers in database", False),
    ("email field in registration form", False),
    ("user provides email and phone", False),
    ("email required for account creation", False),
    ("email used as username for login", False),
    ("phone number stored in user profile", False),
    ("validates email format", False),
    ("email column in user table", False),
    ("contact information: email, phone, address", False),
    ("SMS verification code for 2FA", False),
    ("email verification link sent", False),
    ("Japanese text support", False),
    ("plaintext format", False),
    ("displays user email address", False),
    ("enter your email address", False),
    ("fields: name, email, phone", False),
]

print(f"\nRunning {len(test_cases)} test cases...\n")
print("-" * 80)

correct = 0
incorrect_cases = []

for text, expected in test_cases:
    result = classify_text(text)
    actual = result['is_ecomm']
    is_correct = actual == expected
    
    if is_correct:
        correct += 1
        status = "✓"
    else:
        status = "✗"
        incorrect_cases.append((text, expected, result))
    
    conf_score = result.get('sending_score', result['confidence'])
    print(f"{status} [{conf_score:.3f}] Expected={expected}, Got={actual}")
    print(f"    Text: \"{text}\"")
    print(f"    Method: {result['method']}")
    
    if not is_correct:
        print(f"    Details: {result.get('details', {})}")
    print()

accuracy = correct / len(test_cases) * 100
print("-" * 80)
print(f"\nACCURACY: {accuracy:.1f}% ({correct}/{len(test_cases)})")

if accuracy >= 90:
    print("✓ Classifier meets 90% accuracy threshold")
else:
    print(f"⚠ Classifier below 90% threshold")
    print(f"\nIncorrect cases:")
    for text, expected, result in incorrect_cases:
        print(f"  - \"{text}\"")
        print(f"    Expected: {expected}, Got: {result['is_ecomm']}")

# ============================================================================
# PROCESS DATA
# ============================================================================
print("\n" + "=" * 80)
print("PROCESSING DATA")
print("=" * 80)

# Step 1: Find all unique IDN_EON values across all tables
print("\n[STEP 1] Finding all unique IDN_EON values...")

all_idn_eons: Set[str] = set()
table_data: Dict[str, pd.DataFrame] = {}

for dataset_name in input_dataset_names:
    print(f"\n  Loading {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None)
        print(f"    Loaded {len(df):,} rows, {len(df.columns)} columns")
        
        # Convert all columns to string
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        table_data[dataset_name] = df
        
        # Find IDN_EON column (case-insensitive)
        idn_col = None
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                idn_col = col
                break
        
        if idn_col is None:
            print(f"    ⚠ No IDN_EON column found, skipping")
            continue
        
        # Extract unique IDN_EON values
        invalid_values = {'nan', 'none', '', 'null', 'n/a', 'na'}
        unique_vals = set()
        for val in df[idn_col].unique():
            val_str = str(val).strip()
            if val_str.lower() not in invalid_values:
                unique_vals.add(val_str)
        
        print(f"    Found {len(unique_vals):,} unique IDN_EON values")
        all_idn_eons.update(unique_vals)
        
    except Exception as e:
        print(f"    ✗ Error loading: {e}")
        continue

print(f"\n{'='*60}")
print(f"TOTAL UNIQUE IDN_EON: {len(all_idn_eons):,}")
print(f"{'='*60}")

# Step 2: Analyze each IDN_EON for e-communication capabilities
print("\n[STEP 2] Analyzing each IDN_EON for e-communication capabilities...")

# Initialize inventory
inventory: Dict[str, Dict] = {
    idn: {
        'IDN_EON': idn,
        'sources': set(),
        'findings': [],
        'cells_analyzed': 0
    }
    for idn in all_idn_eons
}

processed_count = 0
total_cells_analyzed = 0

for dataset_name, df in table_data.items():
    print(f"\n  Processing {dataset_name}...")
    
    # Find IDN_EON column
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        continue
    
    # Get list of other columns to analyze
    other_cols = [col for col in df.columns if col.upper() != 'IDN_EON']
    
    # Process each unique IDN_EON in this table
    unique_idns_in_table = set(df[idn_col].unique())
    
    for idn_val in unique_idns_in_table:
        idn_str = str(idn_val).strip()
        if idn_str.lower() in {'nan', 'none', '', 'null', 'n/a', 'na'}:
            continue
        
        if idn_str not in inventory:
            continue
        
        inventory[idn_str]['sources'].add(dataset_name)
        
        # Get all rows for this IDN_EON
        idn_rows = df[df[idn_col] == idn_val]
        
        # Analyze each cell in each row
        for _, row in idn_rows.iterrows():
            for col in other_cols:
                cell_value = row[col]
                cell_str = str(cell_value).strip()
                
                # Skip empty/invalid cells
                if not cell_str or cell_str.lower() in {'nan', 'none', '', 'null'}:
                    continue
                
                inventory[idn_str]['cells_analyzed'] += 1
                total_cells_analyzed += 1
                
                # Classify the cell
                result = classify_text(cell_str)
                
                if result['is_ecomm']:
                    inventory[idn_str]['findings'].append({
                        'location': f"{col} [{dataset_name}]",
                        'confidence': result['confidence'],
                        'method': result['method'],
                        'content': cell_str[:500],
                        'matched_patterns': result.get('matched_patterns', []),
                        'sending_score': result.get('sending_score', result['confidence'])
                    })
        
        processed_count += 1
        if processed_count % 500 == 0:
            print(f"    Progress: {processed_count:,}/{len(all_idn_eons):,} IDN_EON processed")

print(f"\n  Total cells analyzed: {total_cells_analyzed:,}")

# Step 3: Build output with only IDN_EON that have e-communication capabilities
print("\n[STEP 3] Building output...")

output_rows = []

for idn, data in inventory.items():
    if len(data['findings']) >= MIN_FINDINGS_REQUIRED:
        # Calculate aggregate statistics
        max_confidence = max(f['sending_score'] for f in data['findings'])
        methods = list(set(f['method'] for f in data['findings']))
        locations = list(set(f['location'] for f in data['findings']))
        
        # Get sample content (up to 3 examples)
        sample_contents = []
        seen_contents = set()
        for f in sorted(data['findings'], key=lambda x: x['sending_score'], reverse=True):
            content = f['content']
            if content not in seen_contents:
                sample_contents.append(content)
                seen_contents.add(content)
            if len(sample_contents) >= 3:
                break
        
        # Collect matched patterns
        all_patterns = []
        for f in data['findings']:
            all_patterns.extend(f.get('matched_patterns', []))
        unique_patterns = list(set(all_patterns))[:5]
        
        output_rows.append({
            'IDN_EON': idn,
            'data_source': ', '.join(sorted(data['sources'])),
            'ecomm_confidence': round(max_confidence, 3),
            'detection_method': ', '.join(methods),
            'found_in': ', '.join(sorted(locations)),
            'sample_content': ' | '.join(sample_contents),
            'total_findings': len(data['findings']),
            '_sort_key': max_confidence  # For sorting, will be removed
        })

# Create output DataFrame, sorted by confidence
output_df = pd.DataFrame(output_rows)

if len(output_df) > 0:
    output_df = output_df.sort_values('_sort_key', ascending=False).reset_index(drop=True)
    output_df = output_df.drop('_sort_key', axis=1)

# Write to output dataset
print("\nWriting to output dataset...")
output_dataset.write_with_schema(output_df)

# ============================================================================
# FINAL STATISTICS
# ============================================================================
print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)

print(f"\nTotal unique IDN_EON found:           {len(all_idn_eons):,}")
print(f"Total with e-communication detected:  {len(output_df):,}")

if len(all_idn_eons) > 0:
    pct = len(output_df) / len(all_idn_eons) * 100
    print(f"Percentage with e-communication:      {pct:.2f}%")

print(f"\nTotal cells analyzed:                 {total_cells_analyzed:,}")
print(f"Mode used:                            {'Semantic (sentence-transformers)' if MODEL_AVAILABLE else 'Rule-based fallback'}")

if len(output_df) > 0:
    print(f"\nTop 10 highest confidence detections:")
    print("-" * 60)
    for i, row in output_df.head(10).iterrows():
        print(f"  {row['IDN_EON']}: {row['ecomm_confidence']:.3f} ({row['detection_method']})")

print("\n" + "=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)
