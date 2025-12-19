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
# You can expose these as recipe parameters in Dataiku for easy tuning

# CONFIDENCE THRESHOLD: How confident must the model be to flag an IDN_EON?
# Lower = more results but more false positives
# Higher = fewer results but more accurate
# Recommended range: 0.50 (lenient) to 0.80 (strict)
CONFIDENCE_THRESHOLD = 0.65  # Adjust this in Dataiku recipe settings

# MINIMUM FINDINGS: Minimum number of communication mentions needed
# Set to 1 to flag if even one mention found
# Set higher if you want multiple pieces of evidence
MIN_FINDINGS_REQUIRED = 1  # Adjust in Dataiku

# KEYWORD SEARCH MODE: If True, also uses simple keyword matching as backup
# Useful if neural network is too strict
USE_KEYWORD_FALLBACK = True  # Adjust in Dataiku

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

# ============================================================================
# MASSIVE TRAINING DATASET FOR HIGH ACCURACY
# ============================================================================
# The more examples we have, the better the model learns patterns
# We need diverse examples covering every possible way communication is described

POSITIVE_EXAMPLES = [
    # ===== CAPABILITY LANGUAGE =====
    # These explicitly describe the app's ability to send communications
    "app provides ability to send email messages to users",
    "users can send text messages through the app",
    "platform enables email communication between users and staff",
    "system allows sending sms notifications to customers",
    "application supports text messaging capabilities",
    "service provides email notification capability to subscribers",
    "app has email messaging feature built in",
    "platform includes text message sending functionality",
    "enables users to communicate via email with support",
    "allows customers to send text messages to representatives",
    "provides sms communication feature for alerts",
    "supports email-based communication with users",
    "includes ability to send email notifications",
    "features text messaging between users",
    "offers email communication tools",
    "allows sending text alerts to customers",
    "supports sending email messages",
    "enables sms notifications to users",
    "provides email messaging functionality",
    "includes text notification capabilities",
    
    # ===== E-COMMUNICATIONS =====
    # Electronic communications is a strong signal
    "e-communications enabled for all users",
    "electronic communications supported by platform",
    "e-communication platform for customer outreach",
    "e-communications feature available",
    "electronic communication capability active",
    "e-communication channel active for notifications",
    "supports e-communications with customers",
    "e-communication system integrated",
    "electronic communications infrastructure",
    "e-communications module installed",
    "e-communication tools available",
    "electronic communication services enabled",
    
    # ===== ACTIVE SENDING/RECEIVING =====
    # These show the app actively transmits messages
    "app sends email notifications to users automatically",
    "system delivers text alerts to customers in real-time",
    "platform transmits email updates to subscribers",
    "service dispatches sms reminders to users",
    "application pushes email messages to customers",
    "tool sends text notifications when events occur",
    "users receive email alerts from the app",
    "customers get text messages from the system",
    "subscribers receive email communications regularly",
    "users get sms notifications instantly",
    "sends email confirmations to users",
    "delivers text messages to customer phones",
    "transmits email updates automatically",
    "dispatches sms alerts when triggered",
    "pushes email notifications to devices",
    "sends text reminders to users",
    "delivers email messages instantly",
    "transmits sms notifications",
    "dispatches email alerts",
    "pushes text messages to users",
    "application sends emails to users when orders are placed",
    "system delivers text notifications upon status changes",
    "platform sends email updates about account activity",
    "service texts customers when appointments are scheduled",
    "app emails users with important alerts",
    "system messages customers via text",
    "platform notifies users by email",
    "service alerts customers through sms",
    
    # ===== NOTIFICATION SYSTEMS =====
    # Infrastructure that sends notifications
    "email notification system configured and active",
    "text message delivery system operational",
    "sms alert infrastructure in place",
    "email communication module enabled",
    "text messaging service active",
    "notification delivery platform running",
    "message sending capability available",
    "alert distribution system configured",
    "communication engine operational",
    "email notification engine",
    "text alert system",
    "sms notification platform",
    "email delivery infrastructure",
    "text messaging framework",
    "notification distribution system",
    "messaging infrastructure active",
    "alert delivery mechanism",
    "communication delivery system",
    "notification service enabled",
    "messaging platform operational",
    
    # ===== USER CONSENT & OPT-IN =====
    # Users explicitly agree to receive communications
    "users opt-in to receive email notifications",
    "customers consent to text message alerts",
    "subscribers agree to email communications",
    "users enable sms notification alerts",
    "customers subscribe to promotional text messages",
    "users grant permission for email contact",
    "opted in for order status emails",
    "agreed to receive appointment reminder texts",
    "user preferences set to receive email updates",
    "customer chose to get text alerts",
    "subscribed to email notifications",
    "consented to receive sms messages",
    "opted in to text alerts",
    "agreed to email communications",
    "enabled notification emails",
    "subscribed to text messages",
    "opted in to receive communications",
    "granted permission for notifications",
    "subscribed to alert emails",
    "consented to text notifications",
    
    # ===== TWO-WAY COMMUNICATION =====
    # Interactive messaging features
    "users can reply to notification emails",
    "customers respond via text message",
    "email conversation feature with support",
    "text messaging chat capability",
    "back-and-forth email communication",
    "interactive text messaging with staff",
    "reply to emails directly",
    "respond via text",
    "email conversations enabled",
    "text message replies supported",
    "two-way email communication",
    "interactive sms messaging",
    "email dialogue feature",
    "text chat functionality",
    "conversational email",
    "messaging dialogue system",
    
    # ===== TRIGGERED & AUTOMATED =====
    # Communications triggered by events
    "automatically sends email when order is placed",
    "triggers text message upon account creation",
    "email sent automatically after purchase",
    "sms dispatched when event occurs",
    "automated email notification system",
    "automatic text alert feature",
    "triggered email notifications",
    "event-based text alerts",
    "auto-send email messages",
    "automated sms notifications",
    "trigger-based email system",
    "automatic message delivery",
    "event-driven text alerts",
    "auto-triggered emails",
    "system-triggered notifications",
    "automated alert messages",
    
    # ===== MARKETING & CAMPAIGNS =====
    # Mass communication features
    "email marketing campaigns to subscribers",
    "text message marketing blasts sent monthly",
    "promotional email sending capability",
    "sms campaign management tools",
    "bulk email distribution system",
    "mass text messaging capability",
    "email campaign platform",
    "text marketing features",
    "promotional message sending",
    "campaign email tools",
    "marketing text messages",
    "email blast functionality",
    "sms marketing campaigns",
    "promotional email system",
    "marketing message distribution",
    "campaign messaging tools",
    
    # ===== TRANSACTIONAL MESSAGES =====
    # Functional communications
    "transactional email delivery for receipts",
    "order confirmation emails sent automatically",
    "shipping notification delivered via text",
    "invoice emailed to customer",
    "appointment reminder texts sent",
    "password reset email dispatched",
    "verification code sent via sms",
    "payment receipt emailed automatically",
    "order status emails",
    "delivery text notifications",
    "transaction confirmation emails",
    "receipt messages via text",
    "account alert emails",
    "status update texts",
    "confirmation email messages",
    "transaction sms alerts",
    
    # ===== CHANNEL PREFERENCES =====
    # Users choose how to be contacted
    "users choose email as notification method",
    "customers select text for alerts",
    "email preferred for communications",
    "sms as primary contact channel",
    "notification delivery via email",
    "alerts sent through text messaging",
    "contact preference email",
    "text as preferred channel",
    "email notification preference",
    "sms alert preference",
    "choose email delivery",
    "select text notifications",
    
    # ===== SETTINGS & CONTROLS =====
    # Users manage communication preferences
    "email notification settings available",
    "text alert preferences configurable",
    "manage communication preferences in account",
    "control message delivery options",
    "customize notification channels",
    "configure alert methods",
    "notification settings panel",
    "message preference controls",
    "communication settings page",
    "alert configuration options",
    
    # ===== TIMING & SCHEDULING =====
    # When messages are sent
    "real-time email alerts sent immediately",
    "instant text notifications on events",
    "scheduled email reports sent daily",
    "periodic sms updates delivered weekly",
    "immediate notification delivery",
    "timed message sending",
    "scheduled email delivery",
    "instant text alerts",
    "real-time notifications",
    "periodic message sending",
    
    # ===== DELIVERY & TRACKING =====
    # Monitoring message delivery
    "email delivery tracking enabled",
    "text message open rates monitored",
    "notification engagement metrics tracked",
    "message delivery confirmation",
    "communication analytics available",
    "alert response tracking",
    "email delivery status",
    "sms delivery confirmation",
    "message engagement tracking",
    "notification delivery reports",
    
    # ===== BUILT-IN FEATURES =====
    # Native functionality
    "built-in messaging system",
    "integrated notification platform",
    "native email functionality",
    "embedded text messaging",
    "in-app communication tools",
    "communication feature set",
    "messaging capabilities included",
    "notification features built-in",
    "integrated messaging system",
    "native communication tools",
    
    # ===== USER-FACING PROMISES =====
    # What users are told they'll receive
    "users will receive email confirmations",
    "customers get text notifications about orders",
    "app notifies via email when status changes",
    "system alerts through text messages",
    "you can message via email",
    "send text messages to users",
    "receive email updates",
    "get text alerts",
    "email notifications sent",
    "text messages delivered",
    
    # ===== MULTI-CHANNEL =====
    # Multiple communication methods
    "email and text notification options",
    "sms or email delivery available",
    "multiple communication channels supported",
    "cross-channel messaging enabled",
    "omnichannel notifications",
    "multi-channel communication",
    
    # ===== AUTHORIZATION & PERMISSION =====
    # System permissions
    "authorized to send emails to users",
    "permission to text customers granted",
    "approved communication channels",
    "enabled messaging capabilities",
    "licensed to send notifications",
    "approved for email delivery",
    
    # ===== SPECIFIC USE CASES =====
    "sends password reset emails",
    "delivers order confirmation texts",
    "emails shipping notifications",
    "texts appointment reminders",
    "sends account alert emails",
    "delivers verification codes via sms",
    "emails monthly statements",
    "texts delivery updates",
    "sends welcome emails",
    "delivers promotional texts",
    "emails newsletter content",
    "texts special offers",
    "sends billing emails",
    "delivers service alerts via text",
    "emails security notifications",
    "texts payment reminders",
    
    # ===== SYSTEM CAPABILITIES =====
    "system can send email messages",
    "platform has texting capability",
    "app includes email features",
    "service offers sms notifications",
    "tool provides email delivery",
    "system supports text messaging",
    "platform enables email sending",
    "app allows text notifications",
    
    # ===== ENGAGEMENT & INTERACTION =====
    "email click tracking enabled",
    "text message response rates measured",
    "notification engagement analytics",
    "message interaction tracking",
    "communication effectiveness metrics",
    "alert response monitoring",
    
    # ===== COMPLIANCE & OPT-OUT =====
    # Shows communication exists even if users can opt-out
    "users can unsubscribe from emails",
    "opt-out link in every text message",
    "manage email subscription preferences",
    "stop text messages by replying STOP",
    "unsubscribe from notifications",
    "manage message preferences",
    
    # ===== DELIVERY METHODS =====
    "notification via email",
    "alert via text message",
    "message through sms",
    "communication by email",
    "updates sent via text",
    "alerts delivered by email",
    "notifications through messaging",
    "contact via email or text",
    
    # ===== FREQUENCY & CADENCE =====
    "daily email digest delivered",
    "hourly text alerts for monitoring",
    "weekly email summary sent",
    "monthly text bill reminders",
    "regular email updates",
    "periodic text notifications",
    
    # ===== TARGETING & SEGMENTATION =====
    "targeted emails to specific users",
    "segmented text campaigns by location",
    "personalized email based on behavior",
    "custom text messages by preference",
    "tailored email content",
    "audience-specific texts",
    
    # ===== INTEGRATION & CONNECTIVITY =====
    "email integrated with customer database",
    "text notifications sync with calendar",
    "messaging connected to crm",
    "notifications linked to account",
    "email system integrated",
    "text platform connected",
    
    # ===== DELIVERY INFRASTRUCTURE =====
    "smtp email delivery configured",
    "sms gateway connected",
    "email server active",
    "text messaging api integrated",
    "notification service operational",
    "message delivery system running"
]

