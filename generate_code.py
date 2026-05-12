import sqlite3, uuid
from pathlib import Path
import sys

conn = sqlite3.connect(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\mathquest.db')
c = conn.cursor()

# Generate a fresh access code
access_code = 'MQ' + str(uuid.uuid4())[:8].upper()
print(f"Generated access code: {access_code}")

# Add to access_codes table as unused
c.execute('INSERT INTO access_codes (code, used) VALUES (?, 0)', (access_code,))
conn.commit()
print("Saved to access_codes table")

# Check it's there
c.execute('SELECT code, used FROM access_codes WHERE code = ?', (access_code,))
print(f"Verified in DB: {c.fetchone()}")

conn.close()
print(f"\nAccess code ready: {access_code}")
print(f"This code can be used at mathquest-fbkr.onrender.com/parent/register/step1")