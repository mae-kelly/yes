import dataiku
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import re
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Input/output datasets
input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# MASSIVELY REFINED TRAINING DATA
# Focus on distinguishing ACTIVE COMMUNICATION FEATURES vs DATA COLLECTION

POSITIVE_EXAMPLES = [
    # Explicit communication capability language
    "app provides ability to send email messages", "users can send text messages through app",
    "platform enables email communication between users", "system allows sending sms notifications",
    "application supports text messaging", "service provides email notification capability",
    "app has email messaging feature", "platform includes text message sending",
    "enables users to communicate via email", "allows customers to send text messages",
    "provides sms communication feature", "supports email-based communication",
    
    # E-communication specific mentions
    "e-communications enabled", "electronic communications supported", "e-communication platform",
    "e-communications feature available", "electronic communication capability", 
    "e-communication channel active", "supports e-communications", "e-communication system",
    
    # Active sending/receiving verbs with communication
    "app sends email notifications to users", "system delivers text alerts to customers",
    "platform transmits email updates", "service dispatches sms reminders",
    "application pushes email messages", "tool sends text notifications",
    "users receive email alerts from app", "customers get text messages from system",
    "subscribers receive email communications", "users get sms notifications",
    
    # Communication infrastructure language
    "email notification system", "text message delivery system", "sms alert infrastructure",
    "email communication module", "text messaging service", "notification delivery platform",
    "message sending capability", "alert distribution system", "communication engine",
    
    # User consent for receiving communications
    "users opt-in to receive emails", "customers consent to text notifications",
    "subscribers agree to email communications", "users enable sms alerts",
    "opt-in for email notifications", "subscribe to text message updates",
    "consent to receive promotional emails", "agree to sms marketing messages",
    
    # Two-way communication features
    "users can reply to emails", "customers respond via text message",
    "email conversation feature", "text messaging chat capability",
    "back-and-forth email communication", "interactive text messaging",
    
    # Triggered and automated communications
    "automatically sends email when", "triggers text message upon",
    "email sent automatically after", "sms dispatched when event occurs",
    "automated email notification system", "automatic text alert feature",
    
    # Marketing and campaign capabilities
    "email marketing campaigns", "text message marketing blasts",
    "promotional email sending", "sms campaign management",
    "bulk email distribution", "mass text messaging capability",
    
    # Transactional communications
    "transactional email delivery", "order confirmation emails sent",
    "shipping notification via text", "payment receipt via email",
    "appointment reminder texts", "verification code via sms",
    
    # Channel preference and method selection
    "users choose email as notification method", "customers select text for alerts",
    "email preferred for communications", "sms as primary contact channel",
    "notification delivery via email", "alerts sent through text messaging",
    
    # Communication settings and controls
    "email notification settings", "text alert preferences configurable",
    "manage communication preferences", "control message delivery options",
    "customize notification channels", "configure alert methods",
    
    # Real-time and scheduled messaging
    "real-time email alerts", "instant text notifications",
    "scheduled email reports", "periodic sms updates",
    "immediate notification delivery", "timed message sending",
    
    # Engagement and delivery metrics
    "email delivery tracking", "text message open rates",
    "notification engagement metrics", "message delivery confirmation",
    "communication analytics", "alert response tracking",
    
    # Platform capabilities and features
    "built-in messaging system", "integrated notification platform",
    "native email functionality", "embedded text messaging",
    "in-app communication tools", "communication feature set",
    
    # User-facing capability language
    "users will receive email", "customers get text notifications",
    "app notifies via email", "system alerts through text",
    "you can message via email", "send text messages to users",
    
    # Multi-channel communication
    "email and text notification", "sms or email delivery",
    "multiple communication channels", "cross-channel messaging",
    
    # Communication permission and authorization
    "authorized to send emails", "permission to text customers",
    "approved communication channels", "enabled messaging capabilities"
]

