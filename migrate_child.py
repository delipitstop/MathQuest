import sqlite3, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
conn = sqlite3.connect('mathquest.db')
c = conn.cursor()

# Add missing columns if they don't exist
try:
    c.execute('ALTER TABLE children ADD COLUMN day_streak INTEGER DEFAULT 0')
    print('added day_streak')
except Exception as e:
    print('day_streak:', e)

try:
    c.execute('ALTER TABLE children ADD COLUMN last_active_date TEXT DEFAULT ""')
    print('added last_active_date')
except Exception as e:
    print('last_active_date:', e)

conn.commit()

# Verify
c.execute('PRAGMA table_info(children)')
cols = [r[1] for r in c.fetchall()]
print('children columns:', cols)
conn.close()
print('migration done')