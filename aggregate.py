# -*- coding: utf-8 -*-
# ================================================================================
# input and output tables - configure these
# ================================================================================

INPUT_TABLE_1 = 'table1'
INPUT_TABLE_2 = 'table2'
INPUT_TABLE_3 = 'table3'
INPUT_TABLE_4 = 'table4'
INPUT_TABLE_5 = 'table5'

OUTPUT_TABLE = 'ecomm_detection_results'

# ================================================================================
# detection settings
# ================================================================================

# tfidf confidence threshold (0.0 to 1.0)
# lower = more lenient, higher = stricter
CONFIDENCE_THRESHOLD = 0.52

# ================================================================================
# false positives - strings incorrectly flagged (add as you find them)
# ================================================================================

FALSE_POSITIVES = [
]

# ================================================================================
# false negatives - strings that should be flagged (add as you find them)
# ================================================================================

FALSE_NEGATIVES = [
]

# ================================================================================
# end of configuration
# ================================================================================

import dataiku
import pandas as pd
import numpy as np
import re
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ================================================================================
# training data: e-communication capability examples
# these describe apps that CAN send/facilitate communication
# ================================================================================

ECOMM_EXAMPLES = [
    # email sending
    "users can send emails to each other",
    "app sends email notifications to customers",
    "email delivery system for marketing campaigns",
    "sends automated email alerts",
    "customers receive order confirmation emails",
    "newsletter sent to subscribers",
    "bulk email capability",
    "transactional emails are delivered",
    "email blast feature",
    "compose and send email messages",
    "outbound email system",
    "email communication platform",
    "drip email campaigns",
    "sends welcome emails to new users",
    "promotional emails delivered to inbox",
    "reply to customer emails",
    "email correspondence with clients",
    "automated email responses",
    "email marketing platform",
    "sends reminder emails",
    
    # sms and text
    "sends sms messages to users",
    "text message alerts",
    "sms notification system",
    "customers receive text updates",
    "bulk sms capability",
    "sends appointment reminders via text",
    "sms marketing campaigns",
    "text messaging platform",
    "mobile text alerts",
    "sends shipping notifications via sms",
    "two-way sms communication",
    "text message broadcasting",
    "sms gateway integration",
    "sends promotional texts",
    "mms messaging support",
    
    # video and voice calls
    "video calling feature",
    "users can make video calls",
    "voice call capability",
    "video conferencing platform",
    "voip phone system",
    "make phone calls through the app",
    "video chat between users",
    "audio calling feature",
    "conference call capability",
    "screen sharing with video",
    "one-on-one video calls",
    "group video meetings",
    "webrtc video communication",
    "sip calling support",
    "telephone integration",
    "caller can reach support",
    "dial customers directly",
    "voice communication platform",
    
    # instant messaging and chat
    "instant messaging between users",
    "real-time chat feature",
    "users can message each other",
    "direct messaging capability",
    "in-app chat system",
    "private messaging",
    "group chat functionality",
    "live chat support",
    "chat with customer service",
    "messaging platform",
    "send and receive messages",
    "conversation threads",
    "chat rooms",
    "peer to peer messaging",
    "team messaging",
    "chat widget",
    "chatbot responds to users",
    "dialogue with customers",
    "correspondence through app",
    "communicate with other users",
    
    # push notifications
    "sends push notifications",
    "mobile push alerts",
    "app notifications delivered",
    "push notification system",
    "real-time alerts to devices",
    "notifies users of updates",
    "push messages to mobile",
    "notification delivery platform",
    "alerts sent to users",
    "broadcast notifications",
    
    # general communication
    "e-communication capability",
    "electronic communication platform",
    "unified communications",
    "omnichannel messaging",
    "multi-channel communication",
    "customer outreach platform",
    "facilitates communication between parties",
    "enables users to reach out",
    "contact customers directly",
    "communication hub",
    "outbound communication system",
    "lets users connect and communicate",
    "platform for client correspondence",
    "users can ping each other",
    "reach out to customers",
    "broadcast updates to subscribers",
    "announcement system",
    "bulletin distribution",
    "mass communication feature",
    "customer engagement platform",
    
    # inbox/compose features
    "inbox for messages",
    "outbox shows sent items",
    "compose new message",
    "reply to messages",
    "forward emails",
    "message drafts",
    "sent folder",
    "mailbox feature",
    "recipient selection",
    "address book for contacts",
]

