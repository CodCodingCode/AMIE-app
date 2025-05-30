import pandas as pd

df = pd.read_csv('Disease Relationships Data.csv')

df = df['Concept_Unique_Identifier_1']

df = df.drop_duplicates()

df.to_csv('onlyCUIs.csv', index=False)