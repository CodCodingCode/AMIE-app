import pandas as pd

input_file = "filtered_diseases.csv"

df = pd.read_csv(input_file)

df = df[:10000]

df.to_csv("filtered_diseases_10000.csv", index=False)