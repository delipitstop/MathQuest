import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app

# Test with session set properly
with app.test_client() as c:
    # Set session via login
    login_resp = c.post('/child/login', data={'name': 'Ana', 'pin': '1234'}, follow_redirects=False)
    print(f'Login: {login_resp.status_code} -> {login_resp.headers.get("Location")}')
    
    # Now try to get the game
    game_resp = c.get('/game/targetshoot')
    print(f'Game page: {game_resp.status_code}, length={len(game_resp.data)}')
    
    # Check the session in the response
    import re
    body = game_resp.data.decode('utf-8', errors='replace')
    
    # Find ALL script tags
    scripts = re.findall(r'<script[^>]*>', body)
    print(f'Script tags ({len(scripts)}): {scripts}')
    
    # Find all JS content blocks
    js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', body, re.DOTALL)
    for i, block in enumerate(js_blocks):
        print(f'\nJS block {i} (len={len(block)}):')
        print(block[:500])
        
    # Check startBtn ID
    print(f'\nstartBtn in body: {"startBtn" in body}')
    print(f'startGame function: {"function startGame" in body}')
    print(f'startGame called: {"startGame()" in body}')

    # Check static js
    static_js = c.get('/static/js/main.js')
    print(f'\nStatic JS length: {len(static_js.data)}')
    print(f'StartGame in static: {"startGame" in static_js.data.decode()}')