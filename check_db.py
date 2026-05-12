import sqlite3, json
from pathlib import Path

conn = sqlite3.connect(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\mathquest.db')
c = conn.cursor()

# List tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print('Tables:', tables)
print()

# Check pending_payments.json
p = Path(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\pending_payments.json')
if p.exists():
    data = json.loads(p.read_text())
    print('Pending payments:', json.dumps(data, indent=2))
else:
    print('No pending_payments.json found')

print()
# Check access_codes table
c.execute('SELECT code, used FROM access_codes LIMIT 20')
print('Access codes in DB:')
for row in c.fetchall():
    print(' ', row)

print()
# Check parents table
c.execute('SELECT email, name, access_code, has_access FROM parents LIMIT 20')
print('Parents:')
for row in c.fetchall():
    print(' ', row)

conn.close()