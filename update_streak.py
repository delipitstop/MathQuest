import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('mathquest.db')
c = conn.cursor()

try:
    c.execute("ALTER TABLE children ADD COLUMN day_streak INTEGER DEFAULT 0")
    print('added day_streak')
except Exception as e:
    print('day_streak:', e)

try:
    c.execute("ALTER TABLE children ADD COLUMN last_active_date TEXT DEFAULT ''")
    print('added last_active_date')
except Exception as e:
    print('last_active_date:', e)

conn.commit()

# Show current state
c.execute("SELECT id, name, day_streak, last_active_date FROM children")
for r in c.fetchall():
    print(r)

conn.close()
print('Done')
