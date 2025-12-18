import dataiku
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (precision_recall_fscore_support, confusion_matrix, 
                            classification_report, roc_auc_score)
import re
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Set random seed so we get the same results each time we run this
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Input/output datasets
input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# Training examples - these teach the model what real communication looks like
POSITIVE_EXAMPLES = [
    "app provides ability to send email messages", "users can send text messages through app",
    "platform enables email communication between users", "system allows sending sms notifications",
    "application supports text messaging", "service provides email notification capability",
    "app has email messaging feature", "platform includes text message sending",
    "enables users to communicate via email", "allows customers to send text messages",
    "provides sms communication feature", "supports email-based communication",
    "e-communications enabled", "electronic communications supported", "e-communication platform",
    "e-communications feature available", "electronic communication capability", 
    "e-communication channel active", "supports e-communications", "e-communication system",
    "app sends email notifications to users", "system delivers text alerts to customers",
    "platform transmits email updates", "service dispatches sms reminders",
    "application pushes email messages", "tool sends text notifications",
    "users receive email alerts from app", "customers get text messages from system",
    "subscribers receive email communications", "users get sms notifications",
    "email notification system", "text message delivery system", "sms alert infrastructure",
    "email communication module", "text messaging service", "notification delivery platform",
    "message sending capability", "alert distribution system", "communication engine",
    "users opt-in to receive emails", "customers consent to text notifications",
    "subscribers agree to email communications", "users enable sms alerts",
    "opt-in for email notifications", "subscribe to text message updates",
    "consent to receive promotional emails", "agree to sms marketing messages",
    "users can reply to emails", "customers respond via text message",
    "email conversation feature", "text messaging chat capability",
    "back-and-forth email communication", "interactive text messaging",
    "automatically sends email when", "triggers text message upon",
    "email sent automatically after", "sms dispatched when event occurs",
    "automated email notification system", "automatic text alert feature",
    "email marketing campaigns", "text message marketing blasts",
    "promotional email sending", "sms campaign management",
    "bulk email distribution", "mass text messaging capability",
    "transactional email delivery", "order confirmation emails sent",
    "shipping notification via text", "payment receipt via email",
    "appointment reminder texts", "verification code via sms",
    "users choose email as notification method", "customers select text for alerts",
    "email preferred for communications", "sms as primary contact channel",
    "notification delivery via email", "alerts sent through text messaging",
    "email notification settings", "text alert preferences configurable",
    "manage communication preferences", "control message delivery options",
    "customize notification channels", "configure alert methods",
    "real-time email alerts", "instant text notifications",
    "scheduled email reports", "periodic sms updates",
    "immediate notification delivery", "timed message sending",
    "email delivery tracking", "text message open rates",
    "notification engagement metrics", "message delivery confirmation",
    "communication analytics", "alert response tracking",
    "built-in messaging system", "integrated notification platform",
    "native email functionality", "embedded text messaging",
    "in-app communication tools", "communication feature set",
    "users will receive email", "customers get text notifications",
    "app notifies via email", "system alerts through text",
    "you can message via email", "send text messages to users",
    "email and text notification", "sms or email delivery",
    "multiple communication channels", "cross-channel messaging",
    "authorized to send emails", "permission to text customers",
    "approved communication channels", "enabled messaging capabilities"
]

