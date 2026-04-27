import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import get_db, hash_password

conn = get_db()
c = conn.cursor()
c.execute('SELECT name, pin_hash FROM children')
rows = c.fetchall()
for row in rows:
    print(f'Name: {row["name"]}, pin_hash: {row["pin_hash"]}')
conn.close()

print('\nExpected hash for "1234":', hash_password('1234'))
print('Match:', rows[0]["pin_hash"] == hash_password('1234') if rows else 'no children')