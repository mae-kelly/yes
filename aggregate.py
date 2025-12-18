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
# Without this, the neural network would start with different random numbers each run
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Input/output datasets
input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# Training examples - these teach the model what real communication looks like
# We need LOTS of examples because the model learns by seeing patterns
POSITIVE_EXAMPLES = [
    # These show apps that actually SEND/RECEIVE communications
    "app provides ability to send email messages", "users can send text messages through app",
    "platform enables email communication between users", "system allows sending sms notifications",
    "application supports text messaging", "service provides email notification capability",
    "app has email messaging feature", "platform includes text message sending",
    "enables users to communicate via email", "allows customers to send text messages",
    "provides sms communication feature", "supports email-based communication",
    
    # E-communication is a strong indicator - it means electronic communication capability
    "e-communications enabled", "electronic communications supported", "e-communication platform",
    "e-communications feature available", "electronic communication capability", 
    "e-communication channel active", "supports e-communications", "e-communication system",
    
    # Active verbs like "sends" mean the app is doing the communicating
    "app sends email notifications to users", "system delivers text alerts to customers",
    "platform transmits email updates", "service dispatches sms reminders",
    "application pushes email messages", "tool sends text notifications",
    "users receive email alerts from app", "customers get text messages from system",
    "subscribers receive email communications", "users get sms notifications",
    
    # These describe the infrastructure needed to send messages
    "email notification system", "text message delivery system", "sms alert infrastructure",
    "email communication module", "text messaging service", "notification delivery platform",
    "message sending capability", "alert distribution system", "communication engine",
    
    # Opt-in means users agree to RECEIVE communications (not just give their email)
    "users opt-in to receive emails", "customers consent to text notifications",
    "subscribers agree to email communications", "users enable sms alerts",
    "opt-in for email notifications", "subscribe to text message updates",
    "consent to receive promotional emails", "agree to sms marketing messages",
    
    # Two-way communication features
    "users can reply to emails", "customers respond via text message",
    "email conversation feature", "text messaging chat capability",
    "back-and-forth email communication", "interactive text messaging",
    
    # Automated communication features
    "automatically sends email when", "triggers text message upon",
    "email sent automatically after", "sms dispatched when event occurs",
    "automated email notification system", "automatic text alert feature",
    
    # Marketing features mean mass communication capability
    "email marketing campaigns", "text message marketing blasts",
    "promotional email sending", "sms campaign management",
    "bulk email distribution", "mass text messaging capability",
    
    # Transactional communications are functional messages the app sends
    "transactional email delivery", "order confirmation emails sent",
    "shipping notification via text", "payment receipt via email",
    "appointment reminder texts", "verification code via sms",
    
    # Channel selection means choosing HOW to be contacted
    "users choose email as notification method", "customers select text for alerts",
    "email preferred for communications", "sms as primary contact channel",
    "notification delivery via email", "alerts sent through text messaging",
    
    # Settings and controls for communication preferences
    "email notification settings", "text alert preferences configurable",
    "manage communication preferences", "control message delivery options",
    "customize notification channels", "configure alert methods",
    
    # Timing features
    "real-time email alerts", "instant text notifications",
    "scheduled email reports", "periodic sms updates",
    "immediate notification delivery", "timed message sending",
    
    # Metrics mean the app tracks message sending
    "email delivery tracking", "text message open rates",
    "notification engagement metrics", "message delivery confirmation",
    "communication analytics", "alert response tracking",
    
    # Built-in features mean it's part of the app
    "built-in messaging system", "integrated notification platform",
    "native email functionality", "embedded text messaging",
    "in-app communication tools", "communication feature set",
    
    # User-facing language that promises communication
    "users will receive email", "customers get text notifications",
    "app notifies via email", "system alerts through text",
    "you can message via email", "send text messages to users",
    
    # Multi-channel means multiple ways to communicate
    "email and text notification", "sms or email delivery",
    "multiple communication channels", "cross-channel messaging",
    
    # Permission language
    "authorized to send emails", "permission to text customers",
    "approved communication channels", "enabled messaging capabilities"
]

