import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app

# Test wrong password
print("=== WRONG PASSWORD ===")
with app.test_client() as c:
    r = c.post('/child/login', data={'name':'Ana','pin':'9999'}, follow_redirects=False)
    print('Status:', r.status_code)
    print('Location:', r.headers.get('Location'))
    body = r.data.decode()
    if 'incorrect' in body.lower():
        print('Shows error message: YES')
    else:
        print('Shows error message: NO')

# Test correct password
print("\n=== CORRECT PASSWORD ===")
with app.test_client() as c:
    r = c.post('/child/login', data={'name':'Ana','pin':'1234'}, follow_redirects=False)
    print('Status:', r.status_code)
    print('Location:', r.headers.get('Location'))

# Check what's in the database
print("\n=== DATABASE CHECK ===")
conn = app.get_db()
c = conn.cursor()
c.execute('SELECT name, pin_hash FROM children')
for row in c.fetchall():
    print(f'{row["name"]}: {row["pin_hash"]}')
conn.close()