NEGATIVE_EXAMPLES = [
    # ===== PURE DATA COLLECTION =====
    # Just saving information, not sending anything
    "collect email address from users",
    "gather phone number during registration",
    "capture email information at signup",
    "store email address in database",
    "save phone number to user profile",
    "record email data for account",
    "email address collected during checkout",
    "phone number captured at registration",
    "email info gathered from form",
    "collect user email for account creation",
    "gather customer phone for records",
    "obtain email address from user",
    "collecting email addresses",
    "gathering phone numbers",
    "capturing user emails",
    "storing contact information",
    "saving email data",
    "recording phone numbers",
    "obtaining email addresses",
    "acquiring user emails",
    "compiling email lists",
    "harvesting phone numbers",
    
    # ===== LIST FORMAT (MAJOR RED FLAG) =====
    # Listing data fields means collection, not communication
    "email, phone number, address collected",
    "email and phone number stored",
    "fields: email, phone, name, address",
    "data collected: email, phone, dob",
    "email address, mobile number, zip code",
    "phone, email, date of birth recorded",
    "user provides email, phone, name",
    "enter email and phone number here",
    "email phone address city state",
    "collects email phone name age",
    "fields include email phone",
    "data points: email, phone",
    "information: email, phone, address",
    "required: email, phone number",
    "user data: email, phone",
    "personal info: email, phone",
    
    # ===== REGISTRATION & SIGNUP =====
    # Email as part of account creation
    "email required for registration process",
    "phone number needed for account creation",
    "email address required in user profile",
    "phone stored in user account",
    "registration requires valid email",
    "signup needs phone number",
    "email field in registration form",
    "phone number field for signup",
    "create account with email address",
    "register using phone number",
    "email needed to register",
    "phone required for signup",
    "registration email field",
    "signup phone field",
    "account creation email",
    "profile setup email",
    "new user email requirement",
    "registration form email",
    
    # ===== AUTHENTICATION & LOGIN =====
    # Email/phone as credentials
    "email used as login username",
    "phone number for authentication purposes",
    "sign in with email address",
    "login via phone number",
    "email as username credential",
    "phone for account access",
    "authenticate using email",
    "verify identity with phone",
    "email credential for login",
    "phone-based login system",
    "email authentication",
    "phone verification for access",
    "login email field",
    "signin phone number",
    "email username",
    "phone credential",
    
    # ===== STORAGE & ARCHIVAL =====
    # Keeping data on file
    "email address on file in system",
    "phone number in customer database",
    "contact info stored securely",
    "email information saved in records",
    "phone number recorded in database",
    "email data maintained in system",
    "keep email address on record",
    "retain phone number in profile",
    "email stored in user table",
    "phone saved to database",
    "contact data archived",
    "email record maintained",
    "phone information stored",
    "email data persisted",
    
    # ===== DISPLAY & UI =====
    # Showing information on screen
    "display email address on profile page",
    "show phone number in settings",
    "email visible in user profile",
    "phone displayed in account settings",
    "email appears on dashboard screen",
    "phone shown to administrator",
    "render email field in ui",
    "present phone information to user",
    "email shown in contact section",
    "phone displayed on screen",
    "view email address",
    "see phone number",
    "email visible to user",
    "phone appears in profile",
    
    # ===== VALIDATION & VERIFICATION =====
    # Checking format, not sending
    "validate email format is correct",
    "verify phone number format valid",
    "email syntax check performed",
    "phone number validation rules",
    "email address verification",
    "phone format check",
    "confirm email structure valid",
    "validate phone digits correct",
    "email format validation",
    "phone syntax check",
    "verify email structure",
    "check phone format",
    "email validation rules",
    "phone verification check",
    
    # ===== TECHNICAL METADATA =====
    # Backend technical details
    "email metadata stored in system",
    "phone number format specification",
    "email header information",
    "phone field data type integer",
    "email protocol configuration",
    "phone number schema definition",
    "email api endpoint documentation",
    "phone data structure design",
    "email database column",
    "phone table schema",
    "email field specification",
    "phone number data type",
    
    # ===== PLAINTEXT (HUGE RED FLAG) =====
    # Technical term, not text messaging
    "plaintext format for password",
    "plain text encoding used",
    "data in plaintext format",
    "plaintext file exported",
    "plaintext encoding utf-8",
    "convert to plaintext",
    "plaintext representation",
    "plaintext string in database",
    "save as plaintext document",
    "plaintext content type",
    "plaintext vs html format",
    "plaintext email body stored",
    
    # ===== TEXT AS DATA TYPE =====
    # Technical "text" field
    "text field in database schema",
    "text data type for comments",
    "text column for user notes",
    "text area for feedback",
    "text input box on form",
    "text string variable type",
    "text format for output",
    "text representation of data",
    "text encoding utf-8",
    "text content stored",
    "text length validation",
    "text field max length",
    
    # ===== LANGUAGE CONTEXT =====
    # "text" means language
    "japanese text displayed in app",
    "chinese characters rendered as text",
    "korean text input supported",
    "text in japanese language",
    "japanese plaintext format",
    "chinese text rendering engine",
    "multilingual text support",
    "japanese character encoding",
    "text translation to japanese",
    "japanese text processing",
    "chinese text display",
    "korean text characters",
    
    # ===== LOGGING & MONITORING =====
    # Recording activity, not communicating
    "log email activity in system",
    "email events logged for audit",
    "track email usage in system",
    "record email interactions",
    "monitor email access patterns",
    "audit email activity log",
    "email logs maintained",
    "log email attempts",
    "email logging enabled",
    "track email changes",
    "record email updates",
    "monitor email usage",
    
    # ===== ANALYSIS & REPORTING =====
    # Analyzing data
    "analyze email patterns in data",
    "email data analytics dashboard",
    "report on email metrics",
    "email statistics calculated",
    "aggregate email data",
    "email data mining project",
    "email trends analyzed",
    "email reporting dashboard",
    "analyze email distribution",
    "email metrics report",
    
    # ===== SEARCH & FILTERING =====
    # Finding records
    "search by email address field",
    "filter users by email domain",
    "email in search results",
    "find email in database records",
    "query email field in table",
    "email lookup feature",
    "search email records",
    "email search functionality",
    "find by email",
    "filter by phone",
    "search email column",
    "query phone field",
    
    # ===== THIRD-PARTY CONTACT =====
    # Not app functionality
    "contact us via email at support@company.com",
    "email us at info@business.com",
    "reach support by emailing help@domain.com",
    "send inquiries to contact@company.com",
    "support email address listed",
    "customer service email on website",
    "contact email displayed",
    "support email shown",
    
    # ===== IMPORT/EXPORT =====
    # Data transfer
    "export email list to csv file",
    "import email addresses from file",
    "email data exported to excel",
    "download email records as file",
    "email import feature available",
    "export phone numbers",
    "import contact data",
    "download email list",
    
    # ===== DATA CLEANUP =====
    # Data quality operations
    "deduplicate email addresses in system",
    "clean email data for quality",
    "remove invalid emails from list",
    "email data quality check",
    "normalize email format",
    "cleanse phone numbers",
    "standardize email format",
    "validate email list",
    
    # ===== MATCHING & LINKING =====
    # Data operations
    "match email across multiple systems",
    "compare email addresses for duplicates",
    "email as join key in query",
    "link records by email field",
    "email used for record matching",
    "match by phone number",
    "join on email field",
    "link via email",
    
    # ===== ERROR STATES =====
    # Invalid data
    "email address invalid format",
    "email format incorrect",
    "email validation failed",
    "email syntax error",
    "invalid email structure",
    "phone number invalid",
    "email error",
    "invalid phone format",
    
    # ===== MISSING DATA =====
    # Empty fields
    "email address not provided by user",
    "email field empty in form",
    "no email on file for user",
    "email missing from record",
    "email data unavailable",
    "phone not provided",
    "email field blank",
    "missing email address",
    
    # ===== HISTORICAL DATA =====
    # Old records
    "old email address on record",
    "previous email in system",
    "archived email data",
    "historical email information",
    "past email addresses stored",
    "legacy email in database",
    "former email address",
    "outdated phone number",
    
    # ===== PRIVACY & SECURITY (STORAGE FOCUS) =====
    # Protecting stored data
    "email encrypted at rest in database",
    "email data anonymized for privacy",
    "email pii protected by encryption",
    "email redacted for privacy compliance",
    "secure email storage implemented",
    "email data retention policy",
    "phone data encrypted",
    "email security measures",
    
    # ===== SMS FOR 2FA ONLY =====
    # Authentication only, not general communication
    "sms one-time password for login only",
    "2fa via sms code for authentication",
    "sms for account verification only",
    "authentication sms not for marketing",
    "security sms for login verification",
    "sms used solely for 2fa purposes",
    "verification code via sms",
    "two-factor sms code",
    
    # ===== PHONE NUMBER STORAGE =====
    # Keeping phone info
    "phone number stored in user profile",
    "mobile number saved to account",
    "phone field in database schema",
    "telephone number recorded",
    "phone contact information on file",
    "mobile number for reference",
    "phone data stored",
    "phone number saved",
    
    # ===== EMAIL AS IDENTIFIER =====
    # Using email as unique key
    "email as primary key in database",
    "email uniqueness constraint enforced",
    "email index in database table",
    "email as unique identifier field",
    "email for record matching purposes",
    "email unique constraint",
    "email primary key",
    
    # ===== BOUNCED/FAILED (NO ACTIVE COMMUNICATION) =====
    "email address bounced permanently",
    "email delivery failed permanently",
    "email does not exist anymore",
    "email hard bounce recorded",
    "invalid email destination",
    "email rejected by server",
    "email bounce status",
    "failed email delivery",
    
    # ===== CONFIGURATION (NOT ACTIVE USE) =====
    "email settings available to configure",
    "email preferences page exists",
    "email options in settings menu",
    "email setup instructions provided",
    "email configuration panel",
    "email settings page",
    
    # ===== COPY/DUPLICATE OPERATIONS =====
    "copy email address to clipboard",
    "duplicate email field in form",
    "clone email data to new record",
    "replicate email information",
    "copy phone number",
    "duplicate email entry",
    
    # ===== TEXT FILES =====
    "text file uploaded by user",
    "text document saved to system",
    "text-based file format",
    "save as text file",
    "text document export feature",
    "text file download option",
    "text format file",
    
    # ===== ERROR MESSAGES & LOGS =====
    "error text displayed to user",
    "log text message in file",
    "debug text output shown",
    "system text warning displayed",
    "error message text field",
    
    # ===== TEMPLATES =====
    "template text for future emails",
    "placeholder email text shown",
    "sample text content displayed",
    "draft text for message",
    "text template saved",
    
    # ===== PROGRAMMING CONTEXT =====
    "text parsing algorithm implemented",
    "text manipulation function",
    "regex text matching pattern",
    "text tokenization process",
    "text preprocessing steps",
    "text extraction method",
    "natural language text processing",
    "text mining technique used",
    "text classification model",
    
    # ===== DOCUMENTATION =====
    "help text displayed to user",
    "tooltip text shown on hover",
    "instruction text provided",
    "description text field",
    "placeholder text in input field",
    "label text for form element",
    
    # ===== PROFILE/ACCOUNT CONTEXT =====
    "email in user profile section",
    "phone in account details page",
    "profile contains email field",
    "account shows phone number",
    "user details include email",
    "contact section has phone",
    
    # ===== FORM ELEMENTS =====
    "email input field on form",
    "phone number textbox element",
    "email form element",
    "phone entry field",
    "email field required",
    "phone field optional",
    
    # ===== HELP TEXT =====
    "enter your email address here",
    "provide valid phone number",
    "email field help text",
    "phone number tooltip text",
    "email format example shown",
    "phone number pattern displayed",
    
    # ===== OPT-OUT STATUS (NO ACTIVE COMMUNICATION) =====
    "user opted out of all communications",
    "email completely disabled by user",
    "unsubscribed from everything",
    "no communication permission granted",
    "email contact prohibited",
    "opted out permanently",
    
    # ===== COMPARISON OPERATIONS =====
    "compare email addresses for match",
    "check if emails are identical",
    "verify email equivalence",
    "compare phone numbers",
    "check email similarity"
]