# Negative examples - these are apps that just COLLECT data, they don't send messages
NEGATIVE_EXAMPLES = [
    # Pure data collection - just saving information
    "collect email address", "gather phone number", "capture email information",
    "store email address", "save phone number", "record email data",
    "email address collected", "phone number captured", "email info gathered",
    "collect user email", "gather customer phone", "obtain email address",
    
    # List format is a red flag - it means they're just listing what data they collect
    "email, phone number, address", "email and phone number collected",
    "fields: email, phone, name", "data collected: email, phone",
    "email address, mobile number", "phone, email, date of birth",
    "user provides email, phone", "enter email and phone number",
    "email phone address city", "collects email phone name",
    
    # Registration means creating an account, not sending messages
    "email required for registration", "phone number for account creation",
    "email address in user profile", "phone stored in account",
    "registration requires email", "signup needs phone number",
    "email field in registration form", "phone number field for signup",
    "create account with email", "register using phone number",
    
    # Authentication means logging in, not communicating
    "email used as login", "phone number for authentication",
    "sign in with email", "login via phone number",
    "email as username", "phone for account access",
    "authenticate using email", "verify identity with phone",
    "email credential", "phone-based login",
    
    # Storage language - keeping information on file
    "email address on file", "phone number in database",
    "contact info stored", "email information saved",
    "phone number recorded", "email data maintained",
    "keep email address", "retain phone number",
    
    # Display means showing on screen, not sending messages
    "display email address", "show phone number",
    "email visible in profile", "phone displayed in settings",
    "email appears on screen", "phone shown to user",
    "render email field", "present phone information",
    
    # Validation means checking if format is correct
    "validate email format", "verify phone number format",
    "email syntax check", "phone number validation",
    "email address verification", "phone format check",
    "confirm email structure", "validate phone digits",
    
    # Technical/metadata - backend stuff
    "email metadata", "phone number format",
    "email header information", "phone field data type",
    "email protocol", "phone number schema",
    "email api endpoint", "phone data structure",
    
    # Plaintext is a technical term, not about text messaging
    "plaintext format", "plain text encoding",
    "text field in database", "text data type",
    "text column", "text string variable",
    "text file format", "text-based storage",
    "text encoding utf-8", "text content type",
    
    # Language references - "text" means language, not messaging
    "japanese text", "chinese characters",
    "korean text input", "multilingual text",
    "text in japanese", "chinese text display",
    
    # Search functionality
    "search by email", "filter by phone",
    "email in search results", "find phone number",
    "query email field", "lookup phone",
    
    # Import/export - moving data around
    "export email list", "import phone numbers",
    "email data export", "phone list download",
    "csv of emails", "spreadsheet with phones",
    
    # Logging means recording activity, not communicating
    "log email address", "track phone number",
    "record email entry", "monitor phone usage",
    "email activity log", "phone access tracking",
    
    # Security/privacy - protecting stored data
    "encrypt email data", "secure phone storage",
    "email pii protection", "phone number privacy",
    "email data retention", "phone information security",
    
    # Third-party contact info (not app functionality)
    "contact us at email address", "call phone number",
    "email support at", "phone customer service",
    "support email listed", "help desk phone",
    
    # Data cleanup operations
    "deduplicate emails", "clean phone list",
    "remove invalid emails", "normalize phone format",
    "email data quality", "phone number cleanup",
    
    # Missing data
    "email address missing", "phone number not provided",
    "invalid email", "phone number empty",
    "no email on file", "phone unavailable",
    
    # Historical data
    "old email address", "previous phone number",
    "archived email", "historical phone data",
    "past email information", "former phone contact",
    
    # 2FA is authentication only, not general communication
    "sms for two-factor authentication", "text code for login",
    "sms verification code only", "2fa via text",
    "authentication sms", "security text message",
    "one-time password via sms", "login code by text",
    
    # Profile fields
    "email in user profile", "phone in account details",
    "profile contains email", "account shows phone",
    "user details include email", "contact section has phone",
    
    # Form fields
    "email input field", "phone number textbox",
    "email form element", "phone entry field",
    "email field required", "phone field optional",
    
    # Help text
    "enter your email", "provide phone number",
    "email field help text", "phone number tooltip",
    "email format example", "phone number pattern",
    
    # Data matching operations
    "match records by email", "link accounts via phone",
    "email as unique identifier", "phone as primary key",
    "join on email field", "merge using phone",
    
    # Analytics
    "analyze email patterns", "phone number statistics",
    "email data mining", "phone usage analytics",
    "email distribution report", "phone number frequency"
]

# Balance the dataset - we want equal positive and negative examples
# Otherwise the model might just learn to always predict the more common class
print("="*80)
print("BALANCING TRAINING DATA")
print("="*80)
print(f"Original positive examples: {len(POSITIVE_EXAMPLES)}")
print(f"Original negative examples: {len(NEGATIVE_EXAMPLES)}")