NEGATIVE_EXAMPLES = [
    "collect email address", "gather phone number", "capture email information",
    "store email address", "save phone number", "record email data",
    "email address collected", "phone number captured", "email info gathered",
    "collect user email", "gather customer phone", "obtain email address",
    "email, phone number, address", "email and phone number collected",
    "fields: email, phone, name", "data collected: email, phone",
    "email address, mobile number", "phone, email, date of birth",
    "user provides email, phone", "enter email and phone number",
    "email phone address city", "collects email phone name",
    "email required for registration", "phone number for account creation",
    "email address in user profile", "phone stored in account",
    "registration requires email", "signup needs phone number",
    "email field in registration form", "phone number field for signup",
    "create account with email", "register using phone number",
    "email used as login", "phone number for authentication",
    "sign in with email", "login via phone number",
    "email as username", "phone for account access",
    "authenticate using email", "verify identity with phone",
    "email credential", "phone-based login",
    "email address on file", "phone number in database",
    "contact info stored", "email information saved",
    "phone number recorded", "email data maintained",
    "keep email address", "retain phone number",
    "display email address", "show phone number",
    "email visible in profile", "phone displayed in settings",
    "email appears on screen", "phone shown to user",
    "render email field", "present phone information",
    "validate email format", "verify phone number format",
    "email syntax check", "phone number validation",
    "email address verification", "phone format check",
    "confirm email structure", "validate phone digits",
    "email metadata", "phone number format",
    "email header information", "phone field data type",
    "email protocol", "phone number schema",
    "email api endpoint", "phone data structure",
    "plaintext format", "plain text encoding",
    "text field in database", "text data type",
    "text column", "text string variable",
    "text file format", "text-based storage",
    "text encoding utf-8", "text content type",
    "japanese text", "chinese characters",
    "korean text input", "multilingual text",
    "text in japanese", "chinese text display",
    "search by email", "filter by phone",
    "email in search results", "find phone number",
    "query email field", "lookup phone",
    "export email list", "import phone numbers",
    "email data export", "phone list download",
    "csv of emails", "spreadsheet with phones",
    "log email address", "track phone number",
    "record email entry", "monitor phone usage",
    "email activity log", "phone access tracking",
    "encrypt email data", "secure phone storage",
    "email pii protection", "phone number privacy",
    "email data retention", "phone information security",
    "contact us at email address", "call phone number",
    "email support at", "phone customer service",
    "support email listed", "help desk phone",
    "deduplicate emails", "clean phone list",
    "remove invalid emails", "normalize phone format",
    "email data quality", "phone number cleanup",
    "email address missing", "phone number not provided",
    "invalid email", "phone number empty",
    "no email on file", "phone unavailable",
    "old email address", "previous phone number",
    "archived email", "historical phone data",
    "past email information", "former phone contact",
    "sms for two-factor authentication", "text code for login",
    "sms verification code only", "2fa via text",
    "authentication sms", "security text message",
    "one-time password via sms", "login code by text",
    "email in user profile", "phone in account details",
    "profile contains email", "account shows phone",
    "user details include email", "contact section has phone",
    "email input field", "phone number textbox",
    "email form element", "phone entry field",
    "email field required", "phone field optional",
    "enter your email", "provide phone number",
    "email field help text", "phone number tooltip",
    "email format example", "phone number pattern",
    "match records by email", "link accounts via phone",
    "email as unique identifier", "phone as primary key",
    "join on email field", "merge using phone",
    "analyze email patterns", "phone number statistics",
    "email data mining", "phone usage analytics",
    "email distribution report", "phone number frequency"
]

# Balance dataset
min_samples = min(len(POSITIVE_EXAMPLES), len(NEGATIVE_EXAMPLES))
np.random.shuffle(POSITIVE_EXAMPLES)
np.random.shuffle(NEGATIVE_EXAMPLES)
POSITIVE_EXAMPLES = POSITIVE_EXAMPLES[:min_samples]
NEGATIVE_EXAMPLES = NEGATIVE_EXAMPLES[:min_samples]

print("="*80)
print("TRAINING DATA SUMMARY")
print("="*80)
print(f"Positive examples (communication): {len(POSITIVE_EXAMPLES)}")
print(f"Negative examples (data collection): {len(NEGATIVE_EXAMPLES)}")

# Key phrases for immediate classification
DEFINITIVE_COMMUNICATION_PHRASES = [
    'provides ability to send email', 'provides ability to send text',
    'e-communications', 'e-communication', 'electronic communications',
    'sends email to users', 'sends text to customers', 'delivers email notifications',
    'email notification system', 'text notification system',
    'email campaign', 'text campaign', 'sms campaign',
    'opt-in to receive email', 'subscribe to email',
    'via email', 'via text', 'via sms'
]