# Balance dataset to prevent bias
min_samples = min(len(POSITIVE_EXAMPLES), len(NEGATIVE_EXAMPLES))
np.random.shuffle(POSITIVE_EXAMPLES)
np.random.shuffle(NEGATIVE_EXAMPLES)
POSITIVE_EXAMPLES = POSITIVE_EXAMPLES[:min_samples]
NEGATIVE_EXAMPLES = NEGATIVE_EXAMPLES[:min_samples]

print(f"\nTraining with {len(POSITIVE_EXAMPLES)} positive and {len(NEGATIVE_EXAMPLES)} negative examples")

# ============================================================================
# COMPREHENSIVE KEYWORD LISTS FOR PATTERN MATCHING
# ============================================================================

# Very strong signals that almost always indicate communication
DEFINITIVE_COMMUNICATION_KEYWORDS = [
    'e-communications', 'e-communication', 'electronic communications', 'ecommunications',
    'provides ability to send email', 'provides ability to send text',
    'allows users to send email', 'allows users to send text',
    'enables users to send email', 'enables users to send text',
    'email notification system', 'text notification system', 'sms alert system',
    'email campaign', 'text campaign', 'sms campaign',
    'sends email to users', 'sends text to customers', 'sends sms to users',
    'delivers email notifications', 'delivers text alerts',
    'email messaging platform', 'text messaging service',
    'opted in to receive email', 'opted in to receive text',
    'subscribed to receive email', 'subscribed to receive sms',
    'user receives email', 'user receives text', 'customer gets email', 'customer gets sms'
]

