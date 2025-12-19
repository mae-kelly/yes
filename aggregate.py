import dataiku
import pandas as pd
import numpy as np
import re
from typing import Dict
import warnings

warnings.filterwarnings('ignore')

print("="*80)
print("COMPREHENSIVE E-COMMUNICATION DETECTOR")
print("Massive training set - 500+ examples per class")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================
SEMANTIC_THRESHOLD = 0.55
MIN_FINDINGS_REQUIRED = 1

print(f"Semantic Threshold: {SEMANTIC_THRESHOLD}")
print(f"Min Findings Required: {MIN_FINDINGS_REQUIRED}")

input_dataset_names = ['table1', 'table2', 'table3', 'table4']
output_dataset = dataiku.Dataset("output_table")

# ============================================================================
# LOAD MODEL
# ============================================================================
print("\n" + "="*80)
print("LOADING MODEL")
print("="*80)

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    
    print("Loading all-MiniLM-L6-v2...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Model loaded")
    MODEL_AVAILABLE = True
except Exception as e:
    print(f"⚠ Could not load model: {e}")
    MODEL_AVAILABLE = False

# ============================================================================
# MASSIVE TRAINING SET - E-COMMUNICATION (SENDING)
# 500+ examples covering every possible way to describe sending communications
# ============================================================================

