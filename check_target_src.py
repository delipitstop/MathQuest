import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app
with app.test_client() as c:
    c.post('/child/login', data={'name':'Ana','pin':'1234'})
    r = c.get('/game/targetshoot')
    body = r.data.decode('utf-8', errors='replace')

    import re

    # Find all script tags with src
    scripts = re.findall(r'<script[^>]+src="([^"]+)"[^>]*>', body)
    print('Scripts with src:', scripts)

    # Find all inline script blocks
    js_blocks = re.findall(r'<script(?! src)([^>]*)>(.*?)</script>', body, re.DOTALL)
    print('Inline script blocks:', len(js_blocks))
    for tag_attrs, content in js_blocks:
        print('  Attributes:', tag_attrs.strip(), 'Content len:', len(content))

    # Check if target_shoot.js is loaded
    print('\ntarget_shoot.js in body:', 'target_shoot.js' in body)
    print('startGame in body:', 'startGame' in body)

    # Check the actual rendered HTML for extra_js block
    extra_js_match = re.search(r'{% block extra_js %}(.*?){% endblock', body, re.DOTALL)
    print('\nextra_js block found:', bool(extra_js_match))
    if extra_js_match:
        print('extra_js content:', extra_js_match.group(1)[:200])