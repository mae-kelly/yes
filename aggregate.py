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

# Training data - these are example sentences that help the model learn what indicates capability vs non-capability
# The model needs to see many different ways people write about communication preferences in data
POSITIVE_EXAMPLES = [
    # These examples show language that indicates someone CAN be contacted
    "email opt-in preference", "can receive text messages", "subscribed to email communications",
    "consent for sms notifications", "email delivery enabled", "text message capability available",
    "authorized email contact", "accepts electronic communications", "prefers email method",
    "messaging channel active", "email address on file", "mobile number for texting",
    
    # Permission and consent language - these indicate the person agreed to be contacted
    "agrees to receive emails", "opted in for text alerts", "permission granted for messaging",
    "consented to email marketing", "allows text notifications", "approved for sms contact",
    "accepts promotional emails", "subscribes to text updates", "email communications permitted",
    "messaging opt-in confirmed", "authorized to send emails", "can text customer",
    
    # Preference and channel selection - these show which method they prefer
    "email is preferred contact method", "text messaging preferred", "chose email communication",
    "selected sms as notification channel", "email preferred over mail", "wants text reminders",
    "email communication channel selected", "text message option enabled", "prefers electronic mail",
    "messaging is primary contact", "email for notifications", "text for urgent alerts",
    
    # Active status indicators - these suggest the channel is working and being used
    "email actively monitored", "text messaging active", "email account verified",
    "phone number validated for sms", "email reachable", "text delivery successful",
    "email engagement high", "responds to text messages", "email opens tracked",
    "text message delivered", "email bounces none", "sms active subscriber",
    
    # Business/formal contexts - common in corporate databases
    "email address provided for correspondence", "text number on record", "email contact information",
    "sms capability confirmed", "email communication established", "text messaging available",
    "email registered in system", "mobile contact for texting", "email on customer profile",
    "text alerts enabled in account", "email notification settings active", "sms delivery channel open",
    
    # Implicit capability indicators - these suggest communication is happening
    "check your email for updates", "we'll text you when ready", "sent via email",
    "text message sent", "email confirmation received", "sms code delivered",
    "email newsletter subscriber", "text alert recipient", "receives email invoices",
    "gets text appointment reminders", "email statements delivered", "sms verification enabled",
    
    # Technical/system contexts - how systems describe active communication channels
    "email gateway configured", "text api enabled", "email server accessible",
    "sms provider active", "email routing established", "text service provisioned",
    "email protocol supported", "messaging infrastructure ready", "email capability verified",
    "text platform integrated", "email system operational", "sms gateway connected",
    
    # Variation in phrasing - people describe the same thing many ways
    "has email", "can email", "email available", "text ok", "texting allowed",
    "email works", "texts accepted", "email good", "sms yes", "email valid",
    "text capable", "email functional", "messaging on", "email accessible", "text ready",
    
    # Double-opt-in and verification - strong indicators of consent
    "email verified and confirmed", "text opt-in double confirmed", "email validation complete",
    "sms confirmation received", "email double opt-in", "text subscription verified",
    
    # Frequency and cadence - shows ongoing communication
    "receives weekly emails", "daily text updates", "monthly email newsletter",
    "real-time text alerts", "periodic email communications", "regular sms notifications",
    
    # Context with other channels - shows preference over alternatives
    "prefers email over phone", "text instead of mail", "email rather than call",
    "sms preferred to postal", "email more than fax", "text not phone call"
]

