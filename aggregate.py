import dataiku
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import re

# Input/output datasets
input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# Keywords to search for
EMAIL_KEYWORDS = ['email', 'e-mail', 'mail', 'electronic mail']
TEXT_KEYWORDS = ['text', 'sms', 'message', 'messaging', 'txt']
GENERAL_KEYWORDS = ['e communication', 'ecommunication', 'e-communication', 'electronic communication']

# Comprehensive training data covering diverse real-world scenarios
POSITIVE_EXAMPLES = [
    # Direct capability statements
    "email opt-in preference", "can receive text messages", "subscribed to email communications",
    "consent for sms notifications", "email delivery enabled", "text message capability available",
    "authorized email contact", "accepts electronic communications", "prefers email method",
    "messaging channel active", "email address on file", "mobile number for texting",
    
    # Permission and consent language
    "agrees to receive emails", "opted in for text alerts", "permission granted for messaging",
    "consented to email marketing", "allows text notifications", "approved for sms contact",
    "accepts promotional emails", "subscribes to text updates", "email communications permitted",
    "messaging opt-in confirmed", "authorized to send emails", "can text customer",
    
    # Preference and channel selection
    "email is preferred contact method", "text messaging preferred", "chose email communication",
    "selected sms as notification channel", "email preferred over mail", "wants text reminders",
    "email communication channel selected", "text message option enabled", "prefers electronic mail",
    "messaging is primary contact", "email for notifications", "text for urgent alerts",
    
    # Active status indicators
    "email actively monitored", "text messaging active", "email account verified",
    "phone number validated for sms", "email reachable", "text delivery successful",
    "email engagement high", "responds to text messages", "email opens tracked",
    "text message delivered", "email bounces none", "sms active subscriber",
    
    # Business/formal contexts
    "email address provided for correspondence", "text number on record", "email contact information",
    "sms capability confirmed", "email communication established", "text messaging available",
    "email registered in system", "mobile contact for texting", "email on customer profile",
    "text alerts enabled in account", "email notification settings active", "sms delivery channel open",
    
    # Implicit capability indicators
    "check your email for updates", "we'll text you when ready", "sent via email",
    "text message sent", "email confirmation received", "sms code delivered",
    "email newsletter subscriber", "text alert recipient", "receives email invoices",
    "gets text appointment reminders", "email statements delivered", "sms verification enabled",
    
    # Technical/system contexts
    "email gateway configured", "text api enabled", "email server accessible",
    "sms provider active", "email routing established", "text service provisioned",
    "email protocol supported", "messaging infrastructure ready", "email capability verified",
    "text platform integrated", "email system operational", "sms gateway connected",
    
    # Variation in phrasing
    "has email", "can email", "email available", "text ok", "texting allowed",
    "email works", "texts accepted", "email good", "sms yes", "email valid",
    "text capable", "email functional", "messaging on", "email accessible", "text ready",
    
    # Double-opt-in and verification
    "email verified and confirmed", "text opt-in double confirmed", "email validation complete",
    "sms confirmation received", "email double opt-in", "text subscription verified",
    
    # Frequency and cadence
    "receives weekly emails", "daily text updates", "monthly email newsletter",
    "real-time text alerts", "periodic email communications", "regular sms notifications",
    
    # Context with other channels
    "prefers email over phone", "text instead of mail", "email rather than call",
    "sms preferred to postal", "email more than fax", "text not phone call"
]