min_samples = min(len(POSITIVE_EXAMPLES), len(NEGATIVE_EXAMPLES))
np.random.shuffle(POSITIVE_EXAMPLES)
np.random.shuffle(NEGATIVE_EXAMPLES)
POSITIVE_EXAMPLES = POSITIVE_EXAMPLES[:min_samples]
NEGATIVE_EXAMPLES = NEGATIVE_EXAMPLES[:min_samples]

print(f"Balanced positive examples: {len(POSITIVE_EXAMPLES)}")
print(f"Balanced negative examples: {len(NEGATIVE_EXAMPLES)}")

# Key phrases that are almost always correct
DEFINITIVE_COMMUNICATION_PHRASES = [
    'provides ability to send email', 'provides ability to send text', 'ability to send sms',
    'allows users to send email', 'allows users to send text', 'enables email sending',
    'e-communications', 'e-communication', 'electronic communications',
    'sends email to users', 'sends text to customers', 'delivers email notifications',
    'email notification system', 'text notification system', 'sms alert system',
    'email campaign', 'text campaign', 'sms campaign',
    'opt-in to receive email', 'opt-in to receive text', 'subscribe to email',
    'via email', 'via text', 'via sms', 'through email', 'through text'
]

DEFINITIVE_DATA_COLLECTION_PHRASES = [
    'collect email', 'collect phone', 'gather email', 'gather phone',
    'email, phone', 'phone, email', 'email and phone',
    'store email', 'store phone', 'save email', 'save phone',
    'email required', 'phone required', 'email for registration', 'phone for signup',
    'email for login', 'phone for authentication', 'email as username',
    'email field', 'phone field', 'email input', 'phone input',
    'plaintext', 'plain text', 'text field', 'text data type', 'text column',
    'japanese text', 'chinese text', 'korean text'
]

