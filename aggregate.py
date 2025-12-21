# -*- coding: utf-8 -*-
"""
================================================================================
E-COMMUNICATION CAPABILITY DETECTION - LOCAL SCRIPT WITH DATAIKU API
================================================================================

PURPOSE:
    Detect applications with e-communication capabilities (ability to SEND emails,
    texts, SMS, video calls, voice calls, instant messages, push notifications, etc.)
    by semantically analyzing text data across multiple database tables in Dataiku.

CRITICAL DISTINCTION:
    ✅ DETECT: Apps that LET USERS SEND communications
    ❌ DO NOT DETECT: Apps that just COLLECT/STORE communication data

USAGE:
    1. Install requirements: pip install dataiku-api-client sentence-transformers pandas numpy
    2. Configure your Dataiku connection settings below
    3. Run: python ecomm_detection_local.py

REQUIREMENTS:
    - dataiku-api-client (pip install dataiku-api-client)
    - sentence-transformers (pip install sentence-transformers)
    - pandas
    - numpy

AUTHOR: Generated for Dataiku Integration
VERSION: 4.0.0 (Local Execution with Sentence-Transformers)
================================================================================
"""

import os
import sys
import re
import warnings
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Set, Any
from datetime import datetime

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ================================================================================
# STEP 1: INSTALL AND IMPORT DEPENDENCIES
# ================================================================================

def install_package(package_name: str) -> bool:
    """Attempt to install a package using pip."""
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name, '-q'])
        return True
    except subprocess.CalledProcessError:
        return False

# Check and install required packages
required_packages = {
    'dataiku': 'dataiku-api-client',
    'sentence_transformers': 'sentence-transformers',
    'pandas': 'pandas',
    'numpy': 'numpy',
}

for module_name, pip_name in required_packages.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"Installing {pip_name}...")
        if not install_package(pip_name):
            print(f"ERROR: Failed to install {pip_name}. Please install manually:")
            print(f"  pip install {pip_name}")
            sys.exit(1)

# Now import all required packages
import pandas as pd
import numpy as np
import dataiku
from sentence_transformers import SentenceTransformer

# ================================================================================
# CONFIGURATION - MODIFY THESE SETTINGS
# ================================================================================

# Dataiku Connection Settings
DATAIKU_URL = "https://your-dataiku-instance.com"  # Your Dataiku DSS URL
DATAIKU_API_KEY = "your-api-key-here"              # Your API key
PROJECT_KEY = "YOUR_PROJECT_KEY"                    # Your project key

# Alternatively, use environment variables (recommended for security):
# DATAIKU_URL = os.environ.get('DKU_DSS_URL', 'https://your-dataiku-instance.com')
# DATAIKU_API_KEY = os.environ.get('DKU_API_KEY', 'your-api-key-here')
# PROJECT_KEY = os.environ.get('DKU_PROJECT_KEY', 'YOUR_PROJECT_KEY')

# Input table names to scan
INPUT_TABLES = ['table1', 'table2', 'table3', 'table4']

# Output dataset name (will be created if it doesn't exist)
OUTPUT_DATASET = "ecomm_detection_results"

# Sentence-Transformers model to use
# Options: 'all-MiniLM-L6-v2' (fast), 'all-mpnet-base-v2' (more accurate)
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

# Classification threshold (0.0 to 1.0)
# Lower = more lenient (catches more, may have false positives)
# Higher = more strict (fewer results, higher precision)
SEMANTIC_THRESHOLD = 0.55

# Minimum evidence pieces required to flag an IDN_EON
MIN_FINDINGS_REQUIRED = 1

# Progress reporting interval
PROGRESS_INTERVAL = 100

# Maximum sample content examples to store per IDN_EON
MAX_SAMPLE_CONTENT = 3

# Invalid IDN_EON values to exclude
INVALID_VALUES = {'nan', 'none', '', 'null', 'n/a', 'na', 'n.a.', '-', '--', 'unknown', ' '}

# Batch size for embedding (adjust based on available memory)
EMBEDDING_BATCH_SIZE = 64

# ================================================================================
# TRAINING DATA - E-COMMUNICATION SENDING EXAMPLES (200+)
# ================================================================================