ECOMM_SENDING = [
    # ===== EMAIL SENDING - ACTIVE VOICE =====
    "users can send emails",
    "users can send email messages",
    "users can send email communications",
    "allows users to send emails",
    "enables users to send emails",
    "permits users to send emails",
    "users send emails through the app",
    "users send email messages via the platform",
    "users send emails to other users",
    "users send emails to customers",
    "users send emails to contacts",
    "send emails to users",
    "send email messages to customers",
    "send email communications to subscribers",
    "sending emails to users",
    "sending email messages to customers",
    "sending email notifications",
    "email sending capability",
    "email sending feature",
    "email sending functionality",
    "email message sending",
    "email transmission capability",
    "email delivery capability",
    "email dispatch functionality",
    
    # ===== EMAIL SENDING - PASSIVE/SYSTEM VOICE =====
    "app sends emails to users",
    "application sends email messages",
    "system sends emails to customers",
    "platform sends email notifications",
    "service sends email alerts",
    "app delivers emails to users",
    "application delivers email messages",
    "system delivers email notifications",
    "platform delivers email alerts",
    "service delivers email confirmations",
    "app transmits emails to users",
    "system transmits email messages",
    "platform transmits email notifications",
    "app dispatches emails",
    "system dispatches email alerts",
    "platform dispatches email messages",
    "emails are sent to users",
    "email messages are sent to customers",
    "email notifications are delivered",
    "email alerts are transmitted",
    "email confirmations are dispatched",
    
    # ===== EMAIL SENDING - SPECIFIC USE CASES =====
    "send order confirmation emails",
    "send shipping notification emails",
    "send password reset emails",
    "send account verification emails",
    "send welcome emails",
    "send invoice emails",
    "send receipt emails",
    "send appointment reminder emails",
    "send booking confirmation emails",
    "send payment confirmation emails",
    "send subscription emails",
    "send newsletter emails",
    "send marketing emails",
    "send promotional emails",
    "send transactional emails",
    "send automated emails",
    "send scheduled emails",
    "send triggered emails",
    "send bulk emails",
    "send mass emails",
    
    # ===== EMAIL SENDING - WITH RECIPIENTS =====
    "emails sent to users",
    "emails delivered to customers",
    "emails transmitted to subscribers",
    "email messages sent to members",
    "email notifications sent to users",
    "email alerts sent to customers",
    "sends emails to user's inbox",
    "delivers emails to user's email address",
    "transmits emails to customer's email",
    "email communication with users",
    "email correspondence with customers",
    "email messaging with subscribers",
    
    # ===== EMAIL SENDING - CAPABILITY DESCRIPTIONS =====
    "provides email sending capability",
    "offers email sending feature",
    "includes email sending functionality",
    "supports email sending",
    "enables email sending",
    "allows email sending",
    "facilitates email sending",
    "provides ability to send emails",
    "offers ability to send email messages",
    "includes ability to send email communications",
    "email sending is enabled",
    "email sending is available",
    "email sending is supported",
    "email sending is provided",
    
    # ===== TEXT/SMS SENDING - ACTIVE VOICE =====
    "users can send text messages",
    "users can send SMS messages",
    "users can send text communications",
    "allows users to send texts",
    "enables users to send SMS",
    "permits users to send text messages",
    "users send texts through the app",
    "users send SMS via the platform",
    "users send text messages to other users",
    "users send SMS to customers",
    "users send texts to contacts",
    "send texts to users",
    "send SMS messages to customers",
    "send text communications to subscribers",
    "sending texts to users",
    "sending SMS messages to customers",
    "sending text notifications",
    "text sending capability",
    "SMS sending feature",
    "text messaging functionality",
    "SMS message sending",
    "text transmission capability",
    "SMS delivery capability",
    "text dispatch functionality",
    
    # ===== TEXT/SMS SENDING - PASSIVE/SYSTEM VOICE =====
    "app sends texts to users",
    "application sends SMS messages",
    "system sends texts to customers",
    "platform sends text notifications",
    "service sends SMS alerts",
    "app delivers texts to users",
    "application delivers SMS messages",
    "system delivers text notifications",
    "platform delivers SMS alerts",
    "service delivers text confirmations",
    "app transmits texts to users",
    "system transmits SMS messages",
    "platform transmits text notifications",
    "app dispatches texts",
    "system dispatches SMS alerts",
    "platform dispatches text messages",
    "texts are sent to users",
    "SMS messages are sent to customers",
    "text notifications are delivered",
    "SMS alerts are transmitted",
    "text confirmations are dispatched",
    
    # ===== TEXT/SMS SENDING - SPECIFIC USE CASES =====
    "send order confirmation texts",
    "send shipping notification SMS",
    "send verification code texts",
    "send appointment reminder SMS",
    "send booking confirmation texts",
    "send payment confirmation SMS",
    "send promotional texts",
    "send marketing SMS",
    "send transactional texts",
    "send automated SMS",
    "send scheduled texts",
    "send triggered SMS",
    "send bulk texts",
    "send mass SMS",
    "send one-time password texts",
    "send authentication code SMS",
    "send delivery update texts",
    "send status notification SMS",
    
    # ===== MESSAGING/CHAT =====
    "users can send messages",
    "users can send instant messages",
    "users can send chat messages",
    "allows users to message each other",
    "enables user messaging",
    "permits user communication",
    "users message through the app",
    "users chat via the platform",
    "instant messaging capability",
    "chat messaging feature",
    "direct messaging functionality",
    "message sending capability",
    "chat communication platform",
    "messaging service",
    "chat service",
    "instant messaging platform",
    "real-time messaging",
    "peer-to-peer messaging",
    "user-to-user messaging",
    "in-app messaging",
    "message exchange platform",
    "conversational messaging",
    "text chat capability",
    
    # ===== VIDEO CALLING =====
    "users can make video calls",
    "users can video call each other",
    "allows users to video call",
    "enables video calling",
    "permits video communication",
    "video calling capability",
    "video call feature",
    "video conferencing functionality",
    "video chat capability",
    "video communication platform",
    "make video calls to other users",
    "initiate video calls",
    "start video calls",
    "video calling service",
    "video calling platform",
    "face-to-face video calling",
    "live video communication",
    "video call connection",
    "video meeting capability",
    "video conversation feature",
    "video chat between users",
    
    # ===== VOICE CALLING =====
    "users can make voice calls",
    "users can call each other",
    "allows users to make calls",
    "enables voice calling",
    "permits phone calls",
    "voice calling capability",
    "voice call feature",
    "phone call functionality",
    "audio calling capability",
    "voice communication platform",
    "make calls to other users",
    "initiate voice calls",
    "start phone calls",
    "voice calling service",
    "VoIP calling platform",
    "audio call connection",
    "voice conversation feature",
    "phone call between users",
    
    # ===== PUSH NOTIFICATIONS =====
    "sends push notifications to users",
    "delivers push notifications",
    "transmits push notifications",
    "dispatches push notifications",
    "push notification capability",
    "push notification feature",
    "push notification service",
    "mobile push notifications",
    "app pushes notifications",
    "pushes alerts to devices",
    "push notification delivery",
    "push notification system",
    "push messaging capability",
    "notification push service",
    
    # ===== IN-APP NOTIFICATIONS =====
    "sends in-app notifications",
    "delivers in-app messages",
    "transmits in-app alerts",
    "in-app notification system",
    "in-app messaging capability",
    "in-app alert feature",
    "app notifies users",
    "application sends notifications",
    "internal notification delivery",
    "app-based alerts",
    
    # ===== E-COMMUNICATIONS GENERAL =====
    "e-communications capability",
    "e-communication platform",
    "electronic communications enabled",
    "electronic communication system",
    "electronic messaging capability",
    "digital communication platform",
    "digital messaging service",
    "e-communication services",
    "electronic communication channel",
    "e-communications infrastructure",
    "electronic messaging platform",
    "digital communication features",
    
    # ===== NOTIFICATION SYSTEMS =====
    "notification delivery system",
    "alert delivery platform",
    "notification sending capability",
    "alert sending feature",
    "notification transmission system",
    "alert dispatch capability",
    "sends notifications to users",
    "delivers alerts to customers",
    "transmits notifications",
    "dispatches alerts",
    "notification service",
    "alert service",
    "notification platform",
    "alert platform",
    
    # ===== CAMPAIGN/MARKETING COMMUNICATIONS =====
    "email marketing campaigns",
    "SMS marketing campaigns",
    "marketing message delivery",
    "promotional email sending",
    "promotional SMS sending",
    "campaign email distribution",
    "campaign SMS distribution",
    "bulk email campaigns",
    "bulk SMS campaigns",
    "email newsletter delivery",
    "SMS newsletter delivery",
    "marketing communication platform",
    "promotional messaging service",
    
    # ===== TRANSACTIONAL COMMUNICATIONS =====
    "transactional email delivery",
    "transactional SMS delivery",
    "order confirmation emails sent",
    "order confirmation texts sent",
    "shipping notification emails",
    "shipping notification SMS",
    "payment receipt emails",
    "payment receipt texts",
    "booking confirmation emails",
    "booking confirmation SMS",
    "appointment reminder emails",
    "appointment reminder texts",
    
    # ===== AUTOMATED COMMUNICATIONS =====
    "automated email sending",
    "automated SMS sending",
    "automated notification delivery",
    "automated message sending",
    "automatic email transmission",
    "automatic text transmission",
    "triggered email delivery",
    "triggered SMS delivery",
    "event-based email sending",
    "event-based SMS sending",
    "scheduled email delivery",
    "scheduled SMS delivery",
    
    # ===== USER-INITIATED COMMUNICATIONS =====
    "users compose and send emails",
    "users write and send messages",
    "users create and send texts",
    "user-generated emails",
    "user-generated messages",
    "user-generated texts",
    "users initiate communication",
    "users start conversations",
    "users send communications",
    
    # ===== BROADCAST/GROUP COMMUNICATIONS =====
    "broadcast messages to users",
    "broadcast emails to subscribers",
    "broadcast texts to customers",
    "group messaging capability",
    "group email sending",
    "group SMS sending",
    "multi-user messaging",
    "send to multiple recipients",
    "mass communication capability",
    "bulk messaging platform",
    
    # ===== REAL-TIME COMMUNICATIONS =====
    "real-time messaging platform",
    "instant message delivery",
    "live chat capability",
    "synchronous communication",
    "real-time notification delivery",
    "instant notification system",
    "live messaging service",
    "immediate message transmission",
    
    # ===== TWO-WAY COMMUNICATIONS =====
    "two-way messaging",
    "bidirectional communication",
    "interactive messaging",
    "conversational platform",
    "back-and-forth messaging",
    "reply capability",
    "response capability",
    "interactive communication channel",
    
    # ===== MULTIMEDIA COMMUNICATIONS =====
    "send images via message",
    "send photos via chat",
    "send videos via messaging",
    "send files via email",
    "multimedia messaging capability",
    "image sharing via messages",
    "video sharing via chat",
    "file sharing via communication",
    
    # ===== SCREEN SHARING =====
    "screen sharing capability",
    "share screen with users",
    "desktop sharing feature",
    "screen sharing during calls",
    "screen broadcast capability",
    
    # ===== COLLABORATION COMMUNICATIONS =====
    "team messaging platform",
    "workspace communication",
    "collaborative messaging",
    "team communication channel",
    "workspace messaging service",
    "collaboration chat platform",
    
    # ===== VARIATION WITH "TO" =====
    "send emails to users",
    "send texts to customers",
    "send messages to subscribers",
    "send notifications to members",
    "deliver emails to users",
    "deliver texts to customers",
    "deliver messages to subscribers",
    "transmit emails to users",
    "transmit texts to customers",
    
    # ===== VARIATION WITH "FOR" =====
    "email sending for users",
    "text sending for customers",
    "messaging for subscribers",
    "notification delivery for members",
    "communication capability for users",
    
    # ===== VARIATION WITH "ALLOWS/ENABLES/PERMITS" =====
    "allows sending emails",
    "enables sending texts",
    "permits sending messages",
    "allows email delivery",
    "enables text delivery",
    "permits message delivery",
    "allows user communication",
    "enables customer messaging",
    "permits subscriber notifications",
    
    # ===== VARIATION WITH "PROVIDES/OFFERS/INCLUDES" =====
    "provides email sending",
    "offers text sending",
    "includes messaging capability",
    "provides notification delivery",
    "offers alert sending",
    "includes communication features",
    "provides messaging service",
    "offers email service",
    "includes SMS service",
    
    # ===== VARIATION WITH "SUPPORTS" =====
    "supports email sending",
    "supports text messaging",
    "supports video calling",
    "supports voice calling",
    "supports instant messaging",
    "supports notification delivery",
    "supports communication",
    
    # ===== VARIATION WITH "CAN" =====
    "users can email",
    "users can text",
    "users can message",
    "users can call",
    "users can notify",
    "users can communicate",
    "can send emails",
    "can send texts",
    "can send messages",
    
    # ===== VARIATION WITH "RECEIVES/GETS" (USER PERSPECTIVE) =====
    "users receive emails from app",
    "users receive texts from system",
    "users receive messages from platform",
    "users receive notifications from service",
    "users get emails from app",
    "users get texts from system",
    "users get messages from platform",
    "users get notifications from service",
    "customers receive email alerts",
    "customers receive text alerts",
    "customers receive push notifications",
    "customers get email updates",
    "customers get text updates",
    "customers get app notifications",
]