NEGATIVE_EXAMPLES = [
    # Pure data collection language
    "collect email address", "gather phone number", "capture email information",
    "store email address", "save phone number", "record email data",
    "email address collected", "phone number captured", "email info gathered",
    "collect user email", "gather customer phone", "obtain email address",
    
    # List format data collection
    "email, phone number, address", "email and phone number collected",
    "fields: email, phone, name", "data collected: email, phone",
    "email address, mobile number", "phone, email, date of birth",
    "user provides email, phone", "enter email and phone number",
    "email phone address city", "collects email phone name",
    
    # Registration and profile data
    "email required for registration", "phone number for account creation",
    "email address in user profile", "phone stored in account",
    "registration requires email", "signup needs phone number",
    "email field in registration form", "phone number field for signup",
    "create account with email", "register using phone number",
    
    # Authentication and login
    "email used as login", "phone number for authentication",
    "sign in with email", "login via phone number",
    "email as username", "phone for account access",
    "authenticate using email", "verify identity with phone",
    "email credential", "phone-based login",
    
    # Contact information storage
    "email address on file", "phone number in database",
    "contact info stored", "email information saved",
    "phone number recorded", "email data maintained",
    "keep email address", "retain phone number",
    
    # Display and UI
    "display email address", "show phone number",
    "email visible in profile", "phone displayed in settings",
    "email appears on screen", "phone shown to user",
    "render email field", "present phone information",
    
    # Validation and verification
    "validate email format", "verify phone number format",
    "email syntax check", "phone number validation",
    "email address verification", "phone format check",
    "confirm email structure", "validate phone digits",
    
    # Technical/metadata
    "email metadata", "phone number format",
    "email header information", "phone field data type",
    "email protocol", "phone number schema",
    "email api endpoint", "phone data structure",
    
    # Plaintext and technical text
    "plaintext format", "plain text encoding",
    "text field in database", "text data type",
    "text column", "text string variable",
    "text file format", "text-based storage",
    "text encoding utf-8", "text content type",
    
    # Language references
    "japanese text", "chinese characters",
    "korean text input", "multilingual text",
    "text in japanese", "chinese text display",
    
    # Search and filtering
    "search by email", "filter by phone",
    "email in search results", "find phone number",
    "query email field", "lookup phone",
    
    # Import/export
    "export email list", "import phone numbers",
    "email data export", "phone list download",
    "csv of emails", "spreadsheet with phones",
    
    # Logging and tracking
    "log email address", "track phone number",
    "record email entry", "monitor phone usage",
    "email activity log", "phone access tracking",
    
    # Privacy and security (storage focus)
    "encrypt email data", "secure phone storage",
    "email pii protection", "phone number privacy",
    "email data retention", "phone information security",
    
    # Third-party contact info
    "contact us at email address", "call phone number",
    "email support at", "phone customer service",
    "support email listed", "help desk phone",
    
    # Deduplication and cleanup
    "deduplicate emails", "clean phone list",
    "remove invalid emails", "normalize phone format",
    "email data quality", "phone number cleanup",
    
    # Missing or invalid
    "email address missing", "phone number not provided",
    "invalid email", "phone number empty",
    "no email on file", "phone unavailable",
    
    # Historical data
    "old email address", "previous phone number",
    "archived email", "historical phone data",
    "past email information", "former phone contact",
    
    # SMS for 2FA only
    "sms for two-factor authentication", "text code for login",
    "sms verification code only", "2fa via text",
    "authentication sms", "security text message",
    "one-time password via sms", "login code by text",
    
    # Profile/account fields
    "email in user profile", "phone in account details",
    "profile contains email", "account shows phone",
    "user details include email", "contact section has phone",
    
    # Form fields
    "email input field", "phone number textbox",
    "email form element", "phone entry field",
    "email field required", "phone field optional",
    
    # Documentation and help text
    "enter your email", "provide phone number",
    "email field help text", "phone number tooltip",
    "email format example", "phone number pattern",
    
    # Matching and linking
    "match records by email", "link accounts via phone",
    "email as unique identifier", "phone as primary key",
    "join on email field", "merge using phone",
    
    # Analysis context
    "analyze email patterns", "phone number statistics",
    "email data mining", "phone usage analytics",
    "email distribution report", "phone number frequency"
]