# ================================================================================
# training data: not e-communication (just data/storage/display)
# ================================================================================

NOT_ECOMM_EXAMPLES = [
    # data collection
    "collects email addresses",
    "stores phone numbers",
    "gathers contact information",
    "email field in database",
    "captures user email",
    "saves email for records",
    "phone number storage",
    "email data collection",
    "retains email addresses",
    "logs contact details",
    "email is recorded",
    "stores customer phone",
    "contact information saved",
    "email kept on file",
    "maintains email list",
    
    # form fields
    "email input field",
    "enter your email address",
    "phone number textbox",
    "email form field",
    "provide your email",
    "fill in email",
    "email is required",
    "phone field optional",
    "type your email",
    "submit email address",
    "email entry form",
    "input phone number",
    
    # database schema
    "email varchar column",
    "phone number table",
    "email field type string",
    "contact column in database",
    "email primary key",
    "phone data type",
    "email schema definition",
    "text field for email",
    "email column index",
    "phone number format",
    
    # authentication
    "login with email",
    "email as username",
    "sign in using email",
    "register with email",
    "email for account creation",
    "phone verification",
    "email authentication",
    "signin requires email",
    "account email address",
    "email used for login",
    
    # verification codes
    "sms verification code",
    "email confirmation code",
    "two factor authentication",
    "otp sent via text",
    "verification pin",
    "2fa code",
    "mfa via sms",
    "one time password",
    "security code via email",
    "confirm email address",
    
    # validation
    "validates email format",
    "checks phone number",
    "email syntax validation",
    "verify email address",
    "phone format check",
    "valid email required",
    "email regex pattern",
    "phone validation rule",
    "invalid email error",
    "malformed email address",
    
    # display only
    "displays user email",
    "shows phone number",
    "email visible in profile",
    "contact info displayed",
    "view email address",
    "phone shown on screen",
    "email in account settings",
    "displays contact details",
    "email appears in header",
    "shows customer phone",
    
    # settings and preferences
    "email notification settings",
    "phone preferences",
    "opt out of emails",
    "unsubscribe from notifications",
    "email frequency settings",
    "notification preferences",
    "disable email alerts",
    "manage phone settings",
    "opt in to texts",
    "email subscription options",
    
    # logs and history
    "email audit log",
    "call history records",
    "message log table",
    "notification history",
    "email delivery log",
    "phone call records",
    "communication log",
    "message archive",
    "email trail",
    "contact history",
    
    # templates
    "email template",
    "message template",
    "notification template",
    "sms template",
    "email format template",
    "standard email template",
    "template for messages",
    
    # errors
    "email bounce",
    "failed delivery",
    "invalid phone",
    "email error",
    "undeliverable message",
    "phone not found",
    "email rejected",
    "spam filter",
    "blocked email",
    
    # technical
    "smtp server",
    "email protocol",
    "pop3 configuration",
    "imap settings",
    "mail server",
    "mx record",
    "email routing",
    "phone carrier",
    "sip trunk",
]

# ================================================================================
# fast pre-filter keywords - must have at least one to be a candidate
# ================================================================================

PREFILTER_KEYWORDS = [
    'email', 'e-mail', 'mail',
    'sms', 'mms', 'text',
    'message', 'messaging', 'msg',
    'call', 'calling', 'caller', 'phone', 'telephone', 'dial',
    'video', 'voice', 'voip', 'audio',
    'chat', 'chatting',
    'notification', 'notify', 'alert',
    'push',
    'communication', 'communicate', 'contact', 'reach',
    'inbox', 'outbox', 'compose', 'reply', 'forward', 'draft',
    'conversation', 'thread', 'dialogue', 'correspondence',
    'conference', 'meeting',
    'broadcast', 'announcement', 'bulletin',
    'subscriber', 'recipient',
    'twilio', 'sendgrid', 'mailchimp', 'mailgun',
    'webrtc', 'sip',
]