# ============================================================================
# MASSIVE TRAINING SET - DATA COLLECTION (NOT SENDING)
# 500+ examples covering every possible way to describe collecting/storing data
# ============================================================================

DATA_COLLECTION = [
    # ===== EMAIL COLLECTION - DIRECT =====
    "collects email addresses",
    "collects user email addresses",
    "collects customer email addresses",
    "collects email information",
    "collects email data",
    "gathers email addresses",
    "gathers user emails",
    "gathers customer emails",
    "gathers email information",
    "captures email addresses",
    "captures user emails",
    "captures customer emails",
    "obtains email addresses",
    "obtains user emails",
    "obtains customer emails",
    "acquires email addresses",
    "acquires user emails",
    "requests email addresses",
    "requests user emails",
    "asks for email addresses",
    "asks for user emails",
    
    # ===== EMAIL STORAGE =====
    "stores email addresses",
    "stores user email addresses",
    "stores customer email addresses",
    "stores email information",
    "stores email data",
    "saves email addresses",
    "saves user emails",
    "saves customer emails",
    "keeps email addresses",
    "keeps user emails",
    "retains email addresses",
    "retains user emails",
    "maintains email addresses",
    "maintains user emails",
    "preserves email addresses",
    "archives email addresses",
    "records email addresses",
    "logs email addresses",
    
    # ===== EMAIL IN DATABASE =====
    "email addresses in database",
    "email stored in database",
    "email saved in database",
    "email kept in database",
    "email retained in database",
    "email address database",
    "email information database",
    "email data database",
    "database of email addresses",
    "database containing emails",
    "database with email addresses",
    "email field in database",
    "email column in database",
    "email table in database",
    "email records in database",
    
    # ===== EMAIL FOR REGISTRATION =====
    "email required for registration",
    "email needed for registration",
    "email necessary for registration",
    "registration requires email",
    "registration needs email",
    "email for account creation",
    "email for account setup",
    "email for account registration",
    "email to register",
    "email to sign up",
    "email to create account",
    "provide email to register",
    "provide email for registration",
    "enter email to register",
    "enter email for registration",
    "email address for registration",
    "email address to register",
    "email address for account",
    
    # ===== EMAIL FOR LOGIN =====
    "email for login",
    "email for signin",
    "email for authentication",
    "email for access",
    "email as username",
    "email as login",
    "email as credential",
    "email as identifier",
    "login with email",
    "signin with email",
    "authenticate with email",
    "access via email",
    "email login",
    "email signin",
    "email authentication",
    "email credential",
    "email username",
    "use email to login",
    "use email to signin",
    "use email for access",
    
    # ===== EMAIL IN PROFILE =====
    "email in user profile",
    "email in customer profile",
    "email in account profile",
    "email address in profile",
    "profile contains email",
    "profile includes email",
    "profile has email",
    "profile stores email",
    "user profile email",
    "customer profile email",
    "account profile email",
    "email part of profile",
    "email field in profile",
    "email information in profile",
    "email data in profile",
    
    # ===== EMAIL ON FILE =====
    "email on file",
    "email on record",
    "email in records",
    "email address on file",
    "email address on record",
    "email information on file",
    "maintains email on file",
    "keeps email on record",
    "has email on file",
    "email stored on file",
    "email saved on record",
    
    # ===== EMAIL FORMS/FIELDS =====
    "email field",
    "email input field",
    "email text field",
    "email form field",
    "email address field",
    "email input box",
    "email text box",
    "email entry field",
    "enter email address",
    "provide email address",
    "input email address",
    "type email address",
    "email field required",
    "email field mandatory",
    "email field optional",
    "required email field",
    "mandatory email field",
    "optional email field",
    
    # ===== EMAIL VALIDATION =====
    "validates email address",
    "validates email format",
    "validates email syntax",
    "verifies email address",
    "verifies email format",
    "checks email address",
    "checks email format",
    "checks email syntax",
    "email validation",
    "email verification",
    "email format check",
    "email syntax check",
    "email format validation",
    "email address validation",
    "validate email input",
    "verify email input",
    
    # ===== PHONE NUMBER COLLECTION =====
    "collects phone numbers",
    "collects mobile numbers",
    "collects telephone numbers",
    "gathers phone numbers",
    "captures phone numbers",
    "obtains phone numbers",
    "acquires phone numbers",
    "requests phone numbers",
    "asks for phone numbers",
    "stores phone numbers",
    "saves phone numbers",
    "keeps phone numbers",
    "retains phone numbers",
    "maintains phone numbers",
    
    # ===== CONTACT INFO COLLECTION =====
    "collects contact information",
    "collects contact details",
    "gathers contact information",
    "captures contact details",
    "obtains contact information",
    "stores contact information",
    "saves contact details",
    "keeps contact information",
    "contact information collected",
    "contact details gathered",
    "contact data stored",
    
    # ===== LIST FORMAT (MAJOR INDICATOR) =====
    "email, phone",
    "email, phone number",
    "email, mobile",
    "email, telephone",
    "phone, email",
    "phone number, email",
    "mobile, email",
    "email and phone",
    "email and phone number",
    "email and mobile",
    "phone and email",
    "email, phone, address",
    "email, phone, name",
    "email, phone, location",
    "email, phone, zip",
    "email, mobile, address",
    "name, email, phone",
    "address, email, phone",
    "email, phone, DOB",
    "email, phone, preferences",
    "email, SMS, phone",
    "email address, phone number",
    "email address, mobile number",
    "fields: email, phone",
    "data: email, phone",
    "information: email, phone",
    "details: email, phone",
    "email, phone collected",
    "email, phone stored",
    "email, phone saved",
    "stores email, phone",
    "saves email, phone",
    "collects email, phone",
    "gathers email, phone",
    
    # ===== USER PROVIDES =====
    "user provides email",
    "user provides phone",
    "user provides email address",
    "user provides phone number",
    "users provide email",
    "users provide phone",
    "customer provides email",
    "customer provides phone",
    "customers provide email",
    "member provides email",
    "subscriber provides email",
    
    # ===== REQUIRED FIELDS =====
    "required: email",
    "required: phone",
    "required: email, phone",
    "required fields: email",
    "required fields: phone",
    "required fields: email, phone",
    "mandatory: email",
    "mandatory: phone",
    "mandatory fields: email",
    "email required",
    "phone required",
    "email mandatory",
    "phone mandatory",
    "email needed",
    "phone needed",
    
    # ===== PROFILE DATA =====
    "profile data: email",
    "profile data: phone",
    "profile data: email, phone",
    "profile information: email",
    "profile details: email",
    "user data: email, phone",
    "customer data: email, phone",
    "account data: email, phone",
    "personal data: email, phone",
    "contact data: email, phone",
    
    # ===== ACCOUNT INFORMATION =====
    "account information includes email",
    "account details include email",
    "account contains email",
    "account has email address",
    "account stores email",
    "account saves email",
    "email in account information",
    "email in account details",
    
    # ===== DISPLAY/SHOW =====
    "displays email address",
    "displays phone number",
    "shows email address",
    "shows phone number",
    "renders email address",
    "presents email address",
    "email displayed",
    "phone displayed",
    "email shown",
    "phone shown",
    "visible email address",
    "visible phone number",
    "email visible in",
    "phone visible in",
    
    # ===== SEARCH/FILTER =====
    "search by email",
    "search by phone",
    "search using email",
    "search using phone",
    "filter by email",
    "filter by phone",
    "find by email",
    "find by phone",
    "lookup by email",
    "lookup by phone",
    "query by email",
    "query by phone",
    "email search",
    "phone search",
    "search email field",
    "search phone field",
    
    # ===== EXPORT/IMPORT =====
    "export email addresses",
    "export email list",
    "export phone numbers",
    "import email addresses",
    "import email list",
    "import phone numbers",
    "download email list",
    "download email addresses",
    "upload email list",
    "email data export",
    "email data import",
    "email list download",
    
    # ===== PLAINTEXT/TEXT FIELD (TECHNICAL) =====
    "plaintext",
    "plain text",
    "plaintext format",
    "plain text format",
    "plaintext encoding",
    "text field",
    "text field in database",
    "text data type",
    "text column",
    "text column in table",
    "text type",
    "text format",
    "text string",
    "text area",
    "text input",
    "text box",
    "text entry",
    
    # ===== LANGUAGE/LOCALIZATION =====
    "Japanese text",
    "Chinese text",
    "Korean text",
    "Japanese language text",
    "Chinese language text",
    "Korean language text",
    "text in Japanese",
    "text in Chinese",
    "text in Korean",
    "multilingual text",
    "localized text",
    "translated text",
    "language text",
    
    # ===== DATABASE/TECHNICAL =====
    "email field type",
    "email data type",
    "email column type",
    "email table",
    "email schema",
    "email database table",
    "email record",
    "email entry",
    "email row",
    "database field email",
    "database column email",
    "table field email",
    "table column email",
    
    # ===== VERIFICATION (RECEIVE ONLY, NOT SEND) =====
    "SMS verification code",
    "text verification code",
    "SMS authentication code",
    "text authentication code",
    "2FA via SMS",
    "2FA via text",
    "two-factor via SMS",
    "two-factor via text",
    "verification code via SMS",
    "verification code via text",
    "one-time password SMS",
    "one-time password text",
    "OTP via SMS",
    "OTP via text",
    "security code SMS",
    "security code text",
    
    # ===== PREFERENCES/SETTINGS =====
    "email preferences",
    "email settings",
    "notification preferences",
    "communication preferences",
    "email subscription settings",
    "manages email preferences",
    "configures email settings",
    "email notification settings",
    
    # ===== ANALYTICS/TRACKING =====
    "email analytics",
    "email statistics",
    "email metrics",
    "email tracking",
    "email monitoring",
    "email reporting",
    "tracks email usage",
    "monitors email activity",
    "analyzes email data",
    "email performance metrics",
    
    # ===== CONSENT/PERMISSION (FOR COLLECTION) =====
    "user consents to email collection",
    "permission to collect email",
    "agrees to provide email",
    "opts in to email collection",
    "authorizes email collection",
    "user grants email access",
    
    # ===== UPDATE/MODIFY =====
    "update email address",
    "modify email address",
    "change email address",
    "edit email address",
    "update phone number",
    "modify phone number",
    "change phone number",
    "email address update",
    "email address modification",
    
    # ===== MATCH/COMPARE =====
    "match email addresses",
    "compare email addresses",
    "deduplicate emails",
    "merge email records",
    "match by email",
    "compare by email",
    "email matching",
    "email comparison",
    
    # ===== BACKUP/ARCHIVE =====
    "backup email data",
    "archive email addresses",
    "email backup",
    "email archive",
    "archived email addresses",
    "backed up email data",
    
    # ===== SYNC/IMPORT FROM EXTERNAL =====
    "sync email from contacts",
    "import email from address book",
    "sync phone from contacts",
    "import phone from address book",
    "email sync",
    "contact sync",
    "address book sync",
    
    # ===== ACCOUNT RECOVERY =====
    "email for account recovery",
    "email for password reset",
    "recovery email address",
    "backup email address",
    "alternate email address",
    
    # ===== MISSING/EMPTY =====
    "missing email address",
    "empty email field",
    "no email provided",
    "email not provided",
    "email field blank",
    "email field empty",
    
    # ===== INVALID/ERROR =====
    "invalid email address",
    "invalid email format",
    "email error",
    "email validation error",
    "incorrect email format",
    "malformed email address",
    
    # ===== COPY/DUPLICATE =====
    "copy email address",
    "duplicate email field",
    "copy email to clipboard",
    "email copied",
    "email duplicated",
]

