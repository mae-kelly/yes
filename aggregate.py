import dataiku
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, classification_report
import re
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Set random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ============================================================================
# DATAIKU PARAMETERS - EASY TO ADJUST IN DATAIKU UI
# ============================================================================

CONFIDENCE_THRESHOLD = 0.60  # Lower to catch more results
MIN_FINDINGS_REQUIRED = 1
USE_KEYWORD_FALLBACK = True

print("="*80)
print("CONFIGURATION")
print("="*80)
print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
print(f"Minimum Findings Required: {MIN_FINDINGS_REQUIRED}")
print(f"Keyword Fallback Enabled: {USE_KEYWORD_FALLBACK}")
print("="*80)

# Input/output datasets
input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# Simplified but comprehensive training data
POSITIVE_EXAMPLES = [
    "app provides ability to send email messages",
    "users can send text messages through app",
    "platform enables email communication",
    "system allows sending sms notifications",
    "application supports text messaging",
    "service provides email notification capability",
    "e-communications enabled",
    "electronic communications supported",
    "e-communication platform",
    "app sends email notifications to users",
    "system delivers text alerts to customers",
    "platform transmits email updates",
    "service dispatches sms reminders",
    "users receive email alerts from app",
    "customers get text messages from system",
    "email notification system",
    "text message delivery system",
    "sms alert infrastructure",
    "users opt-in to receive emails",
    "customers consent to text notifications",
    "subscribed to email communications",
    "automatically sends email when order placed",
    "triggers text message upon account creation",
    "email marketing campaigns",
    "text message marketing blasts",
    "transactional email delivery",
    "order confirmation emails sent",
    "shipping notification via text",
    "appointment reminder texts",
    "users choose email as notification method",
    "email notification settings available",
    "real-time email alerts",
    "instant text notifications",
    "email delivery tracking",
    "built-in messaging system",
    "users will receive email confirmations",
    "app notifies via email",
    "email and text notification options",
    "authorized to send emails to users",
    "sends password reset emails",
    "delivers order confirmation texts",
    "system can send email messages",
    "platform has texting capability",
    "users can unsubscribe from emails",
    "notification via email",
    "daily email digest delivered",
    "targeted emails to specific users",
    "email integrated with customer database",
    "smtp email delivery configured",
    "sms gateway connected"
]

NEGATIVE_EXAMPLES = [
    "collect email address from users",
    "store email address in database",
    "email address collected during checkout",
    "email, phone number, address collected",
    "fields: email, phone, name",
    "email required for registration",
    "email address in user profile",
    "signup needs phone number",
    "email used as login username",
    "sign in with email address",
    "email as username credential",
    "email address on file in system",
    "contact info stored securely",
    "display email address on profile",
    "show phone number in settings",
    "validate email format is correct",
    "email syntax check performed",
    "email metadata stored in system",
    "phone field data type integer",
    "plaintext format for password",
    "plain text encoding used",
    "text field in database schema",
    "text data type for comments",
    "text column for user notes",
    "japanese text displayed in app",
    "chinese characters rendered as text",
    "log email activity in system",
    "track email usage in system",
    "analyze email patterns in data",
    "email data analytics dashboard",
    "search by email address field",
    "filter users by email domain",
    "contact us via email at support@company.com",
    "export email list to csv file",
    "import email addresses from file",
    "deduplicate email addresses in system",
    "clean email data for quality",
    "match email across multiple systems",
    "email address invalid format",
    "email field empty in form",
    "old email address on record",
    "email encrypted at rest in database",
    "sms one-time password for login only",
    "2fa via sms code",
    "email as primary key in database",
    "email settings available to configure",
    "copy email address to clipboard",
    "text file uploaded by user",
    "help text displayed to user",
    "email in user profile section",
    "email input field on form",
    "enter your email address here"
]

# Make sure we have equal numbers
min_samples = min(len(POSITIVE_EXAMPLES), len(NEGATIVE_EXAMPLES))
POSITIVE_EXAMPLES = POSITIVE_EXAMPLES[:min_samples]
NEGATIVE_EXAMPLES = NEGATIVE_EXAMPLES[:min_samples]

print(f"\nTraining with {len(POSITIVE_EXAMPLES)} positive and {len(NEGATIVE_EXAMPLES)} negative examples")

