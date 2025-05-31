import pandas as pd
import re

# Load your CSV file
df = pd.read_csv('datasets/balanced_diseases_sample2.csv')

# Function to clean the 'Title' column - remove commas
def clean_title(text):
    if isinstance(text, str):
        text = text.replace(',', '')  # Remove commas
        text = text.replace('"', '')  # Remove double quotes
        text = re.sub(r"\s*\([^)]*\)", "", text)  # Remove content inside brackets like (TM1)
    return text

# Apply to 'Title' only
df['Title'] = df['Title'].apply(clean_title)

# Save normally with quotes where needed (default)
df.to_csv('datasets/classified_diseases_cleaned.csv', index=False)

print("✅ Cleaned 'Title' column (removed commas) and saved to 'classified_diseases_cleaned.csv'")