import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import get_db, hash_password
conn = get_db()
c = conn.cursor()
c.execute('SELECT name, pin_hash FROM children')
for row in c.fetchall():
    print(f'{row["name"]}: {row["pin_hash"]}')
conn.close()
print('Expected hash for 1234:', hash_password('1234'))