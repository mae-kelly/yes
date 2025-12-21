# -*- coding: utf-8 -*-
"""
================================================================================
E-COMMUNICATION CAPABILITY DETECTION - DATAIKU PYTHON RECIPE
================================================================================

USAGE IN DATAIKU:
    1. Create a new Python Recipe in your Dataiku project
    2. Set 4 input datasets (your source tables with IDN_EON column)
    3. Set 1 output dataset name (will be created with schema)
    4. Paste this entire script into the recipe
    5. Run the recipe

SEMANTIC UNDERSTANDING OPTIONS (in order of preference):
    1. Dataiku LLM Mesh embeddings (if LLM connection configured)
    2. Dataiku LLM Mesh completion for classification (if LLM connection configured)  
    3. TF-IDF vectorization with scikit-learn (always available, no setup needed)

OUTPUT COLUMNS:
    - IDN_EON: Unique identifier
    - source_tables: Which table(s) the IDN_EON was found in (comma-separated)
    - has_ecomm_capability: YES/NO
    - ecomm_confidence: 0.0 to 1.0 confidence score
    - ecomm_evidence: Sample text that triggered detection
    - detection_details: Columns and method used for detection

VERSION: 6.0.0
================================================================================
"""

import dataiku
import pandas as pd
import numpy as np
import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Set, Any

# Try to import scikit-learn for TF-IDF fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("WARNING: scikit-learn not available. Using pattern matching only.")

# ================================================================================
# CONFIGURATION
# ================================================================================

# LLM Configuration (set to None to skip LLM, or set to your LLM ID)
# To find your LLM ID, run: project.list_llms() 
# Example: "openai:my-connection:gpt-4" or "azure-openai:my-connection:gpt-35-turbo"
LLM_ID = None  # Set to your LLM ID string, or None to use TF-IDF/patterns only

# Classification threshold (0.0 to 1.0)
ECOMM_THRESHOLD = 0.55

# Minimum text length to analyze
MIN_TEXT_LENGTH = 5

# Maximum evidence samples per IDN_EON
MAX_EVIDENCE_SAMPLES = 3

# Batch size for LLM calls (to avoid rate limits)
LLM_BATCH_SIZE = 10

# Invalid IDN_EON values to exclude
INVALID_IDN_EON_VALUES = {
    'nan', 'none', '', 'null', 'n/a', 'na', 'n.a.', 
    '-', '--', 'unknown', ' ', 'undefined', '#n/a', '#null'
}

# ================================================================================
# FALSE POSITIVES - Strings incorrectly flagged as e-comm (add your own)
# ================================================================================

FALSE_POSITIVES = [
    # --- ADD YOUR FALSE POSITIVES BELOW ---
    # Example: "message queue for batch processing",
    # Example: "call stack trace logging",
    
    
    # --- ADD YOUR FALSE POSITIVES ABOVE ---
]

# ================================================================================
# FALSE NEGATIVES - Strings that SHOULD be flagged but aren't (add your own)
# ================================================================================

FALSE_NEGATIVES = [
    # --- ADD YOUR FALSE NEGATIVES BELOW ---
    # Example: "proprietary messaging system",
    # Example: "custom notification framework",
    
    
    # --- ADD YOUR FALSE NEGATIVES ABOVE ---
]

# ================================================================================
# TRAINING EXAMPLES FOR SEMANTIC MATCHING
# ================================================================================

