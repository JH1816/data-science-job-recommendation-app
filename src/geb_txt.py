import pandas as pd
# extract job description column(in JobsDB.csv) to txt file
df_data = pd.read_csv("/Users/cx/Documents/JobsDB.csv",encoding='utf-8')
with open("/Users/cx/Documents/data.txt", 'w', encoding="utf-8") as f:
    for i in df_data.index:
        f.write(df_data["Job description"].iloc[i].lower())

