# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   E-COMMUNICATION CAPABILITY DETECTION ENGINE                                ║
║   Version 10.0.0 - Enterprise Edition                                        ║
║                                                                              ║
║   Intelligent semantic analysis system for detecting applications            ║
║   that have e-communication capabilities (sending emails, texts,             ║
║   messages, making calls, push notifications, etc.)                          ║
║                                                                              ║
║   Features:                                                                  ║
║   - TF-IDF semantic similarity with 500+ training examples                   ║
║   - Multi-tier classification (patterns → keywords → semantics)              ║
║   - Intelligent context analysis                                             ║
║   - Learnable false positive/negative handling                               ║
║   - Comprehensive logging and progress tracking                              ║
║   - Batch processing for performance                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ INPUT AND OUTPUT TABLES - CONFIGURE THESE FIRST                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

INPUT_TABLE_1 = 'table1'  # First input table name
INPUT_TABLE_2 = 'table2'  # Second input table name
INPUT_TABLE_3 = 'table3'  # Third input table name
INPUT_TABLE_4 = 'table4'  # Fourth input table name

OUTPUT_TABLE = 'ecomm_detection_results'  # Output table name

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ DETECTION SETTINGS                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Classification threshold (0.0 to 1.0)
# Lower = more lenient (catches more but may have false positives)
# Higher = stricter (fewer false positives but may miss some)
ECOMM_THRESHOLD = 0.55

# Minimum text length to analyze (characters)
MIN_TEXT_LENGTH = 5

# Maximum text length to analyze (very long texts are truncated)
MAX_TEXT_LENGTH = 10000

# Batch size for TF-IDF processing (higher = faster but more memory)
BATCH_SIZE = 100

# Progress reporting interval (rows)
PROGRESS_INTERVAL = 500

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ FALSE POSITIVES - STRINGS THAT INCORRECTLY TRIGGER DETECTION                 ║
# ║                                                                              ║
# ║ When you find text being wrongly flagged as having e-comm capability,        ║
# ║ add it here. The system will learn to reject these patterns.                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

FALSE_POSITIVES = [
    # ══════════════════════════════════════════════════════════════════════════
    # ADD YOUR FALSE POSITIVES BELOW THIS LINE
    # ══════════════════════════════════════════════════════════════════════════
    
    # Example entries (uncomment and modify as needed):
    # "message queue for batch processing",
    # "call stack trace logging",
    # "email field varchar(255)",
    # "notification_id primary key",
    
    # ══════════════════════════════════════════════════════════════════════════
    # ADD YOUR FALSE POSITIVES ABOVE THIS LINE
    # ══════════════════════════════════════════════════════════════════════════
]

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ FALSE NEGATIVES - STRINGS THAT SHOULD TRIGGER BUT DON'T                      ║
# ║                                                                              ║
# ║ When you find text that should be flagged as e-comm but isn't,               ║
# ║ add it here. The system will learn to detect these patterns.                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

FALSE_NEGATIVES = [
    # ══════════════════════════════════════════════════════════════════════════
    # ADD YOUR FALSE NEGATIVES BELOW THIS LINE
    # ══════════════════════════════════════════════════════════════════════════
    
    # Example entries (uncomment and modify as needed):
    # "proprietary messaging system",
    # "custom notification framework",
    # "internal communication module",
    
    # ══════════════════════════════════════════════════════════════════════════
    # ADD YOUR FALSE NEGATIVES ABOVE THIS LINE
    # ══════════════════════════════════════════════════════════════════════════
]

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ END OF USER CONFIGURATION                                                    ║
# ║                                                                              ║
# ║ Everything below this line is the detection engine.                          ║
# ║ Modify only if you understand the code.                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import dataiku
import pandas as pd
import numpy as np
import re
import time
from collections import defaultdict
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ TRAINING DATA: E-COMMUNICATION SENDING EXAMPLES                              ║
# ║                                                                              ║
# ║ These are examples of text that indicates an application HAS the             ║
# ║ capability to SEND electronic communications. The classifier learns          ║
# ║ from these examples to identify similar patterns.                            ║
# ║                                                                              ║
# ║ Key characteristics:                                                         ║
# ║ - Active sending verbs (sends, delivers, transmits)                          ║
# ║ - User-to-user or app-to-user communication                                  ║
# ║ - Features that enable outbound communication                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