class ImprovedNeuralNetwork:
    """
    This is our neural network - think of it as a complex mathematical function
    that learns to distinguish between communication apps and data collection apps.
    
    How it works:
    1. Takes in text as numbers (features)
    2. Passes through multiple layers that transform the data
    3. Each layer learns different patterns (early layers: simple, later layers: complex)
    4. Final output: probability from 0 to 1 (is this communication capability?)
    """
    
    def __init__(self, input_size, hidden_sizes=[64, 48, 32, 16], learning_rate=0.005, 
                 dropout_rate=0.25, l2_lambda=0.001):
        """
        Initialize the network structure
        
        Why these parameters:
        - input_size: how many features we have from text analysis
        - hidden_sizes: [64,48,32,16] means 4 layers that gradually compress information
          (more neurons = can learn more complex patterns)
        - learning_rate: how quickly we adjust weights (too high = unstable, too low = slow)
        - dropout_rate: randomly turn off 25% of neurons during training to prevent memorization
        - l2_lambda: penalty for large weights (prevents overfitting)
        """
        self.layers = []
        self.learning_rate = learning_rate
        self.initial_learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        self.l2_lambda = l2_lambda
        
        # Track performance over time
        self.train_losses = []
        self.val_losses = []
        self.train_accs = []
        self.val_accs = []
        
        # Create the network structure
        layer_sizes = [input_size] + hidden_sizes + [1]
        
        for i in range(len(layer_sizes) - 1):
            # Initialize weights randomly (He initialization helps training start better)
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * scale
            b = np.zeros((1, layer_sizes[i+1]))
            
            # Batch normalization helps stabilize training
            # It normalizes values so they don't get too big or small
            gamma = np.ones((1, layer_sizes[i+1]))
            beta = np.zeros((1, layer_sizes[i+1]))
            
            self.layers.append({
                'W': W,  # Weights - the main learnable parameters
                'b': b,  # Biases - allow shifting the output
                'A': None,  # Will store activations during forward pass
                'Z': None,  # Will store pre-activation values
                'gamma': gamma,  # Batch norm scale
                'beta': beta,  # Batch norm shift
                'bn_mean': None,  # Running mean for batch norm
                'bn_var': None   # Running variance for batch norm
            })
    
    def batch_norm(self, Z, layer, training=True, epsilon=1e-8):
        """
        Batch normalization: standardizes inputs to each layer
        
        Why we need this:
        - Prevents "internal covariate shift" (fancy term for values getting out of whack)
        - Makes training much more stable
        - Allows us to use higher learning rates
        """
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
        """
        Activation function: introduces non-linearity
        
        Why we need this:
        - Without non-linearity, the network would just be a fancy linear equation
        - "Leaky" means it allows small negative values (prevents "dying neurons")
        """
        return np.where(Z > 0, Z, alpha * Z)
    
    def leaky_relu_derivative(self, Z, alpha=0.01):
        """Derivative for backpropagation - tells us how to adjust weights"""
        return np.where(Z > 0, 1, alpha)
    
    def sigmoid(self, Z):
        """
        Sigmoid squashes any number to range 0-1 (perfect for probabilities)
        Only used in the final layer to output a probability
        """
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def forward(self, X, training=True):
        """
        Forward pass: push data through the network to get predictions
        
        Think of it like an assembly line:
        1. Input goes into first layer
        2. Gets transformed by weights
        3. Batch norm stabilizes it
        4. Activation function adds non-linearity
        5. Repeat for each layer
        6. Final layer outputs probability
        """
        A = X
        
        for i, layer in enumerate(self.layers):
            # Linear transformation: multiply by weights, add bias
            Z = np.dot(A, layer['W']) + layer['b']
            
            # Apply batch norm to hidden layers (not output layer)
            if i < len(self.layers) - 1:
                Z = self.batch_norm(Z, layer, training)
            
            layer['Z'] = Z
            
            if i < len(self.layers) - 1:
                # Hidden layers: use leaky ReLU
                A = self.leaky_relu(Z)
                
                # Dropout: randomly turn off neurons to prevent memorization
                if training and self.dropout_rate > 0:
                    dropout_mask = np.random.binomial(1, 1 - self.dropout_rate, size=A.shape)
                    A = A * dropout_mask / (1 - self.dropout_rate)
            else:
                # Output layer: use sigmoid to get probability
                A = self.sigmoid(Z)
            
            layer['A'] = A
        
        return A
    
    def compute_l2_loss(self):
        """
        L2 regularization: penalizes large weights
        
        Why we need this:
        - Large weights mean the model is being too specific to training data
        - This penalty encourages smaller, more general weights
        - Helps prevent overfitting
        """
        l2_loss = 0
        for layer in self.layers:
            l2_loss += np.sum(layer['W'] ** 2)
        return 0.5 * self.l2_lambda * l2_loss
    
    def backward(self, X, y):
        """
        Backpropagation: figure out how to adjust weights to reduce error
        
        How it works:
        1. Calculate error at output (how wrong were we?)
        2. Work backwards through layers
        3. For each layer, calculate gradient (which direction to adjust weights)
        4. Update weights in that direction
        
        This is where the actual "learning" happens
        """
        m = X.shape[0]
        
        # Start with output error
        dA = self.layers[-1]['A'] - y
        
        # Work backwards through each layer
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            
            # Calculate gradient based on activation function
            if i < len(self.layers) - 1:
                dZ = dA * self.leaky_relu_derivative(layer['Z'])
            else:
                dZ = dA
            
            # Get input to this layer
            A_prev = X if i == 0 else self.layers[i-1]['A']
            
            # Calculate how much to adjust weights and biases
            dW = (np.dot(A_prev.T, dZ) / m) + (self.l2_lambda * layer['W'])
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            # Clip gradients to prevent exploding gradients
            # (sometimes gradients can become huge and destabilize training)
            dW = np.clip(dW, -5, 5)
            db = np.clip(db, -5, 5)
            
            # Actually update the weights (this is the learning step)
            layer['W'] -= self.learning_rate * dW
            layer['b'] -= self.learning_rate * db
            
            # Calculate gradient for previous layer
            if i > 0:
                dA = np.dot(dZ, layer['W'].T)
    
    def learning_rate_schedule(self, epoch):
        """
        Gradually reduce learning rate as training progresses
        
        Why we need this:
        - Early in training: big steps to get close to solution
        - Later in training: small steps to fine-tune
        - Like zooming in on a target as you get closer
        """
        # Reduce learning rate by half every 200 epochs
        self.learning_rate = self.initial_learning_rate * (0.5 ** (epoch // 200))
    
    def train(self, X, y, epochs=1000, batch_size=16, validation_split=0.2):
        """
        Train the network on data
        
        Process:
        1. Split data into training (80%) and validation (20%)
        2. For each epoch:
           - Shuffle training data (prevents learning order)
           - Process in small batches (more stable than all at once)
           - Forward pass: make predictions
           - Backward pass: update weights
           - Check validation performance
        3. Stop early if validation stops improving (prevents overfitting)
        """
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        best_val_loss = float('inf')
        best_f1 = 0.0
        patience = 100  # Stop if no improvement for 100 checks
        patience_counter = 0
        
        print("\nTraining Progress:")
        print("-" * 90)
        print(f"{'Epoch':<8} {'Train Loss':<12} {'Val Loss':<12} {'Train Acc':<12} {'Val Acc':<12} {'Val F1':<12}")
        print("-" * 90)
        
        for epoch in range(epochs):
            # Adjust learning rate as we progress
            self.learning_rate_schedule(epoch)
            
            # Shuffle data each epoch
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            # Process in mini-batches
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                # Forward pass + backward pass = one training step
                self.forward(X_batch, training=True)
                self.backward(X_batch, y_batch)
            
            # Check progress every 20 epochs
            if epoch % 20 == 0:
                # Get predictions
                train_output = self.forward(X_train, training=False)
                val_output = self.forward(X_val, training=False)
                
                # Calculate loss (how wrong are we?)
                train_loss = -np.mean(y_train * np.log(train_output + 1e-8) + 
                                     (1 - y_train) * np.log(1 - train_output + 1e-8))
                train_loss += self.compute_l2_loss() / len(X_train)
                
                val_loss = -np.mean(y_val * np.log(val_output + 1e-8) + 
                                   (1 - y_val) * np.log(1 - val_output + 1e-8))
                
                # Calculate accuracy
                train_pred = (train_output > 0.5).astype(int)
                val_pred = (val_output > 0.5).astype(int)
                
                train_acc = np.mean(train_pred == y_train)
                val_acc = np.mean(val_pred == y_val)
                
                # Calculate F1 score (balances precision and recall)
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_val, val_pred, average='binary', zero_division=0
                )
                
                # Store metrics
                self.train_losses.append(train_loss)
                self.val_losses.append(val_loss)
                self.train_accs.append(train_acc)
                self.val_accs.append(val_acc)
                
                print(f"{epoch:<8} {train_loss:<12.4f} {val_loss:<12.4f} {train_acc:<12.3f} "
                      f"{val_acc:<12.3f} {f1:<12.3f}")
                
                # Early stopping: stop if validation F1 stops improving
                if f1 > best_f1:
                    best_val_loss = val_loss
                    best_f1 = f1
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"\nStopping early at epoch {epoch}")
                    print(f"Best validation F1: {best_f1:.3f}")
                    break
        
        print("-" * 90)
        return {'best_val_loss': best_val_loss, 'best_f1': best_f1}
    
    def predict(self, X):
        """Make predictions without dropout (use full network)"""
        return self.forward(X, training=False)