NEGATIVE_EXAMPLES = [
    # These examples show language that indicates someone CANNOT or should NOT be contacted
    "no email preference", "opted out of text", "email declined", "unsubscribed from messages",
    "text not available", "email prohibited", "cannot send sms", "messaging disabled",
    "do not email", "rejected text communications", "email blocked", "text messaging off",
    
    # Opt-out language - these indicate the person explicitly declined
    "unsubscribed from emails", "opted out of texts", "removed from email list",
    "text opt-out confirmed", "email preference removed", "sms unsubscribe",
    "no longer receives emails", "text alerts disabled", "email communications stopped",
    "messaging opt-out", "declined email marketing", "refused text notifications",
    
    # Explicit refusal - clear rejection of contact
    "does not want emails", "refuses text messages", "no email contact",
    "rejects sms notifications", "email not permitted", "text messages unwanted",
    "email contact denied", "messaging not allowed", "no email authorization",
    "text delivery blocked", "email not authorized", "sms not approved",
    
    # Invalid or missing information - technical issues preventing contact
    "email address missing", "no phone number for text", "email invalid",
    "text number unavailable", "email not provided", "mobile number unknown",
    "email bounced permanently", "text undeliverable", "email does not exist",
    "phone disconnected for sms", "email hard bounce", "text number invalid",
    
    # Inactive status - the channel exists but is no longer active
    "email account closed", "text messaging inactive", "email suspended",
    "sms service terminated", "email deactivated", "text capability removed",
    "email no longer monitored", "text line disconnected", "email abandoned",
    "messaging service cancelled", "email unreachable", "text delivery failed",
    
    # Privacy and restriction - user or system blocks
    "email privacy settings block", "text restricted by carrier", "email spam filtered",
    "sms blocked by user", "email suppressed", "text number on dnc list",
    "email blacklisted", "messaging restricted", "email quarantined",
    "text suppression active", "email do not contact", "sms opt-out list",
    
    # Past tense - capability existed before but not anymore
    "previously had email", "used to text", "formerly email subscriber",
    "past text recipient", "email was active", "text messaging was enabled",
    "old email address", "previous mobile number", "expired email contact",
    "outdated text number", "historical email preference", "legacy messaging contact",
    
    # Negative with absolutes - very strong rejection language
    "never email", "never text", "absolutely no email", "definitely no texts",
    "under no circumstances email", "will not accept sms", "refuses all email",
    "blocks all texts", "no email whatsoever", "zero text messages",
    
    # Legal/compliance restrictions - regulatory blocks
    "email restricted by law", "text forbidden by regulation", "email prohibited by policy",
    "sms not compliant", "email violates terms", "text not legal",
    "email against guidelines", "messaging non-compliant", "email restricted account",
    
    # System/technical blocks - infrastructure preventing delivery
    "email filtering all messages", "text gateway blocked", "email server rejects",
    "sms carrier blocking", "email firewall blocking", "text service unavailable",
    "email system down", "messaging platform offline", "email delivery impossible",
    
    # Conditional negatives - limited use cases only
    "email only if emergency", "text not for marketing", "email restricted use only",
    "sms for security only", "email prohibited for promotions", "text limited to alerts",
    
    # Variation in phrasing - different ways to say no
    "no email", "cant email", "email unavailable", "text not ok", "texting not allowed",
    "email doesnt work", "texts rejected", "email bad", "sms no", "email invalid",
    "text not capable", "email nonfunctional", "messaging off", "email inaccessible", "text not ready",
    
    # Ambiguous negatives - unclear status
    "email unknown", "text unclear", "email status pending", "text unconfirmed",
    "email not verified", "text awaiting confirmation"
]

