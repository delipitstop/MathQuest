import sys, os
os.chdir(r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")
sys.path.insert(0, r"C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest")
from app import app, init_db
init_db()
print("DB initialized")