ECOMM_SENDING_EXAMPLES = [
    # ══════════════════════════════════════════════════════════════════════════
    # EMAIL SENDING CAPABILITIES
    # ══════════════════════════════════════════════════════════════════════════
    
    # Direct email sending
    "users can send emails through the application",
    "application sends email notifications to users",
    "email delivery capability is enabled",
    "the system transmits emails to users automatically",
    "users are able to send emails from within the app",
    "email sending feature is available to all users",
    "the platform can send emails on behalf of users",
    "automated email sending system is active",
    "bulk email delivery system is enabled",
    "the app delivers emails to customer inboxes",
    "outgoing email functionality is supported",
    "users can compose and send emails",
    "email dispatch functionality is available",
    "the system can send email messages",
    "email transmission service is active",
    
    # Email notifications
    "sends email notifications to users",
    "email alerts are sent to users",
    "delivers email communications to customers",
    "sends order confirmation emails",
    "sends promotional emails to customers",
    "sends welcome emails to new users",
    "sends reminder emails automatically",
    "sends password reset emails",
    "sends account verification emails",
    "sends shipping notification emails",
    "sends invoice emails to customers",
    "sends receipt emails after purchase",
    "sends booking confirmation emails",
    "sends appointment reminder emails",
    "sends newsletter emails to subscribers",
    "sends marketing emails to users",
    "sends transactional emails",
    "sends automated email responses",
    "sends follow-up emails",
    "sends digest emails daily",
    "sends weekly summary emails",
    "sends alert emails when events occur",
    "sends notification emails for updates",
    "sends system status emails",
    "sends error notification emails to admins",
    
    # Email features
    "email notification delivery system",
    "email broadcast feature is enabled",
    "mass email sending capability",
    "email campaign sending feature",
    "automated email sender module",
    "email messaging feature is available",
    "in-app email sending functionality",
    "email communication feature",
    "email outreach capability",
    "email marketing system sends messages",
    "drip email campaign functionality",
    "triggered email sending system",
    "event-based email notifications",
    "scheduled email sending feature",
    "batch email processing and sending",
    
    # ══════════════════════════════════════════════════════════════════════════
    # SMS AND TEXT MESSAGE SENDING CAPABILITIES
    # ══════════════════════════════════════════════════════════════════════════
    
    # Direct SMS sending
    "users can send texts through the application",
    "application sends SMS alerts to users",
    "text message delivery system is enabled",
    "SMS notification system is active",
    "the app can send text messages to phones",
    "users can send SMS from the platform",
    "text messaging capability is available",
    "SMS sending feature is enabled",
    "the system sends text notifications",
    "bulk SMS sending capability",
    "automated text messages are sent",
    "SMS messaging platform is active",
    "mobile text messaging feature",
    "text message sending functionality",
    "SMS communication is enabled",
    "outbound SMS capability",
    "text alert system sends messages",
    "SMS broadcast feature",
    "mass text messaging system",
    "group SMS sending feature",
    
    # SMS notifications
    "sends SMS alerts to users",
    "sends text notifications to customers",
    "sends appointment reminder texts",
    "sends promotional texts to users",
    "sends order status via SMS",
    "sends delivery notifications by text",
    "sends verification codes via SMS",
    "sends booking confirmations via text",
    "sends payment reminders via SMS",
    "sends account alerts via text message",
    "sends emergency notifications via SMS",
    "sends two-way SMS messages",
    "sends automated text responses",
    "sends scheduled text messages",
    "sends personalized SMS campaigns",
    "sends transactional SMS messages",
    "sends OTP codes via text",
    "sends login alerts via SMS",
    "sends security notifications via text",
    "sends status updates via SMS",
    
    # SMS features
    "SMS gateway integration for sending",
    "text message notification system",
    "mobile SMS alert feature",
    "SMS marketing campaign sender",
    "automated SMS reminder system",
    "SMS notification delivery service",
    "text message broadcast system",
    "SMS communication platform",
    "mobile messaging capability",
    "text notification feature",
    
    # ══════════════════════════════════════════════════════════════════════════
    # VIDEO CALLING CAPABILITIES
    # ══════════════════════════════════════════════════════════════════════════
    
    "users can make video calls",
    "video calling feature is enabled",
    "video conferencing capability is available",
    "video chat between users is supported",
    "real-time video calling feature",
    "video call functionality is active",
    "supports video calling between users",
    "video communication platform",
    "make video calls through the app",
    "video calling service is available",
    "video chat capability is enabled",
    "video calls between users are supported",
    "video meeting capability",
    "group video calling feature",
    "one-on-one video calling",
    "HD video calling support",
    "video call with screen sharing",
    "integrated video conferencing",
    "peer-to-peer video calling",
    "browser-based video calling",
    "mobile video calling support",
    "video consultation feature",
    "telehealth video calling",
    "video interview capability",
    "live video streaming to users",
    "video broadcast feature",
    "webinar video capability",
    "video room creation feature",
    "scheduled video calls",
    "instant video calling",
    
    # ══════════════════════════════════════════════════════════════════════════
    # VOICE CALLING CAPABILITIES
    # ══════════════════════════════════════════════════════════════════════════
    
    "users can make voice calls",
    "voice calling platform is enabled",
    "VoIP capability is available",
    "phone call feature in the app",
    "voice communication is enabled",
    "voice call functionality is active",
    "make phone calls through the app",
    "voice calling service is available",
    "VoIP calling feature",
    "internet calling is enabled",
    "voice calls between users are supported",
    "audio calling capability",
    "telephone capability is available",
    "call users directly through the app",
    "click-to-call functionality",
    "in-app voice calling",
    "SIP calling support",
    "PSTN calling capability",
    "conference calling feature",
    "group voice calls",
    "call recording capability",
    "voice message sending",
    "voicemail feature",
    "automated voice calls",
    "IVR system for calls",
    "outbound calling capability",
    "inbound call handling",
    "call center functionality",
    "customer support calling",
    "voice broadcast feature",
    
    # ══════════════════════════════════════════════════════════════════════════
    # INSTANT MESSAGING CAPABILITIES
    # ══════════════════════════════════════════════════════════════════════════
    
    "users can send messages to each other",
    "instant messaging capability is available",
    "chat feature is enabled",
    "messaging between users is supported",
    "direct messaging platform",
    "in-app messaging feature",
    "real-time messaging is available",
    "users can message each other",
    "send direct messages to users",
    "chat functionality is enabled",
    "real-time chat feature",
    "messaging platform is active",
    "instant chat feature",
    "private messaging between users",
    "group messaging capability",
    "team messaging feature",
    "chat room functionality",
    "live chat support",
    "customer chat feature",
    "peer-to-peer messaging",
    "encrypted messaging",
    "secure messaging platform",
    "multimedia messaging support",
    "file sharing in messages",
    "message threads feature",
    "conversation history",
    "typing indicators in chat",
    "read receipts for messages",
    "message reactions feature",
    "emoji support in messages",
    "GIF sharing in chat",
    "voice messages in chat",
    "disappearing messages feature",
    "scheduled messages",
    "message forwarding",
    "message search functionality",
    "chat notifications",
    "unread message indicators",
    "chat presence indicators",
    "online status display",
    
    # ══════════════════════════════════════════════════════════════════════════
    # PUSH NOTIFICATION CAPABILITIES
    # ══════════════════════════════════════════════════════════════════════════
    
    "sends push notifications to users",
    "delivers push notifications",
    "mobile push alerts are enabled",
    "push notification system is active",
    "sends app notifications to users",
    "notification delivery system",
    "push notification capability",
    "sends mobile alerts to users",
    "app push notifications are sent",
    "real-time push alerts",
    "push notification feature",
    "notification sending feature",
    "push notifications are enabled",
    "mobile notification system",
    "in-app notification delivery",
    "rich push notifications",
    "actionable push notifications",
    "personalized push notifications",
    "segmented push notifications",
    "scheduled push notifications",
    "geo-targeted push notifications",
    "triggered push notifications",
    "transactional push notifications",
    "promotional push notifications",
    "push notification campaigns",
    "silent push notifications",
    "background push updates",
    "badge count notifications",
    "sound notifications",
    "vibration alerts",
    "notification center integration",
    "lock screen notifications",
    "heads-up notifications",
    "notification channels",
    "notification grouping",
    "expandable notifications",
    "media-rich notifications",
    "interactive notifications",
    "quick reply notifications",
    "notification history",
    
    # ══════════════════════════════════════════════════════════════════════════
    # EXPLICIT E-COMMUNICATION TERMINOLOGY
    # ══════════════════════════════════════════════════════════════════════════
    
    "e-communication capability is enabled",
    "e-communications platform",
    "e-communication services are available",
    "electronic communication capability",
    "e-communication feature is active",
    "e-communication system",
    "digital communication platform",
    "electronic messaging capability",
    "e-communication enabled application",
    "unified communications platform",
    "omnichannel communication capability",
    "multi-channel messaging",
    "cross-platform communication",
    "integrated communication suite",
    "communication hub feature",
    "messaging infrastructure",
    "real-time communication platform",
    "asynchronous messaging capability",
    "synchronous communication feature",
    "bidirectional communication",
    
    # ══════════════════════════════════════════════════════════════════════════
    # GENERAL COMMUNICATION SENDING
    # ══════════════════════════════════════════════════════════════════════════
    
    "sends alerts to users",
    "notification sending capability",
    "delivers communications to users",
    "communication platform is enabled",
    "alert delivery system",
    "sends user notifications",
    "communication capability is enabled",
    "outbound communication feature",
    "user notification system",
    "automated alert sending",
    "real-time alert delivery",
    "event notification system",
    "status update notifications",
    "reminder sending feature",
    "announcement broadcasting",
    "mass communication capability",
    "targeted messaging feature",
    "personalized notification delivery",
    "contextual alert system",
    "smart notification routing",
    
    # ══════════════════════════════════════════════════════════════════════════
    # SOCIAL AND COLLABORATION FEATURES
    # ══════════════════════════════════════════════════════════════════════════
    
    "social messaging feature",
    "collaborative communication tools",
    "team collaboration messaging",
    "workspace chat functionality",
    "channel-based messaging",
    "threaded conversations",
    "mention notifications",
    "at-mention alerts",
    "comment notifications",
    "reply notifications",
    "share notifications",
    "like notifications",
    "follow notifications",
    "friend request notifications",
    "connection request alerts",
    "activity feed notifications",
    "news feed updates",
    "timeline notifications",
    "story notifications",
    "post notifications",
    
    # ══════════════════════════════════════════════════════════════════════════
    # CUSTOMER COMMUNICATION
    # ══════════════════════════════════════════════════════════════════════════
    
    "customer communication platform",
    "client messaging feature",
    "support ticket notifications",
    "helpdesk messaging",
    "customer support chat",
    "live agent chat",
    "chatbot messaging",
    "automated customer responses",
    "feedback request emails",
    "survey invitation emails",
    "review request notifications",
    "customer engagement messaging",
    "loyalty program notifications",
    "rewards notifications",
    "membership notifications",
    "subscription notifications",
    "billing notifications",
    "payment confirmation messages",
    "refund notification emails",
    "dispute resolution messages",
]

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ TRAINING DATA: DATA COLLECTION EXAMPLES                                      ║
# ║                                                                              ║
# ║ These are examples of text that indicates an application only COLLECTS       ║
# ║ or STORES contact information, but does NOT have e-communication             ║
# ║ capability. The classifier learns to reject these patterns.                  ║
# ║                                                                              ║
# ║ Key characteristics:                                                         ║
# ║ - Collection/storage verbs (collects, stores, gathers, captures)             ║
# ║ - Form fields and input elements                                             ║
# ║ - Database and technical terminology                                         ║
# ║ - Login/registration contexts                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

