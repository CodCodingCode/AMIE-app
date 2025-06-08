import pandas as pd

data = []
with open("manual.csv", 'r') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if line:
            # Split only on the first comma to handle commas in descriptions
            parts = line.split(',', 1)  # Split on first comma only
            if len(parts) == 2:
                code, description = parts
                data.append([code, description])
            else:
                print(f"Problematic line {line_num}: {line}")

df = pd.DataFrame(data, columns=['code', 'description'])

df.to_csv("manual1.csv", index=False)