# Strong keyword indicators
STRONG_COMMUNICATION_KEYWORDS = [
    'e-communication', 'e-communications', 'electronic communications',
    'provides ability to send', 'notification system', 'alert system',
    'sends email to', 'sends text to', 'delivers email', 'delivers text',
    'email campaign', 'text campaign', 'sms campaign'
]

STRONG_NEGATIVE_KEYWORDS = [
    'email, phone', 'phone, email', 'plaintext', 'text field',
    'text data type', 'japanese text', 'chinese text',
    'email for login', 'email as username', 'collect email',
    'store email', 'email required for'
]

class SimpleNeuralNetwork:
    """Simplified neural network that actually learns"""
    
    def __init__(self, input_size, hidden_size=32, learning_rate=0.01):
        # Simple 2-layer network
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, 1) * 0.01
        self.b2 = np.zeros((1, 1))
        self.learning_rate = learning_rate
    
    def sigmoid(self, Z):
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def relu(self, Z):
        return np.maximum(0, Z)
    
    def forward(self, X):
        self.Z1 = np.dot(X, self.W1) + self.b1
        self.A1 = self.relu(self.Z1)
        self.Z2 = np.dot(self.A1, self.W2) + self.b2
        self.A2 = self.sigmoid(self.Z2)
        return self.A2
    
    def backward(self, X, y):
        m = X.shape[0]
        
        # Output layer gradients
        dZ2 = self.A2 - y
        dW2 = np.dot(self.A1.T, dZ2) / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m
        
        # Hidden layer gradients
        dA1 = np.dot(dZ2, self.W2.T)
        dZ1 = dA1 * (self.Z1 > 0)  # ReLU derivative
        dW1 = np.dot(X.T, dZ1) / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m
        
        # Update weights
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
    
    def train(self, X, y, epochs=500, batch_size=8):
        split = int(0.8 * len(X))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        best_f1 = 0
        
        print("\nTraining Progress:")
        print("-" * 70)
        
        for epoch in range(epochs):
            # Shuffle
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            # Mini-batch training
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                self.forward(X_batch)
                self.backward(X_batch, y_batch)
            
            # Evaluate every 50 epochs
            if epoch % 50 == 0 or epoch == epochs - 1:
                train_pred = (self.forward(X_train) > 0.5).astype(int)
                val_pred = (self.forward(X_val) > 0.5).astype(int)
                
                train_acc = np.mean(train_pred == y_train)
                val_acc = np.mean(val_pred == y_val)
                
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_val, val_pred, average='binary', zero_division=0
                )
                
                print(f"Epoch {epoch:3d}: Train Acc={train_acc:.3f}, Val Acc={val_acc:.3f}, "
                      f"Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
                
                if f1 > best_f1:
                    best_f1 = f1
        
        print("-" * 70)
        return best_f1

def safe_str(value):
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

def extract_simple_features(text):
    """Extract 20 simple but effective features"""
    text_str = safe_str(text)
    if not text_str:
        return np.zeros(20)
    
    text_lower = text_str.lower()
    features = []
    
    # Communication indicators
    features.append(1 if any(k in text_lower for k in STRONG_COMMUNICATION_KEYWORDS) else 0)
    features.append(1 if any(k in text_lower for k in STRONG_NEGATIVE_KEYWORDS) else 0)
    
    # Action verbs
    features.append(1 if any(v in text_lower for v in ['send', 'deliver', 'dispatch']) else 0)
    features.append(1 if any(v in text_lower for v in ['collect', 'store', 'save']) else 0)
    
    # Context
    features.append(1 if 'notification' in text_lower or 'alert' in text_lower else 0)
    features.append(1 if 'campaign' in text_lower else 0)
    features.append(1 if 'opt-in' in text_lower or 'subscribe' in text_lower else 0)
    features.append(1 if 'login' in text_lower or 'registration' in text_lower else 0)
    features.append(1 if 'database' in text_lower or 'field' in text_lower else 0)
    features.append(1 if 'via email' in text_lower or 'via text' in text_lower else 0)
    
    # Pattern detection
    features.append(1 if re.search(r'email\s*,\s*phone', text_lower) else 0)
    features.append(1 if 'plaintext' in text_lower else 0)
    features.append(1 if 'text field' in text_lower or 'text data type' in text_lower else 0)
    features.append(1 if 'system sends' in text_lower or 'app sends' in text_lower else 0)
    features.append(1 if 'users receive' in text_lower or 'customers get' in text_lower else 0)
    
    # Additional simple features
    features.append(1 if 'messaging' in text_lower else 0)
    features.append(1 if 'reply' in text_lower or 'respond' in text_lower else 0)
    features.append(1 if 'required' in text_lower else 0)
    features.append(1 if 'display' in text_lower or 'show' in text_lower else 0)
    features.append(1 if 'validate' in text_lower else 0)
    
    return np.array(features)

# ============================================================================
# TRAIN THE MODEL
# ============================================================================
print("\n" + "="*80)
print("TRAINING NEURAL NETWORK")
print("="*80)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

# TF-IDF with simpler settings
vectorizer = TfidfVectorizer(
    max_features=50,  # Fewer features to avoid overfitting
    ngram_range=(1, 3),  # Simpler ngrams
    min_df=1
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()
print(f"TF-IDF features: {X_tfidf.shape[1]}")

# Semantic features
X_features = np.array([extract_simple_features(text) for text in all_examples])
print(f"Semantic features: {X_features.shape[1]}")

# Combine
X_combined = np.hstack([X_tfidf, X_features])
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)
print(f"Total features: {X_train.shape[1]}")

# Train simpler model
nn = SimpleNeuralNetwork(input_size=X_train.shape[1], hidden_size=32, learning_rate=0.01)
best_f1 = nn.train(X_train, labels, epochs=500, batch_size=8)

# Final evaluation
y_pred_proba = nn.forward(X_train)
y_pred = (y_pred_proba > 0.5).astype(int)

accuracy = np.mean(y_pred == labels)
precision, recall, f1, _ = precision_recall_fscore_support(labels, y_pred, average='binary', zero_division=0)
conf_matrix = confusion_matrix(labels, y_pred)

print("\n" + "="*80)
print("FINAL MODEL PERFORMANCE")
print("="*80)
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1:.4f}")
print(f"\nConfusion Matrix:")
print(f"              Predicted")
print(f"            Neg    Pos")
print(f"Actual Neg  {conf_matrix[0,0]:3d}   {conf_matrix[0,1]:3d}")
print(f"Actual Pos  {conf_matrix[1,0]:3d}   {conf_matrix[1,1]:3d}")

