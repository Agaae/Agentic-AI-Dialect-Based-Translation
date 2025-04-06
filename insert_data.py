import sqlite3
import pandas as pd

# Load dataset from Hugging Face
df = pd.read_json("hf://datasets/BaselMousi/Arabic-Dialects-Translation/test.json")
df = df.drop(columns=["MSA", "Levantine", "Qatari"])
df.rename(columns={"English": "input_text", "Egyptian": "translated_text"}, inplace=True)
# Connect to SQLite
conn = sqlite3.connect("translations.db")

# Insert `df` into a new table called `dialect_translations`
df.to_sql("translations", conn, if_exists="replace", index=False)

conn.close()

print("✅ DataFrame inserted into SQLite as a table!")