# Very strong signals that almost always indicate data collection
DEFINITIVE_COLLECTION_KEYWORDS = [
    'email, phone', 'phone, email', 'email and phone number collected',
    'plaintext', 'plain text format',
    'text field in database', 'text data type', 'text column',
    'japanese text', 'chinese text', 'korean text',
    'email stored in database', 'phone stored in database',
    'email for login', 'email as username', 'login email',
    'email for registration', 'registration email', 'signup email',
    'collect email', 'collect phone', 'gather email', 'gather phone',
    'store email', 'save email', 'record email',
    'email field', 'phone field', 'email input', 'phone input'
]

class DeepNeuralNetwork:
    """
    Advanced neural network with multiple layers for high accuracy
    
    Architecture: 5 hidden layers with batch normalization and dropout
    This deep architecture allows the model to learn complex patterns
    """
    
    def __init__(self, input_size, hidden_sizes=[128, 96, 64, 48, 32], learning_rate=0.003, 
                 dropout_rate=0.3, l2_lambda=0.002):
        """
        Initialize network with deeper architecture for better learning
        
        Parameters:
        - input_size: Number of input features
        - hidden_sizes: [128, 96, 64, 48, 32] - 5 hidden layers
        - learning_rate: 0.003 - slower learning for more accuracy
        - dropout_rate: 0.3 - higher dropout to prevent overfitting
        - l2_lambda: 0.002 - regularization to keep weights small
        """
        self.layers = []
        self.learning_rate = learning_rate
        self.initial_learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        self.l2_lambda = l2_lambda
        
        # Track metrics during training
        self.train_losses = []
        self.val_losses = []
        self.train_accs = []
        self.val_accs = []
        
        layer_sizes = [input_size] + hidden_sizes + [1]
        
        # Initialize all layers with proper weight initialization
        for i in range(len(layer_sizes) - 1):
            # He initialization for better gradient flow
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * scale
            b = np.zeros((1, layer_sizes[i+1]))
            
            # Batch normalization parameters
            gamma = np.ones((1, layer_sizes[i+1]))
            beta = np.zeros((1, layer_sizes[i+1]))
            
            self.layers.append({
                'W': W,  # Weights
                'b': b,  # Biases
                'A': None,  # Activations
                'Z': None,  # Pre-activation values
                'gamma': gamma,  # BN scale
                'beta': beta,  # BN shift
                'bn_mean': None,  # Running mean for BN
                'bn_var': None   # Running variance for BN
            })
    
    def batch_norm(self, Z, layer, training=True, epsilon=1e-8):
        """
        Batch normalization: normalizes inputs to each layer
        Helps with training stability and allows higher learning rates
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
        Leaky ReLU activation: allows small negative values
        Better than regular ReLU because it prevents "dead neurons"
        """
        return np.where(Z > 0, Z, alpha * Z)
    
    def leaky_relu_derivative(self, Z, alpha=0.01):
        """Derivative for backpropagation"""
        return np.where(Z > 0, 1, alpha)
    
    def sigmoid(self, Z):
        """
        Sigmoid activation for output layer
        Squashes output to range [0, 1] for probability
        """
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def forward(self, X, training=True):
        """
        Forward pass through all layers
        Each layer transforms the data to learn patterns
        """
        A = X
        
        for i, layer in enumerate(self.layers):
            # Linear transformation
            Z = np.dot(A, layer['W']) + layer['b']
            
            # Apply batch normalization to hidden layers
            if i < len(self.layers) - 1:
                Z = self.batch_norm(Z, layer, training)
            
            layer['Z'] = Z
            
            if i < len(self.layers) - 1:
                # Hidden layers: use Leaky ReLU
                A = self.leaky_relu(Z)
                
                # Apply dropout during training
                if training and self.dropout_rate > 0:
                    dropout_mask = np.random.binomial(1, 1 - self.dropout_rate, size=A.shape)
                    A = A * dropout_mask / (1 - self.dropout_rate)
            else:
                # Output layer: use sigmoid for probability
                A = self.sigmoid(Z)
            
            layer['A'] = A
        
        return A
    
    def compute_l2_loss(self):
        """
        L2 regularization: penalizes large weights
        Helps prevent overfitting by encouraging simpler models
        """
        l2_loss = 0
        for layer in self.layers:
            l2_loss += np.sum(layer['W'] ** 2)
        return 0.5 * self.l2_lambda * l2_loss
    
    def backward(self, X, y):
        """
        Backpropagation: compute gradients and update weights
        This is where the learning happens
        """
        m = X.shape[0]
        dA = self.layers[-1]['A'] - y
        
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            
            if i < len(self.layers) - 1:
                dZ = dA * self.leaky_relu_derivative(layer['Z'])
            else:
                dZ = dA
            
            A_prev = X if i == 0 else self.layers[i-1]['A']
            
            # Compute gradients with L2 regularization
            dW = (np.dot(A_prev.T, dZ) / m) + (self.l2_lambda * layer['W'])
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            # Gradient clipping to prevent exploding gradients
            dW = np.clip(dW, -5, 5)
            db = np.clip(db, -5, 5)
            
            # Update weights and biases
            layer['W'] -= self.learning_rate * dW
            layer['b'] -= self.learning_rate * db
            
            if i > 0:
                dA = np.dot(dZ, layer['W'].T)
    
    def learning_rate_schedule(self, epoch):
        """
        Gradually reduce learning rate as training progresses
        Helps fine-tune the model in later epochs
        """
        self.learning_rate = self.initial_learning_rate * (0.5 ** (epoch // 300))
    
    def train(self, X, y, epochs=1500, batch_size=16, validation_split=0.2):
        """
        Train the network with mini-batch gradient descent
        
        Parameters:
        - epochs: 1500 - more training for better accuracy
        - batch_size: 16 - small batches for more frequent updates
        - validation_split: 0.2 - 20% held out for validation
        """
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        best_f1 = 0.0
        patience = 150  # Stop if no improvement for 150 checks
        patience_counter = 0
        
        print("\nTraining Progress (every 25 epochs):")
        print("-" * 95)
        print(f"{'Epoch':<8} {'Train Loss':<12} {'Val Loss':<12} {'Train Acc':<12} {'Val Acc':<12} {'Val F1':<12}")
        print("-" * 95)
        
        for epoch in range(epochs):
            # Update learning rate
            self.learning_rate_schedule(epoch)
            
            # Shuffle training data
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            # Mini-batch training
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                self.forward(X_batch, training=True)
                self.backward(X_batch, y_batch)
            
            # Evaluate every 25 epochs
            if epoch % 25 == 0:
                train_output = self.forward(X_train, training=False)
                val_output = self.forward(X_val, training=False)
                
                # Compute loss with regularization
                train_loss = -np.mean(y_train * np.log(train_output + 1e-8) + 
                                     (1 - y_train) * np.log(1 - train_output + 1e-8))
                train_loss += self.compute_l2_loss() / len(X_train)
                
                val_loss = -np.mean(y_val * np.log(val_output + 1e-8) + 
                                   (1 - y_val) * np.log(1 - val_output + 1e-8))
                
                # Compute accuracy
                train_pred = (train_output > 0.5).astype(int)
                val_pred = (val_output > 0.5).astype(int)
                
                train_acc = np.mean(train_pred == y_train)
                val_acc = np.mean(val_pred == y_val)
                
                # Compute F1 score
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_val, val_pred, average='binary', zero_division=0
                )
                
                self.train_losses.append(train_loss)
                self.val_losses.append(val_loss)
                self.train_accs.append(train_acc)
                self.val_accs.append(val_acc)
                
                print(f"{epoch:<8} {train_loss:<12.4f} {val_loss:<12.4f} {train_acc:<12.3f} "
                      f"{val_acc:<12.3f} {f1:<12.3f}")
                
                # Early stopping based on F1 score
                if f1 > best_f1:
                    best_f1 = f1
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"\nEarly stopping at epoch {epoch} (no improvement for {patience} checks)")
                    print(f"Best validation F1 score: {best_f1:.4f}")
                    break
        
        print("-" * 95)
        return {'best_f1': best_f1, 'final_epoch': epoch}
    
    def predict(self, X):
        """Make predictions without dropout"""
        return self.forward(X, training=False)