def safe_str(value):
    """Convert any value to string safely - handles None, NaN, weird types"""
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

def extract_semantic_features(text):
    """
    Extract 30 hand-crafted features that capture meaning
    
    Why we need this:
    - TF-IDF gives us word frequencies, but not context
    - These features capture semantic patterns like:
      "Is this describing sending or collecting?"
      "Does it mention capability or storage?"
      "Is email/text in a communication context or data context?"
    
    Think of each feature as answering a specific question about the text
    """
    text_str = safe_str(text)
    if not text_str:
        return np.zeros(30)
    
    text_lower = text_str.lower()
    features = []
    
    # FEATURE 1: Does text contain definitive communication phrases?
    has_def_comm = any(phrase in text_lower for phrase in DEFINITIVE_COMMUNICATION_PHRASES)
    features.append(1 if has_def_comm else 0)
    
    # FEATURE 2: Does text contain definitive data collection phrases?
    has_def_collection = any(phrase in text_lower for phrase in DEFINITIVE_DATA_COLLECTION_PHRASES)
    features.append(1 if has_def_collection else 0)
    
    # FEATURE 3: E-communication mention (very strong signal)
    has_ecomm = any(word in text_lower for word in ['e-communication', 'ecommunication', 'e-communications'])
    features.append(1 if has_ecomm else 0)
    
    # FEATURE 4: Capability language ("provides ability to", "allows users to")
    capability_language = ['provides ability', 'ability to send', 'allows users', 'enables users']
    features.append(1 if any(phrase in text_lower for phrase in capability_language) else 0)
    
    # FEATURE 5: List format detection ("email, phone" is a red flag)
    list_patterns = [r'email\s*,\s*phone', r'phone\s*,\s*email', r'email\s+and\s+phone']
    has_list_format = any(re.search(pattern, text_lower) for pattern in list_patterns)
    features.append(1 if has_list_format else 0)
    
    # FEATURE 6: Active sending verbs
    active_sending = ['send', 'deliver', 'dispatch', 'transmit', 'push']
    features.append(1 if any(verb in text_lower for verb in active_sending) else 0)
    
    # FEATURE 7: Collection verbs (negative signal)
    collection_verbs = ['collect', 'gather', 'capture', 'obtain']
    features.append(1 if any(verb in text_lower for verb in collection_verbs) else 0)
    
    # FEATURE 8: Storage verbs (negative signal)
    storage_verbs = ['store', 'save', 'record', 'log']
    features.append(1 if any(verb in text_lower for verb in storage_verbs) else 0)
    
    # FEATURE 9: Notification context (positive signal)
    notif_context = ['notification', 'alert', 'notify', 'reminder']
    features.append(1 if any(word in text_lower for word in notif_context) else 0)
    
    # FEATURE 10: System capability language
    system_capability = ['system sends', 'platform sends', 'app sends']
    features.append(1 if any(phrase in text_lower for phrase in system_capability) else 0)
    
    # FEATURE 11: Registration context (negative signal)
    registration = ['registration', 'signup', 'sign up', 'create account']
    features.append(1 if any(word in text_lower for word in registration) else 0)
    
    # FEATURE 12: Authentication context (negative signal)
    auth = ['login', 'log in', 'sign in', 'authentication']
    features.append(1 if any(word in text_lower for word in auth) else 0)
    
    # FEATURE 13: Profile/account field context (negative signal)
    profile = ['profile', 'account details', 'user information']
    features.append(1 if any(phrase in text_lower for phrase in profile) else 0)
    
    # FEATURE 14: Form field context (negative signal)
    form_field = ['field', 'input', 'form', 'enter', 'provide']
    features.append(1 if any(word in text_lower for word in form_field) else 0)
    
    # FEATURE 15: Method of delivery ("via email" is positive)
    method_delivery = ['via email', 'via text', 'via sms', 'through email']
    features.append(1 if any(phrase in text_lower for phrase in method_delivery) else 0)
    
    # FEATURE 16: Opt-in language (positive signal)
    opt_in = ['opt-in', 'opt in', 'subscribe', 'consent to receive']
    features.append(1 if any(phrase in text_lower for phrase in opt_in) else 0)
    
    # FEATURE 17: Campaign/marketing (positive signal)
    campaign = ['campaign', 'marketing', 'promotional', 'blast']
    features.append(1 if any(word in text_lower for word in campaign) else 0)
    
    # FEATURE 18: Database context (negative signal)
    database = ['database', 'stored in', 'saved to', 'in table']
    features.append(1 if any(phrase in text_lower for phrase in database) else 0)
    
    # FEATURE 19: Plaintext (negative signal)
    features.append(1 if 'plaintext' in text_lower or 'plain text' in text_lower else 0)
    
    # FEATURE 20: Technical text terms (negative signal)
    technical_text = ['text field', 'text data type', 'text column']
    features.append(1 if any(phrase in text_lower for phrase in technical_text) else 0)
    
    # FEATURE 21: Language context (negative signal)
    language_context = ['japanese text', 'chinese text', 'korean text']
    features.append(1 if any(phrase in text_lower for phrase in language_context) else 0)
    
    # FEATURE 22: User-facing language (positive signal)
    user_facing = ['you will receive', 'you can send', 'users receive']
    features.append(1 if any(phrase in text_lower for phrase in user_facing) else 0)
    
    # FEATURE 23: Two-way communication (positive signal)
    two_way = ['reply', 'respond', 'conversation', 'chat']
    features.append(1 if any(word in text_lower for word in two_way) else 0)
    
    # FEATURE 24: Required field language (negative signal)
    required = ['required', 'mandatory', 'must provide']
    features.append(1 if any(word in text_lower for word in required) else 0)
    
    # FEATURE 25: Display context (negative signal)
    display = ['display', 'show', 'visible', 'appears']
    features.append(1 if any(word in text_lower for word in display) else 0)
    
    # Features 26-29: Placeholder for extensibility
    features.extend([0.5, 0.5, 0.5, 0.5])
    
    # FEATURE 30: Combined semantic score
    score = 0
    if has_def_comm: score += 5
    if has_ecomm: score += 4
    if has_def_collection: score -= 5
    if has_list_format: score -= 4
    features.append(max(0, min(1, (score + 5) / 10)))
    
    return np.array(features)

