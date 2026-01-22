# -*- coding: utf-8 -*-

import dataiku
import pandas as pd
from dataiku import pandasutils as pdu

# Input datasets

output_dataset = dataiku.Dataset(“your_output_dataset_name”)  # Replace with your output dataset name
archive_inventory = dataiku.Dataset(“your_archive_inventory_name”)  # Replace with your archive inventory dataset name

# Read the datasets

df_output = output_dataset.get_dataframe()
df_archive = archive_inventory.get_dataframe()

# Get unique IDN_EON values from the archive inventory

archive_idn_eon_set = set(df_archive[‘IDN_EON’].dropna())

# Create the PRESENT_IN_ARCHIVE_INVENTORY column

df_output[‘PRESENT_IN_ARCHIVE_INVENTORY’] = df_output[‘IDN_EON’].apply(
lambda x: ‘YES’ if pd.notna(x) and x in archive_idn_eon_set else ‘NO’
)

# Reorder columns to place PRESENT_IN_ARCHIVE_INVENTORY as the 2nd column

cols = df_output.columns.tolist()

# Remove the new column from its current position

cols.remove(‘PRESENT_IN_ARCHIVE_INVENTORY’)

# Insert it at position 1 (2nd column, 0-indexed)

cols.insert(1, ‘PRESENT_IN_ARCHIVE_INVENTORY’)
df_output = df_output[cols]

# Write to output dataset - replace with your actual output dataset name

output = dataiku.Dataset(“your_output_dataset_name_here”)
output.write_with_schema(df_output)

print(f”Processing complete!”)
print(f”Total records: {len(df_output)}”)
print(f”Records present in archive: {(df_output[‘PRESENT_IN_ARCHIVE_INVENTORY’] == ‘YES’).sum()}”)
print(f”Records NOT present in archive: {(df_output[‘PRESENT_IN_ARCHIVE_INVENTORY’] == ‘NO’).sum()}”)