DEFINITIVE_DATA_COLLECTION_PHRASES = [
    'collect email', 'collect phone', 'gather email',
    'email, phone', 'phone, email',
    'store email', 'save email',
    'email required', 'email for registration',
    'email for login', 'email as username',
    'email field', 'phone field',
    'plaintext', 'text field', 'text data type',
    'japanese text', 'chinese text'
]

class ImprovedNeuralNetwork:
    """Neural network that learns to classify text as communication vs data collection"""
    
    def __init__(self, input_size, hidden_sizes=[64, 48, 32, 16], learning_rate=0.005, 
                 dropout_rate=0.25, l2_lambda=0.001):
        self.layers = []
        self.learning_rate = learning_rate
        self.initial_learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        self.l2_lambda = l2_lambda
        
        self.train_losses = []
        self.val_losses = []
        self.train_accs = []
        self.val_accs = []
        
        layer_sizes = [input_size] + hidden_sizes + [1]
        
        for i in range(len(layer_sizes) - 1):
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * scale
            b = np.zeros((1, layer_sizes[i+1]))
            gamma = np.ones((1, layer_sizes[i+1]))
            beta = np.zeros((1, layer_sizes[i+1]))
            
            self.layers.append({
                'W': W, 'b': b, 'A': None, 'Z': None,
                'gamma': gamma, 'beta': beta,
                'bn_mean': None, 'bn_var': None
            })
    
    def batch_norm(self, Z, layer, training=True, epsilon=1e-8):
        if training:
            mean = np.mean(Z, axis=0, keepdims=True)
            var = np.var(Z, axis=0, keepdims=True)
            layer['bn_mean'] = mean
            layer['bn_var'] = var
        else:
            mean = layer['bn_mean'] if layer['bn_mean'] is not None else 0
            var = layer['bn_var'] if layer['bn_var'] is not None else 1
        
        Z_norm = (Z - mean) / np.sqrt(var + epsilon)
        Z_scaled = layer['gamma'] * Z_norm + layer['beta']
        return Z_scaled
    
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
            
            if i < len(self.layers) - 1:
                Z = self.batch_norm(Z, layer, training)
            
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
    
    def compute_l2_loss(self):
        l2_loss = 0
        for layer in self.layers:
            l2_loss += np.sum(layer['W'] ** 2)
        return 0.5 * self.l2_lambda * l2_loss
    
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
            
            dW = (np.dot(A_prev.T, dZ) / m) + (self.l2_lambda * layer['W'])
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            dW = np.clip(dW, -5, 5)
            db = np.clip(db, -5, 5)
            
            layer['W'] -= self.learning_rate * dW
            layer['b'] -= self.learning_rate * db
            
            if i > 0:
                dA = np.dot(dZ, layer['W'].T)
    
    def learning_rate_schedule(self, epoch):
        self.learning_rate = self.initial_learning_rate * (0.5 ** (epoch // 200))
    
    def train(self, X, y, epochs=1000, batch_size=16, validation_split=0.2):
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        best_val_loss = float('inf')
        best_f1 = 0.0
        patience = 100
        patience_counter = 0
        
        print("\nTraining Progress:")
        print("-" * 90)
        print(f"{'Epoch':<8} {'Train Loss':<12} {'Val Loss':<12} {'Train Acc':<12} {'Val Acc':<12} {'Val F1':<12}")
        print("-" * 90)
        
        for epoch in range(epochs):
            self.learning_rate_schedule(epoch)
            
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
                train_loss += self.compute_l2_loss() / len(X_train)
                
                val_loss = -np.mean(y_val * np.log(val_output + 1e-8) + 
                                   (1 - y_val) * np.log(1 - val_output + 1e-8))
                
                train_pred = (train_output > 0.5).astype(int)
                val_pred = (val_output > 0.5).astype(int)
                
                train_acc = np.mean(train_pred == y_train)
                val_acc = np.mean(val_pred == y_val)
                
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_val, val_pred, average='binary', zero_division=0
                )
                
                self.train_losses.append(train_loss)
                self.val_losses.append(val_loss)
                self.train_accs.append(train_acc)
                self.val_accs.append(val_acc)
                
                print(f"{epoch:<8} {train_loss:<12.4f} {val_loss:<12.4f} {train_acc:<12.3f} "
                      f"{val_acc:<12.3f} {f1:<12.3f}")
                
                if f1 > best_f1:
                    best_val_loss = val_loss
                    best_f1 = f1
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"\nEarly stopping at epoch {epoch}")
                    print(f"Best validation F1: {best_f1:.3f}")
                    break
        
        print("-" * 90)
        return {'best_val_loss': best_val_loss, 'best_f1': best_f1}
    
    def predict(self, X):
        return self.forward(X, training=False)