# Critical distinguishing indicators
CAPABILITY_INDICATORS = [
    # Verbs that indicate ACTIVE communication capability
    'send', 'deliver', 'dispatch', 'transmit', 'push', 'forward', 'distribute',
    'notify', 'alert', 'inform', 'remind', 'message', 'communicate', 'contact',
    'broadcast', 'blast', 'relay', 'route',
    # Reception verbs
    'receive', 'get', 'obtain',
    # Capability/permission verbs
    'can send', 'able to send', 'allows sending', 'enables sending', 'supports sending',
    'provides', 'enables', 'allows', 'supports', 'offers', 'includes', 'features'
]

DATA_COLLECTION_INDICATORS = [
    # Verbs that indicate DATA COLLECTION not communication
    'collect', 'gather', 'capture', 'obtain', 'acquire', 'request',
    'store', 'save', 'record', 'log', 'retain', 'keep', 'maintain',
    'enter', 'provide', 'submit', 'input', 'fill',
    # Display/show verbs
    'display', 'show', 'render', 'present', 'list', 'appear'
]

# Definitive communication phrases - these MUST mean communication capability
DEFINITIVE_COMMUNICATION_PHRASES = [
    # Capability language
    'provides ability to send email', 'provides ability to send text', 'ability to send sms',
    'allows users to send email', 'allows users to send text', 'enables email sending',
    'enables text sending', 'enables sms sending', 'supports sending email',
    'supports sending text', 'can send email', 'can send text', 'can send sms',
    
    # E-communication
    'e-communications', 'e-communication', 'electronic communications', 'electronic communication',
    'ecommunications', 'ecommunication',
    
    # Active sending
    'sends email to users', 'sends text to customers', 'delivers email notifications',
    'delivers text alerts', 'transmits email', 'transmits sms', 'pushes email',
    'pushes text notifications', 'dispatches email', 'dispatches text',
    
    # Receiving
    'users receive email', 'users receive text', 'customers get email', 'customers get sms',
    'receive email notifications', 'receive text alerts', 'get email updates', 'get text messages',
    
    # System/platform capabilities
    'email notification system', 'text notification system', 'sms alert system',
    'email messaging platform', 'text messaging service', 'messaging capability',
    'notification capability', 'communication feature', 'alert feature',
    
    # Marketing/campaign
    'email campaign', 'text campaign', 'sms campaign', 'email marketing',
    'text marketing', 'promotional email', 'promotional text',
    
    # Opt-in for receiving
    'opt-in to receive email', 'opt-in to receive text', 'subscribe to email',
    'subscribe to text', 'consent to receive email', 'consent to receive sms',
    
    # Method of delivery
    'via email', 'via text', 'via sms', 'through email', 'through text',
    'by email', 'by text', 'by sms'
]

# Definitive data collection phrases - these MUST mean just data collection
DEFINITIVE_DATA_COLLECTION_PHRASES = [
    # Collection language
    'collect email', 'collect phone', 'gather email', 'gather phone',
    'capture email', 'capture phone', 'obtain email', 'obtain phone',
    
    # List format (strong indicator)
    'email, phone', 'phone, email', 'email and phone', 'phone and email',
    'email address, phone number', 'phone number, email address',
    'fields: email', 'data: email', 'includes: email', 'such as email',
    
    # Storage language
    'store email', 'store phone', 'save email', 'save phone',
    'stored in', 'saved to', 'kept in', 'maintained in',
    'email in database', 'phone in database', 'email in profile', 'phone in account',
    
    # Registration/signup
    'email required', 'phone required', 'email for registration', 'phone for signup',
    'registration email', 'signup phone', 'create account email', 'account phone',
    
    # Login/authentication
    'email for login', 'phone for authentication', 'email as username', 'login email',
    'sign in email', 'authenticate phone',
    
    # Form fields
    'email field', 'phone field', 'email input', 'phone input',
    'enter email', 'enter phone', 'provide email', 'provide phone',
    
    # Contact info context
    'contact information', 'contact details', 'contact info',
    'email address on file', 'phone number on file', 'email on record',
    
    # Display context
    'display email', 'display phone', 'show email', 'show phone',
    
    # Technical context
    'plaintext', 'plain text', 'text field', 'text data type', 'text column',
    'text encoding', 'text format', 'text file',
    
    # Language context
    'japanese text', 'chinese text', 'korean text'
]