# E-COMMUNICATION SENDING EXAMPLES (what we want to DETECT)
ECOMM_SENDING_EXAMPLES = [
    # Email sending
    "users can send emails through the app",
    "app sends email notifications to users",
    "email delivery capability enabled",
    "sends promotional emails to customers",
    "email sending feature available",
    "users send emails within the platform",
    "automatic email sending system",
    "sends welcome emails to new users",
    "email notification delivery system",
    "outgoing email functionality",
    "bulk email delivery system",
    "sends confirmation emails automatically",
    "email broadcast feature enabled",
    "delivers email communications",
    "email dispatch functionality",
    
    # SMS/Text sending
    "users can send texts through the app",
    "app sends SMS alerts to users",
    "text message delivery system",
    "SMS notification system enabled",
    "send appointment reminder texts",
    "text messaging capability",
    "SMS sending feature",
    "sends text notifications",
    "bulk SMS sending capability",
    "automated text messages",
    "SMS messaging platform",
    "text notification delivery",
    "mobile SMS alerts sent",
    "sends promotional texts",
    
    # Video/Voice calling
    "users can make video calls",
    "video calling feature enabled",
    "video conferencing capability",
    "video chat between users",
    "voice calling platform enabled",
    "VoIP capability available",
    "make phone calls through app",
    "video call functionality",
    "voice communication enabled",
    "real-time video calling",
    "audio calling capability",
    
    # Instant messaging
    "users can send messages",
    "instant messaging capability",
    "chat feature enabled",
    "messaging between users",
    "direct messaging platform",
    "in-app messaging",
    "real-time messaging",
    "users message each other",
    "chat functionality",
    "send direct messages",
    "messaging platform enabled",
    "instant chat feature",
    
    # Push notifications
    "sends push notifications to users",
    "delivers push notifications",
    "mobile push alerts enabled",
    "push notification system",
    "sends app notifications",
    "notification delivery system",
    "mobile notifications enabled",
    "push notification capability",
    "sends mobile alerts",
    "app push notifications sent",
    
    # E-communications explicit
    "e-communication enabled",
    "e-communications platform",
    "e-communication services",
    "electronic communication capability",
    "digital communication platform",
    
    # General sending
    "sends alerts to users",
    "notification sending capability",
    "delivers communications automatically",
    "communication platform enabled",
    "alert delivery system",
]

# DATA COLLECTION EXAMPLES (what we want to REJECT)
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
    "stores email data",
    
    # Storage
    "saves email in database",
    "email on file for records",
    "retains email address",
    "email records stored",
    "maintains email addresses",
    "email stored in system",
    "stores email permanently",
    "keeps email on record",
    "email archived in database",
    
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
    
    # Forms
    "email field in form",
    "email input field",
    "enter email address",
    "provide email in form",
    "email form field",
    "email text box",
    "email entry field",
    "email address input",
    "email field required",
    
    # Validation
    "validates email format",
    "verifies email address",
    "checks email syntax",
    "email format validation",
    "email validation check",
    
    # Database/Technical
    "email field in database",
    "email column in table",
    "email data type",
    "plaintext email field",
    "text field for email",
    "varchar email field",
    "email database column",
    "stored as text",
    
    # List format (major indicator)
    "email, phone",
    "phone, email",
    "email and phone number",
    "email, phone, address",
    "name, email, phone",
    "email phone fields",
    "email, phone collected",
    "contact: email, phone",
    
    # Phone collection
    "collects phone numbers",
    "stores phone numbers",
    "gathers mobile numbers",
    "phone number field",
    "phone number collected",
    
    # Profile/Display
    "email in user profile",
    "profile contains email",
    "displays email address",
    "email visible in profile",
    "shows email address",
    
    # 2FA only
    "SMS verification code",
    "text verification code",
    "2FA via SMS",
    "one-time password text",
    "SMS OTP code",
    "verification SMS",
    "SMS authentication code",
    
    # Non-communication text
    "Japanese text",
    "Chinese text",
    "unicode text",
    "plain text format",
    "text encoding",
    "email optional",
]

# ================================================================================
# HARD PATTERN MATCHING
# ================================================================================

HARD_DISQUALIFIER_PATTERNS = [
    r'email\s*,\s*phone', r'phone\s*,\s*email',
    r'email\s*,\s*(?:phone|mobile|address|fax)',
    r'(?:phone|mobile)\s*,\s*email',
    r'name\s*,\s*email', r'fields?\s*:\s*email',
    r'collects?\s+(?:email|phone)', r'gathers?\s+(?:email|phone)',
    r'stores?\s+(?:email|phone)', r'captures?\s+(?:email|phone)',
    r'email\s+(?:for|as)\s+(?:login|username)',
    r'login\s+(?:with|using)\s+email',
    r'sign\s+in\s+(?:with|using)\s+email',
    r'email\s+(?:required|needed)\s+(?:for|to)',
    r'email\s+(?:field|input|textbox)',
    r'(?:field|input)\s+(?:for\s+)?email',
    r'enter\s+(?:your\s+)?email',
    r'email\s+(?:column|field)\s+(?:in\s+)?(?:database|table)',
    r'(?:varchar|text|string)\s+(?:field\s+)?(?:for\s+)?email',
    r'plaintext', r'validates?\s+email', r'verif(?:y|ies)\s+email',
    r'(?:sms|text)\s+verification', r'2fa\s+(?:via|through)',
    r'(?:otp|one[- ]?time\s+password)',
    r'displays?\s+(?:email|phone)', r'shows?\s+(?:email|phone)',
    r'japanese\s+text', r'chinese\s+text', r'korean\s+text',
    r'email\s+(?:is\s+)?optional',
]