ECOMM_SENDING_EXAMPLES = [
    # EMAIL SENDING
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
    "email communication system",
    "outgoing email functionality",
    "email send capability",
    "can dispatch emails",
    "email delivery service",
    "sends confirmation emails automatically",
    "email sending integrated",
    "users email each other",
    "send emails to contacts",
    "email recipients receive messages",
    "email sending workflow",
    
    # TEXT/SMS SENDING
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
    "SMS alerts delivered",
    "sends promotional texts",
    "text messaging service",
    "SMS enabled application",
    "text delivery system",
    "sends order updates via text",
    "SMS communication capability",
    "text message sender",
    "mobile SMS alerts",
    "text messaging enabled",
    "SMS dispatch functionality",
    "sends transactional SMS",
    "text messaging feature",
    "SMS notification delivery",
    "sends confirmation texts",
    "text alert capability",
    
    # VIDEO CALLING
    "users can make video calls",
    "video calling feature enabled",
    "video conferencing capability",
    "video chat between users",
    "video call functionality",
    "supports video calling",
    "video communication platform",
    "video call feature",
    "make video calls in app",
    "video calling service",
    "video chat capability",
    "video conferencing enabled",
    "video call support",
    "real-time video calling",
    "video communication feature",
    "video calls between users",
    "video meeting capability",
    "video calling platform",
    "HD video calls",
    "video call system",
    "group video calling",
    "one-on-one video calls",
    "video calling enabled",
    "video chat service",
    "video conference calls",
    "video call integration",
    "face-to-face video calls",
    "video calling application",
    "video communication service",
    "video call experience",
    
    # VOICE CALLING
    "users can make voice calls",
    "voice calling platform enabled",
    "VoIP capability available",
    "phone call feature in app",
    "voice communication enabled",
    "voice call functionality",
    "make phone calls through app",
    "voice calling service",
    "VoIP calling feature",
    "voice call capability",
    "internet calling enabled",
    "voice calls between users",
    "phone calling platform",
    "voice communication feature",
    "audio calling capability",
    "voice call support",
    "make calls via app",
    "voice calling enabled",
    "phone call capability",
    "VoIP phone service",
    "voice call feature",
    "calling functionality",
    "voice communication system",
    "audio calls supported",
    "voice calling application",
    "telephone capability",
    "call users directly",
    "voice chat feature",
    "audio communication",
    "voice calling system",
    
    # INSTANT MESSAGING
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
    "instant message feature",
    "chat platform",
    "messaging service",
    "user-to-user messaging",
    "chat messaging enabled",
    "message delivery system",
    "send chat messages",
    "messaging feature available",
    "instant communication",
    "chat capability",
    "messaging enabled",
    "direct chat feature",
    "real-time chat",
    "message each other",
    "chat between users",
    "messaging platform",
    "instant messaging service",
    "chat system",
    "send instant messages",
    "messaging functionality",
    "chat communication",
    "user messaging feature",
    
    # PUSH NOTIFICATIONS
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
    "delivers mobile notifications",
    "notification push service",
    "sends in-app notifications",
    "push messaging enabled",
    "notification delivery capability",
    "mobile push capability",
    "sends notification alerts",
    "push notification delivery",
    "app notifications sent",
    "push alert system",
    "notification sending feature",
    "delivers app alerts",
    "push notifications enabled",
    "mobile alert system",
    "notification dispatch",
    "sends push alerts",
    
    # E-COMMUNICATIONS EXPLICIT
    "e-communication enabled",
    "e-communications platform",
    "e-communication services",
    "electronic communication capability",
    "e-communication feature",
    "electronic messaging enabled",
    "e-communication system",
    "digital communication platform",
    "e-communication capability",
    "electronic communication services",
    "e-comms enabled",
    "e-communication functionality",
    "electronic communication feature",
    "e-communication support",
    "digital messaging capability",
    
    # GENERAL COMMUNICATION SENDING
    "notification delivery system",
    "alert sending feature",
    "communication capability enabled",
    "messaging service active",
    "sends alerts to users",
    "notification sending capability",
    "delivers communications",
    "communication sending feature",
    "alert delivery system",
    "sends user notifications",
    "communication platform enabled",
    "delivers alerts automatically",
    "notification capability",
    "sends communications",
    "message delivery service",
    "alert notification system",
    "communication delivery feature",
    "sends alerts automatically",
    "notification service enabled",
    "communication dispatch",
]

# ================================================================================
# TRAINING DATA - DATA COLLECTION EXAMPLES (200+)
# ================================================================================