def safe_str(value):
    """Safely convert any value to string, handling None/NaN"""
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

def extract_comprehensive_features(text):
    """
    Extract 50 hand-crafted semantic features
    More features = more patterns the model can learn
    """
    text_str = safe_str(text)
    if not text_str:
        return np.zeros(50)
    
    text_lower = text_str.lower()
    features = []
    
    # FEATURE 1-2: Definitive keyword presence
    has_def_comm = any(phrase in text_lower for phrase in DEFINITIVE_COMMUNICATION_KEYWORDS)
    features.append(1 if has_def_comm else 0)
    
    has_def_collection = any(phrase in text_lower for phrase in DEFINITIVE_COLLECTION_KEYWORDS)
    features.append(1 if has_def_collection else 0)
    
    # FEATURE 3: E-communication mentions
    features.append(1 if 'e-communication' in text_lower or 'ecommunication' in text_lower else 0)
    
    # FEATURE 4-5: Capability language
    capability_verbs = ['provides ability', 'allows users', 'enables users', 'supports sending']
    features.append(1 if any(phrase in text_lower for phrase in capability_verbs) else 0)
    
    can_send = ['can send', 'able to send', 'capability to send']
    features.append(1 if any(phrase in text_lower for phrase in can_send) else 0)
    
    # FEATURE 6: List format detection (major negative signal)
    list_patterns = [r'email\s*,\s*phone', r'phone\s*,\s*email', r'email\s+and\s+phone']
    features.append(1 if any(re.search(p, text_lower) for p in list_patterns) else 0)
    
    # FEATURE 7-10: Action verbs
    send_verbs = ['send', 'deliver', 'dispatch', 'transmit', 'push', 'forward']
    features.append(min(sum(1 for v in send_verbs if v in text_lower) / 3, 1))
    
    receive_verbs = ['receive', 'get', 'obtain', 'retrieve']
    features.append(1 if any(v in text_lower for v in receive_verbs) else 0)
    
    collection_verbs = ['collect', 'gather', 'capture', 'obtain', 'acquire']
    features.append(1 if any(v in text_lower for v in collection_verbs) else 0)
    
    storage_verbs = ['store', 'save', 'record', 'log', 'retain', 'keep']
    features.append(1 if any(v in text_lower for v in storage_verbs) else 0)
    
    # FEATURE 11-15: Context nouns
    notif_nouns = ['notification', 'alert', 'reminder', 'update', 'message']
    features.append(min(sum(1 for n in notif_nouns if n in text_lower) / 2, 1))
    
    system_nouns = ['system', 'platform', 'app', 'application', 'service', 'tool']
    features.append(1 if any(n in text_lower for n in system_nouns) else 0)
    
    campaign_nouns = ['campaign', 'marketing', 'promotional', 'blast', 'distribution']
    features.append(1 if any(n in text_lower for n in campaign_nouns) else 0)
    
    database_nouns = ['database', 'table', 'field', 'column', 'record', 'storage']
    features.append(1 if any(n in text_lower for n in database_nouns) else 0)
    
    profile_nouns = ['profile', 'account', 'registration', 'signup', 'login']
    features.append(1 if any(n in text_lower for n in profile_nouns) else 0)
    
    # FEATURE 16-20: Specific patterns
    features.append(1 if 'notification system' in text_lower or 'alert system' in text_lower else 0)
    features.append(1 if 'opt-in' in text_lower or 'subscribe' in text_lower else 0)
    features.append(1 if 'via email' in text_lower or 'via text' in text_lower or 'via sms' in text_lower else 0)
    features.append(1 if 'plaintext' in text_lower or 'plain text' in text_lower else 0)
    features.append(1 if 'text field' in text_lower or 'text data type' in text_lower else 0)
    
    # FEATURE 21-25: Language and technical context
    features.append(1 if 'japanese' in text_lower or 'chinese' in text_lower or 'korean' in text_lower else 0)
    features.append(1 if 'for login' in text_lower or 'for registration' in text_lower else 0)
    features.append(1 if 'as username' in text_lower or 'as identifier' in text_lower else 0)
    features.append(1 if 'stored in' in text_lower or 'saved to' in text_lower else 0)
    features.append(1 if 'required' in text_lower or 'mandatory' in text_lower else 0)
    
    # FEATURE 26-30: Communication indicators
    features.append(1 if 'sends to' in text_lower or 'delivered to' in text_lower else 0)
    features.append(1 if 'users receive' in text_lower or 'customers get' in text_lower else 0)
    features.append(1 if 'messaging' in text_lower or 'communication' in text_lower else 0)
    features.append(1 if 'transactional' in text_lower else 0)
    features.append(1 if 'confirmation' in text_lower or 'receipt' in text_lower else 0)
    
    # FEATURE 31-35: Two-way communication
    features.append(1 if 'reply' in text_lower or 'respond' in text_lower else 0)
    features.append(1 if 'conversation' in text_lower or 'dialogue' in text_lower else 0)
    features.append(1 if 'interactive' in text_lower else 0)
    features.append(1 if 'chat' in text_lower else 0)
    features.append(1 if 'back-and-forth' in text_lower or 'two-way' in text_lower else 0)
    
    # FEATURE 36-40: Display and UI context
    features.append(1 if 'display' in text_lower or 'show' in text_lower else 0)
    features.append(1 if 'visible' in text_lower or 'appears' in text_lower else 0)
    features.append(1 if 'input' in text_lower or 'form' in text_lower else 0)
    features.append(1 if 'enter' in text_lower or 'provide' in text_lower else 0)
    features.append(1 if 'field' in text_lower and 'email' in text_lower else 0)
    
    # FEATURE 41-45: Validation and verification
    features.append(1 if 'validate' in text_lower or 'verify' in text_lower else 0)
    features.append(1 if 'format check' in text_lower or 'syntax' in text_lower else 0)
    features.append(1 if 'invalid' in text_lower or 'error' in text_lower else 0)
    features.append(1 if 'missing' in text_lower or 'empty' in text_lower else 0)
    features.append(1 if 'bounced' in text_lower or 'failed' in text_lower else 0)
    
    # FEATURE 46-50: Advanced semantic scoring
    # Ratio of positive to negative indicators
    positive_count = sum([
        1 for word in ['send', 'deliver', 'notify', 'alert', 'receive', 'message', 'campaign']
        if word in text_lower
    ])
    negative_count = sum([
        1 for word in ['collect', 'store', 'save', 'field', 'database', 'login', 'registration']
        if word in text_lower
    ])
    
    if positive_count + negative_count > 0:
        ratio = positive_count / (positive_count + negative_count)
        features.append(ratio)
    else:
        features.append(0.5)
    
    # System-user interaction pattern
    features.append(1 if 'system sends' in text_lower or 'app sends' in text_lower else 0)
    features.append(1 if 'user receives' in text_lower or 'customer gets' in text_lower else 0)
    features.append(1 if 'you will receive' in text_lower or "you'll get" in text_lower else 0)
    
    # Overall semantic score
    score = 0
    if has_def_comm: score += 5
    if 'e-communication' in text_lower: score += 4
    if any(phrase in text_lower for phrase in capability_verbs): score += 3
    if has_def_collection: score -= 5
    if any(re.search(p, text_lower) for p in list_patterns): score -= 4
    if 'plaintext' in text_lower: score -= 3
    
    features.append(max(0, min(1, (score + 5) / 10)))
    
    return np.array(features)