NEGATIVE_EXAMPLES = [
    # Direct rejection
    "no email preference", "opted out of text", "email declined", "unsubscribed from messages",
    "text not available", "email prohibited", "cannot send sms", "messaging disabled",
    "do not email", "rejected text communications", "email blocked", "text messaging off",
    
    # Opt-out language
    "unsubscribed from emails", "opted out of texts", "removed from email list",
    "text opt-out confirmed", "email preference removed", "sms unsubscribe",
    "no longer receives emails", "text alerts disabled", "email communications stopped",
    "messaging opt-out", "declined email marketing", "refused text notifications",
    
    # Explicit refusal
    "does not want emails", "refuses text messages", "no email contact",
    "rejects sms notifications", "email not permitted", "text messages unwanted",
    "email contact denied", "messaging not allowed", "no email authorization",
    "text delivery blocked", "email not authorized", "sms not approved",
    
    # Invalid or missing information
    "email address missing", "no phone number for text", "email invalid",
    "text number unavailable", "email not provided", "mobile number unknown",
    "email bounced permanently", "text undeliverable", "email does not exist",
    "phone disconnected for sms", "email hard bounce", "text number invalid",
    
    # Inactive status
    "email account closed", "text messaging inactive", "email suspended",
    "sms service terminated", "email deactivated", "text capability removed",
    "email no longer monitored", "text line disconnected", "email abandoned",
    "messaging service cancelled", "email unreachable", "text delivery failed",
    
    # Privacy and restriction
    "email privacy settings block", "text restricted by carrier", "email spam filtered",
    "sms blocked by user", "email suppressed", "text number on dnc list",
    "email blacklisted", "messaging restricted", "email quarantined",
    "text suppression active", "email do not contact", "sms opt-out list",
    
    # Past tense (capability no longer exists)
    "previously had email", "used to text", "formerly email subscriber",
    "past text recipient", "email was active", "text messaging was enabled",
    "old email address", "previous mobile number", "expired email contact",
    "outdated text number", "historical email preference", "legacy messaging contact",
    
    # Negative with absolutes
    "never email", "never text", "absolutely no email", "definitely no texts",
    "under no circumstances email", "will not accept sms", "refuses all email",
    "blocks all texts", "no email whatsoever", "zero text messages",
    
    # Legal/compliance restrictions
    "email restricted by law", "text forbidden by regulation", "email prohibited by policy",
    "sms not compliant", "email violates terms", "text not legal",
    "email against guidelines", "messaging non-compliant", "email restricted account",
    
    # System/technical blocks
    "email filtering all messages", "text gateway blocked", "email server rejects",
    "sms carrier blocking", "email firewall blocking", "text service unavailable",
    "email system down", "messaging platform offline", "email delivery impossible",
    
    # Conditional negatives
    "email only if emergency", "text not for marketing", "email restricted use only",
    "sms for security only", "email prohibited for promotions", "text limited to alerts",
    
    # Variation in phrasing
    "no email", "cant email", "email unavailable", "text not ok", "texting not allowed",
    "email doesnt work", "texts rejected", "email bad", "sms no", "email invalid",
    "text not capable", "email nonfunctional", "messaging off", "email inaccessible", "text not ready",
    
    # Ambiguous negatives
    "email unknown", "text unclear", "email status pending", "text unconfirmed",
    "email not verified", "text awaiting confirmation"
]

# Additional contextual patterns for feature engineering
CAPABILITY_INDICATORS = [
    'opt', 'prefer', 'consent', 'agree', 'subscribe', 'allow', 'enable', 'accept',
    'permission', 'authorized', 'can', 'able', 'capability', 'available', 'method',
    'channel', 'contact', 'communicate', 'send', 'receive', 'deliver', 'notification',
    'alert', 'yes', 'approved', 'confirmed', 'verified', 'active', 'on', 'ok',
    'permitted', 'granted', 'allowed', 'ready', 'functional', 'working', 'operational',
    'valid', 'registered', 'enrolled', 'signed up', 'monitored', 'reachable'
]

NON_CAPABILITY_INDICATORS = [
    'no', 'not', 'never', 'none', 'denied', 'reject', 'refuse', 'decline',
    'opt out', 'opt-out', 'optout', 'unsubscribe', 'disable', 'block', 'prohibit',
    'restrict', 'ban', 'forbidden', 'cannot', 'unable', 'invalid', 'missing',
    'unavailable', 'closed', 'suspended', 'deactivated', 'terminated', 'removed',
    'blocked', 'suppressed', 'blacklisted', 'restricted', 'quarantined', 'bounced',
    'failed', 'disconnected', 'off', 'inactive', 'cancelled', 'expired', 'old',
    'previous', 'former', 'past', 'historical', 'legacy', 'outdated', 'bad'
]