def safe_str(value):
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

def extract_semantic_features(text):
    """Extract 30 features that capture semantic meaning"""
    text_str = safe_str(text)
    if not text_str:
        return np.zeros(30)
    
    text_lower = text_str.lower()
    features = []
    
    # Feature 1: Definitive communication phrases
    has_def_comm = any(phrase in text_lower for phrase in DEFINITIVE_COMMUNICATION_PHRASES)
    features.append(1 if has_def_comm else 0)
    
    # Feature 2: Definitive collection phrases
    has_def_collection = any(phrase in text_lower for phrase in DEFINITIVE_DATA_COLLECTION_PHRASES)
    features.append(1 if has_def_collection else 0)
    
    # Feature 3: E-communication
    has_ecomm = any(word in text_lower for word in ['e-communication', 'ecommunication', 'e-communications'])
    features.append(1 if has_ecomm else 0)
    
    # Feature 4: Capability language
    capability_language = ['provides ability', 'ability to send', 'allows users', 'enables users']
    features.append(1 if any(phrase in text_lower for phrase in capability_language) else 0)
    
    # Feature 5: List format
    list_patterns = [r'email\s*,\s*phone', r'phone\s*,\s*email']
    has_list_format = any(re.search(pattern, text_lower) for pattern in list_patterns)
    features.append(1 if has_list_format else 0)
    
    # Features 6-30: Additional semantic indicators
    active_sending = ['send', 'deliver', 'dispatch', 'transmit', 'push']
    features.append(1 if any(verb in text_lower for verb in active_sending) else 0)
    
    collection_verbs = ['collect', 'gather', 'capture', 'obtain']
    features.append(1 if any(verb in text_lower for verb in collection_verbs) else 0)
    
    storage_verbs = ['store', 'save', 'record', 'log']
    features.append(1 if any(verb in text_lower for verb in storage_verbs) else 0)
    
    notif_context = ['notification', 'alert', 'notify', 'reminder']
    features.append(1 if any(word in text_lower for word in notif_context) else 0)
    
    system_capability = ['system sends', 'platform sends', 'app sends']
    features.append(1 if any(phrase in text_lower for phrase in system_capability) else 0)
    
    registration = ['registration', 'signup', 'sign up', 'create account']
    features.append(1 if any(word in text_lower for word in registration) else 0)
    
    auth = ['login', 'log in', 'sign in', 'authentication']
    features.append(1 if any(word in text_lower for word in auth) else 0)
    
    profile = ['profile', 'account details', 'user information']
    features.append(1 if any(phrase in text_lower for phrase in profile) else 0)
    
    form_field = ['field', 'input', 'form', 'enter', 'provide']
    features.append(1 if any(word in text_lower for word in form_field) else 0)
    
    method_delivery = ['via email', 'via text', 'via sms', 'through email']
    features.append(1 if any(phrase in text_lower for phrase in method_delivery) else 0)
    
    opt_in = ['opt-in', 'opt in', 'subscribe', 'consent to receive']
    features.append(1 if any(phrase in text_lower for phrase in opt_in) else 0)
    
    campaign = ['campaign', 'marketing', 'promotional', 'blast']
    features.append(1 if any(word in text_lower for word in campaign) else 0)
    
    database = ['database', 'stored in', 'saved to', 'in table']
    features.append(1 if any(phrase in text_lower for phrase in database) else 0)
    
    features.append(1 if 'plaintext' in text_lower or 'plain text' in text_lower else 0)
    
    technical_text = ['text field', 'text data type', 'text column']
    features.append(1 if any(phrase in text_lower for phrase in technical_text) else 0)
    
    language_context = ['japanese text', 'chinese text', 'korean text']
    features.append(1 if any(phrase in text_lower for phrase in language_context) else 0)
    
    user_facing = ['you will receive', 'you can send', 'users receive']
    features.append(1 if any(phrase in text_lower for phrase in user_facing) else 0)
    
    two_way = ['reply', 'respond', 'conversation', 'chat']
    features.append(1 if any(word in text_lower for word in two_way) else 0)
    
    required = ['required', 'mandatory', 'must provide']
    features.append(1 if any(word in text_lower for word in required) else 0)
    
    display = ['display', 'show', 'visible', 'appears']
    features.append(1 if any(word in text_lower for word in display) else 0)
    
    features.extend([0.5, 0.5, 0.5, 0.5])
    
    # Combined score
    score = 0
    if has_def_comm: score += 5
    if has_ecomm: score += 4
    if has_def_collection: score -= 5
    if has_list_format: score -= 4
    features.append(max(0, min(1, (score + 5) / 10)))
    
    return np.array(features)