DATA_COLLECTION_EXAMPLES = [
    # EMAIL COLLECTION
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
    "email address gathered",
    "collects emails for records",
    "email data collection",
    "captures user email address",
    "email collection process",
    "gathers customer emails",
    "stores user email addresses",
    "email collected from users",
    "collects contact email",
    "email address captured",
    "gathers email information",
    "email storage system",
    "collects email for contact",
    "email data gathered",
    "captures email addresses",
    
    # STORAGE
    "saves email in database",
    "email on file for records",
    "retains email address",
    "email records stored",
    "maintains email addresses",
    "email stored in system",
    "preserves email data",
    "email retained in database",
    "stores email permanently",
    "email saved for reference",
    "keeps email on record",
    "email archived in database",
    "stores user emails",
    "email data preserved",
    "maintains email records",
    "email address retained",
    "stores contact emails",
    "email kept in system",
    "saves user email",
    "email data stored",
    "retains user email",
    "email maintained in database",
    "stores email information",
    "email preserved in records",
    "keeps email addresses",
    
    # REGISTRATION/LOGIN
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
    "account email required",
    "login using email address",
    "email for user registration",
    "email-based login",
    "register using email",
    "email for account setup",
    "email required to register",
    "sign in using email",
    "email authentication required",
    "login email address",
    "email for signup process",
    "account creation email",
    "email needed for login",
    "register email address",
    
    # FORMS
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
    "form email field",
    "email address input",
    "type email address",
    "email field required",
    "enter your email",
    "email input box",
    "form requires email",
    "email text field",
    "input field for email",
    "email address field",
    "provide your email",
    "email entry required",
    "fill email field",
    "email input area",
    "email form input",
    
    # VALIDATION
    "validates email format",
    "verifies email address",
    "checks email syntax",
    "email format validation",
    "email validation check",
    "verify email format",
    "email syntax check",
    "validates user email",
    "email address verification",
    "check email format",
    "email validation required",
    "verifies email format",
    "email format check",
    "validates email address",
    "email verification process",
    "checks email validity",
    "email format verified",
    "validates email input",
    "email syntax validation",
    "verify email address",
    
    # DATABASE/TECHNICAL
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
    "text data type email",
    "email varchar column",
    "database email field",
    "email stored as text",
    "plaintext email storage",
    "text field stores email",
    "email text column",
    "varchar email storage",
    "database column email",
    "email string field",
    "text type email",
    "email column varchar",
    "field type text email",
    "email plaintext field",
    "text storage email",
    
    # LIST FORMAT (MAJOR REJECTION INDICATOR)
    "email, phone",
    "phone, email",
    "email and phone number",
    "email, phone, address",
    "fields: email, phone",
    "email phone address",
    "contact: email, phone",
    "email, phone collected",
    "stores email, phone",
    "email, mobile, address",
    "name, email, phone",
    "email phone fields",
    "email, telephone",
    "phone and email",
    "email, phone, fax",
    "email phone number",
    "collects email phone",
    "email, cell phone",
    "email, phone stored",
    "email, phone required",
    "fields email phone",
    "email phone collected",
    "email, phone data",
    "email, phone information",
    "email and phone fields",
    
    # PHONE COLLECTION
    "collects phone numbers",
    "stores phone numbers",
    "gathers mobile numbers",
    "phone number field",
    "collects telephone numbers",
    "phone number collected",
    "stores mobile numbers",
    "phone field in form",
    "gathers phone data",
    "collects cell phone",
    "phone number storage",
    "captures phone number",
    "phone data collected",
    "stores telephone number",
    "phone number gathered",
    "collects contact phone",
    "mobile number field",
    "phone number input",
    "gathers user phone",
    "collects mobile phone",
    
    # PROFILE
    "email in user profile",
    "profile contains email",
    "account email address",
    "user profile email",
    "email on profile",
    "profile email field",
    "user account email",
    "email stored in profile",
    "profile shows email",
    "account profile email",
    "user email in profile",
    "profile email address",
    "email displayed in profile",
    "account contains email",
    "profile stores email",
    "user profile stores email",
    "email in account",
    "profile email storage",
    "account email field",
    "profile with email",
    
    # DISPLAY
    "displays email address",
    "shows email to user",
    "email visible in profile",
    "renders email field",
    "email shown on screen",
    "displays user email",
    "shows email address",
    "email displayed on page",
    "renders email address",
    "email visible to users",
    "displays contact email",
    "shows stored email",
    "email rendered on screen",
    "displays email data",
    "shows email in profile",
    "email address shown",
    "displays account email",
    "shows email field",
    "email visible on screen",
    "renders stored email",
    
    # 2FA ONLY
    "SMS verification code",
    "text verification code",
    "2FA via SMS",
    "one-time password text",
    "SMS OTP code",
    "text-based 2FA",
    "verification SMS",
    "SMS authentication code",
    "text message OTP",
    "2FA text message",
    "SMS security code",
    "verification text",
    "OTP via SMS",
    "text-based verification",
    "SMS one-time code",
    "authentication SMS",
    "verification code text",
    "SMS 2FA code",
    "text authentication",
    "OTP text message",
    
    # ADDITIONAL REJECTION PATTERNS
    "Japanese text",
    "Chinese text",
    "Korean text",
    "unicode text",
    "rich text field",
    "plain text format",
    "text encoding",
    "text representation",
    "text content type",
    "text blob field",
    "text area input",
    "multiline text",
    "text paragraph",
    "text document",
    "text string",
    "email optional",
    "email not required",
    "email can be blank",
    "email may be empty",
    "no email needed",
]

# ================================================================================
# HARD PATTERN MATCHING
# ================================================================================