class AdvancedNeuralNet:
    """Advanced feedforward neural network with dropout and batch normalization concepts"""
    
    def __init__(self, input_size, hidden_sizes=[32, 16], learning_rate=0.01, dropout_rate=0.2):
        self.layers = []
        self.learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        
        # Initialize multi-layer architecture
        layer_sizes = [input_size] + hidden_sizes + [1]
        
        for i in range(len(layer_sizes) - 1):
            # Xavier/He initialization
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * scale
            b = np.zeros((1, layer_sizes[i+1]))
            self.layers.append({'W': W, 'b': b, 'A': None, 'Z': None})
    
    def relu(self, Z):
        """ReLU activation with numerical stability"""
        return np.maximum(0, Z)
    
    def leaky_relu(self, Z, alpha=0.01):
        """Leaky ReLU to prevent dying neurons"""
        return np.where(Z > 0, Z, alpha * Z)
    
    def relu_derivative(self, Z):
        """Derivative of ReLU"""
        return (Z > 0).astype(float)
    
    def leaky_relu_derivative(self, Z, alpha=0.01):
        """Derivative of Leaky ReLU"""
        return np.where(Z > 0, 1, alpha)
    
    def sigmoid(self, Z):
        """Sigmoid with numerical stability"""
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def forward(self, X, training=True):
        """Forward propagation through all layers"""
        A = X
        
        for i, layer in enumerate(self.layers):
            Z = np.dot(A, layer['W']) + layer['b']
            layer['Z'] = Z
            
            # Apply activation
            if i < len(self.layers) - 1:
                # Hidden layers use Leaky ReLU
                A = self.leaky_relu(Z)
                
                # Apply dropout during training
                if training and self.dropout_rate > 0:
                    dropout_mask = np.random.binomial(1, 1 - self.dropout_rate, size=A.shape)
                    A = A * dropout_mask / (1 - self.dropout_rate)
            else:
                # Output layer uses sigmoid
                A = self.sigmoid(Z)
            
            layer['A'] = A
        
        return A
    
    def backward(self, X, y):
        """Backward propagation with gradient clipping"""
        m = X.shape[0]
        
        # Start with output layer gradient
        dA = self.layers[-1]['A'] - y
        
        # Backpropagate through layers
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            
            if i < len(self.layers) - 1:
                # Hidden layers
                dZ = dA * self.leaky_relu_derivative(layer['Z'])
            else:
                # Output layer
                dZ = dA
            
            # Get input to this layer
            A_prev = X if i == 0 else self.layers[i-1]['A']
            
            # Compute gradients
            dW = np.dot(A_prev.T, dZ) / m
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            # Gradient clipping to prevent exploding gradients
            dW = np.clip(dW, -5, 5)
            db = np.clip(db, -5, 5)
            
            # Update parameters
            layer['W'] -= self.learning_rate * dW
            layer['b'] -= self.learning_rate * db
            
            # Prepare gradient for previous layer
            if i > 0:
                dA = np.dot(dZ, layer['W'].T)
    
    def train(self, X, y, epochs=500, batch_size=16, validation_split=0.2):
        """Train with mini-batch gradient descent and validation"""
        # Split into train/validation
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        best_val_loss = float('inf')
        patience = 50
        patience_counter = 0
        
        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            # Mini-batch training
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                # Forward and backward pass
                self.forward(X_batch, training=True)
                self.backward(X_batch, y_batch)
            
            # Validation and early stopping
            if epoch % 10 == 0:
                train_output = self.forward(X_train, training=False)
                val_output = self.forward(X_val, training=False)
                
                train_loss = -np.mean(y_train * np.log(train_output + 1e-8) + 
                                     (1 - y_train) * np.log(1 - train_output + 1e-8))
                val_loss = -np.mean(y_val * np.log(val_output + 1e-8) + 
                                   (1 - y_val) * np.log(1 - val_output + 1e-8))
                
                # Calculate accuracy
                train_acc = np.mean((train_output > 0.5) == y_train)
                val_acc = np.mean((val_output > 0.5) == y_val)
                
                print(f"Epoch {epoch}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, "
                      f"Train Acc={train_acc:.3f}, Val Acc={val_acc:.3f}")
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch}")
                    break
    
    def predict(self, X):
        """Make predictions"""
        return self.forward(X, training=False)