def perform_cross_validation(X, y, n_folds=5):
    """
    Cross-validation: test the model on different data splits
    
    Why we need this:
    - Single train/test split might be lucky/unlucky
    - Cross-validation tests on multiple splits to get average performance
    - Gives us confidence that the model will work on new data
    
    Process:
    1. Split data into 5 parts
    2. Train on 4 parts, test on 1 part
    3. Repeat 5 times with different test parts
    4. Average the results
    """
    print("\n" + "="*80)
    print("CROSS-VALIDATION (Testing on Multiple Data Splits)")
    print("="*80)
    
    # Stratified K-Fold ensures each fold has same class distribution
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
    
    fold_metrics = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': []
    }
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        print(f"\nFold {fold + 1}/{n_folds}")
        
        X_train_fold, X_val_fold = X[train_idx], X[val_idx]
        y_train_fold, y_val_fold = y[train_idx], y[val_idx]
        
        # Train a model for this fold
        nn_fold = ImprovedNeuralNetwork(
            input_size=X.shape[1],
            hidden_sizes=[64, 48, 32, 16],
            learning_rate=0.005,
            dropout_rate=0.25,
            l2_lambda=0.001
        )
        
        nn_fold.train(X_train_fold, y_train_fold, epochs=500, batch_size=16, validation_split=0.2)
        
        # Evaluate this fold
        y_pred_proba = nn_fold.predict(X_val_fold)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        accuracy = np.mean(y_pred == y_val_fold)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_val_fold, y_pred, average='binary', zero_division=0
        )
        
        fold_metrics['accuracy'].append(accuracy)
        fold_metrics['precision'].append(precision)
        fold_metrics['recall'].append(recall)
        fold_metrics['f1'].append(f1)
        
        print(f"  Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, "
              f"Recall: {recall:.3f}, F1: {f1:.3f}")
    
    # Show average results
    print("\n" + "-"*80)
    print("AVERAGE RESULTS ACROSS ALL FOLDS")
    print("-"*80)
    for metric_name, values in fold_metrics.items():
        mean_val = np.mean(values)
        std_val = np.std(values)
        print(f"{metric_name.capitalize()}: {mean_val:.3f} ± {std_val:.3f}")
    
    return fold_metrics

