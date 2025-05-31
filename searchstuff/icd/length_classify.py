import pandas as pd

# Load original data
df = pd.read_csv('classified_diseases_live.csv')

# Filter by disease category
common_df = df[df['Category'].str.contains("Common Diseases/Conditions", na=False)]
emergency_df = df[df['Category'].str.contains("Emergency Diseases/Conditions", na=False)]
rare_df = df[df['Category'].str.contains("Rare Diseases/Conditions", na=False)]

# Randomly sample each group
common_sample = common_df.sample(n=500, random_state=42)
emergency_sample = emergency_df.sample(n=300, random_state=42)
rare_sample = rare_df.sample(n=200, random_state=42)

# Concatenate all samples
balanced_df = pd.concat([common_sample, emergency_sample, rare_sample])

# Optional: Shuffle the final dataset
balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save to new CSV
balanced_df.to_csv('datasets/balanced_diseases_sample2.csv', index=False)

print("✅ Balanced dataset created and saved to 'balanced_diseases_sample.csv'")