# These words help the model identify positive vs negative contexts
# Think of these as features that help distinguish between "can contact" and "cannot contact"
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
    """
    Neural network for binary classification (yes/no capability prediction)
    
    Architecture explanation:
    - Input layer: Takes in numerical features representing text
    - Hidden layers: Two layers that learn complex patterns in the data
    - Output layer: Produces a probability score between 0 and 1
    
    Think of this like a series of filters that progressively learn to identify
    whether text indicates communication capability or not.
    """
    
    def __init__(self, input_size, hidden_sizes=[32, 16], learning_rate=0.01, dropout_rate=0.2):
        """
        Initialize the network structure
        
        Args:
            input_size: Number of input features (derived from text processing)
            hidden_sizes: Number of neurons in each hidden layer (more = more complex patterns)
            learning_rate: How much to adjust weights during training (smaller = slower but more precise)
            dropout_rate: Percentage of neurons to randomly disable during training (prevents memorization)
        """
        self.layers = []
        self.learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        
        # Create layers with decreasing sizes: input -> 32 -> 16 -> 1
        layer_sizes = [input_size] + hidden_sizes + [1]
        
        # Initialize weights and biases for each layer
        # Weights determine how much each input contributes to the output
        # Biases allow the model to shift its predictions up or down
        for i in range(len(layer_sizes) - 1):
            # Use He initialization - helps the network train faster
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * scale
            b = np.zeros((1, layer_sizes[i+1]))
            self.layers.append({'W': W, 'b': b, 'A': None, 'Z': None})
    
    def relu(self, Z):
        """
        ReLU activation: outputs the input if positive, otherwise outputs 0
        This introduces non-linearity so the network can learn complex patterns
        """
        return np.maximum(0, Z)
    
    def leaky_relu(self, Z, alpha=0.01):
        """
        Leaky ReLU: like ReLU but allows small negative values
        This prevents neurons from "dying" (getting stuck at 0) during training
        """
        return np.where(Z > 0, Z, alpha * Z)
    
    def relu_derivative(self, Z):
        """
        Derivative of ReLU - needed for backpropagation
        Returns 1 where Z is positive, 0 elsewhere
        """
        return (Z > 0).astype(float)
    
    def leaky_relu_derivative(self, Z, alpha=0.01):
        """
        Derivative of Leaky ReLU - needed for backpropagation
        Returns 1 where Z is positive, alpha elsewhere
        """
        return np.where(Z > 0, 1, alpha)
    
    def sigmoid(self, Z):
        """
        Sigmoid activation: squashes any input to a value between 0 and 1
        Used in the output layer to produce probability scores
        """
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def forward(self, X, training=True):
        """
        Forward propagation: pass data through the network to get predictions
        
        This is like passing data through a series of transformations:
        1. Multiply by weights, add bias
        2. Apply activation function (introduces non-linearity)
        3. Repeat for each layer
        4. Final layer outputs probability
        
        Args:
            X: Input data
            training: If True, applies dropout (random neuron disabling)
        
        Returns:
            Predictions (probabilities between 0 and 1)
        """
        A = X
        
        for i, layer in enumerate(self.layers):
            # Linear transformation: Z = W*A + b
            Z = np.dot(A, layer['W']) + layer['b']
            layer['Z'] = Z
            
            # Apply activation function
            if i < len(self.layers) - 1:
                # Hidden layers use Leaky ReLU
                A = self.leaky_relu(Z)
                
                # During training, randomly disable some neurons
                # This forces the network to learn robust patterns instead of memorizing
                if training and self.dropout_rate > 0:
                    dropout_mask = np.random.binomial(1, 1 - self.dropout_rate, size=A.shape)
                    A = A * dropout_mask / (1 - self.dropout_rate)
            else:
                # Output layer uses sigmoid for probability
                A = self.sigmoid(Z)
            
            layer['A'] = A
        
        return A
    
    def backward(self, X, y):
        """
        Backward propagation: calculate how wrong the predictions were and adjust weights
        
        This is the learning step. The network:
        1. Calculates the error (difference between prediction and actual)
        2. Figures out which weights contributed to the error
        3. Adjusts those weights to reduce the error next time
        
        This process uses calculus (chain rule) to propagate errors backward through layers.
        
        Args:
            X: Input data
            y: True labels (what we wanted to predict)
        """
        m = X.shape[0]
        
        # Start with the error at the output layer
        dA = self.layers[-1]['A'] - y
        
        # Work backwards through layers
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            
            # Calculate gradient (how much each weight contributed to error)
            if i < len(self.layers) - 1:
                dZ = dA * self.leaky_relu_derivative(layer['Z'])
            else:
                dZ = dA
            
            # Get the input to this layer
            A_prev = X if i == 0 else self.layers[i-1]['A']
            
            # Calculate weight and bias gradients
            dW = np.dot(A_prev.T, dZ) / m
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            # Clip gradients to prevent exploding gradients
            # (Sometimes gradients can become extremely large and destabilize training)
            dW = np.clip(dW, -5, 5)
            db = np.clip(db, -5, 5)
            
            # Update weights using gradient descent
            # Subtract a small portion of the gradient to move toward lower error
            layer['W'] -= self.learning_rate * dW
            layer['b'] -= self.learning_rate * db
            
            # Calculate gradient for previous layer
            if i > 0:
                dA = np.dot(dZ, layer['W'].T)
    
    def train(self, X, y, epochs=500, batch_size=16, validation_split=0.2):
        """
        Train the neural network on data
        
        Training process:
        1. Split data into training and validation sets
        2. For each epoch (pass through the data):
           - Shuffle the training data
           - Process in small batches (faster and more stable than full dataset)
           - Forward pass: make predictions
           - Backward pass: update weights based on errors
        3. Check validation performance to prevent overfitting
        4. Stop early if validation performance stops improving
        
        Args:
            X: Training features
            y: Training labels
            epochs: Number of times to go through the entire dataset
            batch_size: Number of examples to process at once
            validation_split: Fraction of data to hold out for validation
        """
        # Split data: use most for training, some for validation
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Early stopping variables
        # If validation loss doesn't improve for 50 epochs, stop training
        best_val_loss = float('inf')
        patience = 50
        patience_counter = 0
        
        for epoch in range(epochs):
            # Shuffle training data each epoch
            # This helps the model generalize better
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            # Process data in mini-batches
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                # Make predictions and update weights
                self.forward(X_batch, training=True)
                self.backward(X_batch, y_batch)
            
            # Every 10 epochs, check how well we're doing
            if epoch % 10 == 0:
                # Get predictions on training and validation sets
                train_output = self.forward(X_train, training=False)
                val_output = self.forward(X_val, training=False)
                
                # Calculate loss (how wrong the predictions are)
                # This uses binary cross-entropy, standard for yes/no classification
                train_loss = -np.mean(y_train * np.log(train_output + 1e-8) + 
                                     (1 - y_train) * np.log(1 - train_output + 1e-8))
                val_loss = -np.mean(y_val * np.log(val_output + 1e-8) + 
                                   (1 - y_val) * np.log(1 - val_output + 1e-8))
                
                # Calculate accuracy (percentage correct)
                train_acc = np.mean((train_output > 0.5) == y_train)
                val_acc = np.mean((val_output > 0.5) == y_val)
                
                print(f"Epoch {epoch}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, "
                      f"Train Acc={train_acc:.3f}, Val Acc={val_acc:.3f}")
                
                # Early stopping: if validation loss stops improving, stop training
                # This prevents overfitting (memorizing training data instead of learning patterns)
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch}")
                    break
    
    def predict(self, X):
        """
        Make predictions on new data
        Returns probability scores between 0 and 1
        """
        return self.forward(X, training=False)

