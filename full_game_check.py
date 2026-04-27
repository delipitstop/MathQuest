import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app

# Test each game page loads
games = ['/game/mathman', '/game/mathsnake', '/game/targetshoot', '/game/math_invaders']
for g in games:
    with app.test_client() as c:
        # No session - should redirect
        r = c.get(g, follow_redirects=False)
        print(f'{g} (no session): {r.status_code} -> {r.headers.get("Location")}')
        
        # With session
        with c.session_transaction() as sess:
            sess['child_id'] = 1
            sess['child_name'] = 'Ana'
        r2 = c.get(g)
        print(f'{g} (with session): {r2.status_code}, length={len(r2.data)}')

# Test START GAME button click via JS evaluate
print('\n=== Testing JS function definition ===')
with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['child_id'] = 1
        sess['child_name'] = 'Ana'
    r = c.get('/game/targetshoot')
    body = r.data.decode('utf-8', errors='replace')
    
    import re
    # Check startGame function defined in extra_js block
    js_match = re.search(r'{% block extra_js %}(.*?){% endblock %}', body, re.DOTALL)
    if js_match:
        js_content = js_match.group(1)
        print('startGame defined:', 'function startGame' in js_content)
        print('startBtn event listener:', 'startBtn' in js_content and 'addEventListener' in js_content)
        print('JS length:', len(js_content))
    else:
        print('NO extra_js block found!')
        # Find what blocks are in the template
        blocks = re.findall(r'{% block (\w+) %}', body)
        print('Template blocks:', blocks)
        # Check where the game script is
        print('Script tags:', re.findall(r'<script[^>]*>', body))
        print('extra_js in body:', 'extra_js' in body)

    # Check static files
    print('\nStatic files check:')
    for f in ['/static/js/main.js', '/static/css/style.css']:
        r3 = c.get(f)
        print(f'{f}: {r3.status_code}, len={len(r3.data)}')