HARD_QUALIFIER_PATTERNS = [
    r'e[-\s]?communication(?:s)?', r'electronic\s+communication',
    r'(?:can|able\s+to)\s+send\s+(?:email|text|message|sms)',
    r'(?:user|app|system)s?\s+sends?\s+(?:email|notification|text|sms|alert)',
    r'sends?\s+(?:email|text|sms)\s+(?:notification|alert|message)s?',
    r'(?:email|sms|text)\s+(?:sending|delivery)\s+(?:capability|feature|system)',
    r'video\s+call(?:ing)?', r'voice\s+call(?:ing)?',
    r'video\s+(?:conferencing|conference|chat)',
    r'voip\s+(?:capability|calling|feature)',
    r'instant\s+messag(?:ing|e)', r'(?:real[- ]?time|live)\s+(?:messaging|chat)',
    r'(?:direct|in[- ]?app)\s+messag(?:ing|e)',
    r'chat\s+(?:capability|feature|enabled|platform)',
    r'(?:user|users)\s+(?:can\s+)?(?:message|chat)\s+each\s+other',
    r'sends?\s+push\s+notification', r'delivers?\s+push\s+notification',
    r'push\s+notification\s+(?:capability|feature|system)',
    r'(?:mobile|app)\s+(?:push\s+)?notification(?:s)?\s+(?:enabled|sent)',
    r'notification\s+(?:sending|delivery)\s+(?:capability|feature)',
]

COMMUNICATION_KEYWORDS = [
    'email', 'e-mail', 'mail', 'text', 'sms', 'mms',
    'message', 'messaging', 'msg', 'call', 'calling', 'phone',
    'video', 'voice', 'audio', 'chat', 'notification', 'notify',
    'alert', 'push', 'communicat', 'voip',
]

# ================================================================================
# SEMANTIC CLASSIFIER CLASS
# ================================================================================

