import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()












#import pandas as pd
#import sqlite3

#csv_path = "cancer-risk-factors.csv"
#sqlite_path = "cancer-risk-factors.db"
#table_name = "cancer"

#df = pd.read_csv(csv_path)

#conn = sqlite3.connect(sqlite_path)

#df.to_sql(table_name, conn, if_exists="replace", index=False)

#conn.close()
#print("CSV Succesfully converted into sqlite database")