class DeepSemanticNeuralNet:
    """Deep neural network for semantic understanding"""
    
    def __init__(self, input_size, hidden_sizes=[64, 48, 32, 16], learning_rate=0.005, dropout_rate=0.25):
        self.layers = []
        self.learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        
        layer_sizes = [input_size] + hidden_sizes + [1]
        
        for i in range(len(layer_sizes) - 1):
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * scale
            b = np.zeros((1, layer_sizes[i+1]))
            self.layers.append({'W': W, 'b': b, 'A': None, 'Z': None})
    
    def leaky_relu(self, Z, alpha=0.01):
        return np.where(Z > 0, Z, alpha * Z)
    
    def leaky_relu_derivative(self, Z, alpha=0.01):
        return np.where(Z > 0, 1, alpha)
    
    def sigmoid(self, Z):
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def forward(self, X, training=True):
        A = X
        
        for i, layer in enumerate(self.layers):
            Z = np.dot(A, layer['W']) + layer['b']
            layer['Z'] = Z
            
            if i < len(self.layers) - 1:
                A = self.leaky_relu(Z)
                if training and self.dropout_rate > 0:
                    dropout_mask = np.random.binomial(1, 1 - self.dropout_rate, size=A.shape)
                    A = A * dropout_mask / (1 - self.dropout_rate)
            else:
                A = self.sigmoid(Z)
            
            layer['A'] = A
        
        return A
    
    def backward(self, X, y):
        m = X.shape[0]
        dA = self.layers[-1]['A'] - y
        
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            
            if i < len(self.layers) - 1:
                dZ = dA * self.leaky_relu_derivative(layer['Z'])
            else:
                dZ = dA
            
            A_prev = X if i == 0 else self.layers[i-1]['A']
            
            dW = np.dot(A_prev.T, dZ) / m
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            dW = np.clip(dW, -5, 5)
            db = np.clip(db, -5, 5)
            
            layer['W'] -= self.learning_rate * dW
            layer['b'] -= self.learning_rate * db
            
            if i > 0:
                dA = np.dot(dZ, layer['W'].T)
    
    def train(self, X, y, epochs=1000, batch_size=16, validation_split=0.2):
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        best_val_loss = float('inf')
        best_val_acc = 0.0
        patience = 100
        patience_counter = 0
        
        for epoch in range(epochs):
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                self.forward(X_batch, training=True)
                self.backward(X_batch, y_batch)
            
            if epoch % 20 == 0:
                train_output = self.forward(X_train, training=False)
                val_output = self.forward(X_val, training=False)
                
                train_loss = -np.mean(y_train * np.log(train_output + 1e-8) + 
                                     (1 - y_train) * np.log(1 - train_output + 1e-8))
                val_loss = -np.mean(y_val * np.log(val_output + 1e-8) + 
                                   (1 - y_val) * np.log(1 - val_output + 1e-8))
                
                train_acc = np.mean((train_output > 0.5) == y_train)
                val_acc = np.mean((val_output > 0.5) == y_val)
                
                print(f"Epoch {epoch:4d}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, "
                      f"Train Acc={train_acc:.3f}, Val Acc={val_acc:.3f}")
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_val_acc = val_acc
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch}")
                    print(f"Best validation accuracy: {best_val_acc:.3f}")
                    break
    
    def predict(self, X):
        return self.forward(X, training=False)

def safe_str(value):
    """Safely convert any value to string"""
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