# ============================================================================
# TRAIN THE MODEL
# ============================================================================
print("\n" + "="*80)
print("TRAINING ADVANCED NEURAL NETWORK")
print("="*80)

all_examples = POSITIVE_EXAMPLES + NEGATIVE_EXAMPLES
labels = np.array([1] * len(POSITIVE_EXAMPLES) + [0] * len(NEGATIVE_EXAMPLES)).reshape(-1, 1)

print(f"\nDataset: {len(POSITIVE_EXAMPLES)} positive + {len(NEGATIVE_EXAMPLES)} negative = {len(all_examples)} total")

# Step 1: TF-IDF vectorization
print("\nStep 1: TF-IDF feature extraction...")
print("  Converting text to numerical features based on word importance")
vectorizer = TfidfVectorizer(
    max_features=200,  # More features for better accuracy
    ngram_range=(1, 5),  # Capture 1-5 word phrases
    min_df=1,
    sublinear_tf=True
)
X_tfidf = vectorizer.fit_transform(all_examples).toarray()
print(f"  Generated {X_tfidf.shape[1]} TF-IDF features")

# Step 2: Extract hand-crafted features
print("\nStep 2: Extracting hand-crafted semantic features...")
print("  Creating 50 features that capture meaning and context")
X_features = np.array([extract_comprehensive_features(text) for text in all_examples])
print(f"  Generated {X_features.shape[1]} semantic features")

