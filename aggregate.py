# -*- coding: utf-8 -*-

import dataiku
import pandas as pd

# Read input datasets

print(“Reading input datasets…”)

lcd_in_scope = dataiku.Dataset(“lcd_in_scope”)
risk_b_output = dataiku.Dataset(“Risk_B_Output_2_prepared”)

df_output = lcd_in_scope.get_dataframe()
df_archive = risk_b_output.get_dataframe()

print(f”lcd_in_scope shape: {df_output.shape}”)
print(f”Risk_B_Output_2_prepared shape: {df_archive.shape}”)

# Get unique IDN_EON values from the archive inventory

print(“Creating IDN_EON lookup set…”)
archive_idn_eon_set = set(df_archive[‘IDN_EON’].dropna())
print(f”Unique IDN_EON values in archive: {len(archive_idn_eon_set)}”)

# Create the PRESENT_IN_ARCHIVE_INVENTORY column

print(“Adding PRESENT_IN_ARCHIVE_INVENTORY column…”)
df_output[‘PRESENT_IN_ARCHIVE_INVENTORY’] = df_output[‘IDN_EON’].apply(
lambda x: ‘YES’ if pd.notna(x) and x in archive_idn_eon_set else ‘NO’
)

# Reorder columns to place PRESENT_IN_ARCHIVE_INVENTORY as the 2nd column

print(“Reordering columns…”)
cols = df_output.columns.tolist()
cols.remove(‘PRESENT_IN_ARCHIVE_INVENTORY’)
cols.insert(1, ‘PRESENT_IN_ARCHIVE_INVENTORY’)
df_output = df_output[cols]

print(f”Final dataframe shape: {df_output.shape}”)
print(f”First 5 columns: {df_output.columns.tolist()[:5]}”)

# Write to output dataset

print(“Writing to output dataset…”)
output_dataset = dataiku.Dataset(“in_scope_vs_archive_inventory”)
output_dataset.write_with_schema(df_output)

print(f”\nProcessing complete!”)
print(f”Total records: {len(df_output)}”)
print(f”Records present in archive: {(df_output[‘PRESENT_IN_ARCHIVE_INVENTORY’] == ‘YES’).sum()}”)
print(f”Records NOT present in archive: {(df_output[‘PRESENT_IN_ARCHIVE_INVENTORY’] == ‘NO’).sum()}”)