# -*- coding: utf-8 -*-
import dataiku
import pandas as pd

# Input datasets
dataset1 = dataiku.Dataset("dataset1_name")
dataset2 = dataiku.Dataset("dataset2_name")

# Output dataset
output = dataiku.Dataset("output_name")

# Read the datasets
df1 = dataset1.get_dataframe()
df2 = dataset2.get_dataframe()

# Get unique idn_eon values from dataset2
idn_eon_set = set(df2['idn_eon'].unique())

# Filter dataset1 to only include rows where idn_eon is in dataset2
filtered_df = df1[df1['idn_eon'].isin(idn_eon_set)]

# Write the filtered data to output
output.write_with_schema(filtered_df)