if f1 < 0.5:
    print("\n⚠ WARNING: F1 score is low! Model may not be learning properly.")
    print("This could mean the features aren't discriminative enough.")

def predict_communication_capability(text):
    """Predict with keyword fallback"""
    text_str = safe_str(text)
    if not text_str:
        return 0.0
    
    text_lower = text_str.lower()
    
    # Hard negatives
    for keyword in STRONG_NEGATIVE_KEYWORDS:
        if keyword in text_lower:
            return 0.0
    
    # Hard positives
    for keyword in STRONG_COMMUNICATION_KEYWORDS:
        if keyword in text_lower:
            return 0.95
    
    # Neural network
    try:
        X_tfidf = vectorizer.transform([text_lower]).toarray()
        X_features = extract_simple_features(text_str).reshape(1, -1)
        X_combined = np.hstack([X_tfidf, X_features])
        X = scaler.transform(X_combined)
        prediction = nn.forward(X)[0][0]
        return float(prediction)
    except:
        return 0.0

# ============================================================================
# STEP 1: COUNT ALL UNIQUE IDN_EON
# ============================================================================
print("\n" + "="*80)
print("STEP 1: COUNTING ALL UNIQUE IDN_EON")
print("="*80)

all_unique_idn_eons = set()

for dataset_name in input_dataset_names:
    print(f"\nScanning {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None)
        for col in df.columns:
            df[col] = df[col].astype(str)
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
    
    unique_in_table = df[idn_col].unique()
    valid_idns = set()
    for idn in unique_in_table:
        idn_str = safe_str(idn)
        if idn_str and idn_str not in ['nan', 'None', '', 'NaN']:
            valid_idns.add(idn_str)
    
    print(f"  Found {len(valid_idns):,} unique IDN_EON")
    all_unique_idn_eons.update(valid_idns)

print(f"\n{'='*80}")
print(f"TOTAL UNIQUE IDN_EON: {len(all_unique_idn_eons):,}")
print(f"{'='*80}")

# ============================================================================
# STEP 2: ANALYZE FOR COMMUNICATION
# ============================================================================
print("\n" + "="*80)
print("STEP 2: ANALYZING FOR COMMUNICATION CAPABILITIES")
print("="*80)

communication_findings = {}
processed = 0

for dataset_name in input_dataset_names:
    print(f"\nAnalyzing {dataset_name}...")
    
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
    
    unique_idns = df[idn_col].unique()
    
    for IDN_EON in unique_idns:
        IDN_EON_str = safe_str(IDN_EON)
        if not IDN_EON_str or IDN_EON_str in ['nan', 'None', '', 'NaN']:
            continue
        
        processed += 1
        if processed % 500 == 0:
            print(f"  Progress: {processed:,}/{len(all_unique_idn_eons):,}")
        
        if IDN_EON_str not in communication_findings:
            communication_findings[IDN_EON_str] = {
                'IDN_EON': IDN_EON_str,
                'sources': set(),
                'email_findings': [],
                'text_findings': []
            }
        
        communication_findings[IDN_EON_str]['sources'].add(dataset_name)
        idn_rows = df[df[idn_col] == IDN_EON_str]
        
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            for value in idn_rows[col]:
                val_str = safe_str(value)
                if not val_str or val_str in ['nan', 'None', 'NaN']:
                    continue
                
                val_lower = val_str.lower()
                has_email = any(w in val_lower for w in ['email', 'e-mail'])
                has_text = any(w in val_lower for w in ['text', 'sms', 'messaging'])
                
                if has_email or has_text:
                    confidence = predict_communication_capability(val_str)
                    
                    if confidence > CONFIDENCE_THRESHOLD:
                        finding = {
                            'location': f"{col} [{dataset_name}]",
                            'confidence': confidence,
                            'content': val_str[:200]
                        }
                        
                        if has_email:
                            communication_findings[IDN_EON_str]['email_findings'].append(finding)
                        if has_text and 'plaintext' not in val_lower:
                            communication_findings[IDN_EON_str]['text_findings'].append(finding)

# ============================================================================
# STEP 3: BUILD OUTPUT
# ============================================================================
print("\n" + "="*80)
print("STEP 3: BUILDING OUTPUT")
print("="*80)

output_data = []

for IDN_EON, data in communication_findings.items():
    has_email = len(data['email_findings']) >= MIN_FINDINGS_REQUIRED
    has_text = len(data['text_findings']) >= MIN_FINDINGS_REQUIRED
    
    if has_email or has_text:
        comm_type = []
        if has_email:
            comm_type.append('Email')
        if has_text:
            comm_type.append('Text')
        
        email_confidence = max([f['confidence'] for f in data['email_findings']], default=0.0)
        text_confidence = max([f['confidence'] for f in data['text_findings']], default=0.0)
        max_confidence = max(email_confidence, text_confidence)
        
        email_locs = list(set([f['location'] for f in data['email_findings']]))
        text_locs = list(set([f['location'] for f in data['text_findings']]))
        
        email_contents = list(set([f['content'] for f in data['email_findings']]))[:3]
        text_contents = list(set([f['content'] for f in data['text_findings']]))[:3]
        
        output_data.append({
            'IDN_EON': IDN_EON,
            'max_confidence': max_confidence,
            'data_source': ', '.join(sorted(data['sources'])),
            'communication_type': ', '.join(comm_type),
            'email_found_in': ', '.join(sorted(email_locs)) if email_locs else '',
            'email_cell_content': ' | '.join(email_contents) if email_contents else '',
            'email_confidence': round(email_confidence, 3) if has_email else 0.0,
            'text_found_in': ', '.join(sorted(text_locs)) if text_locs else '',
            'text_cell_content': ' | '.join(text_contents) if text_contents else '',
            'text_confidence': round(text_confidence, 3) if has_text else 0.0,
            'total_email_findings': len(data['email_findings']),
            'total_text_findings': len(data['text_findings'])
        })

output_df = pd.DataFrame(output_data).sort_values('max_confidence', ascending=False).reset_index(drop=True)
output_df = output_df.drop('max_confidence', axis=1)

output_dataset.write_with_schema(output_df)

print("\n" + "="*80)
print("FINAL RESULTS")
print("="*80)
print(f"Total unique IDN_EON: {len(all_unique_idn_eons):,}")
print(f"IDN_EON with communication: {len(output_df):,}")
print(f"Percentage: {len(output_df)/len(all_unique_idn_eons)*100:.2f}%")
print(f"Model F1: {f1:.4f}")
print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
print("="*80)
