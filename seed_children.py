import sys, os
os.chdir(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')
sys.path.insert(0, r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest')

from app import get_db, hash_password

conn = get_db()
c = conn.cursor()

# Check if any children exist
c.execute('SELECT COUNT(*) FROM children')
count = c.fetchone()[0]
print(f'Children in DB: {count}')

# Add sample children if none exist
if count == 0:
    # Get a parent_id
    c.execute('SELECT id FROM parents LIMIT 1')
    parent_row = c.fetchone()
    if parent_row:
        parent_id = parent_row[0]
    else:
        # Create a parent first
        c.execute("INSERT INTO parents (name, email, password_hash) VALUES (?, ?, ?)",
                 ('Test Parent', 'parent@mathquest.com', hash_password('parent123')))
        parent_id = c.lastrowid
    
    # Add Ana with pin 1234
    c.execute("INSERT INTO children (parent_id, name, pin_hash, avatar) VALUES (?, ?, ?, ?)",
             (parent_id, 'Ana', hash_password('1234'), 'rabbit'))
    print(f'Added Ana with id: {c.lastrowid}')
    
    # Add a few other children
    c.execute("INSERT INTO children (parent_id, name, pin_hash, avatar) VALUES (?, ?, ?, ?)",
             (parent_id, 'Mia', hash_password('5678'), 'lion'))
    c.execute("INSERT INTO children (parent_id, name, pin_hash, avatar) VALUES (?, ?, ?, ?)",
             (parent_id, 'Sofia', hash_password('9999'), 'panda'))
    
    conn.commit()
    print('Sample children added')

# Verify
c.execute('SELECT name, pin_hash FROM children')
for row in c.fetchall():
    print(f'Child: {row["name"]}')
conn.close()