# Step 3: Combine and standardize
print("\nStep 3: Combining and standardizing features...")
X_combined = np.hstack([X_tfidf, X_features])
scaler = StandardScaler()
X_train = scaler.fit_transform(X_combined)
print(f"  Total features: {X_train.shape[1]}")

# Step 4: Train deep neural network
print("\nStep 4: Training deep neural network...")
print("  Architecture: 5 hidden layers [128, 96, 64, 48, 32]")
print("  This may take a few minutes...")

nn = DeepNeuralNetwork(
    input_size=X_train.shape[1],
    hidden_sizes=[128, 96, 64, 48, 32],  # Deep architecture
    learning_rate=0.003,
    dropout_rate=0.3,
    l2_lambda=0.002
)

training_results = nn.train(X_train, labels, epochs=1500, batch_size=16, validation_split=0.2)

# Evaluate final model
print("\n" + "="*80)
print("FINAL MODEL EVALUATION")
print("="*80)

y_pred_proba = nn.predict(X_train)
y_pred = (y_pred_proba > 0.5).astype(int)

accuracy = np.mean(y_pred == labels)
precision, recall, f1, _ = precision_recall_fscore_support(labels, y_pred, average='binary', zero_division=0)
conf_matrix = confusion_matrix(labels, y_pred)

print(f"\nPerformance Metrics:")
print(f"  Accuracy:  {accuracy:.4f}")
print(f"  Precision: {precision:.4f} (when we predict communication, how often are we right?)")
print(f"  Recall:    {recall:.4f} (of all actual communications, how many did we find?)")
print(f"  F1-Score:  {f1:.4f} (harmonic mean of precision and recall)")

print(f"\nConfusion Matrix:")
print(f"                Predicted")
print(f"              Not    Is")
print(f"  Actual Not  {conf_matrix[0,0]:4d}  {conf_matrix[0,1]:4d}")
print(f"  Actual Is   {conf_matrix[1,0]:4d}  {conf_matrix[1,1]:4d}")

def predict_communication_capability(text):
    """
    Predict if text indicates communication capability
    Uses both neural network and keyword matching
    """
    text_str = safe_str(text)
    if not text_str:
        return 0.0
    
    text_lower = text_str.lower()
    
    # Immediate disqualifiers
    for keyword in DEFINITIVE_COLLECTION_KEYWORDS:
        if keyword in text_lower:
            return 0.0
    
    # Immediate high confidence qualifiers
    for keyword in DEFINITIVE_COMMUNICATION_KEYWORDS:
        if keyword in text_lower:
            return 0.95
    
    # Neural network prediction
    try:
        X_tfidf = vectorizer.transform([text_lower]).toarray()
        X_features = extract_comprehensive_features(text_str).reshape(1, -1)
        X_combined = np.hstack([X_tfidf, X_features])
        X = scaler.transform(X_combined)
        prediction = nn.predict(X)[0][0]
        return float(prediction)
    except:
        return 0.0

# ============================================================================
# STEP 1: COUNT ALL UNIQUE IDN_EON (DON'T WRITE TO TABLE YET)
# ============================================================================
print("\n" + "="*80)
print("STEP 1: SCANNING ALL TABLES FOR UNIQUE IDN_EON")
print("="*80)
print("This step counts every unique IDN_EON across all tables")
print("No filtering is applied - we want the complete count")

all_unique_idn_eons = set()

for dataset_name in input_dataset_names:
    print(f"\nScanning {dataset_name}...")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None)
        # Convert all columns to string to avoid type issues
        for col in df.columns:
            df[col] = df[col].astype(str)
    except Exception as e:
        print(f"  Error loading table: {e}")
        continue
    
    idn_col = None
    for col in df.columns:
        if col.upper() == 'IDN_EON':
            idn_col = col
            break
    
    if idn_col is None:
        print(f"  ⚠ No IDN_EON column found")
        continue
    
    unique_in_table = df[idn_col].unique()
    valid_idns = set()
    for idn in unique_in_table:
        idn_str = safe_str(idn)
        if idn_str and idn_str not in ['nan', 'None', '', 'NaN', 'NONE']:
            valid_idns.add(idn_str)
    
    print(f"  ✓ Found {len(valid_idns):,} unique IDN_EON in this table")
    all_unique_idn_eons.update(valid_idns)

