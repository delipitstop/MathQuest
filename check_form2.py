import sys
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
from app import app, hash_password
with app.test_client() as c:
    import re
    body = c.get('/child/login').data.decode()
    # Find all forms and buttons
    forms = re.findall(r'<form[^>]*>.*?</form>', body, re.DOTALL)
    print('Forms found:', len(forms))
    if forms:
        print('First form:', forms[0][:200])
    buttons = re.findall(r'<button[^>]*>', body)
    print('Buttons found:', len(buttons))
    for b in buttons:
        print('Button:', b)
    # Check what the submit does - try clicking button via form action
    r = c.post('/child/login', data={'name':'Ana', 'pin':'1234'}, follow_redirects=True)
    print('Followed redirect - final status:', r.status_code)
    print('Final URL location in data:')
    m = re.search(r'<title>(.*?)</title>', r.data.decode())
    print('Page title:', m.group(1) if m else 'not found')