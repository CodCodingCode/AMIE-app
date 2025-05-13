import pandas as pd

# load each CSV (you could read from strings or files)
df1 = pd.read_csv("combined.csv")  # has no source_version
df2 = pd.read_csv(
    "/Users/owner/Downloads/coding projects/AMIE-app/clef_taskC_test3_with_chatgpt_vignettes2.csv"
)  # has source_version

# unify columns
all_cols = sorted(set(df1.columns) | set(df2.columns))
df1 = df1.reindex(columns=all_cols)
df2 = df2.reindex(columns=all_cols)

# stack them
df = pd.concat([df1, df2], ignore_index=True)

# write out
df.to_csv("combined2.csv", index=False)