INVALID_IDN = {'nan', 'none', '', 'null', 'n/a', 'na', '-', 'unknown', ' ', 'undefined', 'test', 'example'}

# learned patterns
FALSE_POS_SET = set(x.lower().strip() for x in FALSE_POSITIVES if x and x.strip())
FALSE_NEG_SET = set(x.lower().strip() for x in FALSE_NEGATIVES if x and x.strip())

# ================================================================================
# tfidf classifier
# ================================================================================

class SemanticClassifier:
    def __init__(self):
        print("building semantic classifier...")
        
        # combine training data
        all_texts = ECOMM_EXAMPLES + NOT_ECOMM_EXAMPLES
        
        # create labels (1 = ecomm, 0 = not ecomm)
        self.labels = [1] * len(ECOMM_EXAMPLES) + [0] * len(NOT_ECOMM_EXAMPLES)
        
        # build tfidf vectorizer
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            min_df=1,
            max_df=0.95,
            stop_words='english',
            sublinear_tf=True,
        )
        
        # fit and transform training data
        self.train_vectors = self.vectorizer.fit_transform(all_texts)
        
        # pre-compute centroids for each class
        ecomm_vectors = self.train_vectors[:len(ECOMM_EXAMPLES)]
        not_ecomm_vectors = self.train_vectors[len(ECOMM_EXAMPLES):]
        
        self.ecomm_centroid = np.asarray(ecomm_vectors.mean(axis=0)).flatten()
        self.not_ecomm_centroid = np.asarray(not_ecomm_vectors.mean(axis=0)).flatten()
        
        print(f"  vocabulary size: {len(self.vectorizer.vocabulary_)}")
        print(f"  ecomm examples: {len(ECOMM_EXAMPLES)}")
        print(f"  not ecomm examples: {len(NOT_ECOMM_EXAMPLES)}")
    
    def get_confidence(self, text):
        """
        get confidence score that text indicates e-comm capability.
        returns float from 0 to 1.
        """
        if not text or len(text) < 10:
            return 0.0
        
        # transform text
        text_vector = self.vectorizer.transform([text])
        text_arr = np.asarray(text_vector.toarray()).flatten()
        
        # compute similarity to each centroid
        ecomm_sim = self._cosine_sim(text_arr, self.ecomm_centroid)
        not_ecomm_sim = self._cosine_sim(text_arr, self.not_ecomm_centroid)
        
        # also compute max similarity to individual examples
        all_sims = cosine_similarity(text_vector, self.train_vectors).flatten()
        
        # get top similarities for each class
        ecomm_sims = all_sims[:len(ECOMM_EXAMPLES)]
        not_ecomm_sims = all_sims[len(ECOMM_EXAMPLES):]
        
        ecomm_max = np.max(ecomm_sims) if len(ecomm_sims) > 0 else 0
        not_ecomm_max = np.max(not_ecomm_sims) if len(not_ecomm_sims) > 0 else 0
        
        ecomm_top3 = np.mean(sorted(ecomm_sims, reverse=True)[:3])
        not_ecomm_top3 = np.mean(sorted(not_ecomm_sims, reverse=True)[:3])
        
        # combine scores
        ecomm_score = 0.3 * ecomm_sim + 0.4 * ecomm_max + 0.3 * ecomm_top3
        not_ecomm_score = 0.3 * not_ecomm_sim + 0.4 * not_ecomm_max + 0.3 * not_ecomm_top3
        
        # normalize to probability
        total = ecomm_score + not_ecomm_score
        if total == 0:
            return 0.5
        
        return ecomm_score / total
    
    def _cosine_sim(self, v1, v2):
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

# ================================================================================
# helper functions
# ================================================================================

def has_keyword(text_lower):
    """fast check if text has any communication keyword."""
    for kw in PREFILTER_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def find_idn_col(df):
    """find idn_eon column case-insensitively."""
    for col in df.columns:
        normalized = col.upper().replace(' ', '_').replace('-', '_')
        if 'IDN_EON' in normalized:
            return col
    return None

# ================================================================================
# main
# ================================================================================

print("=" * 60)
print("e-communication capability detection")
print("hybrid: fast keyword filter + tfidf semantic analysis")
print("=" * 60)