def extract_advanced_features(text):
    """Extract hand-crafted features for better understanding"""
    if pd.isna(text) or not text:
        return np.zeros(10)
    
    text_lower = str(text).lower()
    
    features = []
    
    # Feature 1: Count of positive capability indicators
    positive_count = sum(1 for word in CAPABILITY_INDICATORS if word in text_lower)
    features.append(min(positive_count / 5, 1))  # Normalize
    
    # Feature 2: Count of negative indicators
    negative_count = sum(1 for word in NON_CAPABILITY_INDICATORS if word in text_lower)
    features.append(min(negative_count / 5, 1))
    
    # Feature 3: Presence of strong positive words
    strong_positive = ['yes', 'active', 'enabled', 'confirmed', 'verified', 'ok']
    features.append(1 if any(word in text_lower for word in strong_positive) else 0)
    
    # Feature 4: Presence of strong negative words
    strong_negative = ['no', 'not', 'never', 'blocked', 'unsubscribed', 'opt-out', 'declined']
    features.append(1 if any(word in text_lower for word in strong_negative) else 0)
    
    # Feature 5: Text length (normalized)
    features.append(min(len(text_lower) / 200, 1))
    
    # Feature 6: Word count (normalized)
    features.append(min(len(text_lower.split()) / 20, 1))
    
    # Feature 7: Presence of negation pattern "not/no + positive word"
    negation_pattern = any(re.search(rf'\b(no|not|never)\s+{word}', text_lower) 
                          for word in CAPABILITY_INDICATORS[:10])
    features.append(1 if negation_pattern else 0)
    
    # Feature 8: Presence of permission/consent words
    permission_words = ['consent', 'permission', 'authorized', 'opt-in', 'subscribe']
    features.append(1 if any(word in text_lower for word in permission_words) else 0)
    
    # Feature 9: Ratio of positive to negative words
    if negative_count > 0:
        features.append(positive_count / (positive_count + negative_count))
    else:
        features.append(1 if positive_count > 0 else 0.5)
    
    # Feature 10: Contains both email/text keyword AND capability language
    has_comm_keyword = any(kw in text_lower for kw in 
                          ['email', 'text', 'sms', 'message', 'mail', 'messaging'])
    has_capability = any(kw in text_lower for kw in CAPABILITY_INDICATORS[:15])
    features.append(1 if (has_comm_keyword and has_capability) else 0)
    
    return np.array(features)

# Prepare comprehensive training data
print("="*60)
print("TRAINING ADVANCED NEURAL NETWORK MODEL")
print("="*60)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

print(f"Training examples: {len(POSITIVE_EXAMPLES)} positive, {len(NEGATIVE_EXAMPLES)} negative")

# Create TF-IDF features (capture word importance)
vectorizer = TfidfVectorizer(
    max_features=100,
    ngram_range=(1, 3),  # Capture 1-3 word phrases
    min_df=1,
    sublinear_tf=True
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()

# Extract hand-crafted features
X_features = np.array([extract_advanced_features(text) for text in all_examples])

# Combine TF-IDF and hand-crafted features
X_combined = np.hstack([X_tfidf, X_features])

# Standardize
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)

print(f"Feature dimensionality: {X_train.shape[1]}")
print(f"TF-IDF features: {X_tfidf.shape[1]}, Hand-crafted features: {X_features.shape[1]}")

# Initialize and train advanced neural network
print("\nInitializing neural network architecture...")
print("Architecture: Input -> 32 neurons -> 16 neurons -> Output")
print("Activation: Leaky ReLU (hidden), Sigmoid (output)")
print("Regularization: Dropout (20%)")
print("Optimization: Mini-batch gradient descent with early stopping\n")

nn = AdvancedNeuralNet(
    input_size=X_train.shape[1],
    hidden_sizes=[32, 16],
    learning_rate=0.01,
    dropout_rate=0.2
)

nn.train(X_train, labels, epochs=500, batch_size=16, validation_split=0.2)

print("\n✅ Model training complete!\n")

def extract_context(text, keyword, window=150):
    """Extract broader context around keyword"""
    text_lower = str(text).lower()
    match = re.search(rf'.{{0,{window}}}{re.escape(keyword)}.{{0,{window}}}', text_lower)
    return match.group(0) if match else text_lower[:300]

def predict_capability(text):
    """Use trained neural network to predict capability"""
    if pd.isna(text) or not text:
        return 0.0
    
    text_str = str(text).lower()
    
    # Get TF-IDF features
    X_tfidf = vectorizer.transform([text_str]).toarray()
    
    # Get hand-crafted features
    X_features = extract_advanced_features(text_str).reshape(1, -1)
    
    # Combine and scale
    X_combined = np.hstack([X_tfidf, X_features])
    X = scaler.transform(X_combined)
    
    # Get prediction
    prediction = nn.predict(X)[0][0]
    
    return float(prediction)

# Process datasets
print("="*60)
print("PROCESSING DATASETS")
print("="*60)

results = {}

