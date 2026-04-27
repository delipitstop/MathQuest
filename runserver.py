import sys, os
os.chdir(r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")
sys.path.insert(0, r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")
from app import app
app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)