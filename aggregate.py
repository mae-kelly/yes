# -*- coding: utf-8 -*-
# ================================================================================
# INPUT AND OUTPUT TABLES - CONFIGURE THESE
# ================================================================================

INPUT_TABLE_1 = 'table1'
INPUT_TABLE_2 = 'table2'
INPUT_TABLE_3 = 'table3'
INPUT_TABLE_4 = 'table4'

OUTPUT_TABLE = 'ecomm_detection_results'

# ================================================================================
# FALSE POSITIVES - Add strings that incorrectly trigger detection
# ================================================================================

FALSE_POSITIVES = [
    # "message queue processing",
]

# ================================================================================
# FALSE NEGATIVES - Add strings that should trigger but don't
# ================================================================================

FALSE_NEGATIVES = [
    # "proprietary messaging system",
]

# ================================================================================
# END OF CONFIGURATION
# ================================================================================

import dataiku
import pandas as pd
import re
from collections import defaultdict

# Patterns that REJECT (data collection, not e-comm)
REJECT_PATTERNS = [
    r'email\s*,\s*phone', r'phone\s*,\s*email', r'name\s*,\s*email',
    r'collects?\s+(?:email|phone)', r'gathers?\s+(?:email|phone)',
    r'stores?\s+(?:email|phone)', r'captures?\s+(?:email|phone)',
    r'login\s+(?:with|using)\s+email', r'sign\s+in\s+(?:with|using)\s+email',
    r'email\s+(?:required|needed)\s+for', r'register\s+(?:with|using)\s+email',
    r'email\s+(?:field|input|textbox)', r'enter\s+(?:your\s+)?email',
    r'(?:varchar|text)\s+.*email', r'email\s+(?:column|field)\s+in',
    r'validates?\s+email', r'verif(?:y|ies)\s+email',
    r'(?:sms|text)\s+verification', r'2fa\s+via', r'otp',
    r'displays?\s+(?:email|phone)', r'email\s+optional',
]

# Patterns that ACCEPT (e-comm capability)
ACCEPT_PATTERNS = [
    r'e[-\s]?communication', r'electronic\s+communication',
    r'(?:can|able\s+to)\s+send\s+(?:email|text|message|sms)',
    r'(?:user|app)s?\s+sends?\s+(?:email|notification|text|sms|alert)',
    r'sends?\s+(?:email|text|sms)\s+(?:notification|alert|message)',
    r'(?:email|sms|text)\s+(?:sending|delivery)\s+(?:capability|feature)',
    r'video\s+call(?:ing)?', r'voice\s+call(?:ing)?',
    r'video\s+(?:conferencing|chat)', r'voip',
    r'instant\s+messag', r'real[- ]?time\s+(?:messaging|chat)',
    r'(?:direct|in[- ]?app)\s+messag', r'chat\s+(?:feature|capability|enabled)',
    r'users?\s+(?:can\s+)?message\s+each\s+other',
    r'sends?\s+push\s+notification', r'push\s+notification\s+(?:capability|feature)',
    r'(?:mobile|app)\s+notification(?:s)?\s+(?:enabled|sent)',
]

# Keywords required for any analysis
KEYWORDS = ['email', 'text', 'sms', 'message', 'call', 'phone', 'video', 
            'voice', 'chat', 'notification', 'alert', 'push', 'communicat', 'voip']

INVALID_IDN = {'nan', 'none', '', 'null', 'n/a', 'na', '-', 'unknown', ' '}

# Compile patterns once
REJECT_RE = [re.compile(p, re.IGNORECASE) for p in REJECT_PATTERNS]
ACCEPT_RE = [re.compile(p, re.IGNORECASE) for p in ACCEPT_PATTERNS]
FALSE_POS = set(x.lower().strip() for x in FALSE_POSITIVES if x.strip())
FALSE_NEG = set(x.lower().strip() for x in FALSE_NEGATIVES if x.strip())

def is_ecomm(text):
    """Fast pattern-based classification."""
    if not text or len(text) < 5:
        return False
    
    text_lower = text.lower()
    
    # Check learned patterns
    if any(fp in text_lower for fp in FALSE_POS if fp):
        return False
    if any(fn in text_lower for fn in FALSE_NEG if fn):
        return True
    
    # Must have keyword
    if not any(kw in text_lower for kw in KEYWORDS):
        return False
    
    # Check reject patterns
    for p in REJECT_RE:
        if p.search(text_lower):
            return False
    
    # Check accept patterns
    for p in ACCEPT_RE:
        if p.search(text_lower):
            return True
    
    return False

def find_idn_col(df):
    for col in df.columns:
        if 'IDN_EON' in col.upper().replace(' ','_').replace('-','_'):
            return col
    return None

# ================================================================================
# MAIN
# ================================================================================

print("=" * 60)
print("E-COMMUNICATION DETECTION (Fast Mode)")
print("=" * 60)

# Load tables
tables = {}
for name in [INPUT_TABLE_1, INPUT_TABLE_2, INPUT_TABLE_3, INPUT_TABLE_4]:
    try:
        df = dataiku.Dataset(name).get_dataframe()
        for c in df.columns:
            df[c] = df[c].astype(str)
        tables[name] = df
        print(f"✓ {name}: {len(df):,} rows")
    except Exception as e:
        print(f"✗ {name}: {e}")

if not tables:
    raise ValueError("No tables loaded!")

# Process
print("\nProcessing...")

idn_sources = defaultdict(set)
idn_ecomm = defaultdict(list)
total_rows = 0

for tname, df in tables.items():
    idn_col = find_idn_col(df)
    if not idn_col:
        print(f"  ⚠ {tname}: No IDN_EON column")
        continue
    
    other_cols = [c for c in df.columns if c != idn_col]
    ecomm_count = 0
    
    for idx, row in df.iterrows():
        total_rows += 1
        if total_rows % 5000 == 0:
            print(f"  {total_rows:,} rows processed...")
        
        idn_val = str(row[idn_col]).strip()
        if idn_val.lower() in INVALID_IDN:
            continue
        
        idn_sources[idn_val].add(tname)
        
        for col in other_cols:
            txt = str(row[col]).strip()
            if is_ecomm(txt):
                loc = f"{tname}.{col}"
                if (txt, loc) not in idn_ecomm[idn_val]:
                    idn_ecomm[idn_val].append((txt, loc))
                    ecomm_count += 1
    
    print(f"  ✓ {tname}: {ecomm_count:,} e-comm strings")

# Build output
print("\nBuilding output...")

results = []
for idn, sources in idn_sources.items():
    ecomm_list = idn_ecomm.get(idn, [])
    results.append({
        'IDN_EON': idn,
        'source_tables': ', '.join(sorted(sources)),
        'ecomm_string': ' | '.join([s[0] for s in ecomm_list]) if ecomm_list else '',
        'string_location': ' | '.join([s[1] for s in ecomm_list]) if ecomm_list else '',
    })

output_df = pd.DataFrame(results)
output_df['_sort'] = output_df['ecomm_string'].apply(lambda x: 0 if x else 1)
output_df = output_df.sort_values('_sort').drop(columns=['_sort']).reset_index(drop=True)

# Summary
has_ecomm = (output_df['ecomm_string'] != '').sum()
print(f"\nTotal IDN_EON: {len(output_df):,}")
print(f"With e-comm: {has_ecomm:,}")
print(f"Without: {len(output_df) - has_ecomm:,}")

# Write
print(f"\nWriting to {OUTPUT_TABLE}...")
dataiku.Dataset(OUTPUT_TABLE).write_with_schema(output_df)
print("✓ Done!")
