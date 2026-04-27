import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import app

# Add debug route to test session
@app.route('/test_session')
def test_session():
    from flask import session, jsonify
    return jsonify(dict(session))

with app.test_client() as c:
    # First visit to set session
    r = c.get('/test_session')
    print('Session test:', r.data.decode())
    
    # Now try login
    r2 = c.post('/child/login', data={'name':'Ana','pin':'1234'}, follow_redirects=False)
    print('\nLogin status:', r2.status_code)
    print('Headers:', dict(r2.headers))
    print('Location header:', r2.headers.get('Location'))
    print('Response length:', len(r2.data))
    if r2.status_code == 302:
        print('Redirect URL:', r2.headers.get('Location'))
    else:
        print('Body preview:', r2.data[:300].decode())