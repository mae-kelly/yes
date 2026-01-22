# Import the dataiku package
import dataiku
import pandas as pd

# Read the input dataset
input_dataset = dataiku.Dataset("your_input_dataset_name")
df = input_dataset.get_dataframe()

# Get all distinct values from ONETWOTHREE column
distinct_values = df['ONETWOTHREE'].unique()

# Create indicator columns for each distinct ONETWOTHREE value
for value in distinct_values:
    col_name = f"ONETWOTHREE_{value}"
    df[col_name] = df.groupby('EON_IDN')['ONETWOTHREE'].transform(
        lambda x: 'yes' if value in x.values else ''
    )

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

# Write the output dataset
output_dataset = dataiku.Dataset("your_output_dataset_name")
output_dataset.write_with_schema(final_df)