# START TRAINING
print("="*80)
print("MACHINE LEARNING PIPELINE - COMMUNICATION CAPABILITY DETECTOR")
print("="*80)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

print(f"\nDataset Summary:")
print(f"  Total examples: {len(all_examples)}")
print(f"  Positive (communication): {len(POSITIVE_EXAMPLES)}")
print(f"  Negative (data collection): {len(NEGATIVE_EXAMPLES)}")

# Step 1: Convert text to numbers using TF-IDF
# TF-IDF = Term Frequency-Inverse Document Frequency
# It measures how important a word is to a document
# High score = word appears often here but rarely elsewhere (good discriminator)
print("\nSTEP 1: Converting text to numerical features (TF-IDF)")
print("  Why: Neural networks need numbers, not text")
print("  How: Count word frequencies, adjusted for how common they are overall")

vectorizer = TfidfVectorizer(
    max_features=150,  # Keep only top 150 most informative words
    ngram_range=(1, 5),  # Look at 1-word, 2-word, up to 5-word phrases
    min_df=1,  # Word must appear at least once
    sublinear_tf=True  # Use log scaling for term frequency
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()
print(f"  Result: {X_tfidf.shape[1]} TF-IDF features extracted")

# Step 2: Add semantic features
# These capture patterns that TF-IDF might miss
print("\nSTEP 2: Extracting hand-crafted semantic features")
print("  Why: TF-IDF only looks at word frequency, not meaning")
print("  How: Check for specific patterns like 'provides ability', list format, etc.")

X_features = np.array([extract_semantic_features(text) for text in all_examples])
print(f"  Result: {X_features.shape[1]} semantic features extracted")

# Step 3: Combine and standardize
# Standardization makes all features have mean=0, std=1
# This prevents features with large values from dominating
print("\nSTEP 3: Combining features and standardizing")
print("  Why: Features have different scales (some 0-1, some 0-1000)")
print("  How: Subtract mean, divide by standard deviation for each feature")

X_combined = np.hstack([X_tfidf, X_features])
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)
print(f"  Result: {X_train.shape[1]} total features ready for training")

# Step 4: Cross-validation
# Test on multiple data splits to ensure the model generalizes
print("\nSTEP 4: Cross-validation testing")
cv_metrics = perform_cross_validation(X_train, labels, n_folds=5)

# Step 5: Train final model
print("\n" + "="*80)
print("TRAINING FINAL MODEL")
print("="*80)