# Patterns that automatically DISQUALIFY (return 0.0 confidence)
HARD_DISQUALIFIER_PATTERNS = [
    r'email\s*,\s*phone',
    r'phone\s*,\s*email',
    r'collects?\s+email',
    r'stores?\s+email',
    r'gathers?\s+email',
    r'email\s+for\s+login',
    r'email\s+as\s+username',
    r'email\s+required\s+for',
    r'email\s+needed\s+for',
    r'plaintext',
    r'text\s+field',
    r'text\s+data\s+type',
    r'text\s+column',
    r'varchar',
    r'japanese\s+text',
    r'chinese\s+text',
    r'korean\s+text',
    r'email\s+field',
    r'phone\s+field',
    r'login\s+with\s+email',
    r'sign\s+in\s+with\s+email',
    r'email\s+for\s+registration',
    r'email\s+for\s+account',
    r'email\s+validation',
    r'validates?\s+email',
    r'verif(?:y|ies)\s+email',
    r'email\s+input',
    r'enter\s+email',
    r'provide\s+email',
    r'email\s+address\s+field',
    r'email\s+form',
    r'form\s+email',
    r'email\s+in\s+database',
    r'database\s+email',
    r'email\s+column',
    r'collects?\s+phone',
    r'stores?\s+phone',
    r'phone\s+number\s+field',
    r'2fa\s+via\s+sms',
    r'sms\s+verification',
    r'verification\s+code',
    r'otp\s+(?:via\s+)?(?:sms|text)',
    r'text\s+(?:based\s+)?verification',
    r'one[- ]time\s+password',
    r'email\s*,\s*(?:phone|mobile|address)',
    r'(?:phone|mobile)\s*,\s*email',
    r'fields?\s*:\s*email',
    r'name\s*,\s*email',
    r'contact\s*:\s*email',
    r'stored\s+as\s+text',
    r'text\s+type',
    r'string\s+field',
    r'data\s+type\s*:\s*text',
    r'email\s+optional',
    r'email\s+can\s+be\s+blank',
]

# Patterns that automatically QUALIFY (return 0.95 confidence)
HARD_QUALIFIER_PATTERNS = [
    r'e[-\s]?communication',
    r'e[-\s]?communications',
    r'electronic\s+communication',
    r'can\s+send\s+email',
    r'can\s+send\s+text',
    r'can\s+send\s+message',
    r'can\s+send\s+sms',
    r'users?\s+send\s+email',
    r'users?\s+send\s+text',
    r'users?\s+send\s+message',
    r'app\s+sends?\s+email',
    r'app\s+sends?\s+notification',
    r'app\s+sends?\s+text',
    r'app\s+sends?\s+sms',
    r'app\s+sends?\s+alert',
    r'video\s+call(?:ing)?',
    r'voice\s+call(?:ing)?',
    r'video\s+chat',
    r'voice\s+chat',
    r'instant\s+messaging',
    r'messaging\s+platform',
    r'messaging\s+capability',
    r'messaging\s+feature',
    r'messaging\s+enabled',
    r'sends?\s+push\s+notification',
    r'push\s+notification\s+(?:system|capability|feature)',
    r'delivers?\s+push\s+notification',
    r'delivers?\s+notification',
    r'notification\s+delivery',
    r'sends?\s+(?:sms|text)\s+(?:alert|notification|message)',
    r'sends?\s+email\s+(?:alert|notification)',
    r'email\s+(?:sending|delivery)\s+(?:capability|feature|system)',
    r'sms\s+(?:sending|delivery)\s+(?:capability|feature|system)',
    r'text\s+(?:sending|delivery)\s+(?:capability|feature|system)',
    r'video\s+conferencing',
    r'voip\s+(?:capability|calling|feature)',
    r'real[- ]?time\s+(?:messaging|chat|communication)',
    r'direct\s+messaging',
    r'in[- ]?app\s+messaging',
    r'chat\s+(?:feature|capability|platform)',
    r'users?\s+(?:can\s+)?message\s+each\s+other',
    r'message\s+(?:sending|delivery)',
    r'communication\s+(?:platform|capability|feature)',
    r'alert\s+(?:sending|delivery)',
]

# ================================================================================
# SEMANTIC CLASSIFIER CLASS
# ================================================================================

