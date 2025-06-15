import pandas as pd

df = pd.read_csv("true1.csv")

# Filter for common diseases only
common_diseases = df[df['classification'] == "common disease"]

# Save to new CSV
common_diseases.to_csv("true2.csv", index=False)

print(f"Total entries: {len(df)}")
print(f"Common diseases: {len(common_diseases)}")