nn = ImprovedNeuralNetwork(
    input_size=X_train.shape[1],
    hidden_sizes=[64, 48, 32, 16],
    learning_rate=0.005,
    dropout_rate=0.25,
    l2_lambda=0.001
)

training_results = nn.train(X_train, labels, epochs=1000, batch_size=16, validation_split=0.2)

# Step 6: Final evaluation
print("\n" + "="*80)
print("FINAL MODEL PERFORMANCE")
print("="*80)

y_pred_proba = nn.predict(X_train)
y_pred = (y_pred_proba > 0.5).astype(int)

# Calculate comprehensive metrics
accuracy = np.mean(y_pred == labels)
precision, recall, f1, _ = precision_recall_fscore_support(
    labels, y_pred, average='binary', zero_division=0
)
conf_matrix = confusion_matrix(labels, y_pred)
auc_score = roc_auc_score(labels, y_pred_proba)

print(f"\nMetrics Explained:")
print(f"  Accuracy:  {accuracy:.4f}  (What % we got right overall)")
print(f"  Precision: {precision:.4f}  (When we predict 'communication', how often correct?)")
print(f"  Recall:    {recall:.4f}  (Of all real 'communication', how many did we find?)")
print(f"  F1-Score:  {f1:.4f}  (Harmonic mean of precision and recall)")
print(f"  AUC:       {auc_score:.4f}  (Area under ROC curve, measures overall performance)")

print(f"\nConfusion Matrix:")
print(f"                      Predicted")
print(f"                 Not Comm   Is Comm")
print(f"  Actual Not     {conf_matrix[0,0]:6d}    {conf_matrix[0,1]:6d}  (True Neg, False Pos)")
print(f"  Actual Is      {conf_matrix[1,0]:6d}    {conf_matrix[1,1]:6d}  (False Neg, True Pos)")

print(f"\nDetailed Classification Report:")
print(classification_report(labels, y_pred, target_names=['Data Collection', 'Communication']))

def predict_communication_capability(text):
    """
    Main prediction function - determines if text indicates communication capability
    
    Process:
    1. Check for obvious disqualifiers (plaintext, list format, etc.)
    2. Check for obvious qualifiers (e-communication, capability language)
    3. Run through neural network for nuanced cases
    
    Returns: probability from 0 to 1 (higher = more likely to be communication)
    """
    text_str = safe_str(text)
    if not text_str:
        return 0.0
    
    text_lower = text_str.lower()
    
    # Immediate rejection patterns
    hard_disqualifiers = [
        'email, phone', 'phone, email', 'plaintext', 'text field',
        'japanese text', 'chinese text', 'email stored in database',
        'email for login', 'registration requires email'
    ]
    
    for disqualifier in hard_disqualifiers:
        if disqualifier in text_lower:
            return 0.0
    
    # Immediate acceptance patterns
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
    
    # Standard neural network prediction
    try:
        X_tfidf = vectorizer.transform([text_lower]).toarray()
        X_features = extract_semantic_features(text_str).reshape(1, -1)
        X_combined = np.hstack([X_tfidf, X_features])
        X = scaler.transform(X_combined)
        prediction = nn.predict(X)[0][0]
        return float(prediction)
    except:
        return 0.0

# PROCESS DATASETS
print("\n" + "="*80)
print("APPLYING MODEL TO YOUR DATA")
print("="*80)

results = {}

for dataset_name in input_dataset_names:
    print(f"\nProcessing {dataset_name}...")
    
    try:
        # Load with low_memory=False to avoid dtype warning
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None, infer_with_pandas=False)
    except Exception as e:
        print(f"  Could not load: {e}")
        continue
    
    # Find IDN_EON column (case insensitive)
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        print(f"  No IDN_EON column found, skipping")
        continue
    
    print(f"  Rows: {len(df)}")
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
                
                # Only check cells that mention email or text
                has_email_mention = any(word in value_lower for word in ['email', 'e-mail'])
                has_text_mention = any(word in value_lower for word in ['text', 'sms', 'messaging'])
                
                if has_email_mention or has_text_mention:
                    try:
                        confidence = predict_communication_capability(original_value)
                    except:
                        confidence = 0.0
                    
                    # Only flag if confidence > 0.75 (high threshold for quality)
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
print("COMPLETE")
print("="*80)
print(f"IDN_EONs processed: {len(results)}")
print(f"IDN_EONs with communication capabilities found: {len(output_df)}")
print(f"Model performance - F1: {f1:.3f}, AUC: {auc_score:.3f}")
print(f"Confidence threshold: 0.75 (75% sure before flagging)")
print("="*80)
