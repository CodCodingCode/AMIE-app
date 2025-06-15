import pandas as pd

df = pd.read_csv("common_diseases.csv")

df['verified_classification'] = "common disease"

df.to_csv("common_diseases_standardized.csv", index=False)