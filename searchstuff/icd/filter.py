import pandas as pd

# Load the Excel file
df = pd.read_excel('SimpleTabulation-ICD-11-MMS-en.xlsx')

# Filter for codeable disease categories
filtered_df = df[(df['ClassKind'] == 'category') & (df['isLeaf'] == True)]

# Clean up the Title column by removing leading dashes and spaces
filtered_df['Title'] = filtered_df['Title'].str.replace(r'^[-\s–]+', '', regex=True)

# Limit to desired columns
filtered_df = filtered_df[['Code', 'Title', 'isLeaf', 'ClassKind']]

# Save to CSV
filtered_df.to_csv('icd_codes.csv', index=False)