print(f"\n{'='*80}")
print(f"TOTAL UNIQUE IDN_EON ACROSS ALL TABLES: {len(all_unique_idn_eons):,}")
print(f"{'='*80}")
print(f"Now analyzing these {len(all_unique_idn_eons):,} IDN_EON for communication capabilities...")

# ============================================================================
# STEP 2: ANALYZE EACH IDN_EON FOR COMMUNICATION CAPABILITY
# ============================================================================
print("\n" + "="*80)
print("STEP 2: ANALYZING COMMUNICATION CAPABILITIES")
print("="*80)
print(f"Using confidence threshold: {CONFIDENCE_THRESHOLD}")
print(f"Using minimum findings: {MIN_FINDINGS_REQUIRED}")

communication_findings = {}
processed = 0
total_cells_checked = 0

for dataset_name in input_dataset_names:
    print(f"\nAnalyzing {dataset_name}...")
    
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
        continue
    
    unique_idns = df[idn_col].unique()
    
    for IDN_EON in unique_idns:
        IDN_EON_str = safe_str(IDN_EON)
        if not IDN_EON_str or IDN_EON_str in ['nan', 'None', '', 'NaN', 'NONE']:
            continue
        
        processed += 1
        if processed % 1000 == 0:
            print(f"  Progress: {processed:,}/{len(all_unique_idn_eons):,} IDN_EON analyzed ({processed/len(all_unique_idn_eons)*100:.1f}%)")
        
        if IDN_EON_str not in communication_findings:
            communication_findings[IDN_EON_str] = {
                'IDN_EON': IDN_EON_str,
                'sources': set(),
                'email_findings': [],
                'text_findings': []
            }
        
        communication_findings[IDN_EON_str]['sources'].add(dataset_name)
        idn_rows = df[df[idn_col] == IDN_EON_str]
        
        # Check every column for this IDN_EON
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            for value in idn_rows[col]:
                val_str = safe_str(value)
                if not val_str or val_str in ['nan', 'None', 'NaN', 'NONE']:
                    continue
                
                total_cells_checked += 1
                
                val_lower = val_str.lower()
                has_email = any(w in val_lower for w in ['email', 'e-mail', 'mail'])
                has_text = any(w in val_lower for w in ['text', 'sms', 'messaging'])
                
                if has_email or has_text:
                    confidence = predict_communication_capability(val_str)
                    
                    # Apply configurable threshold
                    if confidence > CONFIDENCE_THRESHOLD:
                        finding = {
                            'location': f"{col} [{dataset_name}]",
                            'confidence': confidence,
                            'content': val_str[:200]  # Limit content length for output
                        }
                        
                        if has_email:
                            communication_findings[IDN_EON_str]['email_findings'].append(finding)
                        if has_text and 'plaintext' not in val_lower and 'plain text' not in val_lower:
                            communication_findings[IDN_EON_str]['text_findings'].append(finding)

print(f"\n✓ Analysis complete!")
print(f"  Total cells checked: {total_cells_checked:,}")
print(f"  IDN_EON analyzed: {processed:,}")

# ============================================================================
# STEP 3: FILTER TO ONLY IDN_EON WITH COMMUNICATION, SORT BY CONFIDENCE
# ============================================================================
print("\n" + "="*80)
print("STEP 3: BUILDING OUTPUT TABLE")
print("="*80)
print("Filtering to IDN_EON with communication capabilities...")
print("Sorting by confidence (highest first)...")

output_data = []

for IDN_EON, data in communication_findings.items():
    has_email = len(data['email_findings']) >= MIN_FINDINGS_REQUIRED
    has_text = len(data['text_findings']) >= MIN_FINDINGS_REQUIRED
    
    # Only include if communication capability found
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
        
        # Limit to top 3 examples to keep output manageable
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

# Sort by max confidence (highest to lowest) - most confident results first
output_df = pd.DataFrame(output_data).sort_values('max_confidence', ascending=False).reset_index(drop=True)

# Drop the helper column before writing
output_df = output_df.drop('max_confidence', axis=1)

# Write to Dataiku output
print(f"Writing {len(output_df):,} IDN_EON with communication capabilities to output table...")
output_dataset.write_with_schema(output_df)

# ============================================================================
# FINAL STATISTICS
# ============================================================================
print("\n" + "="*80)
print("FINAL RESULTS SUMMARY")
print("="*80)

print(f"\nData Scanned:")
print(f"  Total unique IDN_EON in all tables: {len(all_unique_idn_eons):,}")
print(f"  Total cells analyzed: {total_cells_checked:,}")

print(f"\nCommunication Capabilities Found:")
print(f"  IDN_EON with communication: {len(output_df):,}")
print(f"  Percentage with communication: {len(output_df)/len(all_unique_idn_eons)*100:.2f}%")

email_count = len([r for r in output_data if 'Email' in r['communication_type']])
text_count = len([r for r in output_data if 'Text' in r['communication_type']])
both_count = len([r for r in output_data if 'Email' in r['communication_type'] and 'Text' in r['communication_type']])

print(f"\nBreakdown:")
print(f"  Email capability only: {email_count - both_count:,}")
print(f"  Text capability only: {text_count - both_count:,}")
print(f"  Both email AND text: {both_count:,}")

print(f"\nModel Performance:")
print(f"  Training F1 score: {f1:.4f}")
print(f"  Precision: {precision:.4f}")
print(f"  Recall: {recall:.4f}")

print(f"\nConfiguration Used:")
print(f"  Confidence threshold: {CONFIDENCE_THRESHOLD}")
print(f"  Minimum findings required: {MIN_FINDINGS_REQUIRED}")
print(f"  Keyword fallback enabled: {USE_KEYWORD_FALLBACK}")

print("\n" + "="*80)
print("TUNING RECOMMENDATIONS")
print("="*80)
print("To adjust accuracy in Dataiku, modify these variables at the top:")
print("")
print("  CONFIDENCE_THRESHOLD:")
print(f"    Current: {CONFIDENCE_THRESHOLD}")
print("    Increase (e.g., 0.70-0.80) for FEWER but MORE ACCURATE results")
print("    Decrease (e.g., 0.50-0.60) for MORE results but LESS STRICT")
print("")
print("  MIN_FINDINGS_REQUIRED:")
print(f"    Current: {MIN_FINDINGS_REQUIRED}")
print("    Increase (e.g., 2-3) to require MULTIPLE pieces of evidence")
print("    Keep at 1 to flag ANY communication capability found")
print("")
print("Results are sorted by confidence - review top rows first for highest quality!")
print("="*80)