class ECommClassifier:
    """
    Classifier for e-communication capabilities.
    Uses LLM Mesh if available, falls back to TF-IDF, then to patterns.
    """
    
    def __init__(self, project=None, llm_id=None):
        self.project = project
        self.llm_id = llm_id
        self.llm = None
        self.use_llm_embeddings = False
        self.use_llm_completion = False
        self.tfidf_vectorizer = None
        self.ecomm_vectors = None
        self.datacoll_vectors = None
        
        # Compile patterns
        self.disqualifier_patterns = [re.compile(p, re.IGNORECASE) for p in HARD_DISQUALIFIER_PATTERNS]
        self.qualifier_patterns = [re.compile(p, re.IGNORECASE) for p in HARD_QUALIFIER_PATTERNS]
        
        # Normalize false positives/negatives
        self.false_positives = set(fp.lower().strip() for fp in FALSE_POSITIVES if fp.strip())
        self.false_negatives = set(fn.lower().strip() for fn in FALSE_NEGATIVES if fn.strip())
        
        # Initialize semantic understanding
        self._init_semantic_understanding()
    
    def _init_semantic_understanding(self):
        """Initialize the best available semantic understanding method."""
        print("\n" + "=" * 60)
        print("INITIALIZING SEMANTIC CLASSIFIER")
        print("=" * 60)
        
        # Try LLM Mesh first
        if self.project and self.llm_id:
            try:
                self.llm = self.project.get_llm(self.llm_id)
                
                # Test if embeddings work
                try:
                    test_embed = self.llm.new_embeddings()
                    test_embed.add_text("test")
                    test_embed.execute()
                    self.use_llm_embeddings = True
                    print(f"✓ Using LLM Mesh EMBEDDINGS: {self.llm_id}")
                    self._init_llm_embeddings()
                    return
                except:
                    pass
                
                # Try completion-based classification
                try:
                    test_completion = self.llm.new_completion()
                    test_completion.with_message("Say OK")
                    resp = test_completion.execute()
                    if resp.success:
                        self.use_llm_completion = True
                        print(f"✓ Using LLM Mesh COMPLETION: {self.llm_id}")
                        return
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠ LLM Mesh not available: {e}")
        
        # Fall back to TF-IDF
        if SKLEARN_AVAILABLE:
            print("✓ Using TF-IDF semantic similarity (scikit-learn)")
            self._init_tfidf()
        else:
            print("✓ Using pattern matching only (no semantic model)")
    
    def _init_llm_embeddings(self):
        """Pre-compute embeddings for training examples using LLM."""
        print("  Computing embeddings for training examples...")
        
        # Get embeddings for e-comm examples
        self.ecomm_embeddings = []
        for text in ECOMM_SENDING_EXAMPLES[:50]:  # Limit to avoid rate limits
            try:
                embed_query = self.llm.new_embeddings()
                embed_query.add_text(text)
                result = embed_query.execute()
                vectors = result.get_vectors()
                if vectors:
                    self.ecomm_embeddings.append(vectors[0])
            except:
                pass
        
        # Get embeddings for data collection examples
        self.datacoll_embeddings = []
        for text in DATA_COLLECTION_EXAMPLES[:50]:
            try:
                embed_query = self.llm.new_embeddings()
                embed_query.add_text(text)
                result = embed_query.execute()
                vectors = result.get_vectors()
                if vectors:
                    self.datacoll_embeddings.append(vectors[0])
            except:
                pass
        
        if self.ecomm_embeddings and self.datacoll_embeddings:
            self.ecomm_centroid = np.mean(self.ecomm_embeddings, axis=0)
            self.datacoll_centroid = np.mean(self.datacoll_embeddings, axis=0)
            print(f"  ✓ Computed {len(self.ecomm_embeddings)} e-comm embeddings")
            print(f"  ✓ Computed {len(self.datacoll_embeddings)} data-coll embeddings")
        else:
            print("  ⚠ Not enough embeddings, falling back to TF-IDF")
            self.use_llm_embeddings = False
            if SKLEARN_AVAILABLE:
                self._init_tfidf()
    
    def _init_tfidf(self):
        """Initialize TF-IDF vectorizer with training examples."""
        print("  Building TF-IDF model from training examples...")
        
        all_texts = ECOMM_SENDING_EXAMPLES + DATA_COLLECTION_EXAMPLES
        
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            stop_words='english',
            min_df=1
        )
        self.tfidf_vectorizer.fit(all_texts)
        
        # Pre-compute vectors for training examples
        self.ecomm_vectors = self.tfidf_vectorizer.transform(ECOMM_SENDING_EXAMPLES)
        self.datacoll_vectors = self.tfidf_vectorizer.transform(DATA_COLLECTION_EXAMPLES)
        
        # Compute centroids
        self.ecomm_centroid = np.asarray(self.ecomm_vectors.mean(axis=0)).flatten()
        self.datacoll_centroid = np.asarray(self.datacoll_vectors.mean(axis=0)).flatten()
        
        print(f"  ✓ TF-IDF vocabulary size: {len(self.tfidf_vectorizer.vocabulary_)}")
    
    def _cosine_sim(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        vec1 = np.array(vec1).flatten()
        vec2 = np.array(vec2).flatten()
        norm1, norm2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def _contains_comm_keyword(self, text: str) -> bool:
        """Check if text contains communication keywords."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in COMMUNICATION_KEYWORDS)
    
    def _check_false_positive(self, text: str) -> bool:
        """Check if text is a known false positive."""
        text_lower = text.lower().strip()
        if text_lower in self.false_positives:
            return True
        return any(fp in text_lower for fp in self.false_positives)
    
    def _check_false_negative(self, text: str) -> bool:
        """Check if text is a known false negative."""
        text_lower = text.lower().strip()
        if text_lower in self.false_negatives:
            return True
        return any(fn in text_lower for fn in self.false_negatives)
    
    def _classify_with_llm_completion(self, text: str) -> Tuple[float, str]:
        """Classify using LLM completion (zero-shot classification)."""
        try:
            prompt = f"""Classify this text as either "ECOMM" (e-communication capability - the app can SEND emails, texts, calls, messages, notifications) or "COLLECT" (data collection only - the app stores/collects contact info).

Text: "{text}"

Rules:
- ECOMM: App sends emails, sends texts, makes calls, sends push notifications, has messaging/chat features
- COLLECT: App collects email addresses, stores phone numbers, requires email for login, validates email format

Respond with only one word: ECOMM or COLLECT"""

            completion = self.llm.new_completion()
            completion.with_message(role="user", message=prompt)
            resp = completion.execute()
            
            if resp.success:
                answer = resp.text.strip().upper()
                if "ECOMM" in answer:
                    return (0.85, "llm_completion_ecomm")
                elif "COLLECT" in answer:
                    return (0.15, "llm_completion_collect")
            
            return (0.5, "llm_completion_unclear")
        except:
            return (0.5, "llm_completion_error")
    
    def _classify_with_llm_embeddings(self, text: str) -> Tuple[float, str]:
        """Classify using LLM embeddings similarity."""
        try:
            embed_query = self.llm.new_embeddings()
            embed_query.add_text(text)
            result = embed_query.execute()
            vectors = result.get_vectors()
            
            if not vectors:
                return (0.5, "llm_embed_no_vector")
            
            text_vec = vectors[0]
            
            # Compare to centroids
            ecomm_sim = self._cosine_sim(text_vec, self.ecomm_centroid)
            datacoll_sim = self._cosine_sim(text_vec, self.datacoll_centroid)
            
            # Also compare to individual examples (max similarity)
            ecomm_max = max(self._cosine_sim(text_vec, e) for e in self.ecomm_embeddings) if self.ecomm_embeddings else 0
            datacoll_max = max(self._cosine_sim(text_vec, e) for e in self.datacoll_embeddings) if self.datacoll_embeddings else 0
            
            # Combined score
            avg_ecomm = (ecomm_sim + ecomm_max) / 2
            avg_datacoll = (datacoll_sim + datacoll_max) / 2
            
            total = avg_ecomm + avg_datacoll
            confidence = avg_ecomm / total if total > 0 else 0.5
            
            return (confidence, "llm_embedding")
        except:
            return (0.5, "llm_embed_error")
    
    def _classify_with_tfidf(self, text: str) -> Tuple[float, str]:
        """Classify using TF-IDF similarity."""
        try:
            text_vec = self.tfidf_vectorizer.transform([text])
            text_arr = np.asarray(text_vec.toarray()).flatten()
            
            # Similarity to centroids
            ecomm_centroid_sim = self._cosine_sim(text_arr, self.ecomm_centroid)
            datacoll_centroid_sim = self._cosine_sim(text_arr, self.datacoll_centroid)
            
            # Max similarity to individual training examples
            ecomm_sims = cosine_similarity(text_vec, self.ecomm_vectors).flatten()
            datacoll_sims = cosine_similarity(text_vec, self.datacoll_vectors).flatten()
            
            ecomm_max = np.max(ecomm_sims) if len(ecomm_sims) > 0 else 0
            datacoll_max = np.max(datacoll_sims) if len(datacoll_sims) > 0 else 0
            
            # 90th percentile
            ecomm_p90 = np.percentile(ecomm_sims, 90) if len(ecomm_sims) > 0 else 0
            datacoll_p90 = np.percentile(datacoll_sims, 90) if len(datacoll_sims) > 0 else 0
            
            # Average scores
            avg_ecomm = (ecomm_centroid_sim + ecomm_max + ecomm_p90) / 3
            avg_datacoll = (datacoll_centroid_sim + datacoll_max + datacoll_p90) / 3
            
            total = avg_ecomm + avg_datacoll
            confidence = avg_ecomm / total if total > 0 else 0.5
            
            return (confidence, "tfidf_semantic")
        except:
            return (0.5, "tfidf_error")
    
    def classify(self, text: str) -> Tuple[float, str]:
        """
        Classify text for e-communication capability.
        Returns (confidence, method).
        """
        if not text or not isinstance(text, str):
            return (0.0, "invalid_input")
        
        text = str(text).strip()
        if len(text) < MIN_TEXT_LENGTH:
            return (0.0, "text_too_short")
        
        text_lower = text.lower()
        
        # Step 1: Check learned false negatives (should be flagged)
        if self._check_false_negative(text):
            return (0.95, "learned_false_negative")
        
        # Step 2: Check learned false positives (should NOT be flagged)
        if self._check_false_positive(text):
            return (0.0, "learned_false_positive")
        
        # Step 3: Quick filter - must contain communication keyword
        if not self._contains_comm_keyword(text):
            return (0.0, "no_comm_keyword")
        
        # Step 4: Check hard disqualifiers
        for pattern in self.disqualifier_patterns:
            if pattern.search(text_lower):
                return (0.0, "hard_disqualifier")
        
        # Step 5: Check hard qualifiers
        for pattern in self.qualifier_patterns:
            if pattern.search(text_lower):
                return (0.95, "hard_qualifier")
        
        # Step 6: Semantic classification
        if self.use_llm_embeddings:
            return self._classify_with_llm_embeddings(text)
        elif self.use_llm_completion:
            return self._classify_with_llm_completion(text)
        elif self.tfidf_vectorizer is not None:
            return self._classify_with_tfidf(text)
        else:
            # Pattern-only fallback
            return (0.4, "pattern_only_ambiguous")

# ================================================================================
# HELPER FUNCTIONS
# ================================================================================

def find_idn_eon_column(df: pd.DataFrame) -> Optional[str]:
    """Find the IDN_EON column (case-insensitive)."""
    for col in df.columns:
        col_normalized = col.upper().replace(' ', '_').replace('-', '_')
        if col_normalized == 'IDN_EON' or 'IDN_EON' in col_normalized:
            return col
    return None

def is_valid_idn_eon(value: Any) -> bool:
    """Check if IDN_EON value is valid."""
    if value is None or pd.isna(value):
        return False
    str_value = str(value).strip().lower()
    return str_value not in INVALID_IDN_EON_VALUES and len(str_value) > 0

def clean_text(value: Any) -> str:
    """Clean and convert value to string."""
    if value is None or pd.isna(value):
        return ""
    try:
        text = str(value).strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    except:
        return ""

# ================================================================================
# MAIN PROCESSING
# ================================================================================

def collect_idn_eons(input_datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Collect unique IDN_EON values and track source tables."""
    print("\n" + "=" * 60)
    print("STEP 1: COLLECTING UNIQUE IDN_EON VALUES")
    print("=" * 60)
    
    idn_eon_sources = defaultdict(set)
    
    for table_name, df in input_datasets.items():
        idn_col = find_idn_eon_column(df)
        if idn_col is None:
            print(f"  ⚠ '{table_name}': No IDN_EON column - SKIPPING")
            continue
        
        valid_count = 0
        for value in df[idn_col].dropna().unique():
            if is_valid_idn_eon(value):
                idn_eon_sources[str(value).strip()].add(table_name)
                valid_count += 1
        
        print(f"  ✓ '{table_name}': {valid_count:,} valid IDN_EON (column: {idn_col})")
    
    result_data = [
        {'IDN_EON': idn, 'source_tables': ', '.join(sorted(sources))}
        for idn, sources in idn_eon_sources.items()
    ]
    
    result_df = pd.DataFrame(result_data)
    print(f"\n  TOTAL UNIQUE IDN_EON: {len(result_df):,}")
    
    return result_df

def analyze_ecomm(idn_df: pd.DataFrame, input_datasets: Dict[str, pd.DataFrame], 
                  classifier: ECommClassifier) -> pd.DataFrame:
    """Analyze each IDN_EON for e-communication capabilities."""
    print("\n" + "=" * 60)
    print("STEP 2: ANALYZING E-COMMUNICATION CAPABILITIES")
    print("=" * 60)
    
    results = []
    total = len(idn_df)
    ecomm_count = 0
    
    for idx, row in idn_df.iterrows():
        idn_eon = row['IDN_EON']
        source_tables = row['source_tables']
        
        if (idx + 1) % 500 == 0 or (idx + 1) == total:
            print(f"  Progress: {idx+1:,}/{total:,} ({(idx+1)*100/total:.1f}%) - E-comm: {ecomm_count:,}")
        
        best_confidence = 0.0
        best_reason = "no_evidence"
        evidence_samples = []
        evidence_columns = set()
        
        for table_name, df in input_datasets.items():
            idn_col = find_idn_eon_column(df)
            if idn_col is None:
                continue
            
            mask = df[idn_col].astype(str).str.strip() == idn_eon
            matching_rows = df[mask]
            
            if matching_rows.empty:
                continue
            
            for col in df.columns:
                if col == idn_col:
                    continue
                
                for _, cell_value in matching_rows[col].items():
                    text = clean_text(cell_value)
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    
                    confidence, reason = classifier.classify(text)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_reason = reason
                    
                    if confidence > ECOMM_THRESHOLD:
                        evidence_columns.add(f"{table_name}.{col}")
                        if len(evidence_samples) < MAX_EVIDENCE_SAMPLES:
                            evidence_samples.append(text[:200])
        
        has_ecomm = best_confidence > ECOMM_THRESHOLD
        if has_ecomm:
            ecomm_count += 1
        
        results.append({
            'IDN_EON': idn_eon,
            'source_tables': source_tables,
            'has_ecomm_capability': 'YES' if has_ecomm else 'NO',
            'ecomm_confidence': round(best_confidence, 4),
            'ecomm_evidence': ' | '.join(evidence_samples) if evidence_samples else '',
            'detection_details': ', '.join(sorted(evidence_columns)) if evidence_columns else best_reason,
        })
    
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values(
        ['has_ecomm_capability', 'ecomm_confidence'],
        ascending=[True, False]
    ).reset_index(drop=True)
    
    return result_df

# ================================================================================
# RECIPE EXECUTION
# ================================================================================

print("\n" + "=" * 60)
print("E-COMMUNICATION CAPABILITY DETECTION")
print("=" * 60)
print(f"Threshold: {ECOMM_THRESHOLD}")
print(f"LLM ID: {LLM_ID if LLM_ID else 'Not configured (using TF-IDF)'}")

# Get project for LLM access
client = dataiku.api_client()
project = client.get_default_project()

# Load input datasets
input_datasets = {}
for ds in dataiku.recipe.get_inputs_as_datasets():
    name = ds.name
    print(f"\nLoading '{name}'...")
    try:
        df = ds.get_dataframe()
        for col in df.columns:
            df[col] = df[col].astype(str)
        input_datasets[name] = df
        print(f"  ✓ {len(df):,} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

if not input_datasets:
    raise ValueError("No input datasets loaded!")

# Initialize classifier
classifier = ECommClassifier(project=project, llm_id=LLM_ID)

# Step 1: Collect IDN_EON
idn_df = collect_idn_eons(input_datasets)

if len(idn_df) == 0:
    print("\n⚠ No valid IDN_EON found!")
    output_df = pd.DataFrame(columns=[
        'IDN_EON', 'source_tables', 'has_ecomm_capability',
        'ecomm_confidence', 'ecomm_evidence', 'detection_details'
    ])
else:
    # Step 2: Analyze e-comm
    output_df = analyze_ecomm(idn_df, input_datasets, classifier)

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
total = len(output_df)
yes_count = (output_df['has_ecomm_capability'] == 'YES').sum() if total > 0 else 0
print(f"  Total IDN_EON: {total:,}")
print(f"  E-comm YES: {yes_count:,} ({yes_count*100/total:.1f}%)" if total > 0 else "  E-comm YES: 0")
print(f"  E-comm NO: {total - yes_count:,}")

if yes_count > 0:
    print(f"\n  Top 10 E-Comm IDN_EON:")
    for _, r in output_df[output_df['has_ecomm_capability']=='YES'].head(10).iterrows():
        print(f"    {r['IDN_EON']} ({r['ecomm_confidence']:.3f})")

# Write output
print("\n" + "=" * 60)
print("WRITING OUTPUT")
print("=" * 60)

output_dataset = dataiku.recipe.get_outputs_as_datasets()[0]
output_dataset.write_with_schema(output_df)
print(f"  ✓ Wrote {len(output_df):,} rows")

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
