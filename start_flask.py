import sys, os
os.chdir(r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")
sys.path.insert(0, r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")

# Patch Flask to show detailed errors
from werkzeug.debug import DebuggedApplication
from app import app as real_app

app = DebuggedApplication(real_app, evalex=True)
app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