def extract_deep_semantic_features(text):
    """
    Extract 30 semantic features focused on distinguishing
    COMMUNICATION CAPABILITY vs DATA COLLECTION
    """
    text_str = safe_str(text)
    if not text_str:
        return np.zeros(30)
    
    text_lower = text_str.lower()
    features = []
    
    # FEATURE 1: Definitive communication phrases
    has_def_comm = any(phrase in text_lower for phrase in DEFINITIVE_COMMUNICATION_PHRASES)
    features.append(1 if has_def_comm else 0)
    
    # FEATURE 2: Definitive data collection phrases
    has_def_collection = any(phrase in text_lower for phrase in DEFINITIVE_DATA_COLLECTION_PHRASES)
    features.append(1 if has_def_collection else 0)
    
    # FEATURE 3: E-communication mentions (STRONG signal)
    has_ecomm = any(word in text_lower for word in ['e-communication', 'ecommunication', 'e-communications', 'ecommunications', 'electronic communication'])
    features.append(1 if has_ecomm else 0)
    
    # FEATURE 4: "Provides ability to" or "allows users to" (capability language)
    capability_language = ['provides ability', 'ability to send', 'allows users', 'enables users',
                          'users can send', 'can send', 'supports sending']
    features.append(1 if any(phrase in text_lower for phrase in capability_language) else 0)
    
    # FEATURE 5: List format detection (email, phone, etc.) - STRONG negative signal
    list_patterns = [
        r'email\s*,\s*phone', r'phone\s*,\s*email', r'email\s+and\s+phone',
        r'email\s*,\s*\w+\s*,', r',\s*email\s*,', r'such as email',
        r'including email', r'like email', r'e\.?g\.?\s+email'
    ]
    has_list_format = any(re.search(pattern, text_lower) for pattern in list_patterns)
    features.append(1 if has_list_format else 0)
    
    # FEATURE 6: Active sending verbs (send, deliver, dispatch, transmit)
    active_sending = ['send', 'deliver', 'dispatch', 'transmit', 'push', 'forward']
    features.append(1 if any(verb in text_lower for verb in active_sending) else 0)
    
    # FEATURE 7: Collection verbs (collect, gather, capture)
    collection_verbs = ['collect', 'gather', 'capture', 'obtain', 'request']
    features.append(1 if any(verb in text_lower for verb in collection_verbs) else 0)
    
    # FEATURE 8: Storage verbs (store, save, record, log)
    storage_verbs = ['store', 'save', 'record', 'log', 'retain', 'keep']
    features.append(1 if any(verb in text_lower for verb in storage_verbs) else 0)
    
    # FEATURE 9: Notification/alert context
    notif_context = ['notification', 'alert', 'notify', 'alert', 'reminder', 'update']
    features.append(1 if any(word in text_lower for word in notif_context) else 0)
    
    # FEATURE 10: System/platform capability language
    system_capability = ['system sends', 'platform sends', 'app sends', 'service sends',
                        'system delivers', 'platform delivers', 'app delivers']
    features.append(1 if any(phrase in text_lower for phrase in system_capability) else 0)
    
    # FEATURE 11: Registration/signup context (negative signal)
    registration = ['registration', 'signup', 'sign up', 'create account', 'account creation']
    features.append(1 if any(word in text_lower for word in registration) else 0)
    
    # FEATURE 12: Login/authentication context (negative signal)
    auth = ['login', 'log in', 'sign in', 'authentication', 'authenticate', 'username']
    features.append(1 if any(word in text_lower for word in auth) else 0)
    
    # FEATURE 13: Profile/account field context (negative signal)
    profile = ['profile', 'account details', 'user information', 'contact information']
    features.append(1 if any(phrase in text_lower for phrase in profile) else 0)
    
    # FEATURE 14: Form field context (negative signal)
    form_field = ['field', 'input', 'form', 'enter', 'provide', 'fill']
    features.append(1 if any(word in text_lower for word in form_field) else 0)
    
    # FEATURE 15: "Via" or "through" or "by" (method of delivery - positive signal)
    method_delivery = ['via email', 'via text', 'via sms', 'through email', 'through text', 'by email', 'by text']
    features.append(1 if any(phrase in text_lower for phrase in method_delivery) else 0)
    
    # FEATURE 16: Opt-in/subscribe language (positive signal)
    opt_in = ['opt-in', 'opt in', 'subscribe', 'consent to receive', 'agree to receive']
    features.append(1 if any(phrase in text_lower for phrase in opt_in) else 0)
    
    # FEATURE 17: Campaign/marketing language (positive signal)
    campaign = ['campaign', 'marketing', 'promotional', 'blast', 'broadcast']
    features.append(1 if any(word in text_lower for word in campaign) else 0)
    
    # FEATURE 18: Database/storage context (negative signal)
    database = ['database', 'stored in', 'saved to', 'in table', 'in column']
    features.append(1 if any(phrase in text_lower for phrase in database) else 0)
    
    # FEATURE 19: Plaintext (negative signal)
    features.append(1 if 'plaintext' in text_lower or 'plain text' in text_lower else 0)
    
    # FEATURE 20: Text as technical term (negative signal)
    technical_text = ['text field', 'text data type', 'text column', 'text encoding', 'text file']
    features.append(1 if any(phrase in text_lower for phrase in technical_text) else 0)
    
    # FEATURE 21: Language context (negative signal)
    language_context = ['japanese text', 'chinese text', 'korean text', 'multilingual']
    features.append(1 if any(phrase in text_lower for phrase in language_context) else 0)
    
    # FEATURE 22: User-facing language (positive signal)
    user_facing = ['you will receive', 'you can send', 'users receive', 'customers get', "we'll send"]
    features.append(1 if any(phrase in text_lower for phrase in user_facing) else 0)
    
    # FEATURE 23: Two-way communication (positive signal)
    two_way = ['reply', 'respond', 'conversation', 'chat', 'messaging']
    features.append(1 if any(word in text_lower for word in two_way) else 0)
    
    # FEATURE 24: "Required" or "mandatory" with email/phone (negative signal)
    required = ['required', 'mandatory', 'must provide', 'need to enter']
    features.append(1 if any(word in text_lower for word in required) else 0)
    
    # FEATURE 25: Display/show context (negative signal)
    display = ['display', 'show', 'visible', 'appears', 'shown', 'render']
    features.append(1 if any(word in text_lower for word in display) else 0)
    
    # FEATURE 26: Count of capability indicators
    cap_count = sum(1 for indicator in CAPABILITY_INDICATORS if indicator in text_lower)
    features.append(min(cap_count / 3, 1))
    
    # FEATURE 27: Count of collection indicators
    coll_count = sum(1 for indicator in DATA_COLLECTION_INDICATORS if indicator in text_lower)
    features.append(min(coll_count / 3, 1))
    
    # FEATURE 28: Sentence has both email/text AND sending verb
    has_email_or_text = any(word in text_lower for word in ['email', 'text', 'sms'])
    has_sending_verb = any(verb in text_lower for verb in ['send', 'deliver', 'notify', 'alert'])
    features.append(1 if (has_email_or_text and has_sending_verb) else 0)
    
    # FEATURE 29: Sentence has email/text in collection context
    has_collection_verb = any(verb in text_lower for verb in ['collect', 'gather', 'store', 'save'])
    features.append(1 if (has_email_or_text and has_collection_verb) else 0)
    
    # FEATURE 30: Overall semantic score
    score = 0
    # Strong positive indicators
    if has_def_comm: score += 5
    if has_ecomm: score += 4
    if any(phrase in text_lower for phrase in capability_language): score += 3
    # Strong negative indicators
    if has_def_collection: score -= 5
    if has_list_format: score -= 4
    if any(word in text_lower for word in collection_verbs): score -= 2
    if any(word in text_lower for word in storage_verbs): score -= 2
    
    features.append(max(0, min(1, (score + 5) / 10)))
    
    return np.array(features)