def extract_advanced_features(text):
    """
    Extract numerical features from text to help the model understand context
    
    These are hand-crafted features based on domain knowledge about how
    communication preferences are expressed. They complement the TF-IDF features
    by capturing specific patterns we know are important.
    
    Returns a 10-dimensional feature vector where each number represents
    some aspect of the text that indicates capability or non-capability.
    """
    if pd.isna(text) or not text:
        return np.zeros(10)
    
    text_lower = str(text).lower()
    
    features = []
    
    # Feature 1: Count positive words (normalized to 0-1 range)
    # More positive words = more likely to indicate capability
    positive_count = sum(1 for word in CAPABILITY_INDICATORS if word in text_lower)
    features.append(min(positive_count / 5, 1))
    
    # Feature 2: Count negative words (normalized to 0-1 range)
    # More negative words = less likely to indicate capability
    negative_count = sum(1 for word in NON_CAPABILITY_INDICATORS if word in text_lower)
    features.append(min(negative_count / 5, 1))
    
    # Feature 3: Presence of strong positive indicators
    # Words like "yes", "active", "enabled" are strong signals
    strong_positive = ['yes', 'active', 'enabled', 'confirmed', 'verified', 'ok']
    features.append(1 if any(word in text_lower for word in strong_positive) else 0)
    
    # Feature 4: Presence of strong negative indicators
    # Words like "no", "blocked", "unsubscribed" are strong signals
    strong_negative = ['no', 'not', 'never', 'blocked', 'unsubscribed', 'opt-out', 'declined']
    features.append(1 if any(word in text_lower for word in strong_negative) else 0)
    
    # Feature 5: Text length (normalized)
    # Longer text might provide more context
    features.append(min(len(text_lower) / 200, 1))
    
    # Feature 6: Word count (normalized)
    # Number of words can be informative
    features.append(min(len(text_lower.split()) / 20, 1))
    
    # Feature 7: Negation pattern detection
    # Phrases like "not enabled" or "no email" are important to catch
    negation_pattern = any(re.search(rf'\b(no|not|never)\s+{word}', text_lower) 
                          for word in CAPABILITY_INDICATORS[:10])
    features.append(1 if negation_pattern else 0)
    
    # Feature 8: Permission/consent language
    # These words strongly indicate capability
    permission_words = ['consent', 'permission', 'authorized', 'opt-in', 'subscribe']
    features.append(1 if any(word in text_lower for word in permission_words) else 0)
    
    # Feature 9: Ratio of positive to negative words
    # Balance between positive and negative indicators
    if negative_count > 0:
        features.append(positive_count / (positive_count + negative_count))
    else:
        features.append(1 if positive_count > 0 else 0.5)
    
    # Feature 10: Co-occurrence of communication keyword and capability language
    # Finding both together is a strong signal
    has_comm_keyword = any(kw in text_lower for kw in 
                          ['email', 'text', 'sms', 'message', 'mail', 'messaging'])
    has_capability = any(kw in text_lower for kw in CAPABILITY_INDICATORS[:15])
    features.append(1 if (has_comm_keyword and has_capability) else 0)
    
    return np.array(features)