# TRAIN MODEL
print("\n" + "="*80)
print("TRAINING NEURAL NETWORK")
print("="*80)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

print("\nStep 1: TF-IDF feature extraction...")
vectorizer = TfidfVectorizer(
    max_features=150,
    ngram_range=(1, 5),
    min_df=1,
    sublinear_tf=True
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()

print("Step 2: Semantic feature extraction...")
X_features = np.array([extract_semantic_features(text) for text in all_examples])

print("Step 3: Combining and standardizing...")
X_combined = np.hstack([X_tfidf, X_features])
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)

print(f"Total features: {X_train.shape[1]}")

nn = ImprovedNeuralNetwork(
    input_size=X_train.shape[1],
    hidden_sizes=[64, 48, 32, 16],
    learning_rate=0.005,
    dropout_rate=0.25,
    l2_lambda=0.001
)

training_results = nn.train(X_train, labels, epochs=1000, batch_size=16, validation_split=0.2)

# Evaluate
y_pred_proba = nn.predict(X_train)
y_pred = (y_pred_proba > 0.5).astype(int)

accuracy = np.mean(y_pred == labels)
precision, recall, f1, _ = precision_recall_fscore_support(
    labels, y_pred, average='binary', zero_division=0
)

print("\n" + "="*80)
print("MODEL PERFORMANCE")
print("="*80)
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1:.4f}")

def predict_communication_capability(text):
    """Predict if text indicates communication capability"""
    text_str = safe_str(text)
    if not text_str:
        return 0.0
    
    text_lower = text_str.lower()
    
    # Hard disqualifiers
    hard_disqualifiers = [
        'email, phone', 'phone, email', 'plaintext', 'text field',
        'japanese text', 'chinese text', 'email stored in database',
        'email for login', 'registration requires email'
    ]
    
    for disqualifier in hard_disqualifiers:
        if disqualifier in text_lower:
            return 0.0
    
    # Hard qualifiers
    hard_qualifiers = [
        'e-communication', 'ecommunication', 'provides ability to send email',
        'provides ability to send text', 'email notification system'
    ]
    
    for qualifier in hard_qualifiers:
        if qualifier in text_lower:
            try:
                X_tfidf = vectorizer.transform([text_lower]).toarray()
                X_features = extract_semantic_features(text_str).reshape(1, -1)
                X_combined = np.hstack([X_tfidf, X_features])
                X = scaler.transform(X_combined)
                prediction = nn.predict(X)[0][0]
                return min(1.0, float(prediction) + 0.3)
            except:
                return 0.95
    
    try:
        X_tfidf = vectorizer.transform([text_lower]).toarray()
        X_features = extract_semantic_features(text_str).reshape(1, -1)
        X_combined = np.hstack([X_tfidf, X_features])
        X = scaler.transform(X_combined)
        prediction = nn.predict(X)[0][0]
        return float(prediction)
    except:
        return 0.0