# initialize classifier
classifier = SemanticClassifier()

# load tables
tables = {}
for name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4, INPUT_TABLE_5]:
    try:
        df = dataiku.Dataset(name).get_dataframe()
        for c in df.columns:
            df[c] = df[c].astype(str)
        tables[name] = df
        print(f"[ok] {name}: {len(df):,} rows")
    except Exception as e:
        print(f"[fail] {name}: {e}")

if not tables:
    raise ValueError("no tables loaded")

# process tables
print("\nprocessing (keyword filter -> tfidf on candidates)...")

idn_sources = defaultdict(set)
idn_ecomm = defaultdict(list)
total_rows = 0
candidates_analyzed = 0

for tname, df in tables.items():
    idn_col = find_idn_col(df)
    if not idn_col:
        print(f"  [warn] {tname}: no idn_eon column")
        continue
    
    other_cols = [c for c in df.columns if c != idn_col]
    ecomm_count = 0
    table_candidates = 0
    
    for idx, row in df.iterrows():
        total_rows += 1
        if total_rows % 5000 == 0:
            print(f"  {total_rows:,} rows, {candidates_analyzed:,} candidates analyzed...")
        
        idn_val = str(row[idn_col]).strip()
        if idn_val.lower() in INVALID_IDN:
            continue
        
        idn_sources[idn_val].add(tname)
        
        for col in other_cols:
            txt = str(row[col]).strip()
            txt_lower = txt.lower()
            
            # check learned false positives first
            skip = False
            for fp in FALSE_POS_SET:
                if fp and fp in txt_lower:
                    skip = True
                    break
            if skip:
                continue
            
            # check learned false negatives (always accept)
            force_accept = False
            for fn in FALSE_NEG_SET:
                if fn and fn in txt_lower:
                    force_accept = True
                    break
            
            if force_accept:
                loc = f"{tname}.{col}"
                if (txt, loc) not in idn_ecomm[idn_val]:
                    idn_ecomm[idn_val].append((txt, loc))
                    ecomm_count += 1
                continue
            
            # fast keyword filter
            if not has_keyword(txt_lower):
                continue
            
            # passed keyword filter - run tfidf analysis
            table_candidates += 1
            candidates_analyzed += 1
            
            confidence = classifier.get_confidence(txt)
            
            if confidence >= CONFIDENCE_THRESHOLD:
                loc = f"{tname}.{col}"
                if (txt, loc) not in idn_ecomm[idn_val]:
                    idn_ecomm[idn_val].append((txt, loc))
                    ecomm_count += 1
    
    print(f"  [ok] {tname}: {table_candidates:,} candidates, {ecomm_count:,} e-comm found")

print(f"\ntotal rows: {total_rows:,}")
print(f"candidates analyzed with tfidf: {candidates_analyzed:,}")
print(f"tfidf ran on {100*candidates_analyzed/total_rows:.1f}% of rows")

# build output
print("\nbuilding output...")

results = []
for idn, ecomm_list in idn_ecomm.items():
    if ecomm_list:
        sources = idn_sources.get(idn, set())
        results.append({
            'IDN_EON': idn,
            'source_tables': ', '.join(sorted(sources)),
            'ecomm_string': ' | '.join([s[0] for s in ecomm_list]),
            'string_location': ' | '.join([s[1] for s in ecomm_list]),
        })

output_df = pd.DataFrame(results)

print(f"\ntotal idn_eon with e-comm capability: {len(output_df):,}")

if len(output_df) > 0:
    print("\nsample detections:")
    for idx, row in output_df.head(5).iterrows():
        idn_short = row['IDN_EON'][:30] + "..." if len(row['IDN_EON']) > 30 else row['IDN_EON']
        ecomm_short = row['ecomm_string'][:70] + "..." if len(row['ecomm_string']) > 70 else row['ecomm_string']
        print(f"  - {idn_short}")
        print(f"    \"{ecomm_short}\"")

print(f"\nwriting to {OUTPUT_TABLE}...")
dataiku.Dataset(OUTPUT_TABLE).write_with_schema(output_df)
print("[ok] done")