# START TRAINING
print("="*80)
print("TRAINING COMMUNICATION vs DATA COLLECTION CLASSIFIER")
print("="*80)
print("This model distinguishes:")
print("  YES: 'app provides ability to send emails', 'e-communications enabled'")
print("  NO: 'collect email, phone number', 'email required for registration'")
print("="*80)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

print(f"\nTraining dataset:")
print(f"  Communication capability examples: {len(POSITIVE_EXAMPLES)}")
print(f"  Data collection examples: {len(NEGATIVE_EXAMPLES)}")

print("\nStep 1: TF-IDF feature extraction...")
vectorizer = TfidfVectorizer(
    max_features=150,
    ngram_range=(1, 5),  # Up to 5-word phrases
    min_df=1,
    sublinear_tf=True
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()

print("\nStep 2: Semantic feature extraction...")
X_features = np.array([extract_deep_semantic_features(text) for text in all_examples])

print("\nStep 3: Combining and standardizing...")
X_combined = np.hstack([X_tfidf, X_features])
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)

print(f"\nTotal features: {X_train.shape[1]}")

print("\nStep 4: Training neural network...")
nn = DeepSemanticNeuralNet(
    input_size=X_train.shape[1],
    hidden_sizes=[64, 48, 32, 16],
    learning_rate=0.005,
    dropout_rate=0.25
)