# START OF TRAINING PROCESS
print("="*60)
print("TRAINING ADVANCED NEURAL NETWORK MODEL")
print("="*60)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

print(f"Training examples: {len(POSITIVE_EXAMPLES)} positive, {len(NEGATIVE_EXAMPLES)} negative")

# Step 1: Convert text to numerical features using TF-IDF
# TF-IDF (Term Frequency-Inverse Document Frequency) converts text to numbers by:
# - Counting how often words appear in each sentence
# - Giving less weight to common words that appear everywhere
# - The result is a matrix where each row is a sentence and each column is a word's importance
print("\nStep 1: Converting text to TF-IDF features...")
vectorizer = TfidfVectorizer(
    max_features=100,  # Keep top 100 most important words
    ngram_range=(1, 3),  # Look at single words, pairs, and triplets
    min_df=1,  # Word must appear at least once
    sublinear_tf=True  # Use logarithmic scaling for term frequency
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()

# Step 2: Extract hand-crafted features
# These are features we specifically designed based on domain knowledge
print("Step 2: Extracting hand-crafted features...")
X_features = np.array([extract_advanced_features(text) for text in all_examples])

# Step 3: Combine both feature sets
# Using both TF-IDF and hand-crafted features gives the model more information
print("Step 3: Combining feature sets...")
X_combined = np.hstack([X_tfidf, X_features])

# Step 4: Standardize features
# Standardization makes all features have mean=0 and std=1
# This helps the neural network train faster and more reliably
print("Step 4: Standardizing features...")
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)

print(f"Feature dimensionality: {X_train.shape[1]}")
print(f"TF-IDF features: {X_tfidf.shape[1]}, Hand-crafted features: {X_features.shape[1]}")

# Step 5: Initialize neural network
print("\nStep 5: Initializing neural network architecture...")
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

# Step 6: Train the network
# This is where the model learns patterns from the training examples
print("Step 6: Training neural network...")
nn.train(X_train, labels, epochs=500, batch_size=16, validation_split=0.2)

print("\nModel training complete!\n")

def extract_context(text, keyword, window=150):
    """
    Extract text surrounding a keyword to provide context
    Returns up to 150 characters before and after the keyword
    """
    text_lower = str(text).lower()
    match = re.search(rf'.{{0,{window}}}{re.escape(keyword)}.{{0,{window}}}', text_lower)
    return match.group(0) if match else text_lower[:300]

def predict_capability(text):
    """
    Use the trained neural network to predict if text indicates communication capability
    
    Process:
    1. Convert text to TF-IDF features (same as training)
    2. Extract hand-crafted features (same as training)
    3. Combine and standardize (same as training)
    4. Pass through neural network
    5. Get probability score (0-1, higher = more likely to be a capability)
    
    Returns:
        Float between 0 and 1 representing confidence that this indicates capability
    """
    if pd.isna(text) or not text:
        return 0.0
    
    text_str = str(text).lower()
    
    # Convert to TF-IDF features
    X_tfidf = vectorizer.transform([text_str]).toarray()
    
    # Extract hand-crafted features
    X_features = extract_advanced_features(text_str).reshape(1, -1)
    
    # Combine and standardize
    X_combined = np.hstack([X_tfidf, X_features])
    X = scaler.transform(X_combined)
    
    # Get prediction from neural network
    prediction = nn.predict(X)[0][0]
    
    return float(prediction)

# PROCESS DATASETS
print("="*60)
print("PROCESSING DATASETS")
print("="*60)

results = {}

