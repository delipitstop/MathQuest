import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app

# Add a debug endpoint to check what login receives
@app.route('/debug_form', methods=['POST'])
def debug_form():
    from flask import request
    return f"name={request.form.get('name')}, pin={request.form.get('pin')}"

# Test the debug endpoint
with app.test_client() as c:
    r = c.post('/debug_form', data={'name':'Ana','pin':'1234'})
    print('Debug test:', r.data.decode())

# Now test the actual login via HTTP
import urllib.request, urllib.parse

req = urllib.request.Request(
    'http://localhost:5000/debug_form',
    data=urllib.parse.urlencode({'name':'Ana','pin':'1234'}).encode(),
    headers={'Content-Type':'application/x-www-form-urlencoded', 'Accept':'text/html'}
)
try:
    resp = urllib.request.urlopen(req, timeout=5)
    print('HTTP debug:', resp.read().decode())
except Exception as e:
    print('HTTP error:', e)