for dataset_name in input_dataset_names:
    print(f"\n📊 Processing {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe()
    except:
        print(f"⚠️  Could not load {dataset_name}")
        continue
    
    if 'idn_eon' not in df.columns:
        print(f"⚠️  Skipping {dataset_name} - no idn_eon column")
        continue
    
    unique_idns = df['idn_eon'].dropna().unique()
    print(f"   Found {len(unique_idns)} unique idn_eon values")
    
    for idx, idn_eon in enumerate(unique_idns):
        if idx % 100 == 0 and idx > 0:
            print(f"   Processed {idx}/{len(unique_idns)} IDNs...")
        
        if idn_eon not in results:
            results[idn_eon] = {
                'idn_eon': idn_eon,
                'data_sources': set(),
                'email_findings': [],
                'text_findings': []
            }
        
        results[idn_eon]['data_sources'].add(dataset_name)
        idn_rows = df[df['idn_eon'] == idn_eon]
        
        # Check all columns
        for col in df.columns:
            if col == 'idn_eon':
                continue
            
            for value in idn_rows[col]:
                if pd.isna(value):
                    continue
                
                value_str = str(value).lower()
                
                # Check for email keywords
                for keyword in EMAIL_KEYWORDS:
                    if keyword in value_str:
                        context = extract_context(value, keyword)
                        confidence = predict_capability(context)
                        
                        # Threshold: only add if confidence > 0.5
                        if confidence > 0.5:
                            results[idn_eon]['email_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'context': context[:100]
                            })
                        break
                
                # Check for text keywords
                for keyword in TEXT_KEYWORDS:
                    if keyword in value_str:
                        context = extract_context(value, keyword)
                        confidence = predict_capability(context)
                        
                        if confidence > 0.5:
                            results[idn_eon]['text_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'context': context[:100]
                            })
                        break
                
                # Check for general e-communication keywords
                for keyword in GENERAL_KEYWORDS:
                    if keyword in value_str:
                        context = extract_context(value, keyword)
                        confidence = predict_capability(context)
                        
                        if confidence > 0.5:
                            # E-communication could be both
                            results[idn_eon]['email_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'context': context[:100]
                            })
                            results[idn_eon]['text_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'context': context[:100]
                            })
                        break

# Build output
print("\n📝 Building output dataset...")
output_data = []

for idn_eon, data in results.items():
    has_email = len(data['email_findings']) > 0
    has_text = len(data['text_findings']) > 0
    
    if has_email or has_text:
        comm_type = []
        if has_email:
            comm_type.append('Email')
        if has_text:
            comm_type.append('Text')
        
        # Get highest confidence for each type
        email_confidence = max([f['confidence'] for f in data['email_findings']], default=0.0)
        text_confidence = max([f['confidence'] for f in data['text_findings']], default=0.0)
        
        # Deduplicate locations
        email_locations = list(set([f['location'] for f in data['email_findings']]))
        text_locations = list(set([f['location'] for f in data['text_findings']]))
        
        output_data.append({
            'idn_eon': idn_eon,
            'data_source': ', '.join(sorted(data['data_sources'])),
            'communication_type': ', '.join(comm_type),
            'email_found_in': ', '.join(sorted(email_locations)) if email_locations else '',
            'email_confidence': round(email_confidence, 3) if has_email else '',
            'text_found_in': ', '.join(sorted(text_locations)) if text_locations else '',
            'text_confidence': round(text_confidence, 3) if has_text else ''
        })

output_df = pd.DataFrame(output_data).sort_values('idn_eon').reset_index(drop=True)
output_dataset.write_with_schema(output_df)

# Final summary
print("\n" + "="*60)
print("✅ PROCESSING COMPLETE")
print("="*60)
print(f"Total unique idn_eon processed: {len(results)}")
print(f"IDNs with communication capabilities: {len(output_df)}")
print(f"\nConfidence Distribution:")
print(f"  High confidence (>0.8): {len(output_df[(output_df['email_confidence'] > 0.8) | (output_df['text_confidence'] > 0.8)])}")
print(f"  Medium confidence (0.6-0.8): {len(output_df[((output_df['email_confidence'] >= 0.6) & (output_df['email_confidence'] <= 0.8)) | ((output_df['text_confidence'] >= 0.6) & (output_df['text_confidence'] <= 0.8))])}")
print(f"  Lower confidence (0.5-0.6): {len(output_df[((output_df['email_confidence'] >= 0.5) & (output_df['email_confidence'] < 0.6)) | ((output_df['text_confidence'] >= 0.5) & (output_df['text_confidence'] < 0.6))])}")
print(f"\nOutput written to: {output_dataset.name}")
print("="*60)