class ECommSemanticClassifier:
    """
    Semantic classifier for detecting e-communication capabilities
    using sentence-transformers embeddings.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Initialize the classifier with the specified model."""
        print("\n" + "=" * 80)
        print("INITIALIZING SEMANTIC CLASSIFIER")
        print("=" * 80)
        
        # Load the sentence transformer model
        print(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"✓ Model loaded successfully!")
        
        # Compile regex patterns
        self.disqualifier_patterns = [
            re.compile(p, re.IGNORECASE) for p in HARD_DISQUALIFIER_PATTERNS
        ]
        self.qualifier_patterns = [
            re.compile(p, re.IGNORECASE) for p in HARD_QUALIFIER_PATTERNS
        ]
        
        # Generate embeddings for training examples
        self._generate_training_embeddings()
    
    def _generate_training_embeddings(self):
        """Generate embeddings for all training examples."""
        print("\nGenerating embeddings for training data...")
        
        # E-communication examples
        print(f"  Encoding {len(ECOMM_SENDING_EXAMPLES)} e-communication examples...")
        self.ecomm_embeddings = self.model.encode(
            ECOMM_SENDING_EXAMPLES,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=EMBEDDING_BATCH_SIZE
        )
        
        # Data collection examples
        print(f"  Encoding {len(DATA_COLLECTION_EXAMPLES)} data collection examples...")
        self.datacoll_embeddings = self.model.encode(
            DATA_COLLECTION_EXAMPLES,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=EMBEDDING_BATCH_SIZE
        )
        
        # Calculate centroids (mean of each category)
        self.ecomm_centroid = np.mean(self.ecomm_embeddings, axis=0)
        self.datacoll_centroid = np.mean(self.datacoll_embeddings, axis=0)
        
        print("✓ Training embeddings generated!")
        print(f"  E-comm embedding shape: {self.ecomm_embeddings.shape}")
        print(f"  Data collection embedding shape: {self.datacoll_embeddings.shape}")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def _check_hard_patterns(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Check for hard patterns that immediately determine classification.
        
        Returns:
            Tuple of (confidence, detection_method) or (None, None) if no match
        """
        text_lower = text.lower()
        
        # Check disqualifiers first
        for pattern in self.disqualifier_patterns:
            if pattern.search(text_lower):
                return (0.0, "hard_disqualifier")
        
        # Check qualifiers
        for pattern in self.qualifier_patterns:
            if pattern.search(text_lower):
                return (0.95, "hard_qualifier")
        
        return (None, None)
    
    def classify(self, text: str) -> Tuple[float, str]:
        """
        Classify text to determine if it describes e-communication capability.
        
        Args:
            text: The text to classify
            
        Returns:
            Tuple of (confidence, detection_method)
        """
        if not text or not isinstance(text, str) or len(text.strip()) < 3:
            return (0.0, "invalid_input")
        
        text = text.strip()
        
        # Step 1: Check hard patterns first
        hard_result = self._check_hard_patterns(text)
        if hard_result[0] is not None:
            return hard_result
        
        # Step 2: Semantic classification
        try:
            # Encode the input text
            text_embedding = self.model.encode([text], convert_to_numpy=True)[0]
            
            # Calculate similarity to centroids
            ecomm_centroid_sim = self._cosine_similarity(text_embedding, self.ecomm_centroid)
            datacoll_centroid_sim = self._cosine_similarity(text_embedding, self.datacoll_centroid)
            
            # Calculate max similarity to individual examples
            ecomm_sims = np.array([
                self._cosine_similarity(text_embedding, emb) 
                for emb in self.ecomm_embeddings
            ])
            datacoll_sims = np.array([
                self._cosine_similarity(text_embedding, emb) 
                for emb in self.datacoll_embeddings
            ])
            
            ecomm_max_sim = np.max(ecomm_sims)
            datacoll_max_sim = np.max(datacoll_sims)
            
            # Calculate 90th percentile similarity
            ecomm_p90_sim = np.percentile(ecomm_sims, 90)
            datacoll_p90_sim = np.percentile(datacoll_sims, 90)
            
            # Average the three scores for each category
            avg_ecomm = (ecomm_centroid_sim + ecomm_max_sim + ecomm_p90_sim) / 3
            avg_datacoll = (datacoll_centroid_sim + datacoll_max_sim + datacoll_p90_sim) / 3
            
            # Calculate final score
            total = avg_ecomm + avg_datacoll
            if total == 0:
                confidence = 0.5
            else:
                confidence = avg_ecomm / total
            
            return (confidence, "semantic_embedding")
            
        except Exception as e:
            print(f"    Warning: Semantic classification failed: {e}")
            return (0.0, "classification_error")
    
    def classify_batch(self, texts: List[str]) -> List[Tuple[float, str]]:
        """
        Classify multiple texts in batch for efficiency.
        
        Args:
            texts: List of texts to classify
            
        Returns:
            List of (confidence, detection_method) tuples
        """
        results = []
        
        # First, check hard patterns for all texts
        hard_pattern_results = {}
        texts_for_semantic = []
        text_indices = []
        
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str) or len(str(text).strip()) < 3:
                hard_pattern_results[i] = (0.0, "invalid_input")
            else:
                hard_result = self._check_hard_patterns(str(text))
                if hard_result[0] is not None:
                    hard_pattern_results[i] = hard_result
                else:
                    texts_for_semantic.append(str(text).strip())
                    text_indices.append(i)
        
        # Batch encode texts that need semantic classification
        if texts_for_semantic:
            text_embeddings = self.model.encode(
                texts_for_semantic,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=EMBEDDING_BATCH_SIZE
            )
            
            for j, embedding in enumerate(text_embeddings):
                # Calculate similarities
                ecomm_centroid_sim = self._cosine_similarity(embedding, self.ecomm_centroid)
                datacoll_centroid_sim = self._cosine_similarity(embedding, self.datacoll_centroid)
                
                ecomm_sims = np.array([
                    self._cosine_similarity(embedding, emb) 
                    for emb in self.ecomm_embeddings
                ])
                datacoll_sims = np.array([
                    self._cosine_similarity(embedding, emb) 
                    for emb in self.datacoll_embeddings
                ])
                
                ecomm_max_sim = np.max(ecomm_sims)
                datacoll_max_sim = np.max(datacoll_sims)
                ecomm_p90_sim = np.percentile(ecomm_sims, 90)
                datacoll_p90_sim = np.percentile(datacoll_sims, 90)
                
                avg_ecomm = (ecomm_centroid_sim + ecomm_max_sim + ecomm_p90_sim) / 3
                avg_datacoll = (datacoll_centroid_sim + datacoll_max_sim + datacoll_p90_sim) / 3
                
                total = avg_ecomm + avg_datacoll
                confidence = avg_ecomm / total if total > 0 else 0.5
                
                hard_pattern_results[text_indices[j]] = (confidence, "semantic_embedding")
        
        # Compile results in order
        for i in range(len(texts)):
            results.append(hard_pattern_results.get(i, (0.0, "unknown")))
        
        return results

# ================================================================================
# DATAIKU CONNECTION AND DATA FUNCTIONS
# ================================================================================

def connect_to_dataiku() -> Tuple[Any, Any]:
    """
    Connect to Dataiku and return client and project handles.
    
    Returns:
        Tuple of (client, project)
    """
    print("\n" + "=" * 80)
    print("CONNECTING TO DATAIKU")
    print("=" * 80)
    
    try:
        # Set up remote connection
        dataiku.set_remote_dss(DATAIKU_URL, DATAIKU_API_KEY)
        client = dataiku.api_client()
        
        # Test connection
        projects = client.list_project_keys()
        print(f"✓ Connected to Dataiku at {DATAIKU_URL}")
        print(f"  Available projects: {len(projects)}")
        
        # Get the project
        project = client.get_project(PROJECT_KEY)
        print(f"✓ Connected to project: {PROJECT_KEY}")
        
        return client, project
        
    except Exception as e:
        print(f"✗ Failed to connect to Dataiku: {e}")
        print("\nPlease check:")
        print("  1. DATAIKU_URL is correct")
        print("  2. DATAIKU_API_KEY is valid")
        print("  3. PROJECT_KEY exists and you have access")
        raise

def load_datasets(project) -> Dict[str, pd.DataFrame]:
    """
    Load all input datasets from Dataiku.
    
    Args:
        project: Dataiku project handle
        
    Returns:
        Dictionary mapping table names to DataFrames
    """
    print("\n" + "=" * 80)
    print("LOADING INPUT DATASETS")
    print("=" * 80)
    
    tables = {}
    
    for table_name in INPUT_TABLES:
        try:
            print(f"  Loading '{table_name}'...")
            dataset = project.get_dataset(table_name)
            df = dataset.get_dataframe()
            
            # Convert all columns to string for consistent processing
            for col in df.columns:
                df[col] = df[col].astype(str)
            
            tables[table_name] = df
            print(f"    ✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
            
        except Exception as e:
            print(f"    ✗ Failed to load '{table_name}': {e}")
    
    if not tables:
        raise ValueError("No tables could be loaded!")
    
    return tables

def find_idn_eon_column(df: pd.DataFrame) -> Optional[str]:
    """Find the IDN_EON column (case-insensitive)."""
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            return col
    return None

def is_valid_idn_eon(value: Any) -> bool:
    """Check if an IDN_EON value is valid."""
    if value is None:
        return False
    str_value = str(value).strip().lower()
    return str_value not in INVALID_VALUES and len(str_value) > 0

def extract_unique_idn_eons(tables: Dict[str, pd.DataFrame]) -> Set[str]:
    """Extract all unique IDN_EON values across all tables."""
    print("\n" + "=" * 80)
    print("EXTRACTING UNIQUE IDN_EON VALUES")
    print("=" * 80)
    
    all_idn_eons = set()
    
    for table_name, df in tables.items():
        idn_col = find_idn_eon_column(df)
        
        if idn_col is None:
            print(f"  ⚠ Table '{table_name}': No IDN_EON column found - skipping")
            continue
        
        values = df[idn_col].dropna().unique()
        valid_count = 0
        
        for val in values:
            if is_valid_idn_eon(val):
                all_idn_eons.add(str(val).strip())
                valid_count += 1
        
        print(f"  ✓ Table '{table_name}': Found {valid_count:,} valid IDN_EON values")
    
    total = len(all_idn_eons)
    print(f"\n{'=' * 80}")
    print(f"TOTAL UNIQUE IDN_EON: {total:,}")
    print(f"{'=' * 80}")
    
    return all_idn_eons

def contains_communication_keyword(text: str) -> bool:
    """Quick check if text contains any communication-related keywords."""
    if not text or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    keywords = [
        'email', 'e-mail', 'mail',
        'text', 'sms',
        'message', 'messaging',
        'call', 'calling',
        'video', 'voice', 'audio',
        'chat', 'chatting',
        'notification', 'notify',
        'alert',
        'push',
        'communicat',
        'voip', 'telephon',
    ]
    
    return any(kw in text_lower for kw in keywords)

def analyze_idn_eon(
    idn_eon: str,
    tables: Dict[str, pd.DataFrame],
    classifier: ECommSemanticClassifier
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single IDN_EON for e-communication capabilities.
    
    Args:
        idn_eon: The IDN_EON value to analyze
        tables: Dictionary of table DataFrames
        classifier: The semantic classifier
        
    Returns:
        Dictionary with findings if e-communication detected, None otherwise
    """
    findings = []
    found_in_tables = set()
    found_in_columns = set()
    sample_contents = []
    texts_to_classify = []
    text_metadata = []
    
    # Collect all text that needs classification
    for table_name, df in tables.items():
        idn_col = find_idn_eon_column(df)
        if idn_col is None:
            continue
        
        # Find rows with this IDN_EON
        mask = df[idn_col].astype(str).str.strip() == idn_eon
        matching_rows = df[mask]
        
        if matching_rows.empty:
            continue
        
        found_in_tables.add(table_name)
        
        # Collect text from each column
        for col in df.columns:
            if col == idn_col:
                continue
            
            for idx, value in matching_rows[col].items():
                try:
                    text = str(value).strip()
                except:
                    continue
                
                if len(text) < 5:
                    continue
                
                # Quick keyword check for efficiency
                if not contains_communication_keyword(text):
                    continue
                
                texts_to_classify.append(text)
                text_metadata.append({
                    'column': col,
                    'table': table_name,
                    'text': text[:500]
                })
    
    # Batch classify all texts
    if texts_to_classify:
        results = classifier.classify_batch(texts_to_classify)
        
        for i, (confidence, method) in enumerate(results):
            if confidence > SEMANTIC_THRESHOLD:
                meta = text_metadata[i]
                findings.append({
                    'column': meta['column'],
                    'table': meta['table'],
                    'confidence': confidence,
                    'method': method,
                    'text': meta['text']
                })
                found_in_columns.add(meta['column'])
                
                if len(sample_contents) < MAX_SAMPLE_CONTENT:
                    sample_contents.append(meta['text'][:200])
    
    # Return None if no findings meet minimum requirement
    if len(findings) < MIN_FINDINGS_REQUIRED:
        return None
    
    # Calculate aggregate confidence
    confidences = [f['confidence'] for f in findings]
    max_confidence = max(confidences)
    avg_confidence = sum(confidences) / len(confidences)
    
    # Use weighted confidence (max * 0.7 + avg * 0.3)
    final_confidence = max_confidence * 0.7 + avg_confidence * 0.3
    
    # Determine primary detection method
    methods = [f['method'] for f in findings]
    primary_method = max(set(methods), key=methods.count)
    
    return {
        'IDN_EON': idn_eon,
        'data_source': ', '.join(sorted(found_in_tables)),
        'ecomm_confidence': round(final_confidence, 4),
        'detection_method': primary_method,
        'found_in': ', '.join(sorted(found_in_columns)),
        'sample_content': ' | '.join(sample_contents),
        'total_findings': len(findings),
    }

def write_results_to_dataiku(project, results: List[Dict], output_name: str):
    """
    Write results back to Dataiku as a new dataset.
    
    Args:
        project: Dataiku project handle
        results: List of result dictionaries
        output_name: Name for the output dataset
    """
    print("\n" + "=" * 80)
    print("WRITING RESULTS TO DATAIKU")
    print("=" * 80)
    
    # Create DataFrame from results
    if results:
        output_df = pd.DataFrame(results)
        output_df = output_df.sort_values('ecomm_confidence', ascending=False)
    else:
        output_df = pd.DataFrame(columns=[
            'IDN_EON', 'data_source', 'ecomm_confidence', 'detection_method',
            'found_in', 'sample_content', 'total_findings'
        ])
    
    try:
        # Get or create the output dataset
        try:
            dataset = project.get_dataset(output_name)
            print(f"  Using existing dataset: {output_name}")
        except:
            # Create new dataset if it doesn't exist
            builder = project.new_managed_dataset(output_name)
            builder.with_store_into("filesystem_managed")  # Adjust connection as needed
            dataset = builder.create()
            print(f"  Created new dataset: {output_name}")
        
        # Write the data
        with dataset.get_writer() as writer:
            # Write schema
            schema = [
                {'name': 'IDN_EON', 'type': 'string'},
                {'name': 'data_source', 'type': 'string'},
                {'name': 'ecomm_confidence', 'type': 'double'},
                {'name': 'detection_method', 'type': 'string'},
                {'name': 'found_in', 'type': 'string'},
                {'name': 'sample_content', 'type': 'string'},
                {'name': 'total_findings', 'type': 'bigint'},
            ]
            dataset.write_schema(schema)
            
            # Write rows
            for _, row in output_df.iterrows():
                writer.write_row_dict(row.to_dict())
        
        print(f"  ✓ Successfully wrote {len(output_df):,} rows to '{output_name}'")
        
    except Exception as e:
        print(f"  ✗ Failed to write to Dataiku: {e}")
        print("  Saving results locally instead...")
        
        # Save locally as fallback
        local_filename = f"ecomm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_df.to_csv(local_filename, index=False)
        print(f"  ✓ Saved to local file: {local_filename}")

def run_tests(classifier: ECommSemanticClassifier) -> float:
    """Run tests to validate classifier accuracy."""
    print("\n" + "=" * 80)
    print("RUNNING CLASSIFIER TESTS")
    print("=" * 80)
    
    test_cases = [
        # Should DETECT (True positives)
        ("users can send emails through the app", True, "email sending"),
        ("app sends push notifications to users", True, "push notifications"),
        ("video calling between users", True, "video calling"),
        ("instant messaging capability", True, "instant messaging"),
        ("platform enables text messaging", True, "text messaging"),
        ("app sends SMS alerts", True, "SMS alerts"),
        ("voice calling feature enabled", True, "voice calling"),
        ("e-communication services enabled", True, "e-communication"),
        ("delivers email notifications automatically", True, "email delivery"),
        ("real-time chat between users", True, "real-time chat"),
        
        # Should REJECT (True negatives)
        ("collects email addresses", False, "email collection"),
        ("email address for registration", False, "email registration"),
        ("email, phone, address collected", False, "list format"),
        ("login with email", False, "email login"),
        ("stores phone numbers in database", False, "phone storage"),
        ("email field in form", False, "form field"),
        ("validates email format", False, "validation"),
        ("plaintext email field", False, "database field"),
        ("SMS verification code for 2FA", False, "2FA only"),
        ("email, phone required for signup", False, "collection list"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for text, expected, description in test_cases:
        confidence, method = classifier.classify(text)
        predicted = confidence > SEMANTIC_THRESHOLD
        
        status = "✓" if predicted == expected else "✗"
        correct += 1 if predicted == expected else 0
        
        expected_str = "DETECT" if expected else "REJECT"
        actual_str = "DETECT" if predicted else "REJECT"
        
        print(f"  {status} [{description}] Expected: {expected_str}, Got: {actual_str} (conf: {confidence:.3f})")
    
    accuracy = (correct / total) * 100
    
    print(f"\n{'=' * 80}")
    print(f"TEST ACCURACY: {accuracy:.1f}% ({correct}/{total})")
    print(f"{'=' * 80}")
    
    if accuracy >= 90:
        print("✓ Classifier PASSED accuracy threshold (90%+)")
    else:
        print("⚠ Classifier BELOW accuracy threshold (90%+)")
    
    return accuracy

# ================================================================================
# MAIN EXECUTION
# ================================================================================

def main():
    """Main execution function."""
    start_time = datetime.now()
    
    print("\n" + "=" * 80)
    print("E-COMMUNICATION CAPABILITY DETECTION")
    print("Local Execution with Dataiku API + Sentence-Transformers")
    print("=" * 80)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dataiku URL: {DATAIKU_URL}")
    print(f"Project: {PROJECT_KEY}")
    print(f"Input Tables: {INPUT_TABLES}")
    print(f"Output Dataset: {OUTPUT_DATASET}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print(f"Threshold: {SEMANTIC_THRESHOLD}")
    
    # Initialize classifier
    classifier = ECommSemanticClassifier(EMBEDDING_MODEL)
    
    # Run tests
    test_accuracy = run_tests(classifier)
    
    if test_accuracy < 80:
        print("\n⚠ WARNING: Classifier accuracy is below 80%. Results may be unreliable.")
    
    # Connect to Dataiku
    client, project = connect_to_dataiku()
    
    # Load datasets
    tables = load_datasets(project)
    
    # Extract unique IDN_EON values
    all_idn_eons = extract_unique_idn_eons(tables)
    
    if not all_idn_eons:
        print("\n✗ ERROR: No valid IDN_EON values found. Exiting.")
        return
    
    # Analyze each IDN_EON
    print("\n" + "=" * 80)
    print("ANALYZING IDN_EON FOR E-COMMUNICATION CAPABILITIES")
    print("=" * 80)
    
    results = []
    processed = 0
    total_idn_eons = len(all_idn_eons)
    
    for idn_eon in sorted(all_idn_eons):
        processed += 1
        
        # Progress update
        if processed % PROGRESS_INTERVAL == 0 or processed == total_idn_eons:
            pct = processed * 100 / total_idn_eons
            print(f"  Progress: {processed:,}/{total_idn_eons:,} ({pct:.1f}%) - Found {len(results):,} with e-comm")
        
        try:
            result = analyze_idn_eon(idn_eon, tables, classifier)
            if result:
                results.append(result)
        except Exception as e:
            print(f"    ⚠ Error analyzing IDN_EON '{idn_eon}': {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"  Total Unique IDN_EON Found: {total_idn_eons:,}")
    print(f"  IDN_EON with E-Communication: {len(results):,}")
    print(f"  Percentage with E-Communication: {len(results)*100/total_idn_eons:.2f}%")
    print(f"  Detection Mode: Semantic (Sentence-Transformers)")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Threshold: {SEMANTIC_THRESHOLD}")
    
    if results:
        confidences = [r['ecomm_confidence'] for r in results]
        print(f"\n  Confidence Distribution:")
        print(f"    Max: {max(confidences):.4f}")
        print(f"    Min: {min(confidences):.4f}")
        print(f"    Mean: {sum(confidences)/len(confidences):.4f}")
        
        print(f"\n  Top 10 Results by Confidence:")
        sorted_results = sorted(results, key=lambda x: x['ecomm_confidence'], reverse=True)
        for i, r in enumerate(sorted_results[:10]):
            print(f"    {i+1}. {r['IDN_EON']} (conf: {r['ecomm_confidence']:.4f}) - {r['detection_method']}")
    
    # Write results to Dataiku
    write_results_to_dataiku(project, results, OUTPUT_DATASET)
    
    # Final timing
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("SCRIPT COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration: {duration}")

# ================================================================================
# ENTRY POINT
# ================================================================================

if __name__ == "__main__":
    main()