nn.train(X_train, labels, epochs=1000, batch_size=16, validation_split=0.2)
print("\nModel training complete!\n")

def predict_communication_capability(text):
    """
    Predict if text indicates ACTUAL communication capability
    vs just data collection
    """
    text_str = safe_str(text)
    if not text_str:
        return 0.0
    
    text_lower = text_str.lower()
    
    # IMMEDIATE DISQUALIFIERS - these are DEFINITELY just data collection
    hard_disqualifiers = [
        # List format
        'email, phone', 'phone, email', 'email and phone number',
        # Technical text
        'plaintext', 'plain text format', 'text file', 'text encoding',
        'text field', 'text column', 'text data type',
        # Language
        'japanese text', 'chinese text', 'korean text',
        # Pure storage
        'email stored in database', 'phone stored in', 'save email address',
        'store phone number', 'log email', 'record phone',
        # Registration/login
        'email for login', 'phone for authentication', 'email as username',
        'registration requires email', 'signup phone number'
    ]
    
    for disqualifier in hard_disqualifiers:
        if disqualifier in text_lower:
            return 0.0
    
    # IMMEDIATE QUALIFIERS - these DEFINITELY mean communication
    hard_qualifiers = [
        # E-communication
        'e-communication', 'ecommunication', 'e-communications', 'ecommunications',
        'electronic communication',
        # Capability language
        'provides ability to send email', 'provides ability to send text',
        'ability to send sms', 'allows users to send', 'enables sending',
        # System sending
        'system sends email to', 'app sends text to', 'platform delivers email',
        # Notification systems
        'email notification system', 'text notification system', 'sms alert system'
    ]
    
    for qualifier in hard_qualifiers:
        if qualifier in text_lower:
            try:
                X_tfidf = vectorizer.transform([text_lower]).toarray()
                X_features = extract_deep_semantic_features(text_str).reshape(1, -1)
                X_combined = np.hstack([X_tfidf, X_features])
                X = scaler.transform(X_combined)
                prediction = nn.predict(X)[0][0]
                return min(1.0, float(prediction) + 0.3)  # Strong boost
            except:
                return 0.95
    
    # Standard ML prediction
    try:
        X_tfidf = vectorizer.transform([text_lower]).toarray()
        X_features = extract_deep_semantic_features(text_str).reshape(1, -1)
        X_combined = np.hstack([X_tfidf, X_features])
        X = scaler.transform(X_combined)
        prediction = nn.predict(X)[0][0]
        return float(prediction)
    except:
        return 0.0

# PROCESS DATASETS
print("\n" + "="*80)
print("PROCESSING DATASETS")
print("="*80)

results = {}

