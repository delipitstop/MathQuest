import sys
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
from app import app
with app.test_client() as c:
    import re
    body = c.get('/child/login').data.decode()
    form_match = re.search(r'<form[^>]*method="([^"]+)"[^>]*>', body)
    print('form method:', form_match.group(1) if form_match else 'not found')
    action_match = re.search(r'<form[^>]*action="([^"]+)"[^>]*>', body)
    print('form action:', action_match.group(1) if action_match else 'not found')
    # Check inputs
    inputs = re.findall(r'<input[^>]*>', body)
    for inp in inputs:
        print('input:', inp)