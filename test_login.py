import sys, os
os.chdir(r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")
sys.path.insert(0, r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")

from app import app, init_db

# Initialize fresh database
if os.path.exists('mathquest.db'):
    os.remove('mathquest.db')
init_db()

# Test login
with app.test_client() as c:
    r1 = c.get('/child/login')
    print("GET /child/login:", r1.status_code)
    
    r2 = c.post('/child/login', data={'name': 'Ana', 'pin': '1234'})
    print("POST /child/login:", r2.status_code)
    
    if r2.status_code >= 400:
        print("ERROR:", r2.data[:500])
    else:
        loc = r2.headers.get('Location', '')
        print("Redirect to:", loc)
        if loc:
            r3 = c.get('/student/dashboard')
            print("Dashboard:", r3.status_code)
            print("Dashboard bytes:", len(r3.data))