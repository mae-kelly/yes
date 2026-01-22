# Import the dataiku package
import dataiku
import pandas as pd

# Read the input dataset
input_dataset = dataiku.Dataset("your_input_dataset_name")
df = input_dataset.get_dataframe()

# Get all distinct values from ONETWOTHREE column
distinct_values = df['ONETWOTHREE'].unique()

# Create indicator columns for each distinct ONETWOTHREE value with ONEONEONE values
for value in distinct_values:
    col_name = f"ONETWOTHREE_{value}"
    # Truncate column name to 255 characters if needed
    if len(col_name) > 255:
        col_name = col_name[:255]
    
    df[col_name] = df.groupby('EON_IDN').apply(
        lambda group: 'yes, ONEONEONE value: ' + ', '.join(
            group.loc[group['ONETWOTHREE'] == value, 'ONEONEONE'].astype(str).unique()
        ) if value in group['ONETWOTHREE'].values else ''
    ).values

# Define aggregation functions for original columns
agg_dict = {}

for col in df.columns:
    if col == 'EON_IDN':
        continue
    elif col == 'ONETWOTHREE':
        continue
    elif col.startswith('ONETWOTHREE_'):
        agg_dict[col] = 'first'  # All same per group
    else:
        # For other columns, you can choose:
        # 'first' - keep first value
        # 'last' - keep last value
        # lambda x: ', '.join(x.astype(str).unique()) - concatenate unique values
        # lambda x: ', '.join(x.astype(str)) - concatenate all values
        agg_dict[col] = lambda x: ', '.join(x.astype(str).unique())

# Group by EON_IDN
final_df = df.groupby('EON_IDN', as_index=False).agg(agg_dict)

# Rename columns in final dataframe to ensure they're all under 255 characters
final_df.columns = [col[:255] if len(col) > 255 else col for col in final_df.columns]

# Write the output dataset
output_dataset = dataiku.Dataset("your_output_dataset_name")
output_dataset.write_with_schema(final_df)
