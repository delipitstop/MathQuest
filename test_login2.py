import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app, get_db
import urllib.request
import urllib.parse

# Test 1: Via test_client (works)
print("=== TEST CLIENT ===")
with app.test_client() as c:
    r = c.post('/child/login', data={'name':'Ana','pin':'1234'}, follow_redirects=False)
    print('Status:', r.status_code)
    print('Location:', r.headers.get('Location'))
    if r.status_code == 302:
        r2 = c.get('/student/dashboard')
        print('Dashboard:', r2.status_code)

# Test 2: Via real HTTP
print("\n=== REAL HTTP ===")
req = urllib.request.Request(
    'http://localhost:5000/child/login',
    data=urllib.parse.urlencode({'name':'Ana','pin':'1234'}).encode(),
    headers={'Content-Type':'application/x-www-form-urlencoded'}
)
try:
    resp = urllib.request.urlopen(req, timeout=5)
    print('Status:', resp.status)
    print('Location:', resp.headers.get('Location'))
    print('Response:', resp.read()[:200])
except Exception as e:
    print('Error:', e)