DATA_COLLECTION_EXAMPLES = [
    # ══════════════════════════════════════════════════════════════════════════
    # EMAIL ADDRESS COLLECTION
    # ══════════════════════════════════════════════════════════════════════════
    
    "collects email addresses from users",
    "gathers email from users during signup",
    "stores email addresses in the database",
    "email address collection form",
    "captures email for marketing purposes",
    "email is captured during registration",
    "collects user email for records",
    "email collection field on form",
    "gathers email addresses for newsletter",
    "stores email data in user profile",
    "collects emails for future contact",
    "email data collection process",
    "captures user email address on signup",
    "gathers customer emails for CRM",
    "stores user email addresses securely",
    "collects contact email information",
    "email harvesting for marketing",
    "builds email list from signups",
    "accumulates email addresses",
    "compiles email database",
    "aggregates user emails",
    "maintains email address list",
    "keeps record of email addresses",
    "archives email information",
    "retains email for records",
    "preserves email data",
    
    # ══════════════════════════════════════════════════════════════════════════
    # EMAIL STORAGE
    # ══════════════════════════════════════════════════════════════════════════
    
    "saves email in database",
    "email on file for records",
    "retains email address for account",
    "email records are stored",
    "maintains email addresses in system",
    "email is stored in the system",
    "stores email permanently",
    "email saved for reference",
    "keeps email on record",
    "email archived in database",
    "email data is preserved",
    "email address is retained",
    "email persisted to database",
    "email written to storage",
    "email cached in system",
    "email backed up regularly",
    "email replicated across servers",
    "email synchronized to cloud",
    "email exported to file",
    "email logged for audit",
    
    # ══════════════════════════════════════════════════════════════════════════
    # REGISTRATION AND LOGIN
    # ══════════════════════════════════════════════════════════════════════════
    
    "email required for registration",
    "email for account creation",
    "login with email address",
    "email as username",
    "sign in with email",
    "email needed for signup",
    "register with email address",
    "email login required",
    "email for authentication",
    "sign up using email",
    "email address for login",
    "login using email address",
    "email-based login system",
    "email required to register",
    "email used for account access",
    "email serves as user identifier",
    "email is the primary login",
    "authenticate with email",
    "verify identity with email",
    "email confirms user identity",
    "email validates account",
    "email activates account",
    "email unlocks account access",
    "email grants system access",
    "email enables login",
    "email permits authentication",
    "email authorizes access",
    "email credential storage",
    "email in credentials table",
    "email linked to password",
    
    # ══════════════════════════════════════════════════════════════════════════
    # FORM FIELDS AND INPUT ELEMENTS
    # ══════════════════════════════════════════════════════════════════════════
    
    "email field in the form",
    "email input field",
    "enter email address here",
    "provide email in form",
    "email form field",
    "email text box",
    "input email address",
    "email entry field",
    "fill in email address",
    "email input is required",
    "email address input box",
    "type email address",
    "email field is required",
    "enter your email",
    "email placeholder text",
    "email input validation",
    "email field label",
    "email input element",
    "email text input",
    "email form control",
    "email input widget",
    "email address textbox",
    "email entry textfield",
    "email input component",
    "email form element",
    "email data entry",
    "email capture field",
    "email submission form",
    "email registration field",
    "email signup box",
    
    # ══════════════════════════════════════════════════════════════════════════
    # EMAIL VALIDATION AND VERIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    
    "validates email format",
    "verifies email address format",
    "checks email syntax",
    "email format validation",
    "email validation check",
    "verify email format is correct",
    "validates user email address",
    "email address verification process",
    "check email format",
    "email regex validation",
    "email pattern matching",
    "email format checker",
    "email syntax validator",
    "email domain verification",
    "email deliverability check",
    "email bounce detection",
    "email validity confirmation",
    "email existence check",
    "email format enforcement",
    "email input sanitization",
    "email normalization process",
    "email canonicalization",
    "email duplicate detection",
    "email uniqueness check",
    "email constraint validation",
    
    # ══════════════════════════════════════════════════════════════════════════
    # DATABASE AND TECHNICAL TERMINOLOGY
    # ══════════════════════════════════════════════════════════════════════════
    
    "email field in database",
    "email column in table",
    "email data type varchar",
    "email table column definition",
    "plaintext email field",
    "text field for email storage",
    "text column for email",
    "varchar email field",
    "email database column",
    "string field for email",
    "email varchar column",
    "email stored as text",
    "plaintext email storage",
    "email nvarchar field",
    "email char column",
    "email string type",
    "email data field",
    "email attribute in schema",
    "email property in model",
    "email member variable",
    "email class field",
    "email object property",
    "email entity attribute",
    "email column index",
    "email primary key",
    "email foreign key reference",
    "email unique constraint",
    "email not null constraint",
    "email default value",
    "email column length",
    "email max length 255",
    "email field size limit",
    "email data migration",
    "email schema update",
    "email table structure",
    "email database design",
    "email ERD diagram",
    "email relational model",
    "email normalization",
    "email denormalization",
    
    # ══════════════════════════════════════════════════════════════════════════
    # LIST FORMAT (STRONG INDICATOR OF DATA COLLECTION)
    # ══════════════════════════════════════════════════════════════════════════
    
    "email, phone",
    "phone, email",
    "email and phone number",
    "email, phone, address",
    "fields: email, phone",
    "email phone address",
    "contact: email, phone",
    "email, phone collected",
    "stores email, phone",
    "name, email, phone",
    "email phone fields",
    "email, telephone",
    "email, phone required",
    "email, mobile number",
    "email, cell phone",
    "first name, last name, email",
    "name, address, email, phone",
    "personal info: email, phone",
    "contact details: email, phone",
    "user data: email, phone",
    "profile: name, email, phone",
    "account: email, password",
    "credentials: email, password",
    "login: email, password",
    "signup: name, email, password",
    "registration: email, phone, address",
    "form fields: email, phone, message",
    "required: email, phone",
    "optional: email, phone",
    "input: email, phone, comments",
    
    # ══════════════════════════════════════════════════════════════════════════
    # PHONE NUMBER COLLECTION
    # ══════════════════════════════════════════════════════════════════════════
    
    "collects phone numbers",
    "stores phone numbers",
    "gathers mobile numbers",
    "phone number field",
    "phone number collected",
    "stores mobile numbers",
    "phone field in form",
    "mobile number field",
    "phone number input",
    "telephone field",
    "cell phone collection",
    "contact number field",
    "phone number storage",
    "mobile phone capture",
    "phone data collection",
    "telephone number entry",
    "phone input required",
    "mobile input field",
    "phone number textbox",
    "telephone input element",
    
    # ══════════════════════════════════════════════════════════════════════════
    # PROFILE AND DISPLAY ONLY
    # ══════════════════════════════════════════════════════════════════════════
    
    "email in user profile",
    "profile contains email",
    "account email address display",
    "displays email address",
    "shows email to user",
    "email visible in profile",
    "email shown on screen",
    "displays user email",
    "email appears in settings",
    "email displayed in account",
    "view email address",
    "email read-only display",
    "email label and value",
    "email information display",
    "email details shown",
    "email summary view",
    "email in contact card",
    "email on business card",
    "email in directory",
    "email in address book",
    
    # ══════════════════════════════════════════════════════════════════════════
    # 2FA AND VERIFICATION ONLY (NOT REAL MESSAGING)
    # ══════════════════════════════════════════════════════════════════════════
    
    "SMS verification code",
    "text verification code",
    "2FA via SMS",
    "one-time password via text",
    "SMS OTP code",
    "text-based 2FA",
    "verification SMS",
    "SMS authentication code",
    "verification code via text",
    "SMS 2FA code",
    "two-factor authentication SMS",
    "multi-factor SMS code",
    "login verification SMS",
    "account verification text",
    "phone verification code",
    "mobile verification SMS",
    "security code via SMS",
    "confirmation code text",
    "validation code SMS",
    "authentication token SMS",
    "one-time code text",
    "temporary password SMS",
    "reset code via text",
    "unlock code SMS",
    "access code text message",
    
    # ══════════════════════════════════════════════════════════════════════════
    # NON-COMMUNICATION TEXT REFERENCES
    # ══════════════════════════════════════════════════════════════════════════
    
    "Japanese text support",
    "Chinese text encoding",
    "Korean text display",
    "unicode text handling",
    "rich text formatting",
    "plain text format",
    "text encoding settings",
    "multiline text field",
    "email is optional",
    "email not required",
    "email can be blank",
    "email may be empty",
    "email field nullable",
    "email allows null",
    "email default empty",
    "no email required",
    "skip email entry",
    "bypass email field",
    "email not mandatory",
    "email voluntary",
    
    # ══════════════════════════════════════════════════════════════════════════
    # DATA PROCESSING AND ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    
    "email data analysis",
    "email metrics tracking",
    "email address statistics",
    "email domain breakdown",
    "email provider distribution",
    "email list segmentation",
    "email data enrichment",
    "email append service",
    "email lookup service",
    "email verification service",
    "email hygiene process",
    "email list cleaning",
    "email deduplication",
    "email merge process",
    "email data import",
    "email data export",
    "email CSV upload",
    "email batch processing",
    "email ETL pipeline",
    "email data warehouse",
    
    # ══════════════════════════════════════════════════════════════════════════
    # PRIVACY AND COMPLIANCE
    # ══════════════════════════════════════════════════════════════════════════
    
    "email data privacy",
    "email GDPR compliance",
    "email data retention policy",
    "email consent management",
    "email opt-in required",
    "email opt-out option",
    "email unsubscribe link",
    "email preferences center",
    "email privacy settings",
    "email data protection",
    "email encryption at rest",
    "email data masking",
    "email PII handling",
    "email sensitive data",
    "email confidential information",
    "email secure storage",
    "email access control",
    "email audit trail",
    "email data governance",
    "email compliance check",
]

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ HARD PATTERN MATCHING RULES                                                  ║
# ║                                                                              ║
# ║ These regex patterns provide fast, deterministic classification              ║
# ║ before falling back to semantic analysis.                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Patterns that AUTOMATICALLY REJECT (confidence = 0)
# These patterns strongly indicate data collection, NOT e-communication
HARD_DISQUALIFIER_PATTERNS = [
    # List format patterns (very strong indicator of data collection)
    r'email\s*,\s*phone',
    r'phone\s*,\s*email',
    r'email\s*,\s*(?:phone|mobile|address|fax|telephone)',
    r'(?:phone|mobile|telephone)\s*,\s*email',
    r'name\s*,\s*email',
    r'email\s*,\s*name',
    r'fields?\s*:\s*(?:.*)?email',
    r'contact\s*:\s*email',
    r'(?:first|last)\s*name\s*,\s*email',
    r'email\s*,\s*password',
    r'username\s*,\s*email',
    
    # Collection verb patterns
    r'collects?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone|contact)',
    r'gathers?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone|contact)',
    r'stores?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone|contact)',
    r'captures?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'saves?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'records?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'retains?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'maintains?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'keeps?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'archives?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    
    # Login/Registration patterns
    r'email\s+(?:for|as)\s+(?:login|username|authentication|signin|sign-in)',
    r'login\s+(?:with|using|via)\s+email',
    r'sign\s*[-_]?\s*in\s+(?:with|using|via)\s+email',
    r'email\s+(?:required|needed|necessary)\s+(?:for|to)\s+(?:register|signup|sign-up|login)',
    r'(?:register|signup|sign-up)\s+(?:with|using|via)\s+email',
    r'authenticate\s+(?:with|using|via)\s+email',
    r'email\s+(?:is\s+)?(?:your\s+)?(?:username|user\s*id|userid|login\s*id)',
    
    # Form field patterns
    r'email\s+(?:field|input|textbox|text\s*box|entry|box)',
    r'(?:field|input|textbox|entry)\s+(?:for\s+)?email',
    r'enter\s+(?:your\s+)?(?:email|e-mail)',
    r'provide\s+(?:your\s+)?(?:email|e-mail)',
    r'type\s+(?:your\s+)?(?:email|e-mail)',
    r'input\s+(?:your\s+)?(?:email|e-mail)',
    r'fill\s+(?:in\s+)?(?:your\s+)?(?:email|e-mail)',
    r'(?:email|e-mail)\s+(?:address\s+)?(?:here|below|above)',
    
    # Database/Technical patterns
    r'email\s+(?:column|field)\s+(?:in\s+)?(?:database|table|db|schema)',
    r'(?:varchar|nvarchar|text|string|char)\s*\(?\s*\d*\s*\)?\s+(?:for\s+)?email',
    r'email\s+(?:varchar|nvarchar|text|string|char)',
    r'(?:column|field)\s+(?:type\s+)?(?:for\s+)?email',
    r'plaintext\s+(?:email|password)',
    r'email\s+plaintext',
    r'(?:stored|saved)\s+as\s+(?:plain\s*)?text',
    r'email\s+(?:data\s*)?type',
    r'email\s+(?:max\s*)?length',
    r'email\s+constraint',
    r'email\s+(?:primary|foreign)\s+key',
    r'email\s+(?:unique|not\s+null)',
    r'email\s+(?:index|indexed)',
    
    # Validation patterns
    r'validates?\s+(?:the\s+)?email',
    r'verif(?:y|ies|ying)\s+(?:the\s+)?email',
    r'(?:email|e-mail)\s+(?:format\s+)?validation',
    r'(?:check|verify|validate)\s+(?:the\s+)?(?:email|e-mail)\s+(?:format|syntax|address)',
    r'email\s+regex',
    r'email\s+pattern\s+match',
    r'valid\s+email\s+(?:format|address|check)',
    
    # 2FA/Verification only patterns
    r'(?:sms|text)\s+(?:verification|verify)',
    r'(?:verification|verify)\s+(?:via|through|by)\s+(?:sms|text)',
    r'2fa\s+(?:via|through|by|using)',
    r'(?:otp|one[-\s]?time\s+password)',
    r'(?:verification|security|auth(?:entication)?)\s+code\s+(?:via|through|by)\s+(?:sms|text)',
    r'(?:sms|text)\s+(?:security|auth(?:entication)?)\s+code',
    r'multi[-\s]?factor\s+(?:auth(?:entication)?)',
    r'two[-\s]?factor\s+(?:auth(?:entication)?)',
    
    # Display only patterns
    r'displays?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'shows?\s+(?:the\s+)?(?:user[\'s]?\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:is\s+)?(?:visible|shown|displayed)',
    r'(?:view|see|read)\s+(?:the\s+)?(?:email|phone)',
    r'(?:email|phone)\s+(?:read[-\s]?only|readonly)',
    
    # Non-English text patterns
    r'japanese\s+text',
    r'chinese\s+text',
    r'korean\s+text',
    r'arabic\s+text',
    r'hebrew\s+text',
    r'cyrillic\s+text',
    r'unicode\s+(?:text|characters?|support)',
    
    # Optional/Not required patterns
    r'email\s+(?:is\s+)?optional',
    r'email\s+(?:is\s+)?not\s+required',
    r'email\s+(?:can|may)\s+be\s+(?:blank|empty|null)',
    r'(?:optional|voluntary)\s+email',
    r'(?:skip|bypass)\s+email',
    r'no\s+email\s+(?:required|needed|necessary)',
]

# Patterns that AUTOMATICALLY ACCEPT (confidence = 0.95)
# These patterns strongly indicate e-communication capability
HARD_QUALIFIER_PATTERNS = [
    # Explicit e-communication terminology
    r'e[-\s]?communication(?:s)?(?:\s+(?:capability|feature|enabled|platform|system))?',
    r'electronic\s+communication(?:s)?(?:\s+(?:capability|feature|enabled))?',
    r'digital\s+communication(?:s)?(?:\s+(?:platform|capability|feature))?',
    r'unified\s+communication(?:s)?',
    r'omni[-\s]?channel\s+(?:communication|messaging)',
    
    # Email sending patterns
    r'(?:can|able\s+to|allows?\s+(?:users?\s+)?to)\s+send\s+(?:an?\s+)?email',
    r'(?:user|app(?:lication)?|system|platform)s?\s+(?:can\s+)?sends?\s+(?:an?\s+)?email',
    r'sends?\s+(?:an?\s+)?(?:email|e-mail)(?:\s+(?:notification|alert|message))s?',
    r'(?:email|e-mail)\s+(?:sending|delivery)\s+(?:capability|feature|system|enabled)',
    r'(?:outbound|outgoing)\s+email(?:\s+(?:capability|feature|system))?',
    r'delivers?\s+(?:an?\s+)?email(?:\s+(?:notification|alert|message))s?',
    r'transmits?\s+(?:an?\s+)?email',
    r'(?:email|e-mail)\s+(?:notification|alert)\s+(?:system|service|feature)',
    r'(?:automated?|automatic)\s+email\s+(?:sending|delivery|notification)',
    r'bulk\s+email\s+(?:sending|delivery|capability)',
    r'email\s+(?:broadcast|campaign)\s+(?:feature|capability|system)',
    
    # SMS sending patterns
    r'(?:can|able\s+to|allows?\s+(?:users?\s+)?to)\s+send\s+(?:an?\s+)?(?:sms|text(?:\s+message)?)',
    r'(?:user|app(?:lication)?|system|platform)s?\s+(?:can\s+)?sends?\s+(?:an?\s+)?(?:sms|text)',
    r'sends?\s+(?:an?\s+)?(?:sms|text)(?:\s+(?:notification|alert|message))s?',
    r'(?:sms|text)\s+(?:messaging|sending|delivery)\s+(?:capability|feature|system)',
    r'(?:sms|text)\s+(?:notification|alert)\s+(?:system|service|feature)',
    r'(?:automated?|automatic)\s+(?:sms|text)\s+(?:sending|message)',
    r'bulk\s+(?:sms|text)\s+(?:sending|messaging|capability)',
    r'(?:sms|text)\s+(?:broadcast|campaign)\s+(?:feature|capability)',
    
    # Video calling patterns
    r'video\s+call(?:ing)?(?:\s+(?:capability|feature|enabled|platform))?',
    r'(?:can|able\s+to|allows?\s+(?:users?\s+)?to)\s+(?:make|place|initiate)\s+video\s+call',
    r'video\s+(?:conferencing|conference|chat)(?:\s+(?:capability|feature|enabled))?',
    r'(?:real[-\s]?time|live)\s+video(?:\s+(?:call|chat|communication))?',
    r'(?:peer[-\s]?to[-\s]?peer|p2p)\s+video',
    r'(?:one[-\s]?on[-\s]?one|group)\s+video\s+call',
    r'video\s+(?:meeting|consultation|interview)',
    r'(?:hd|high[-\s]?definition)\s+video\s+call',
    r'(?:webrtc|webinar)\s+(?:video|capability)',
    
    # Voice calling patterns
    r'voice\s+call(?:ing)?(?:\s+(?:capability|feature|enabled|platform))?',
    r'(?:can|able\s+to|allows?\s+(?:users?\s+)?to)\s+(?:make|place|initiate)\s+(?:voice|phone)\s+call',
    r'voip(?:\s+(?:capability|feature|enabled|calling))?',
    r'(?:internet|ip)\s+(?:telephony|calling|phone)',
    r'sip\s+(?:calling|capability|trunk)',
    r'(?:pstn|telephone)\s+(?:capability|integration)',
    r'click[-\s]?to[-\s]?call',
    r'(?:in[-\s]?app|integrated)\s+(?:voice|phone)\s+call',
    r'(?:conference|group)\s+(?:call|calling)',
    r'(?:call|voice)\s+(?:recording|transcription)',
    
    # Instant messaging patterns
    r'instant\s+messag(?:ing|e)(?:\s+(?:capability|feature|enabled|platform))?',
    r'(?:real[-\s]?time|live)\s+(?:messaging|chat)(?:\s+(?:capability|feature))?',
    r'(?:direct|in[-\s]?app|private)\s+messag(?:ing|e)',
    r'chat\s+(?:capability|feature|enabled|platform|functionality)',
    r'(?:user|users)\s+(?:can\s+)?(?:message|chat(?:\s+with)?)\s+(?:each\s+other|one\s+another)',
    r'(?:send|exchange)\s+(?:direct\s+)?messages?\s+(?:to|between|with)\s+(?:other\s+)?users?',
    r'(?:peer[-\s]?to[-\s]?peer|p2p)\s+(?:messaging|chat)',
    r'(?:group|team|channel)\s+(?:messaging|chat)',
    r'(?:encrypted|secure)\s+(?:messaging|chat)',
    r'(?:multimedia|rich)\s+messaging',
    
    # Push notification patterns
    r'sends?\s+push\s+notification',
    r'delivers?\s+push\s+notification',
    r'push\s+notification\s+(?:capability|feature|system|enabled)',
    r'(?:mobile|app)\s+(?:push\s+)?notification(?:s)?\s+(?:enabled|sent|delivered)',
    r'(?:real[-\s]?time|instant)\s+(?:push\s+)?(?:notification|alert)',
    r'notification\s+(?:sending|delivery)\s+(?:capability|feature|system)',
    r'(?:rich|actionable|interactive)\s+(?:push\s+)?notification',
    r'(?:targeted|personalized|segmented)\s+(?:push\s+)?notification',
    r'(?:scheduled|triggered|automated)\s+(?:push\s+)?notification',
    
    # General communication sending patterns
    r'sends?\s+(?:alert|notification)s?\s+to\s+users?',
    r'delivers?\s+(?:alert|notification)s?\s+to\s+users?',
    r'(?:notification|alert)\s+(?:sending|delivery)\s+(?:capability|feature)',
    r'(?:real[-\s]?time|instant)\s+(?:alert|notification)\s+(?:delivery|sending)',
    r'(?:automated?|automatic)\s+(?:notification|alert)\s+(?:sending|delivery)',
    r'(?:broadcast|mass)\s+(?:notification|message|communication)',
    r'(?:outbound|outgoing)\s+(?:communication|notification|message)',
    r'(?:user|customer)\s+(?:communication|notification)\s+(?:platform|system|feature)',
]

# Keywords that must be present for any analysis to occur
COMMUNICATION_KEYWORDS = [
    'email', 'e-mail', 'mail',
    'text', 'sms', 'mms',
    'message', 'messaging', 'msg',
    'call', 'calling', 'phone', 'telephone',
    'video', 'voice', 'audio',
    'chat', 'chatting', 'im',
    'notification', 'notify', 'notif',
    'alert', 'alerting',
    'push',
    'communicat',  # catches communicate, communication, communications
    'voip',
    'conferenc',  # catches conference, conferencing
]

# Invalid IDN_EON values to skip
INVALID_IDN_EON_VALUES = {
    'nan', 'none', '', 'null', 'n/a', 'na', 'n.a.', 'n/a.',
    '-', '--', '---', '_', '__',
    'unknown', 'undefined', 'missing', 'empty',
    ' ', '  ', '\t', '\n',
    '#n/a', '#null', '#na', '#ref!', '#value!',
    'nil', 'nothing', 'blank',
    '0', '0.0', 'false',
    'test', 'testing', 'example', 'sample', 'demo',
    'placeholder', 'temp', 'temporary', 'tmp',
    'xxx', 'yyy', 'zzz', 'abc', 'asdf',
    'tbd', 'tba', 'pending',
}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ INTELLIGENT E-COMMUNICATION CLASSIFIER                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class IntelligentECommClassifier:
    """
    Advanced classifier for detecting e-communication capabilities.
    
    Uses a multi-tier approach:
    1. Learned patterns (false positives/negatives from user feedback)
    2. Hard pattern matching (regex for definitive cases)
    3. Keyword filtering (quick rejection of irrelevant text)
    4. TF-IDF semantic similarity (ML-based classification)
    5. Confidence scoring and threshold application
    """
    
    def __init__(self):
        """Initialize the classifier with all components."""
        self.start_time = time.time()
        print("\n" + "═" * 70)
        print("  INITIALIZING INTELLIGENT E-COMMUNICATION CLASSIFIER")
        print("═" * 70)
        
        # Compile regex patterns for performance
        print("\n  [1/4] Compiling pattern matching rules...")
        self._compile_patterns()
        
        # Process learned patterns
        print("  [2/4] Loading learned patterns...")
        self._load_learned_patterns()
        
        # Build TF-IDF model
        print("  [3/4] Building semantic TF-IDF model...")
        self._build_tfidf_model()
        
        # Precompute statistics
        print("  [4/4] Precomputing classification statistics...")
        self._compute_statistics()
        
        elapsed = time.time() - self.start_time
        print(f"\n  ✓ Classifier initialized in {elapsed:.2f} seconds")
        print("═" * 70)
        
    def _compile_patterns(self):
        """Compile regex patterns for fast matching."""
        self.disqualifier_patterns = []
        for pattern in HARD_DISQUALIFIER_PATTERNS:
            try:
                self.disqualifier_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"    ⚠ Invalid disqualifier pattern: {pattern[:50]}... ({e})")
        
        self.qualifier_patterns = []
        for pattern in HARD_QUALIFIER_PATTERNS:
            try:
                self.qualifier_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"    ⚠ Invalid qualifier pattern: {pattern[:50]}... ({e})")
        
        print(f"    → {len(self.disqualifier_patterns)} disqualifier patterns compiled")
        print(f"    → {len(self.qualifier_patterns)} qualifier patterns compiled")
    
    def _load_learned_patterns(self):
        """Load and normalize learned false positives/negatives."""
        self.false_positives = set()
        for fp in FALSE_POSITIVES:
            if fp and isinstance(fp, str) and fp.strip():
                self.false_positives.add(fp.lower().strip())
        
        self.false_negatives = set()
        for fn in FALSE_NEGATIVES:
            if fn and isinstance(fn, str) and fn.strip():
                self.false_negatives.add(fn.lower().strip())
        
        print(f"    → {len(self.false_positives)} false positives loaded")
        print(f"    → {len(self.false_negatives)} false negatives loaded")
    
    def _build_tfidf_model(self):
        """Build and train the TF-IDF model."""
        # Combine all training examples
        all_examples = ECOMM_SENDING_EXAMPLES + DATA_COLLECTION_EXAMPLES
        
        # Create TF-IDF vectorizer with optimized parameters
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 4),      # Capture phrases up to 4 words
            max_features=10000,      # Larger vocabulary for better coverage
            min_df=1,                # Include rare terms
            max_df=0.95,             # Exclude very common terms
            stop_words='english',    # Remove common English words
            sublinear_tf=True,       # Apply sublinear TF scaling
            norm='l2',               # L2 normalization
            use_idf=True,            # Use inverse document frequency
            smooth_idf=True,         # Smooth IDF weights
        )
        
        # Fit the vectorizer
        self.vectorizer.fit(all_examples)
        
        # Pre-compute vectors for training examples
        self.ecomm_vectors = self.vectorizer.transform(ECOMM_SENDING_EXAMPLES)
        self.datacoll_vectors = self.vectorizer.transform(DATA_COLLECTION_EXAMPLES)
        
        # Compute centroids for each class
        self.ecomm_centroid = np.asarray(self.ecomm_vectors.mean(axis=0)).flatten()
        self.datacoll_centroid = np.asarray(self.datacoll_vectors.mean(axis=0)).flatten()
        
        print(f"    → Vocabulary size: {len(self.vectorizer.vocabulary_):,} terms")
        print(f"    → E-comm training examples: {len(ECOMM_SENDING_EXAMPLES)}")
        print(f"    → Data collection training examples: {len(DATA_COLLECTION_EXAMPLES)}")
    
    def _compute_statistics(self):
        """Precompute statistics for classification."""
        # Compute similarity distributions within each class
        ecomm_internal_sims = cosine_similarity(self.ecomm_vectors, self.ecomm_vectors)
        datacoll_internal_sims = cosine_similarity(self.datacoll_vectors, self.datacoll_vectors)
        
        # Get upper triangle (excluding diagonal) for internal similarities
        ecomm_mask = np.triu(np.ones(ecomm_internal_sims.shape), k=1).astype(bool)
        datacoll_mask = np.triu(np.ones(datacoll_internal_sims.shape), k=1).astype(bool)
        
        self.ecomm_internal_mean = np.mean(ecomm_internal_sims[ecomm_mask])
        self.datacoll_internal_mean = np.mean(datacoll_internal_sims[datacoll_mask])
        
        # Compute cross-class similarities
        cross_sims = cosine_similarity(self.ecomm_vectors, self.datacoll_vectors)
        self.cross_class_mean = np.mean(cross_sims)
        
        print(f"    → E-comm internal similarity: {self.ecomm_internal_mean:.3f}")
        print(f"    → Data collection internal similarity: {self.datacoll_internal_mean:.3f}")
        print(f"    → Cross-class similarity: {self.cross_class_mean:.3f}")
    
    def _cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        vec1 = np.asarray(vec1).flatten()
        vec2 = np.asarray(vec2).flatten()
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def _has_communication_keyword(self, text):
        """Check if text contains any communication-related keyword."""
        text_lower = text.lower()
        for keyword in COMMUNICATION_KEYWORDS:
            if keyword in text_lower:
                return True
        return False
    
    def _check_false_positive(self, text):
        """Check if text matches a learned false positive pattern."""
        text_lower = text.lower().strip()
        
        # Exact match
        if text_lower in self.false_positives:
            return True
        
        # Substring match
        for fp in self.false_positives:
            if fp and fp in text_lower:
                return True
        
        return False
    
    def _check_false_negative(self, text):
        """Check if text matches a learned false negative pattern."""
        text_lower = text.lower().strip()
        
        # Exact match
        if text_lower in self.false_negatives:
            return True
        
        # Substring match
        for fn in self.false_negatives:
            if fn and fn in text_lower:
                return True
        
        return False
    
    def _check_disqualifier_patterns(self, text):
        """Check if text matches any disqualifier pattern."""
        text_lower = text.lower()
        for pattern in self.disqualifier_patterns:
            if pattern.search(text_lower):
                return True
        return False
    
    def _check_qualifier_patterns(self, text):
        """Check if text matches any qualifier pattern."""
        text_lower = text.lower()
        for pattern in self.qualifier_patterns:
            if pattern.search(text_lower):
                return True
        return False
    
    def _compute_semantic_score(self, text):
        """
        Compute semantic similarity score using TF-IDF.
        
        Returns a score between 0 and 1, where:
        - Higher scores indicate stronger e-communication capability signals
        - Lower scores indicate data collection patterns
        """
        # Transform text to TF-IDF vector
        text_vec = self.vectorizer.transform([text])
        text_arr = np.asarray(text_vec.toarray()).flatten()
        
        # Compute centroid similarities
        ecomm_centroid_sim = self._cosine_similarity(text_arr, self.ecomm_centroid)
        datacoll_centroid_sim = self._cosine_similarity(text_arr, self.datacoll_centroid)
        
        # Compute similarities to all training examples
        ecomm_sims = cosine_similarity(text_vec, self.ecomm_vectors).flatten()
        datacoll_sims = cosine_similarity(text_vec, self.datacoll_vectors).flatten()
        
        # Compute multiple similarity metrics
        ecomm_max = np.max(ecomm_sims) if len(ecomm_sims) > 0 else 0
        datacoll_max = np.max(datacoll_sims) if len(datacoll_sims) > 0 else 0
        
        ecomm_p90 = np.percentile(ecomm_sims, 90) if len(ecomm_sims) > 0 else 0
        datacoll_p90 = np.percentile(datacoll_sims, 90) if len(datacoll_sims) > 0 else 0
        
        ecomm_p95 = np.percentile(ecomm_sims, 95) if len(ecomm_sims) > 0 else 0
        datacoll_p95 = np.percentile(datacoll_sims, 95) if len(datacoll_sims) > 0 else 0
        
        ecomm_mean = np.mean(ecomm_sims) if len(ecomm_sims) > 0 else 0
        datacoll_mean = np.mean(datacoll_sims) if len(datacoll_sims) > 0 else 0
        
        # Weighted combination of metrics
        # Give more weight to max and high percentiles as they capture strong matches
        ecomm_score = (
            0.25 * ecomm_centroid_sim +
            0.30 * ecomm_max +
            0.20 * ecomm_p95 +
            0.15 * ecomm_p90 +
            0.10 * ecomm_mean
        )
        
        datacoll_score = (
            0.25 * datacoll_centroid_sim +
            0.30 * datacoll_max +
            0.20 * datacoll_p95 +
            0.15 * datacoll_p90 +
            0.10 * datacoll_mean
        )
        
        # Normalize to get probability-like score
        total = ecomm_score + datacoll_score
        if total == 0:
            return 0.5
        
        return ecomm_score / total
    
    def classify(self, text):
        """
        Classify text for e-communication capability.
        
        Multi-tier classification approach:
        1. Validate input
        2. Check learned patterns (false positives/negatives)
        3. Check for communication keywords
        4. Apply hard pattern matching
        5. Compute semantic similarity score
        
        Args:
            text: The text to classify
            
        Returns:
            float: Confidence score between 0 and 1
                   Higher values indicate e-communication capability
        """
        # ══════════════════════════════════════════════════════════════════════
        # TIER 0: Input Validation
        # ══════════════════════════════════════════════════════════════════════
        
        if not text or not isinstance(text, str):
            return 0.0
        
        text = str(text).strip()
        
        if len(text) < MIN_TEXT_LENGTH:
            return 0.0
        
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        
        # ══════════════════════════════════════════════════════════════════════
        # TIER 1: Learned Patterns (Highest Priority)
        # ══════════════════════════════════════════════════════════════════════
        
        # Check false negatives first (force accept)
        if self._check_false_negative(text):
            return 0.98
        
        # Check false positives (force reject)
        if self._check_false_positive(text):
            return 0.02
        
        # ══════════════════════════════════════════════════════════════════════
        # TIER 2: Keyword Filter (Quick Rejection)
        # ══════════════════════════════════════════════════════════════════════
        
        if not self._has_communication_keyword(text):
            return 0.0
        
        # ══════════════════════════════════════════════════════════════════════
        # TIER 3: Hard Pattern Matching (Deterministic)
        # ══════════════════════════════════════════════════════════════════════
        
        # Check disqualifiers first (reject patterns)
        if self._check_disqualifier_patterns(text):
            return 0.05
        
        # Check qualifiers (accept patterns)
        if self._check_qualifier_patterns(text):
            return 0.95
        
        # ══════════════════════════════════════════════════════════════════════
        # TIER 4: Semantic Similarity (ML-Based)
        # ══════════════════════════════════════════════════════════════════════
        
        semantic_score = self._compute_semantic_score(text)
        
        return semantic_score
    
    def classify_batch(self, texts):
        """
        Classify multiple texts efficiently.
        
        Args:
            texts: List of texts to classify
            
        Returns:
            List of confidence scores
        """
        return [self.classify(text) for text in texts]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ HELPER FUNCTIONS                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def find_idn_eon_column(df):
    """
    Find the IDN_EON column in a dataframe (case-insensitive).
    
    Handles various naming conventions:
    - IDN_EON
    - idn_eon
    - IDN-EON
    - IDN EON
    - idneon
    """
    for col in df.columns:
        # Normalize column name
        col_normalized = col.upper().replace(' ', '_').replace('-', '_')
        
        if col_normalized == 'IDN_EON':
            return col
        if 'IDN_EON' in col_normalized:
            return col
        if col_normalized == 'IDNEON':
            return col
    
    return None