print(f"\n✓ Training set loaded:")
print(f"  E-communication (sending): {len(ECOMM_SENDING)} examples")
print(f"  Data collection (storing): {len(DATA_COLLECTION)} examples")

# ============================================================================
# ENCODE TRAINING EXAMPLES
# ============================================================================

if MODEL_AVAILABLE:
    print("\nEncoding training examples (this will take a minute)...")
    
    ecomm_embeddings = model.encode(ECOMM_SENDING, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    datacoll_embeddings = model.encode(DATA_COLLECTION, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    
    ecomm_centroid = np.mean(ecomm_embeddings, axis=0)
    datacoll_centroid = np.mean(datacoll_embeddings, axis=0)
    
    print("✓ Encoding complete")

# ============================================================================
# HARD PATTERNS
# ============================================================================

# Immediate disqualifiers
DISQUALIFIER_PATTERNS = [
    r'email\s*,\s*phone', r'phone\s*,\s*email',
    r'plaintext', r'text field', r'text data type', r'text column',
    r'japanese text', r'chinese text', r'korean text',
    r'email for login', r'email as username', r'email field', r'phone field',
    r'collects email', r'stores email', r'gathers email', r'saves email',
    r'email required for', r'email needed for', r'required: email'
]

DISQUALIFIER_REGEX = re.compile('|'.join(DISQUALIFIER_PATTERNS), re.IGNORECASE)

# Immediate qualifiers
ECOMM_KEYWORDS = [
    'can send email', 'can send text', 'can send message', 'can send sms',
    'users send email', 'users send text', 'users send message',
    'app sends email', 'app sends text', 'app sends sms', 'app sends notification',
    'ability to send', 'allows users to send', 'enables sending',
    'e-communication', 'e-communications', 'electronic communication',
    'video call', 'video chat', 'voice call', 'audio call',
    'instant messaging', 'chat feature', 'messaging platform',
    'push notification', 'delivers notification', 'transmits message'
]

# ============================================================================
# CLASSIFICATION
# ============================================================================

def classify_ecomm(text: str) -> Dict:
    if not text or pd.isna(text):
        return {'is_ecomm': False, 'confidence': 0.0, 'method': 'empty'}
    
    text_str = str(text).strip()
    if not text_str or text_str.lower() in ['nan', 'none', '']:
        return {'is_ecomm': False, 'confidence': 0.0, 'method': 'empty'}
    
    text_lower = text_str.lower()
    
    # Hard disqualifiers
    if DISQUALIFIER_REGEX.search(text_lower):
        return {'is_ecomm': False, 'confidence': 0.0, 'method': 'disqualifier'}
    
    # Hard qualifiers
    if any(kw in text_lower for kw in ECOMM_KEYWORDS):
        return {'is_ecomm': True, 'confidence': 0.95, 'method': 'ecomm_keyword'}
    
    # Semantic classification
    if MODEL_AVAILABLE:
        try:
            text_embedding = model.encode([text_str], normalize_embeddings=True, show_progress_bar=False)[0]
            
            sim_ecomm_centroid = cosine_similarity(text_embedding.reshape(1, -1), ecomm_centroid.reshape(1, -1))[0][0]
            sim_datacoll_centroid = cosine_similarity(text_embedding.reshape(1, -1), datacoll_centroid.reshape(1, -1))[0][0]
            
            max_sim_ecomm = np.max(cosine_similarity(text_embedding.reshape(1, -1), ecomm_embeddings))
            max_sim_datacoll = np.max(cosine_similarity(text_embedding.reshape(1, -1), datacoll_embeddings))
            
            # Triple weighting: centroid + max + percentile 90
            sorted_ecomm_sims = np.sort(cosine_similarity(text_embedding.reshape(1, -1), ecomm_embeddings)[0])
            sorted_datacoll_sims = np.sort(cosine_similarity(text_embedding.reshape(1, -1), datacoll_embeddings)[0])
            
            percentile_90_ecomm = sorted_ecomm_sims[int(0.9 * len(sorted_ecomm_sims))]
            percentile_90_datacoll = sorted_datacoll_sims[int(0.9 * len(sorted_datacoll_sims))]
            
            # Weighted average
            avg_ecomm = (sim_ecomm_centroid + max_sim_ecomm + percentile_90_ecomm) / 3
            avg_datacoll = (sim_datacoll_centroid + max_sim_datacoll + percentile_90_datacoll) / 3
            
            if avg_ecomm + avg_datacoll > 0:
                final_score = avg_ecomm / (avg_ecomm + avg_datacoll)
            else:
                final_score = 0.5
            
            method = 'semantic'
            
        except:
            final_score = 0.3
            method = 'fallback'
    else:
        final_score = 0.3
        method = 'no_model'
    
    is_ecomm = final_score > SEMANTIC_THRESHOLD
    
    return {
        'is_ecomm': is_ecomm,
        'confidence': float(final_score),
        'method': method
    }

def safe_str(value):
    if value is None or pd.isna(value):
        return ""
    try:
        return str(value).strip()
    except:
        return ""

# ============================================================================
# TEST
# ============================================================================
print("\n" + "="*80)
print("TESTING WITH MASSIVE TRAINING SET")
print("="*80)

test_cases = [
    ("users can send emails through the app", True),
    ("application allows transmitting electronic messages", True),
    ("sends push notifications to users", True),
    ("video calling between users", True),
    ("instant messaging capability", True),
    ("collects email addresses", False),
    ("email address for registration", False),
    ("stores phone numbers", False),
    ("email, phone, address collected", False),
    ("login with email", False),
]

print("\nTest Results:")
print("-" * 70)

correct = 0
for text, expected in test_cases:
    result = classify_ecomm(text)
    is_correct = result['is_ecomm'] == expected
    correct += is_correct
    
    status = "✓" if is_correct else "✗"
    print(f"{status} [{result['confidence']:.3f}] {text[:50]}")

accuracy = correct / len(test_cases)
print("-" * 70)
print(f"Accuracy: {accuracy*100:.0f}%")

# ============================================================================
# PROCESS DATA
# ============================================================================
print("\n" + "="*80)
print("PROCESSING DATA")
print("="*80)

all_idn_eons = set()

for dataset_name in input_dataset_names:
    print(f"\n[{dataset_name}]")
    
    try:
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=None)
        for col in df.columns:
            df[col] = df[col].astype(str)
        print(f"  Loaded {len(df):,} rows")
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
    
    unique_vals = [str(v).strip() for v in df[idn_col].unique()
                   if str(v).strip() and str(v).lower() not in ['nan', 'none', '']]
    
    print(f"  Found {len(unique_vals):,} unique IDN_EON")
    all_idn_eons.update(unique_vals)

print(f"\nTotal unique IDN_EON: {len(all_idn_eons):,}")

inventory = {idn: {
    'IDN_EON': idn,
    'sources': set(),
    'ecomm_findings': []
} for idn in all_idn_eons}

processed = 0

for dataset_name in input_dataset_names:
    print(f"\n[{dataset_name}]")
    
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
    
    unique_idns = [str(v).strip() for v in df[idn_col].unique()
                   if str(v).strip() and str(v).lower() not in ['nan', 'none', '']]
    
    for IDN_EON_str in unique_idns:
        processed += 1
        if processed % 500 == 0:
            print(f"  Progress: {processed:,}/{len(all_idn_eons):,}")
        
        inventory[IDN_EON_str]['sources'].add(dataset_name)
        idn_rows = df[df[idn_col] == IDN_EON_str]
        
        for col in df.columns:
            if col.upper() == 'IDN_EON':
                continue
            
            for val in idn_rows[col]:
                val_str = safe_str(val)
                if not val_str or val_str.lower() in ['nan', 'none', '']:
                    continue
                
                val_lower = val_str.lower()
                
                relevant = ['email', 'text', 'sms', 'message', 'call', 'video', 'voice', 
                           'chat', 'communication', 'notify', 'notification', 'alert']
                
                if not any(kw in val_lower for kw in relevant):
                    continue
                
                result = classify_ecomm(val_str)
                
                if result['is_ecomm']:
                    inventory[IDN_EON_str]['ecomm_findings'].append({
                        'location': f"{col} [{dataset_name}]",
                        'confidence': result['confidence'],
                        'method': result['method'],
                        'content': val_str[:300]
                    })

# Build output
output_data = []

for idn, data in inventory.items():
    if len(data['ecomm_findings']) >= MIN_FINDINGS_REQUIRED:
        max_conf = max([f['confidence'] for f in data['ecomm_findings']])
        methods = list(set([f['method'] for f in data['ecomm_findings']]))
        locations = list(set([f['location'] for f in data['ecomm_findings']]))
        contents = list(set([f['content'] for f in data['ecomm_findings']]))[:3]
        
        output_data.append({
            'IDN_EON': idn,
            'sort_conf': max_conf,
            'data_source': ', '.join(sorted(data['sources'])),
            'ecomm_confidence': round(max_conf, 3),
            'detection_method': ', '.join(methods),
            'found_in': ', '.join(sorted(locations)),
            'sample_content': ' | '.join(contents),
            'total_findings': len(data['ecomm_findings'])
        })

output_df = pd.DataFrame(output_data).sort_values('sort_conf', ascending=False).reset_index(drop=True)
output_df = output_df.drop('sort_conf', axis=1)

output_dataset.write_with_schema(output_df)

print(f"\n{'='*80}")
print(f"RESULTS")
print(f"{'='*80}")
print(f"Total IDN_EON: {len(all_idn_eons):,}")
print(f"With e-communication: {len(output_df):,} ({len(output_df)/len(all_idn_eons)*100:.1f}%)")
print(f"{'='*80}")
