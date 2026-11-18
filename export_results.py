import sqlite3, json

DB = r"C:\Users\user\Documents\Custom Office Templates\Intelligent_Tomato_Farm\irrigation.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

# Find tomato results table
target = None
for t in tables:
    if "tomato" in t.lower() and "result" in t.lower():
        target = t
        break
if not target:
    for t in tables:
        if "result" in t.lower():
            target = t
            break

if not target:
    print("No results table found")
else:
    cur.execute(f"SELECT COUNT(*) FROM {target}")
    count = cur.fetchone()[0]
    print(f"Table '{target}' has {count} rows")

    cur.execute(f"SELECT * FROM {target}")
    rows = [dict(r) for r in cur.fetchall()]
    with open("all_detections.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, default=str)
    print(f"Exported {len(rows)} rows to all_detections.json")

conn.close()