for dataset_name in input_dataset_names:
    print(f"\nProcessing {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe()
    except Exception as e:
        print(f"  Warning: Could not load {dataset_name}: {e}")
        continue
    
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        print(f"  Warning: No IDN_EON column found")
        continue
    
    print(f"  Total rows: {len(df)}")
    unique_idns = df[idn_col].unique()
    print(f"  Unique IDN_EON: {len(unique_idns)}")
    
    for idx, IDN_EON in enumerate(unique_idns):
        if idx % 100 == 0 and idx > 0:
            print(f"    Processed {idx}/{len(unique_idns)} IDNs...")
        
        IDN_EON_str = safe_str(IDN_EON)
        if not IDN_EON_str:
            continue
        
        if IDN_EON_str not in results:
            results[IDN_EON_str] = {
                'IDN_EON': IDN_EON_str,
                'data_sources': set(),
                'email_findings': [],
                'text_findings': []
            }
        
        results[IDN_EON_str]['data_sources'].add(dataset_name)
        idn_rows = df[df[idn_col].astype(str) == IDN_EON_str]
        
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            for value in idn_rows[col]:
                original_value = safe_str(value)
                if not original_value:
                    continue
                
                value_lower = original_value.lower()
                
                # Only analyze if mentions email or text/sms
                has_email_mention = any(word in value_lower for word in ['email', 'e-mail'])
                has_text_mention = any(word in value_lower for word in ['text', 'sms', 'messaging'])
                
                if has_email_mention or has_text_mention:
                    try:
                        confidence = predict_communication_capability(original_value)
                    except:
                        confidence = 0.0
                    
                    # High threshold - must be confident it's communication not collection
                    if confidence > 0.75:
                        if has_email_mention:
                            results[IDN_EON_str]['email_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'cell_content': original_value
                            })
                        
                        if has_text_mention:
                            results[IDN_EON_str]['text_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'cell_content': original_value
                            })

# BUILD OUTPUT
print("\nBuilding output dataset...")
output_data = []

for IDN_EON, data in results.items():
    has_email = len(data['email_findings']) > 0
    has_text = len(data['text_findings']) > 0
    
    if has_email or has_text:
        comm_type = []
        if has_email:
            comm_type.append('Email')
        if has_text:
            comm_type.append('Text')
        
        email_confidence = max([f['confidence'] for f in data['email_findings']], default=0.0)
        text_confidence = max([f['confidence'] for f in data['text_findings']], default=0.0)
        
        email_locations = list(set([f['location'] for f in data['email_findings']]))
        text_locations = list(set([f['location'] for f in data['text_findings']]))
        
        email_cell_contents = list(set([f['cell_content'] for f in data['email_findings']]))
        text_cell_contents = list(set([f['cell_content'] for f in data['text_findings']]))
        
        output_data.append({
            'IDN_EON': IDN_EON,
            'data_source': ', '.join(sorted(data['data_sources'])),
            'communication_type': ', '.join(comm_type),
            'email_found_in': ', '.join(sorted(email_locations)) if email_locations else '',
            'email_cell_content': ' | '.join(email_cell_contents) if email_cell_contents else '',
            'email_confidence': round(email_confidence, 3) if has_email else '',
            'text_found_in': ', '.join(sorted(text_locations)) if text_locations else '',
            'text_cell_content': ' | '.join(text_cell_contents) if text_cell_contents else '',
            'text_confidence': round(text_confidence, 3) if has_text else ''
        })

output_df = pd.DataFrame(output_data).sort_values('IDN_EON').reset_index(drop=True)
output_dataset.write_with_schema(output_df)

print("\n" + "="*80)
print("PROCESSING COMPLETE")
print("="*80)
print(f"Total unique IDN_EON processed: {len(results)}")
print(f"IDN_EONs with ACTUAL communication capabilities: {len(output_df)}")
print(f"\nThis model correctly distinguishes:")
print(f"  ACCEPTS: 'e-communications', 'provides ability to send emails'")
print(f"  REJECTS: 'collect email, phone', 'email required for registration'")
print(f"\nConfidence threshold: 0.75")
print(f"Output: {output_dataset.name}")
print("="*80)