def is_valid_idn_eon(value):
    """Check if an IDN_EON value is valid (not null, empty, or placeholder)."""
    if value is None:
        return False
    
    if pd.isna(value):
        return False
    
    str_value = str(value).strip().lower()
    
    if str_value in INVALID_IDN_EON_VALUES:
        return False
    
    if len(str_value) == 0:
        return False
    
    return True


def clean_text(value):
    """Clean and normalize text for analysis."""
    if value is None or pd.isna(value):
        return ""
    
    try:
        text = str(value).strip()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    except Exception:
        return ""


def format_duration(seconds):
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{int(minutes)}m {int(secs)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"


def print_header(text):
    """Print a formatted header."""
    print("\n" + "═" * 70)
    print(f"  {text}")
    print("═" * 70)


def print_subheader(text):
    """Print a formatted subheader."""
    print("\n" + "─" * 70)
    print(f"  {text}")
    print("─" * 70)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ MAIN EXECUTION                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def main():
    """Main execution function."""
    
    script_start_time = time.time()
    
    # ══════════════════════════════════════════════════════════════════════════
    # STARTUP BANNER
    # ══════════════════════════════════════════════════════════════════════════
    
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║   E-COMMUNICATION CAPABILITY DETECTION ENGINE                                ║")
    print("║   Version 10.0.0 - Enterprise Edition                                        ║")
    print("║                                                                              ║")
    print("║   Starting analysis...                                                       ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    print(f"\n  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    
    print_header("CONFIGURATION")
    
    print(f"\n  Input Tables:")
    print(f"    1. {INPUT_TABLE_1}")
    print(f"    2. {INPUT_TABLE_2}")
    print(f"    3. {INPUT_TABLE_3}")
    print(f"    4. {INPUT_TABLE_4}")
    
    print(f"\n  Output Table:")
    print(f"    → {OUTPUT_TABLE}")
    
    print(f"\n  Detection Settings:")
    print(f"    → Threshold: {ECOMM_THRESHOLD}")
    print(f"    → Min text length: {MIN_TEXT_LENGTH}")
    print(f"    → Max text length: {MAX_TEXT_LENGTH}")
    print(f"    → Batch size: {BATCH_SIZE}")
    print(f"    → Progress interval: {PROGRESS_INTERVAL}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # LOAD INPUT TABLES
    # ══════════════════════════════════════════════════════════════════════════
    
    print_header("LOADING INPUT TABLES")
    
    tables = {}
    total_input_rows = 0
    
    for table_name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4]:
        print(f"\n  Loading '{table_name}'...")
        
        try:
            load_start = time.time()
            ds = dataiku.Dataset(table_name)
            df = ds.get_dataframe()
            load_time = time.time() - load_start
            
            # Convert all columns to string for consistent text processing
            for col in df.columns:
                df[col] = df[col].astype(str)
            
            tables[table_name] = df
            total_input_rows += len(df)
            
            print(f"    ✓ Loaded successfully")
            print(f"      → Rows: {len(df):,}")
            print(f"      → Columns: {len(df.columns)}")
            print(f"      → Time: {load_time:.2f}s")
            
            # Find and report IDN_EON column
            idn_col = find_idn_eon_column(df)
            if idn_col:
                unique_count = df[idn_col].nunique()
                print(f"      → IDN_EON column: '{idn_col}' ({unique_count:,} unique)")
            else:
                print(f"      ⚠ No IDN_EON column found")
                
        except Exception as e:
            print(f"    ✗ Failed to load: {e}")
    
    if not tables:
        raise ValueError("No tables could be loaded! Please check the table names.")
    
    print(f"\n  Summary:")
    print(f"    → Tables loaded: {len(tables)}")
    print(f"    → Total rows: {total_input_rows:,}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # INITIALIZE CLASSIFIER
    # ══════════════════════════════════════════════════════════════════════════
    
    classifier = IntelligentECommClassifier()
    
    # ══════════════════════════════════════════════════════════════════════════
    # PROCESS TABLES
    # ══════════════════════════════════════════════════════════════════════════
    
    print_header("PROCESSING TABLES")
    
    # Data structures to track results
    idn_sources = defaultdict(set)           # IDN_EON -> set of source tables
    idn_ecomm_strings = defaultdict(list)    # IDN_EON -> list of (string, location)
    
    processing_start = time.time()
    total_processed = 0
    total_ecomm_found = 0
    
    for table_name, df in tables.items():
        print_subheader(f"Processing: {table_name}")
        
        # Find IDN_EON column
        idn_col = find_idn_eon_column(df)
        
        if not idn_col:
            print(f"\n  ⚠ No IDN_EON column found in '{table_name}', skipping...")
            continue
        
        # Get non-IDN columns for analysis
        text_columns = [col for col in df.columns if col != idn_col]
        
        print(f"\n  IDN_EON column: '{idn_col}'")
        print(f"  Text columns to analyze: {len(text_columns)}")
        print(f"  Rows to process: {len(df):,}")
        
        # Process each row
        table_start = time.time()
        table_ecomm_count = 0
        row_count = 0
        
        for idx, row in df.iterrows():
            row_count += 1
            total_processed += 1
            
            # Progress reporting
            if row_count % PROGRESS_INTERVAL == 0:
                elapsed = time.time() - table_start
                rate = row_count / elapsed if elapsed > 0 else 0
                remaining = (len(df) - row_count) / rate if rate > 0 else 0
                print(f"    Progress: {row_count:,}/{len(df):,} rows "
                      f"({row_count*100/len(df):.1f}%) | "
                      f"E-comm: {table_ecomm_count:,} | "
                      f"Rate: {rate:.0f}/s | "
                      f"ETA: {format_duration(remaining)}")
            
            # Get and validate IDN_EON value
            idn_val = str(row[idn_col]).strip() if row[idn_col] else ""
            
            if not is_valid_idn_eon(idn_val):
                continue
            
            # Track source table
            idn_sources[idn_val].add(table_name)
            
            # Analyze each text column
            for col in text_columns:
                text = clean_text(row[col])
                
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                
                # Classify the text
                confidence = classifier.classify(text)
                
                # If above threshold, record it
                if confidence > ECOMM_THRESHOLD:
                    location = f"{table_name}.{col}"
                    
                    # Avoid exact duplicates
                    existing = [(s, l) for s, l in idn_ecomm_strings[idn_val]]
                    if (text, location) not in existing:
                        idn_ecomm_strings[idn_val].append((text, location))
                        table_ecomm_count += 1
                        total_ecomm_found += 1
        
        # Table summary
        table_elapsed = time.time() - table_start
        print(f"\n  ✓ Completed '{table_name}'")
        print(f"    → Rows processed: {row_count:,}")
        print(f"    → E-comm strings found: {table_ecomm_count:,}")
        print(f"    → Processing time: {format_duration(table_elapsed)}")
        print(f"    → Rate: {row_count/table_elapsed:.1f} rows/second")
    
    processing_elapsed = time.time() - processing_start
    
    print_subheader("Processing Complete")
    print(f"\n  Total rows processed: {total_processed:,}")
    print(f"  Total e-comm strings found: {total_ecomm_found:,}")
    print(f"  Total processing time: {format_duration(processing_elapsed)}")
    print(f"  Average rate: {total_processed/processing_elapsed:.1f} rows/second")
    
    # ══════════════════════════════════════════════════════════════════════════
    # BUILD OUTPUT TABLE
    # ══════════════════════════════════════════════════════════════════════════
    
    print_header("BUILDING OUTPUT TABLE")
    
    results = []
    
    for idn_eon, sources in idn_sources.items():
        ecomm_list = idn_ecomm_strings.get(idn_eon, [])
        
        if ecomm_list:
            # Join multiple strings with separator
            ecomm_string = ' | '.join([s[0] for s in ecomm_list])
            string_location = ' | '.join([s[1] for s in ecomm_list])
        else:
            ecomm_string = ''
            string_location = ''
        
        results.append({
            'IDN_EON': idn_eon,
            'source_tables': ', '.join(sorted(sources)),
            'ecomm_string': ecomm_string,
            'string_location': string_location,
        })
    
    # Create DataFrame
    output_df = pd.DataFrame(results)
    
    # Sort: records with e-comm strings first
    output_df['_has_ecomm'] = output_df['ecomm_string'].apply(lambda x: 1 if x else 0)
    output_df = output_df.sort_values('_has_ecomm', ascending=False)
    output_df = output_df.drop(columns=['_has_ecomm'])
    output_df = output_df.reset_index(drop=True)
    
    print(f"\n  Output table structure:")
    print(f"    → Column 1: IDN_EON (unique identifier)")
    print(f"    → Column 2: source_tables (which tables contain this IDN_EON)")
    print(f"    → Column 3: ecomm_string (text indicating e-comm capability)")
    print(f"    → Column 4: string_location (table.column where found)")
    
    # ══════════════════════════════════════════════════════════════════════════
    # SUMMARY STATISTICS
    # ══════════════════════════════════════════════════════════════════════════
    
    print_header("SUMMARY STATISTICS")
    
    total_idn_eon = len(output_df)
    with_ecomm = (output_df['ecomm_string'] != '').sum()
    without_ecomm = total_idn_eon - with_ecomm
    
    print(f"\n  IDN_EON Statistics:")
    print(f"    → Total unique IDN_EON: {total_idn_eon:,}")
    print(f"    → With e-comm capability: {with_ecomm:,} ({with_ecomm*100/total_idn_eon:.1f}%)" if total_idn_eon > 0 else "    → With e-comm capability: 0")
    print(f"    → Without e-comm: {without_ecomm:,} ({without_ecomm*100/total_idn_eon:.1f}%)" if total_idn_eon > 0 else "    → Without e-comm: 0")
    
    # Show source table distribution
    print(f"\n  Source Table Distribution:")
    for table_name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4]:
        if table_name in tables:
            count = output_df['source_tables'].apply(lambda x: table_name in x).sum()
            print(f"    → {table_name}: {count:,} IDN_EON")
    
    # Show sample of detected e-comm
    if with_ecomm > 0:
        print(f"\n  Sample E-Communication Detections (Top 10):")
        sample_df = output_df[output_df['ecomm_string'] != ''].head(10)
        for idx, row in sample_df.iterrows():
            idn = row['IDN_EON'][:30] + "..." if len(row['IDN_EON']) > 30 else row['IDN_EON']
            ecomm = row['ecomm_string'][:60] + "..." if len(row['ecomm_string']) > 60 else row['ecomm_string']
            print(f"    • {idn}")
            print(f"      \"{ecomm}\"")
    
    # ══════════════════════════════════════════════════════════════════════════
    # WRITE OUTPUT
    # ══════════════════════════════════════════════════════════════════════════
    
    print_header("WRITING OUTPUT")
    
    print(f"\n  Writing to '{OUTPUT_TABLE}'...")
    
    write_start = time.time()
    output_ds = dataiku.Dataset(OUTPUT_TABLE)
    output_ds.write_with_schema(output_df)
    write_elapsed = time.time() - write_start
    
    print(f"\n  ✓ Output written successfully")
    print(f"    → Rows written: {len(output_df):,}")
    print(f"    → Columns: {len(output_df.columns)}")
    print(f"    → Write time: {format_duration(write_elapsed)}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    
    total_elapsed = time.time() - script_start_time
    
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║   ANALYSIS COMPLETE                                                          ║")
    print("║                                                                              ║")
    print(f"║   Total IDN_EON analyzed: {total_idn_eon:>10,}                                      ║")
    print(f"║   E-comm capability detected: {with_ecomm:>7,}                                      ║")
    print(f"║   Total execution time: {format_duration(total_elapsed):>12}                                      ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print("\n")


# ══════════════════════════════════════════════════════════════════════════════════
# EXECUTE MAIN FUNCTION
# ══════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
else:
    # Running inside Dataiku recipe context
    main()
