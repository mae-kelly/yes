# Import the dataiku package
import dataiku
import pandas as pd

# Read the input dataset
input_dataset = dataiku.Dataset("Active_DLM_Plan_Responses")
df = input_dataset.get_dataframe()

# Get all distinct values from TXT_DATA_LIFCYCL_MANG_QSTN column
distinct_values = df['TXT_DATA_LIFCYCL_MANG_QSTN'].unique()

# Create indicator columns for each distinct value
for value in distinct_values:
    col_name = f"TXT_DATA_LIFCYCL_MANG_QSTN_{value}"
    
    # Truncate column name to 255 characters if needed
    if len(col_name) > 255:
        col_name = col_name[:255]
    
    # Create a new column with default empty strings
    df[col_name] = ''
    
    # Fill the new column with appropriate values
    # Filter for rows matching this question value
    mask = df['TXT_DATA_LIFCYCL_MANG_QSTN'] == value
    
    # For each IDN_EON, get the latest answer based on DT2_START
    for idn in df[mask]['IDN_EON'].unique():
        idn_mask = (df['IDN_EON'] == idn) & (df['TXT_DATA_LIFCYCL_MANG_QSTN'] == value)
        
        # Get the row with the maximum DT2_START for this IDN_EON and question
        latest_idx = df[idn_mask]['DT2_START'].idxmax()
        latest_answer = df.loc[latest_idx, 'TXT_DATA_LIFCYCL_MANG_ANSW']
        
        # Set the answer for all rows with this IDN_EON
        df.loc[df['IDN_EON'] == idn, col_name] = latest_answer

# Define aggregation functions for original columns
agg_dict = {}

for col in df.columns:
    if col == 'IDN_EON':
        continue
    elif col == 'TXT_DATA_LIFCYCL_MANG_QSTN':
        continue
    elif col.startswith('TXT_DATA_LIFCYCL_MANG_QSTN_'):
        agg_dict[col] = 'first'  # All same per group
    else:
        # Use a lambda function to join unique values
        agg_dict[col] = lambda x: ', '.join(x.dropna().astype(str).unique())

# Group by IDN_EON
final_df = df.groupby('IDN_EON', as_index=False).agg(agg_dict)

# Rename columns in final dataframe to ensure they're all under 255 characters
final_df.columns = [col[:255] if len(col) > 255 else col for col in final_df.columns]

# Write the output dataset
output_dataset = dataiku.Dataset("separated_values")
output_dataset.write_with_schema(final_df)