for dataset_name in input_dataset_names:
    print(f"\nProcessing {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe()
    except:
        print(f"Warning: Could not load {dataset_name}")
        continue
    
    # Handle both uppercase and lowercase column names
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        print(f"Warning: Skipping {dataset_name} - no IDN_EON column")
        continue
    
    # Convert IDN_EON column to string to avoid type comparison issues
    df[idn_col] = df[idn_col].astype(str)
    
    unique_idns = df[idn_col].dropna().unique()
    print(f"Found {len(unique_idns)} unique IDN_EON values")
    
    for idx, IDN_EON in enumerate(unique_idns):
        if idx % 100 == 0 and idx > 0:
            print(f"Processed {idx}/{len(unique_idns)} IDNs...")
        
        # Convert to string for consistent comparison
        IDN_EON_str = str(IDN_EON)
        
        if IDN_EON_str not in results:
            results[IDN_EON_str] = {
                'IDN_EON': IDN_EON_str,
                'data_sources': set(),
                'email_findings': [],
                'text_findings': []
            }
        
        results[IDN_EON_str]['data_sources'].add(dataset_name)
        idn_rows = df[df[idn_col] == IDN_EON]
        
        # Check all columns for this IDN_EON
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            for value in idn_rows[col]:
                if pd.isna(value):
                    continue
                
                value_str = str(value).lower()
                original_value = str(value)  # Keep original for output
                
                # Check for email keywords
                for keyword in EMAIL_KEYWORDS:
                    if keyword in value_str:
                        context = extract_context(value, keyword)
                        confidence = predict_capability(context)
                        
                        # Only flag if confidence > 0.5 (more likely yes than no)
                        if confidence > 0.5:
                            results[IDN_EON_str]['email_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'cell_content': original_value
                            })
                        break
                
                # Check for text keywords
                for keyword in TEXT_KEYWORDS:
                    if keyword in value_str:
                        context = extract_context(value, keyword)
                        confidence = predict_capability(context)
                        
                        if confidence > 0.5:
                            results[IDN_EON_str]['text_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'cell_content': original_value
                            })
                        break
                
                # Check for general e-communication keywords
                for keyword in GENERAL_KEYWORDS:
                    if keyword in value_str:
                        context = extract_context(value, keyword)
                        confidence = predict_capability(context)
                        
                        if confidence > 0.5:
                            # E-communication could indicate both email and text
                            results[IDN_EON_str]['email_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'cell_content': original_value
                            })
                            results[IDN_EON_str]['text_findings'].append({
                                'location': f"{col} [{dataset_name}]",
                                'confidence': confidence,
                                'cell_content': original_value
                            })
                        break

# BUILD OUTPUT DATASET
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
        
        # Get highest confidence for each type
        email_confidence = max([f['confidence'] for f in data['email_findings']], default=0.0)
        text_confidence = max([f['confidence'] for f in data['text_findings']], default=0.0)
        
        # Deduplicate locations but keep cell content
        email_locations = list(set([f['location'] for f in data['email_findings']]))
        text_locations = list(set([f['location'] for f in data['text_findings']]))
        
        # Get cell contents (deduplicated)
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

# FINAL SUMMARY
print("\n" + "="*60)
print("PROCESSING COMPLETE")
print("="*60)
print(f"Total unique IDN_EON processed: {len(results)}")
print(f"IDN_EONs with communication capabilities: {len(output_df)}")
print(f"\nConfidence Distribution:")

# Fix the comparison by converting confidence columns to float
email_conf = pd.to_numeric(output_df['email_confidence'], errors='coerce').fillna(0)
text_conf = pd.to_numeric(output_df['text_confidence'], errors='coerce').fillna(0)

print(f"  High confidence (>0.8): {len(output_df[(email_conf > 0.8) | (text_conf > 0.8)])}")
print(f"  Medium confidence (0.6-0.8): {len(output_df[((email_conf >= 0.6) & (email_conf <= 0.8)) | ((text_conf >= 0.6) & (text_conf <= 0.8))])}")
print(f"  Lower confidence (0.5-0.6): {len(output_df[((email_conf >= 0.5) & (email_conf < 0.6)) | ((text_conf >= 0.5) & (text_conf < 0.6))])}")
print(f"\nOutput written to: {output_dataset.name}")
print("="*60)