# PROCESS DATASETS - FIRST JUST COUNT ALL IDN_EON
print("\n" + "="*80)
print("STEP 1: COUNTING ALL UNIQUE IDN_EON IN DATA")
print("="*80)

all_idn_eons = set()

for dataset_name in input_dataset_names:
    print(f"\nScanning {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None, infer_with_pandas=False)
    except Exception as e:
        print(f"  Could not load: {e}")
        continue
    
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        print(f"  No IDN_EON column found")
        continue
    
    # Get all unique IDN_EON from this table
    unique_in_table = set(df[idn_col].astype(str).unique())
    unique_in_table.discard('nan')  # Remove NaN
    unique_in_table.discard('')  # Remove empty strings
    
    print(f"  Found {len(unique_in_table)} unique IDN_EON in this table")
    all_idn_eons.update(unique_in_table)

print(f"\n{'='*80}")
print(f"TOTAL UNIQUE IDN_EON ACROSS ALL TABLES: {len(all_idn_eons)}")
print(f"{'='*80}")

# STEP 2: NOW PROCESS EACH IDN_EON
print("\n" + "="*80)
print("STEP 2: ANALYZING EACH IDN_EON FOR COMMUNICATION CAPABILITY")
print("="*80)

results = {}
processed_count = 0

for dataset_name in input_dataset_names:
    print(f"\nProcessing {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None, infer_with_pandas=False)
    except Exception as e:
        print(f"  Could not load: {e}")
        continue
    
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        continue
    
    # Get unique IDN_EON in this table
    unique_idns = df[idn_col].astype(str).unique()
    
    for idx, IDN_EON in enumerate(unique_idns):
        IDN_EON_str = safe_str(IDN_EON)
        if not IDN_EON_str or IDN_EON_str == 'nan':
            continue
        
        processed_count += 1
        if processed_count % 500 == 0:
            print(f"  Processed {processed_count}/{len(all_idn_eons)} IDN_EON...")
        
        # Initialize if first time seeing this IDN_EON
        if IDN_EON_str not in results:
            results[IDN_EON_str] = {
                'IDN_EON': IDN_EON_str,
                'data_sources': set(),
                'email_findings': [],
                'text_findings': []
            }
        
        results[IDN_EON_str]['data_sources'].add(dataset_name)
        
        # Get all rows for this IDN_EON
        idn_rows = df[df[idn_col].astype(str) == IDN_EON_str]
        
        # Check every column in these rows
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            # Get all values in this column for this IDN_EON
            for value in idn_rows[col]:
                original_value = safe_str(value)
                if not original_value:
                    continue
                
                value_lower = original_value.lower()
                
                # Check if mentions email or text
                has_email_mention = any(word in value_lower for word in ['email', 'e-mail'])
                has_text_mention = any(word in value_lower for word in ['text', 'sms', 'messaging'])
                
                if has_email_mention or has_text_mention:
                    try:
                        confidence = predict_communication_capability(original_value)
                    except:
                        confidence = 0.0
                    
                    # Use 0.55 threshold - pretty lenient to catch more
                    if confidence > 0.55:
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

print(f"\nTotal IDN_EON processed: {processed_count}")
print(f"Total IDN_EON in results dict: {len(results)}")

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
print("COMPLETE")
print("="*80)
print(f"Total unique IDN_EON in all data: {len(all_idn_eons)}")
print(f"IDN_EON analyzed: {len(results)}")
print(f"IDN_EON with communication capabilities: {len(output_df)}")
print(f"Percentage flagged: {len(output_df)/len(all_idn_eons)*100:.1f}%")
print(f"Model F1: {f1:.3f}")
print(f"Confidence threshold: 0.55")
print("="*80)
