"""
MathQuest - Educational Math Platform for Kids
Flask Backend - MVP Version
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import uuid
import random
import asyncio
import edge_tts
import io
import stripe
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, jsonify, send_file, Response
import os
import json
import sys

# Stripe payment module
sys.path.insert(0, os.path.dirname(__file__))
try:
    import stripe_payment
    STRIPE_AVAILABLE = True
except ImportError:
    stripe_payment = None
    STRIPE_AVAILABLE = False
    logging.warning("Stripe not available — set STRIPE_SECRET_KEY env var to enable")

app = Flask(__name__)
app.secret_key = 'mathquest-secret-key-2026'
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# ============ ACCESS CODE CONFIG ============
# One-time purchase access codes.
# Each code grants one parent account.
# Luis: Add Gumroad product URL here.
GUMROAD_PRODUCT_URL = 'YOUR_GUMROAD_PRODUCT_LINK_HERE'
VALID_ACCESS_CODES = {
    'MQ2026HOME': True,
}
ACCESS_CODE_PRICE = '£5'

# ============ DATABASE SETUP ============
def init_db():
    # Tables created manually in Neon PostgreSQL — no-op here
    pass

# init_db() intentionally not called — tables exist in Neon

# ============ HELPERS ============
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable not set')
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def get_child_progress(child_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM progress WHERE child_id = %s', (child_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_child_achievements(child_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM achievements WHERE child_id = %s', (child_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def award_badge(child_id, badge):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM achievements WHERE child_id = %s AND badge = %s', (child_id, badge))
    if not c.fetchone():
        c.execute('INSERT INTO achievements (child_id, badge) VALUES (%s, %s)', (child_id, badge))
        conn.commit()
    conn.close()
    conn.close()


def is_valid_access_code(code):
    """
    Check if an access code is valid.
    - Codes from VALID_ACCESS_CODES (manual codes) are always valid
    - Codes registered by Stripe webhook are valid if not already used
    """
    if not code:
        return False
    code = code.strip().upper()
    
    # Check hardcoded valid codes (manual codes like MQ2026HOME)
    if code in VALID_ACCESS_CODES:
        return True
    
    # Check DB for codes registered by Stripe webhook (must not be used yet)
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM access_codes WHERE code = %s AND used = 0', (code,))
    result = c.fetchone()
    conn.close()
    return result is not None


def use_access_code(code):
    """
    Mark an access code as used.
    Returns True if successfully used, False if already used.
    """
    code = code.strip().upper()
    conn = get_db()
    c = conn.cursor()
    
    # Hardcoded codes (MQ2026HOME etc.) — never expire, track in DB
    if code in VALID_ACCESS_CODES:
        # Check if already used
        c.execute('SELECT id FROM access_codes WHERE code = %s AND used = 1', (code,))
        if c.fetchone():
            conn.close()
            return False  # already used
        # Register and mark as used
        c.execute('INSERT OR REPLACE INTO access_codes (code, used) VALUES (%s, 1)', (code,))
        conn.commit()
        conn.close()
        return True
    
    # DB codes (from Stripe) — mark as used if not already used
    c.execute('SELECT id FROM access_codes WHERE code = %s AND used = 1', (code,))
    if c.fetchone():
        conn.close()
        return False  # already used
    c.execute('UPDATE access_codes SET used = 1 WHERE code = %s', (code,))
    conn.commit()
    conn.close()
    return True


def is_access_code_used(code):
    """Check if an access code has already been used."""
    code = code.strip().upper()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM access_codes WHERE code = %s AND used = 1', (code,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_table_progress(child_id, table_num):
    """Get progress for a specific table, returns dict with status"""
    conn = get_db()
    c = conn.cursor()
    topic = f'table_{table_num}'
    c.execute('SELECT * FROM progress WHERE child_id = %s AND topic = %s', (child_id, topic))
    row = c.fetchone()
    conn.close()
    if not row:
        return {'topic': topic, 'questions_completed': 0, 'quiz_score': 0, 'quiz_taken': 0}
    return dict(row)

def mark_table_passed(child_id, table_num, score):
    conn = get_db()
    c = conn.cursor()
    topic = f'table_{table_num}'
    pct = int(score / 10 * 100)
    c.execute('''
        INSERT INTO progress (child_id, topic, questions_completed, quiz_score, quiz_taken)
        VALUES (?, ?, 12, ?, 1)
        ON CONFLICT(child_id, topic) DO UPDATE SET
        questions_completed = 12, quiz_score = MAX(quiz_score, ?), quiz_taken = 1,
        last_activity = CURRENT_TIMESTAMP
    ''', (child_id, topic, pct, pct))
    conn.commit()
    conn.close()

def get_today_str():
    """Return today's date as YYYY-MM-DD string"""
    from datetime import date
    return str(date.today())

def update_streak(child_id):
    """
    Update day streak for a child.
    - If they were active yesterday: increment streak
    - If they were active today already: do nothing
    - If they missed yesterday: reset streak to 1
    Called on login and after completing any activity.
    """
    from datetime import date, timedelta
    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT day_streak, last_active_date FROM children WHERE id = %s', (child_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    
    current_streak = row['day_streak'] or 0
    last_active = row['last_active_date'] or ''
    
    if last_active == today:
        # Already updated today, skip
        conn.close()
        return
    elif last_active == yesterday:
        # Active yesterday — increment streak
        new_streak = current_streak + 1
    else:
        # Either first time or missed yesterday — start fresh at 1
        new_streak = 1
    
    c.execute('UPDATE children SET day_streak = %s, last_active_date = %s WHERE id = %s',
               (new_streak, today, child_id))
    conn.commit()
    conn.close()
    
    # Award streak badges
    if new_streak >= 3:
        award_badge(child_id, 'streak_3')
    if new_streak >= 7:
        award_badge(child_id, 'streak_7')
    if new_streak >= 30:
        award_badge(child_id, 'streak_30')
    if new_streak >= 100:
        award_badge(child_id, 'streak_100')

def get_all_table_progress(child_id):
    """Get progress for all 15 multiplication tables"""
    progress = {}
    for i in range(1, 16):
        progress[i] = get_table_progress(child_id, i)
    return progress

# ============ EXAM HELPERS ============
def check_exam_eligible(child_id):
    """Check if a child has passed all 60 tables (4 ops x 15 each)"""
    all_mult = get_all_table_progress(child_id)
    all_div = get_all_division_progress(child_id)
    all_add = get_all_addition_progress(child_id)
    all_sub = get_all_subtraction_progress(child_id)
    mult_done = all(all_mult[i]['quiz_score'] >= 80 for i in range(1, 16))
    div_done = all(all_div[i]['quiz_score'] >= 80 for i in range(1, 16))
    add_done = all(all_add[i]['quiz_score'] >= 80 for i in range(1, 16))
    sub_done = all(all_sub[i]['quiz_score'] >= 80 for i in range(1, 16))
    return mult_done and div_done and add_done and sub_done

def get_exam_result(child_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM exam_results WHERE child_id = %s ORDER BY taken_at DESC LIMIT 1', (child_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def save_exam_result(child_id, score, total, passed, answers_json):
    conn = get_db()
    c = conn.cursor()
    pct = int(score / total * 100)
    c.execute('''
        INSERT INTO exam_results (child_id, score, total, percentage, passed, answers_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (child_id, score, total, pct, passed, answers_json))
    conn.commit()
    exam_id = c.fetchone()[0]
    conn.close()
    if passed:
        award_badge(child_id, 'exam_passed')
    return exam_id

def generate_exam_questions():
    """Generate 35 mixed questions covering all 4 operations"""
    import random
    questions = []

    # Pool sizes per operation
    # We'll generate ~9 questions per op = 36, take 35
    mult_qs = []
    div_qs = []
    add_qs = []
    sub_qs = []

    # Multiplication word problems (table_n * i)
    mult_templates = [
        lambda n,i: {
            'text': f"{n} groups of {i} stickers are in a packet. How many stickers is that in total?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A bus has {n} rows of seats with {i} seats in each row. How many seats are on the bus?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"Your mum buys {n} packs of crayons. Each pack has {i} crayons. How many crayons does she buy?",

            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"There are {n} feet on {i} people. How many feet is that altogether?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"Each egg carton holds {n} eggs. If you have {i} cartons, how many eggs do you have?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A florist arranges {n} flowers per vase. She fills {i} vases. How many flowers in total?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"You have {n} marbles in each bag. You have {i} bags. How many marbles do you have?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A baker puts {n} cupcakes on each tray. She bakes {i} trays. How many cupcakes?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n} friends each have {i} books. How many books do they have altogether?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A clock chimes {n} times every hour. After {i} hours, how many chimes?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n} x {i} = ?",
            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'equation'
        },
        lambda n,i: {
            'text': f"What is {n} multiplied by {i}?",

            'answer': n*i,
            'topic': 'multiplication',
            'table': n,
            'format': 'word'
        },
    ]

    # Division word problems (product / divisor)
    div_templates = [
        lambda n,i: {
            'text': f"{n*i} sweets are shared equally among {n} children. How many sweets does each child get?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} stickers are shared into {n} packets with the same number in each. How many per packet?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} pencils are put into {n} boxes equally. How many pencils in each box?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} children line up in {n} equal rows. How many children per row?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A teacher has {n*i} books and puts them on {n} shelves equally. How many books per shelf?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} cupcakes are packed into {n} boxes equally. How many cupcakes per box?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} flowers are arranged into {n} bouquets equally. How many flowers per bouquet?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} stars are drawn in {n} equal groups. How many stars per group?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n*i} ÷ {n} = ?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'equation'
        },
        lambda n,i: {
            'text': f"How many {n}s fit into {n*i}?",
            'answer': i,
            'topic': 'division',
            'table': n,
            'format': 'word'
        },
    ]

    # Addition word problems
    add_templates = [
        lambda n,i: {
            'text': f"You have {n} marbles and you find {i} more. How many marbles do you have now?",
            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A shop sells {n} apples in the morning and {i} apples in the afternoon. How many apples in total?",
            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"Sam has {n} stickers and his friend gives him {i} more. How many stickers does Sam have?",
            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"There are {n} birds on a tree and {i} more fly in. How many birds are on the tree now?",

            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"You save {n} coins one week and {i} coins the next week. How many coins have you saved?",

            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A train carries {n} passengers to one station and picks up {i} more at the next. How many on the train now?",
            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n} + {i} = ?",
            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'equation'
        },
        lambda n,i: {
            'text': f"What is {n} plus {i}?",
            'answer': n+i,
            'topic': 'addition',
            'table': n,
            'format': 'word'
        },
    ]

    # Subtraction word problems
    sub_templates = [
        lambda n,i: {
            'text': f"You have {n+i} sweets and give away {n}. How many sweets do you have left?",
            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A shop had {n+i} toys and sold {n}. How many toys are left?",
            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"Tom had {n+i} marbles and lost {n}. How many marbles does Tom have now?",

            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"There were {n+i} children on a bus. {n} got off. How many are still on the bus?",
            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"A book has {n+i} pages. You read {n} pages. How many pages are left to read?",
            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"Mum had {n+i} flowers. She gave {n} to grandma. How many flowers does she have now?",
            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
        lambda n,i: {
            'text': f"{n+i} - {n} = ?",

            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'equation'
        },
        lambda n,i: {
            'text': f"What is {n+i} minus {n}?",

            'answer': i,
            'topic': 'subtraction',
            'table': n,
            'format': 'word'
        },
    ]

    # Generate a pool for each op
    # We'll use tables 2-15 (skip trivial table 1 for add/sub/div, skip for mult)
    for n in range(2, 16):
        for i in range(1, 11):  # 10 values per table
            for t in mult_templates:
                mult_qs.append(t(n, i))
            for t in div_templates:
                div_qs.append(t(n, i))
            for t in add_templates:
                add_qs.append(t(n, i))
            for t in sub_templates:
                sub_qs.append(t(n, i))

    random.shuffle(mult_qs)
    random.shuffle(div_qs)
    random.shuffle(add_qs)
    random.shuffle(sub_qs)

    # Take ~9 each, then fill remaining
    selected = mult_qs[:9] + div_qs[:9] + add_qs[:9] + sub_qs[:8]
    random.shuffle(selected)
    selected = selected[:35]

    for idx, q in enumerate(selected):
        q['id'] = idx + 1

    return selected

# ============ DIVISION TABLE HELPERS ============
def get_division_progress(child_id, table_num):
    """Get progress for a specific division table"""
    conn = get_db()
    c = conn.cursor()
    topic = f'div_table_{table_num}'
    c.execute('SELECT * FROM progress WHERE child_id = %s AND topic = %s', (child_id, topic))
    row = c.fetchone()
    conn.close()
    if not row:
        return {'topic': topic, 'questions_completed': 0, 'quiz_score': 0, 'quiz_taken': 0}
    return dict(row)

def mark_division_passed(child_id, table_num, score):
    """Mark a division table as passed"""
    conn = get_db()
    c = conn.cursor()
    topic = f'div_table_{table_num}'
    pct = int(score / 10 * 100)
    c.execute('''
        INSERT INTO progress (child_id, topic, questions_completed, quiz_score, quiz_taken)
        VALUES (?, ?, 12, ?, 1)
        ON CONFLICT(child_id, topic) DO UPDATE SET
        questions_completed = 12, quiz_score = MAX(quiz_score, ?), quiz_taken = 1,
        last_activity = CURRENT_TIMESTAMP
    ''', (child_id, topic, pct, pct))
    conn.commit()
    conn.close()

def get_all_division_progress(child_id):
    """Get progress for all 15 division tables"""
    progress = {}
    for i in range(1, 16):
        progress[i] = get_division_progress(child_id, i)
    return progress

# ============ ADDITION TABLE HELPERS ============
def get_addition_progress(child_id, table_num):
    conn = get_db()
    c = conn.cursor()
    topic = f'add_table_{table_num}'
    c.execute('SELECT * FROM progress WHERE child_id = %s AND topic = %s', (child_id, topic))
    row = c.fetchone()
    conn.close()
    if not row:
        return {'topic': topic, 'questions_completed': 0, 'quiz_score': 0, 'quiz_taken': 0}
    return dict(row)

def mark_addition_passed(child_id, table_num, score):
    conn = get_db()
    c = conn.cursor()
    topic = f'add_table_{table_num}'
    pct = int(score / 10 * 100)
    c.execute('''
        INSERT INTO progress (child_id, topic, questions_completed, quiz_score, quiz_taken)
        VALUES (?, ?, 12, ?, 1)
        ON CONFLICT(child_id, topic) DO UPDATE SET
        questions_completed = 12, quiz_score = MAX(quiz_score, ?), quiz_taken = 1,
        last_activity = CURRENT_TIMESTAMP
    ''', (child_id, topic, pct, pct))
    conn.commit()
    conn.close()

def get_all_addition_progress(child_id):
    progress = {}
    for i in range(1, 16):
        progress[i] = get_addition_progress(child_id, i)
    return progress

# ============ SUBTRACTION TABLE HELPERS ============
def get_subtraction_progress(child_id, table_num):
    conn = get_db()
    c = conn.cursor()
    topic = f'sub_table_{table_num}'
    c.execute('SELECT * FROM progress WHERE child_id = %s AND topic = %s', (child_id, topic))
    row = c.fetchone()
    conn.close()
    if not row:
        return {'topic': topic, 'questions_completed': 0, 'quiz_score': 0, 'quiz_taken': 0}
    return dict(row)

def mark_subtraction_passed(child_id, table_num, score):
    conn = get_db()
    c = conn.cursor()
    topic = f'sub_table_{table_num}'
    pct = int(score / 10 * 100)
    c.execute('''
        INSERT INTO progress (child_id, topic, questions_completed, quiz_score, quiz_taken)
        VALUES (?, ?, 12, ?, 1)
        ON CONFLICT(child_id, topic) DO UPDATE SET
        questions_completed = 12, quiz_score = MAX(quiz_score, ?), quiz_taken = 1,
        last_activity = CURRENT_TIMESTAMP
    ''', (child_id, topic, pct, pct))
    conn.commit()
    conn.close()

def get_all_subtraction_progress(child_id):
    progress = {}
    for i in range(1, 16):
        progress[i] = get_subtraction_progress(child_id, i)
    return progress

# ============ AUTH ROUTES ============
@app.route('/')
def index():
    return render_template('index.html')

# ============ BARE DOMAIN REDIRECT ============
# Redirect bare domain to www to avoid Railway SSL conflicts
@app.before_request
def redirect_bare_domain():
    from flask import request
    host = request.host
    if host in ('mathquestv1.co.uk', 'mathquest-production-56b4.up.railway.app'):
        from flask import redirect
        return redirect('https://www.mathquestv1.co.uk' + request.path, code=301)

@app.route('/parent/register/step1', methods=['GET', 'POST'])
def parent_register_step1():
    """Step 1: Validate access code, then redirect to registration."""
    if request.method == 'POST':
        code = request.form.get('access_code', '').strip().upper()
        
        if not is_valid_access_code(code):
            return render_template('register_code.html', 
                                 error='Invalid access code. Please check your code and try again.',
                                 success=False)
        
        # Store validated code in session
        session['validated_access_code'] = code
        return redirect('/parent/register')
    
    # GET: show code entry page
    return render_template('register_code.html', error=None, success=False)


@app.route('/parent/register', methods=['GET', 'POST'])
def parent_register():
    """Step 2: Actual registration — only if access code was validated."""
    # Check if code was validated
    validated_code = session.get('validated_access_code')
    if not validated_code:
        return redirect('/parent/register/step1')
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM parents WHERE email = %s', (email,))
        if c.fetchone():
            conn.close()
            return render_template('parent_register.html', error='Email already registered')
        
        c.execute('''INSERT INTO parents (name, email, password_hash, has_access, access_code) 
                     VALUES (%s, %s, %s, 1, %s)
                     RETURNING id''',
                  (name, email, hash_password(password), validated_code))
        conn.commit()
        parent_id = c.fetchone()[0]
        
        # Mark access code as used
        use_access_code(validated_code)
        
        conn.close()
        
        # Clear the validated code from session
        session.pop('validated_access_code', None)
        session['parent_id'] = parent_id
        return redirect('/parent/dashboard')
    
    return render_template('parent_register.html', validated_code=validated_code)

@app.route('/parent/login', methods=['GET', 'POST'])
def parent_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM parents WHERE email = %s AND password_hash = %s',
                  (email, hash_password(password)))
        parent = c.fetchone()
        conn.close()
        
        if parent:
            if parent.get('has_access') == 0:
                return render_template('parent_login.html',
                                     needs_access=True,
                                     error=None)
            session['parent_id'] = parent['id']
            return redirect('/parent/dashboard')
        else:
            return render_template('parent_login.html', error='Invalid email or password')
    
    return render_template('parent_login.html')

@app.route('/parent/logout')
def parent_logout():
    session.pop('parent_id', None)
    return redirect('/parent/login')

@app.route('/parent/dashboard')
def parent_dashboard():
    if 'parent_id' not in session:
        return redirect('/parent/login')
    
    parent_id = session['parent_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM children WHERE parent_id = %s', (parent_id,))
    children = c.fetchall()
    
    children_data = []
    for child in children:
        child_dict = dict(child)
        child_dict['progress'] = get_child_progress(child['id'])
        child_dict['achievements'] = get_child_achievements(child['id'])
        child_dict['all_tables'] = get_all_table_progress(child['id'])
        child_dict['all_division'] = get_all_division_progress(child['id'])
        child_dict['all_addition'] = get_all_addition_progress(child['id'])
        child_dict['all_subtraction'] = get_all_subtraction_progress(child['id'])
        
        # Count passed tables per operation
        mult_passed = sum(1 for i in range(1, 16) if child_dict['all_tables'][i]['quiz_score'] >= 80)
        div_passed = sum(1 for i in range(1, 16) if child_dict['all_division'][i]['quiz_score'] >= 80)
        add_passed = sum(1 for i in range(1, 16) if child_dict['all_addition'][i]['quiz_score'] >= 80)
        sub_passed = sum(1 for i in range(1, 16) if child_dict['all_subtraction'][i]['quiz_score'] >= 80)
        child_dict['mult_passed'] = mult_passed
        child_dict['div_passed'] = div_passed
        child_dict['add_passed'] = add_passed
        child_dict['sub_passed'] = sub_passed
        
        # Struggling topics (quiz_score < 60%)
        struggles = []
        for p in child_dict['progress']:
            if p['quiz_score'] > 0 and p['quiz_score'] < 60:
                topic_name = p['topic'].replace('_', ' ').replace('table', 'Table').replace('div', '÷ ').replace('add', '+ ').replace('sub', '− ')
                struggles.append({'topic': topic_name, 'score': p['quiz_score']})
        child_dict['struggles'] = struggles
        
        # Quiz results history
        c.execute('SELECT * FROM quiz_results WHERE child_id = %s ORDER BY taken_at DESC LIMIT 20',
                 (child['id'],))
        child_dict['quiz_results'] = [dict(r) for r in c.fetchall()]
        child_dict['progress_dict'] = {p['topic']: p for p in child_dict['progress']}
        
        # Best exam result (for certificate)
        c.execute('SELECT * FROM exam_results WHERE child_id = %s ORDER BY percentage DESC LIMIT 1',
                 (child['id'],))
        exam = c.fetchone()
        child_dict['exam_result'] = dict(exam) if exam else None
        child_dict['exam_passed'] = exam and exam['passed'] == 1 if exam else False
        
        # Total quizzes
        child_dict['total_quizzes'] = len(child_dict['quiz_results'])
        
        children_data.append(child_dict)
    
    conn.close()
    return render_template('parent_dashboard2.html', children=children_data)

@app.route('/parent/add-child', methods=['GET', 'POST'])
def add_child():
    if 'parent_id' not in session:
        return redirect('/parent/login')
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            pin = request.form['pin']
            avatar = request.form.get('avatar', 'lion')
            
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO children (parent_id, name, pin_hash, avatar) VALUES (%s, %s, %s, %s) RETURNING id',
                      (session['parent_id'], name, hash_password(pin), avatar))
            child_id = c.fetchone()[0]
            
            # Initialize progress for table_1 (first table is always unlocked)
            c.execute('INSERT INTO progress (child_id, topic, questions_completed, quiz_score, quiz_taken) VALUES (%s, %s, 0, 0, 0)',
                      (child_id, 'table_1'))
            conn.commit()
            conn.close()
            
            return redirect('/parent/dashboard')
        except Exception as e:
            import traceback
            error_msg = f"Add child error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # This will appear in Railway logs
            if conn:
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
            # Return error page instead of 500
            return f"<h1>Error adding child</h1><p>{str(e)}</p><pre>{error_msg}</pre>", 500
    
    return render_template('add_child.html')

# ============ CHILD ROUTES ============
# Auto-login shortcut - logs in as first child and goes straight to dashboard
@app.route('/start')
def quick_start():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM children ORDER BY id ASC LIMIT 1')
    child = c.fetchone()
    conn.close()
    if child:
        session['child_id'] = child['id']
        session['child_name'] = child['name']
        update_streak(child['id'])
        return redirect('/student/dashboard')
    return redirect('/child/login')

@app.route('/child/login', methods=['GET', 'POST'])
def child_login():
    if request.method == 'POST':
        name = request.form['name']
        pin = request.form['pin']
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM children WHERE name = %s AND pin_hash = %s',
                  (name, hash_password(pin)))
        child = c.fetchone()
        conn.close()
        
        if child:
            session['child_id'] = child['id']
            session['child_name'] = child['name']
            update_streak(child['id'])
            return redirect('/student/dashboard')
        else:
            return render_template('child_login.html', error='Name or PIN incorrect')
    
    return render_template('child_login.html')

@app.route('/child/logout')
def child_logout():
    session.pop('child_id', None)
    session.pop('child_name', None)
    return redirect('/child/login')

@app.route('/student/dashboard')
def student_dashboard():
    if 'child_id' not in session:
        return redirect('/child/login')
    
    child_id = session['child_id']
    achievements = get_child_achievements(child_id)
    all_tables = get_all_table_progress(child_id)
    all_division = get_all_division_progress(child_id)
    all_addition = get_all_addition_progress(child_id)
    all_subtraction = get_all_subtraction_progress(child_id)
    
    # Get day streak
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT day_streak, last_active_date FROM children WHERE id = %s', (child_id,))
    child_row = c.fetchone()
    conn.close()
    day_streak = child_row['day_streak'] if child_row else 0

    # Count passed tables
    passed_count = sum(1 for i in range(1, 16) if all_tables[i]['quiz_score'] >= 80)
    div_passed_count = sum(1 for i in range(1, 16) if all_division[i]['quiz_score'] >= 80)
    add_passed_count = sum(1 for i in range(1, 16) if all_addition[i]['quiz_score'] >= 80)
    sub_passed_count = sum(1 for i in range(1, 16) if all_subtraction[i]['quiz_score'] >= 80)

    # Check exam eligibility
    exam_eligible = check_exam_eligible(child_id)
    exam_result = get_exam_result(child_id)
    exam_passed = exam_result and exam_result['passed']

    return render_template('student_dashboard.html',
                           child_name=session['child_name'],
                           achievements=achievements,
                           all_tables=all_tables,
                           all_division=all_division,
                           all_addition=all_addition,
                           all_subtraction=all_subtraction,
                           passed_count=passed_count,
                           div_passed_count=div_passed_count,
                           add_passed_count=add_passed_count,
                           sub_passed_count=sub_passed_count,
                           exam_eligible=exam_eligible,
                           exam_passed=exam_passed,
                           exam_result=exam_result,
                           day_streak=day_streak)

# ============ GAME ROUTES ============
@app.route('/game/mathsnake')
def game_mathsnake():
    if 'child_id' not in session:
        return redirect('/child/login')
    return render_template('math_snake.html', child_name=session['child_name'])

@app.route('/game/targetshoot')
def game_targetshoot():
    if 'child_id' not in session:
        return redirect('/child/login')
    return render_template('target_shoot.html', child_name=session['child_name'])

# ============ LEARN ROUTES ============
@app.route('/learn')
def learn():
    if 'child_id' not in session:
        return redirect('/child/login')
    
    child_id = session['child_id']
    all_tables = get_all_table_progress(child_id)
    
    return render_template('learn.html',
                           child_name=session['child_name'],
                           all_tables=all_tables)

@app.route('/learn/<int:table_num>')
def learn_table(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    
    if table_num < 1 or table_num > 15:
        return redirect('/learn')
    
    child_id = session['child_id']
    all_tables = get_all_table_progress(child_id)
    
    # Check if this table is unlocked
    # Table 1 always unlocked. Table N requires table N-1 passed (>=80%)
    if table_num > 1 and all_tables[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn')
    
    # Generate the 15 questions/facts for this times table
    questions = []
    for i in range(1, 16):
        questions.append({
            'id': i,
            'question': f"{table_num} × {i}",
            'answer': table_num * i,
            'hint': f"Think of {table_num} groups of {i} — or count in {table_num}s!",
            'explanation': f"{table_num} × {i} means add {table_num} to itself {i} times. So {table_num} + {table_num} + ... ({i} times) = {table_num * i}. Another way: {i} groups of {table_num} = {table_num * i}"
        })
    
    return render_template('learn_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'])

@app.route('/quiz_table/<int:table_num>')
def quiz_table(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    
    if table_num < 1 or table_num > 20:
        return redirect('/learn')
    
    child_id = session['child_id']
    all_tables = get_all_table_progress(child_id)
    
    # Table must be unlocked
    if table_num > 1 and all_tables[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn')
    
    # Generate 15 questions for this specific table
    questions = []
    nums = list(range(1, 16))
    random.shuffle(nums)
    selected = nums[:15]
    for idx, i in enumerate(selected):
        questions.append({
            'id': idx + 1,
            'question': f"{table_num} × {i}",
            'answer': table_num * i
        })
    
    session['quiz_questions'] = questions
    session['quiz_topic'] = f'table_{table_num}'
    session['quiz_table_num'] = table_num
    
    return render_template('quiz_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'])

@app.route('/submit_table_quiz', methods=['POST'])
def submit_table_quiz():
    if 'child_id' not in session or 'quiz_questions' not in session:
        return redirect('/child/login')
    
    child_id = session['child_id']
    topic = session['quiz_topic']
    table_num = session.get('quiz_table_num', 1)
    questions = session['quiz_questions']
    
    score = 0
    total = len(questions)
    answers = []
    
    for q in questions:
        user_answer = request.form.get(f'q{q["id"]}', '')
        correct = int(user_answer) == q['answer'] if user_answer.isdigit() else False
        if correct:
            score += 1
        answers.append({
            'question': q['question'],
            'user_answer': user_answer,
            'correct_answer': q['answer'],
            'correct': correct
        })
    
    # Save result
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO quiz_results (child_id, topic, score, total) VALUES (%s, %s, %s, %s)',
              (child_id, topic, score, total))
    
    pct = int(score / total * 100)
    passed = pct >= 80
    
    if passed:
        mark_table_passed(child_id, table_num, score)
        award_badge(child_id, f'table_{table_num}_passed')
        
        # If all 15 tables passed, award champion badge
        all_t = get_all_table_progress(child_id)
        all_passed = all(all_t[i]['quiz_score'] >= 80 for i in range(1, 16))
        if all_passed:
            award_badge(child_id, 'math_champion')
    
    conn.commit()
    conn.close()
    update_streak(child_id)
    
    return render_template('quiz_table_result.html',
                           score=score,
                           total=total,
                           percentage=pct,
                           passed=passed,
                           answers=answers,
                           table_num=table_num)

# Legacy routes - redirect to learn
@app.route('/practice/times_tables')
def practice_redirect():
    return redirect('/learn')

@app.route('/quiz/times_tables')
def quiz_redirect():
    return redirect('/quiz_table/1')

# ============ DIVISION LEARN ROUTES ============
@app.route('/learn_div')
def learn_div():
    if 'child_id' not in session:
        return redirect('/child/login')
    
    child_id = session['child_id']
    all_division = get_all_division_progress(child_id)
    
    return render_template('learn_div.html',
                           child_name=session['child_name'],
                           all_division=all_division)

@app.route('/learn_div/<int:table_num>')
def learn_division_table(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    
    if table_num < 1 or table_num > 15:
        return redirect('/learn_div')
    
    child_id = session['child_id']
    all_division = get_all_division_progress(child_id)
    
    # Check if this table is unlocked
    if table_num > 1 and all_division[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn_div')
    
    # Generate the 15 division facts for this table (reverse of multiplication)
    questions = []
    for i in range(1, 16):
        product = table_num * i
        questions.append({
            'id': i,
            'question': f"{product} ÷ {table_num}",
            'answer': i,
            'hint': f"Think: how many {table_num}s fit into {product}?",
            'explanation': f"{product} ÷ {table_num} means how many groups of {table_num} fit into {product}. Since {table_num} × {i} = {product}, the answer is {i}."
        })
    
    return render_template('learn_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'],
                           operation='div')

@app.route('/quiz_div/<int:table_num>')
def quiz_div(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    
    if table_num < 1 or table_num > 15:
        return redirect('/learn_div')
    
    child_id = session['child_id']
    all_division = get_all_division_progress(child_id)
    
    # Table must be unlocked
    if table_num > 1 and all_division[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn_div')
    
    # Generate 15 division questions
    questions = []
    nums = list(range(1, 16))
    random.shuffle(nums)
    selected = nums[:15]
    for idx, i in enumerate(selected):
        product = table_num * i
        questions.append({
            'id': idx + 1,
            'question': f"{product} ÷ {table_num}",
            'answer': i
        })
    
    session['quiz_questions'] = questions
    session['quiz_topic'] = f'div_table_{table_num}'
    session['quiz_table_num'] = table_num
    session['quiz_division'] = True
    
    return render_template('quiz_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'],
                           operation='div')

@app.route('/submit_division_quiz', methods=['POST'])
def submit_division_quiz():
    if 'child_id' not in session or 'quiz_questions' not in session:
        return redirect('/child/login')
    
    child_id = session['child_id']
    topic = session['quiz_topic']
    table_num = session.get('quiz_table_num', 1)
    questions = session['quiz_questions']
    
    score = 0
    total = len(questions)
    answers = []
    
    for q in questions:
        user_answer = request.form.get(f'q{q["id"]}', '')
        correct = int(user_answer) == q['answer'] if user_answer.isdigit() else False
        if correct:
            score += 1
        answers.append({
            'question': q['question'],
            'user_answer': user_answer,
            'correct_answer': q['answer'],
            'correct': correct
        })
    
    # Save result
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO quiz_results (child_id, topic, score, total) VALUES (%s, %s, %s, %s)',
              (child_id, topic, score, total))
    
    pct = int(score / total * 100)
    passed = pct >= 80
    
    if passed:
        mark_division_passed(child_id, table_num, score)
        award_badge(child_id, f'div_table_{table_num}_passed')
        
        # If all 15 division tables passed, award badge
        all_d = get_all_division_progress(child_id)
        all_passed = all(all_d[i]['quiz_score'] >= 80 for i in range(1, 16))
        if all_passed:
            award_badge(child_id, 'division_champion')
    
    conn.commit()
    conn.close()
    update_streak(child_id)
    
    return render_template('quiz_table_result.html',
                           score=score,
                           total=total,
                           percentage=pct,
                           passed=passed,
                           answers=answers,
                           table_num=table_num,
                           operation='div')

# ============ ADDITION LEARN ROUTES ============
@app.route('/learn_add')
def learn_add():
    if 'child_id' not in session:
        return redirect('/child/login')
    child_id = session['child_id']
    all_addition = get_all_addition_progress(child_id)
    return render_template('learn_add.html',
                           child_name=session['child_name'],
                           all_addition=all_addition)

@app.route('/learn_add/<int:table_num>')
def learn_addition_table(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    if table_num < 1 or table_num > 15:
        return redirect('/learn_add')
    child_id = session['child_id']
    all_addition = get_all_addition_progress(child_id)
    if table_num > 1 and all_addition[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn_add')
    questions = []
    for i in range(1, 16):
        questions.append({
            'id': i,
            'question': f"{table_num} + {i}",
            'answer': table_num + i,
            'hint': f"Count up {table_num} and count forward {i} more!",
            'explanation': f"{table_num} + {i} means start at {table_num} and count forward {i} steps. {table_num} + {i} = {table_num + i}."
        })
    return render_template('learn_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'],
                           operation='add')

@app.route('/quiz_add/<int:table_num>')
def quiz_add(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    if table_num < 1 or table_num > 15:
        return redirect('/learn_add')
    child_id = session['child_id']
    all_addition = get_all_addition_progress(child_id)
    if table_num > 1 and all_addition[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn_add')
    questions = []
    nums = list(range(1, 16))
    random.shuffle(nums)
    selected = nums[:15]
    for idx, i in enumerate(selected):
        questions.append({
            'id': idx + 1,
            'question': f"{table_num} + {i}",
            'answer': table_num + i
        })
    session['quiz_questions'] = questions
    session['quiz_topic'] = f'add_table_{table_num}'
    session['quiz_table_num'] = table_num
    session['quiz_operation'] = 'add'
    return render_template('quiz_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'],
                           operation='add')

@app.route('/submit_addition_quiz', methods=['POST'])
def submit_addition_quiz():
    if 'child_id' not in session or 'quiz_questions' not in session:
        return redirect('/child/login')
    child_id = session['child_id']
    topic = session['quiz_topic']
    table_num = session.get('quiz_table_num', 1)
    questions = session['quiz_questions']
    score = 0
    total = len(questions)
    answers = []
    for q in questions:
        user_answer = request.form.get(f'q{q["id"]}', '')
        correct = int(user_answer) == q['answer'] if user_answer.isdigit() else False
        if correct:
            score += 1
        answers.append({
            'question': q['question'],
            'user_answer': user_answer,
            'correct_answer': q['answer'],
            'correct': correct
        })
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO quiz_results (child_id, topic, score, total) VALUES (%s, %s, %s, %s)',
              (child_id, topic, score, total))
    pct = int(score / total * 100)
    passed = pct >= 80
    if passed:
        mark_addition_passed(child_id, table_num, score)
        award_badge(child_id, f'add_table_{table_num}_passed')
        all_a = get_all_addition_progress(child_id)
        if all(all_a[i]['quiz_score'] >= 80 for i in range(1, 16)):
            award_badge(child_id, 'addition_champion')
    conn.commit()
    conn.close()
    update_streak(child_id)
    return render_template('quiz_table_result.html',
                           score=score,
                           total=total,
                           percentage=pct,
                           passed=passed,
                           answers=answers,
                           table_num=table_num,
                           operation='add')

# ============ SUBTRACTION LEARN ROUTES ============
@app.route('/learn_sub')
def learn_sub():
    if 'child_id' not in session:
        return redirect('/child/login')
    child_id = session['child_id']
    all_subtraction = get_all_subtraction_progress(child_id)
    return render_template('learn_sub.html',
                           child_name=session['child_name'],
                           all_subtraction=all_subtraction)

@app.route('/learn_sub/<int:table_num>')
def learn_subtraction_table(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    if table_num < 1 or table_num > 15:
        return redirect('/learn_sub')
    child_id = session['child_id']
    all_subtraction = get_all_subtraction_progress(child_id)
    if table_num > 1 and all_subtraction[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn_sub')
    questions = []
    for i in range(1, 16):
        total = table_num + i
        questions.append({
            'id': i,
            'question': f"{total} - {table_num}",
            'answer': i,
            'hint': f"Think: {total} minus {table_num}. Remove {table_num} from {total}!",
            'explanation': f"{total} - {table_num} means start at {total} and count backwards {table_num} steps. {table_num} + {i} = {total}, so {total} - {table_num} = {i}."
        })
    return render_template('learn_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'],
                           operation='sub')

@app.route('/quiz_sub/<int:table_num>')
def quiz_sub(table_num):
    if 'child_id' not in session:
        return redirect('/child/login')
    if table_num < 1 or table_num > 15:
        return redirect('/learn_sub')
    child_id = session['child_id']
    all_subtraction = get_all_subtraction_progress(child_id)
    if table_num > 1 and all_subtraction[table_num - 1]['quiz_score'] < 80:
        return redirect('/learn_sub')
    questions = []
    nums = list(range(1, 16))
    random.shuffle(nums)
    selected = nums[:15]
    for idx, i in enumerate(selected):
        total = table_num + i
        questions.append({
            'id': idx + 1,
            'question': f"{total} - {table_num}",
            'answer': i
        })
    session['quiz_questions'] = questions
    session['quiz_topic'] = f'sub_table_{table_num}'
    session['quiz_table_num'] = table_num
    session['quiz_operation'] = 'sub'
    return render_template('quiz_table.html',
                           table_num=table_num,
                           questions=questions,
                           child_name=session['child_name'],
                           operation='sub')

@app.route('/submit_subtraction_quiz', methods=['POST'])
def submit_subtraction_quiz():
    if 'child_id' not in session or 'quiz_questions' not in session:
        return redirect('/child/login')
    child_id = session['child_id']
    topic = session['quiz_topic']
    table_num = session.get('quiz_table_num', 1)
    questions = session['quiz_questions']
    score = 0
    total = len(questions)
    answers = []
    for q in questions:
        user_answer = request.form.get(f'q{q["id"]}', '')
        correct = int(user_answer) == q['answer'] if user_answer.isdigit() else False
        if correct:
            score += 1
        answers.append({
            'question': q['question'],
            'user_answer': user_answer,
            'correct_answer': q['answer'],
            'correct': correct
        })
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO quiz_results (child_id, topic, score, total) VALUES (%s, %s, %s, %s)',
              (child_id, topic, score, total))
    pct = int(score / total * 100)
    passed = pct >= 80
    if passed:
        mark_subtraction_passed(child_id, table_num, score)
        award_badge(child_id, f'sub_table_{table_num}_passed')
        all_s = get_all_subtraction_progress(child_id)
        if all(all_s[i]['quiz_score'] >= 80 for i in range(1, 16)):
            award_badge(child_id, 'subtraction_champion')
    conn.commit()
    conn.close()
    update_streak(child_id)
    return render_template('quiz_table_result.html',
                           score=score,
                           total=total,
                           percentage=pct,
                           passed=passed,
                           answers=answers,
                           table_num=table_num,
                           operation='sub')

# ============ EXAM ROUTES ============
@app.route('/exam')
def exam():
    if 'child_id' not in session:
        return redirect('/child/login')
    child_id = session['child_id']
    if not check_exam_eligible(child_id):
        return redirect('/student/dashboard')
    questions = generate_exam_questions()
    session['exam_questions'] = questions
    exam_result = get_exam_result(child_id)
    return render_template('exam.html',
                           child_name=session['child_name'],
                           questions=questions,
                           exam_result=exam_result)

@app.route('/exam/submit', methods=['POST'])
def exam_submit():
    if 'child_id' not in session or 'exam_questions' not in session:
        return redirect('/child/login')
    child_id = session['child_id']
    questions = session['exam_questions']
    score = 0
    total = len(questions)
    answers = []
    topic_wrong = {}

    for q in questions:
        user_answer = request.form.get(f'q{q["id"]}', '').strip()
        correct = False
        if user_answer.lstrip('-').isdigit():
            correct = int(user_answer) == q['answer']
        answers.append({
            'id': q['id'],
            'question': q['text'],
            'answer': q['answer'],
            'user_answer': user_answer,
            'correct': correct,
            'topic': q['topic'],
            'format': q['format']
        })
        if not correct:
            topic = q['topic']
            topic_wrong[topic] = topic_wrong.get(topic, 0) + 1

    score = sum(1 for a in answers if a['correct'])
    pct = int(score / total * 100)
    passed = pct >= 80

    import json
    answers_json = json.dumps(answers)
    exam_id = save_exam_result(child_id, score, total, passed, answers_json)

    # Topic help guidance
    topic_help = {
        'multiplication': {
            'name': 'Times Tables',
            'icon': '✖️',
            'tip': 'Try counting in groups! If you know 7x5, you also know 7+7+7+7+7. Or use the trick: multiply by 10 then subtract one group!',
            'route': '/learn/'
        },
        'division': {
            'name': 'Division',
            'icon': '➗',
            'tip': 'Division is the opposite of multiplication! If 8x3=24, then 24÷3=8. Think: how many groups of the divisor fit into the number?',
            'route': '/learn_div/'
        },
        'addition': {
            'name': 'Addition',
            'icon': '➕',
            'tip': 'Try counting forward from the bigger number! For 7+4, start at 7 and count forward 4 steps: 8, 9, 10, 11.',
            'route': '/learn_add/'
        },
        'subtraction': {
            'name': 'Subtraction',
            'icon': '➖',
            'tip': 'Subtraction is the opposite of addition! For 15-7, think 7+?=15. Or count backwards from the bigger number!',
            'route': '/learn_sub/'
        },
    }

    weak_topics = sorted(topic_wrong.items(), key=lambda x: x[1], reverse=True)
    weak_topics_info = [{'topic': t, **topic_help[t]} for t, _ in weak_topics if t in topic_help]

    # If passed, notify parent
    if passed:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT p.email, p.name as parent_name, ch.name as child_name FROM children ch JOIN parents p ON ch.parent_id = p.id WHERE ch.id = %s', (child_id,))
        parent = c.fetchone()
        conn.close()
        if parent:
            # Award exam champion badge
            award_badge(child_id, 'math_champion')

    update_streak(child_id)
    return render_template('exam_result.html',
                           score=score,
                           total=total,
                           percentage=pct,
                           passed=passed,
                           answers=answers,
                           weak_topics=weak_topics_info,
                           exam_id=exam_id,
                           child_name=session['child_name'])

# ============ GAMES ============
# ============ EXTRA GAMES (from open source) ============
@app.route('/game/pacman')
def game_pacman():
    if 'child_id' not in session:
        return redirect('/child/login')
    return render_template('game_pacman.html', child_name=session['child_name'])

@app.route('/game/breakout')
def game_breakout():
    if 'child_id' not in session:
        return redirect('/child/login')
    return render_template('game_breakout.html', child_name=session['child_name'])

@app.route('/game/snake')
def game_snake():
    if 'child_id' not in session:
        return redirect('/child/login')
    return render_template('game_snake.html', child_name=session['child_name'])

# ============ TUTOR BOT API ============
@app.route('/api/tutor', methods=['POST'])
def tutor_api():
    if 'child_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    question = data.get('question', '').strip()
    wants_answer = data.get('wants_answer', False)
    
    if not question:
        return jsonify({'reply': "I'm not sure what you mean! Can you tell me the math problem you're looking at?"})
    
    # Parse the question - expect format like "7 × 8" or "3 x 4"
    import re
    match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', question)
    
    if not match:
        return jsonify({'reply': f"Hmm, I didn't catch that! Can you tell me your problem using the format '7 × 8'? For example: 'Can you help me with 7 × 8?'"})
    
    a = int(match.group(1))
    b = int(match.group(2))
    answer = a * b
    
    # Build child-friendly explanation
    groups_a = ' + '.join([str(a)] * b)
    groups_b = ' + '.join([str(b)] * a)
    
    reply = f"Great question! Let's work out **{a} × {b}** together!\n\n"
    reply += f"**Here's a trick:** Multiplication is just fast adding!\n\n"
    reply += f"Think of it as **{b} groups of {a}**:\n"
    reply += f"That means: {groups_a}\n\n"
    reply += f"Counting in {a}s {b} times: "
    
    running = 0
    parts = []
    for i in range(1, b + 1):
        running += a
        parts.append(f"{running}")
    reply += ', '.join(parts) + f"\n\n"
    reply += f"**{a} × {b} = {answer}**\n\n"
    reply += f"Try it yourself: what's {a + 1} × {b}? (Count in {a+1}s!)"
    
    return jsonify({
        'reply': reply,
        'answer': answer,
        'explanation': f"{a} × {b} means {a} groups of {b} or {b} groups of {a}. Adding {a} together {b} times gives {answer}."
    })

# ============ API ROUTES ============
@app.route('/api/progress', methods=['GET'])
def api_progress():
    if 'child_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    progress = get_child_progress(session['child_id'])
    return jsonify(progress)

@app.route('/api/update_table_progress', methods=['POST'])
def api_update_table_progress():
    if 'child_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    table_num = data.get('table_num', 1)
    topic = f'table_{table_num}'
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO progress (child_id, topic, questions_completed, quiz_score, quiz_taken)
        VALUES (?, ?, 1, 0, 0)
        ON CONFLICT(child_id, topic) DO UPDATE SET
        questions_completed = questions_completed + 1,
        last_activity = CURRENT_TIMESTAMP
    ''', (session['child_id'], topic))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ============ CERTIFICATE ============
@app.route('/certificate/<int:child_id>')
def certificate(child_id):
    sample = request.args.get('sample') == '1'

    # Must be logged in as a parent (unless sample mode)
    if not sample and 'parent_id' not in session:
        return redirect('/parent/login')
    
    conn = get_db()
    c = conn.cursor()

    if sample:
        # Sample mode: no auth, fake data
        mult_passed = div_passed = add_passed = sub_passed = 15
        import datetime
        exam = type('obj', (object,), {'score': 58, 'percentage': 97, 'taken_at': datetime.datetime(2026, 4, 12)})()
        child_name = "Alex Thompson"
    else:
        c.execute('SELECT * FROM children WHERE id = %s AND parent_id = %s', (child_id, session['parent_id']))
        child = c.fetchone()
        if not child:
            conn.close()
            return redirect('/parent/dashboard')
        
        # Get best exam result
        c.execute('SELECT * FROM exam_results WHERE child_id = %s AND passed = 1 ORDER BY percentage DESC LIMIT 1', (child_id,))
        exam = c.fetchone()
        
        # Get all table progress
        all_mult = get_all_table_progress(child_id)
        all_div = get_all_division_progress(child_id)
        all_add = get_all_addition_progress(child_id)
        all_sub = get_all_subtraction_progress(child_id)
        
        mult_passed = sum(1 for i in range(1, 16) if all_mult[i]['quiz_score'] >= 80)
        div_passed = sum(1 for i in range(1, 16) if all_div[i]['quiz_score'] >= 80)
        add_passed = sum(1 for i in range(1, 16) if all_add[i]['quiz_score'] >= 80)
        sub_passed = sum(1 for i in range(1, 16) if all_sub[i]['quiz_score'] >= 80)
        child_name = child['name']

        # Only show certificate if all 60 tables passed (15 each × 4 operations)
        all_tables_done = mult_passed == 15 and div_passed == 15 and add_passed == 15 and sub_passed == 15
        if not all_tables_done:
            conn.close()
            return redirect('/parent/dashboard')

    conn.close()
    return render_template('certificate.html',
                           child_name=child_name,
                           exam=exam,
                           mult_passed=mult_passed,
                           div_passed=div_passed,
                           add_passed=add_passed,
                           sub_passed=sub_passed)

# ============ PARENT ADVISOR API ============
@app.route('/api/parent/advice', methods=['POST'])
def parent_advice():
    import logging
    app.logger.setLevel(logging.DEBUG)
    data = request.get_json()
    child_id = data.get('child_id')
    app.logger.debug('parent_advice called with child_id=%s', child_id)
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM children WHERE id = %s', (child_id,))
    child = c.fetchone()
    if not child:
        conn.close()
        return jsonify({'advice': 'Child not found.'})
    
    child_name = child['name']
    day_streak = dict(child).get('day_streak', 0)
    conn.close()
    
    all_mult = get_all_table_progress(child_id)
    all_div = get_all_division_progress(child_id)
    all_add = get_all_addition_progress(child_id)
    all_sub = get_all_subtraction_progress(child_id)
    
    # Scores per table for each operation
    def table_scores(prog):
        return {i: prog[i]['quiz_score'] for i in range(1, 16)}
    
    def passed_tables(scores):
        return sorted([i for i in scores if scores[i] >= 80])
    
    def struggling_tables(scores):
        return sorted([i for i in scores if 0 < scores[i] < 80])
    
    def not_started(scores):
        return sorted([i for i in scores if scores[i] == 0])
    
    mult_scores = table_scores(all_mult)
    div_scores = table_scores(all_div)
    add_scores = table_scores(all_add)
    sub_scores = table_scores(all_sub)
    
    mult_passed = passed_tables(mult_scores)
    div_passed = passed_tables(div_scores)
    add_passed = passed_tables(add_scores)
    sub_passed = passed_tables(sub_scores)
    
    mult_struggling = struggling_tables(mult_scores)
    div_struggling = struggling_tables(div_scores)
    add_struggling = struggling_tables(add_scores)
    sub_struggling = struggling_tables(sub_scores)
    
    mult_not_started = not_started(mult_scores)
    div_not_started = not_started(div_scores)
    add_not_started = not_started(add_scores)
    sub_not_started = not_started(sub_scores)
    
    total_passed = len(mult_passed) + len(div_passed) + len(add_passed) + len(sub_passed)
    total_tables = 60
    
    # Exam results
    exam_res = get_exam_result(child_id)
    exam_passed = exam_res and exam_res.get('passed')
    exam_pct = exam_res.get('percentage', 0) if exam_res else 0
    
    all_mastered = len(mult_passed) == 15 and len(div_passed) == 15 and len(add_passed) == 15 and len(sub_passed) == 15
    
    def fmt_list(nums, op=''):
        if not nums: return 'none'
        if len(nums) <= 5: 
            if op == 'div': return ', '.join(['%d÷%d=%d' % (n, n, 1) if op=='div' else str(n) for n in nums])
            return ', '.join(str(n) for n in nums)
        return '%d tables' % len(nums)
    
    def op_summary(name, passed, struggling, not_started, scores):
        lines = []
        total = len(passed)
        lines.append('%s: %d/15 tables mastered.' % (name, total))
        if passed:
            lines.append('  Mastered: table %s.' % ', '.join(str(n) for n in passed))
        if struggling:
            scores_str = ', '.join(['%d (%d%%)' % (n, scores[n]) for n in struggling[:6]])
            lines.append('  Needs work: table %s.' % scores_str)
            if len(struggling) > 6: lines.append('  Plus %d more tables also need practice.' % (len(struggling) - 6))
        if not_started:
            lines.append('  Not started yet: tables %s.' % ', '.join(str(n) for n in not_started[:5]))
            if len(not_started) > 5: lines.append('  Plus %d more not yet started.' % (len(not_started) - 5))
        return ' '.join(lines)
    
    # --- BUILD COMPREHENSIVE REPORT ---
    report = []
    
    # Header
    report.append('DETAILED MATHS REPORT FOR %s.' % child_name.upper())
    if day_streak > 0:
        report.append('Current learning streak: %d day%s!' % (day_streak, 's' if day_streak != 1 else ''))
    report.append('')
    
    # Overall progress
    report.append('OVERALL PROGRESS: %d of 60 tables mastered.' % total_passed)
    pct = int(total_passed / 60 * 100)
    report.append('That is %d percent complete across all four operations.' % pct)
    if exam_passed:
        report.append('%s has passed the final exam with %d percent!' % (child_name, exam_pct))
    elif exam_res:
        report.append('%s sat the exam but did not pass yet (%d percent). Keep practising!' % (child_name, exam_pct))
    if all_mastered:
        report.append('INCREDIBLE: %s has mastered ALL 60 tables! A true maths champion!' % child_name)
        return jsonify({'advice': ' '.join(report)})
    
    # Per-operation breakdown
    report.append('')
    report.append('TIMES TABLES: %d of 15 mastered.' % len(mult_passed))
    if mult_passed:
        report.append('  Confident with: %s.' % ', '.join(str(n) for n in mult_passed))
    if mult_struggling:
        r = ['Table %d (currently %d%%)' % (n, mult_scores[n]) for n in mult_struggling[:5]]
        report.append('  Still learning: %s.' % ', '.join(r))
        if len(mult_struggling) > 5:
            report.append('  Also: %d more tables need attention.' % (len(mult_struggling) - 5))
    if mult_not_started and len(mult_not_started) <= 5:
        report.append('  Not yet studied: tables %s.' % ', '.join(str(n) for n in mult_not_started))
    
    report.append('')
    report.append('DIVISION: %d of 15 mastered.' % len(div_passed))
    if div_passed:
        report.append('  Confident with: %s.' % ', '.join(str(n) for n in div_passed))
    if div_struggling:
        r = ['Table %d (currently %d%%)' % (n, div_scores[n]) for n in div_struggling[:5]]
        report.append('  Still learning: %s.' % ', '.join(r))
        if len(div_struggling) > 5:
            report.append('  Also: %d more tables need attention.' % (len(div_struggling) - 5))
    
    report.append('')
    report.append('ADDITION: %d of 15 mastered.' % len(add_passed))
    if add_passed:
        report.append('  Confident with: %s.' % ', '.join(str(n) for n in add_passed))
    if add_struggling:
        r = ['Table %d (currently %d%%)' % (n, add_scores[n]) for n in add_struggling[:5]]
        report.append('  Still learning: %s.' % ', '.join(r))
    
    report.append('')
    report.append('SUBTRACTION: %d of 15 mastered.' % len(sub_passed))
    if sub_passed:
        report.append('  Confident with: %s.' % ', '.join(str(n) for n in sub_passed))
    if sub_struggling:
        r = ['Table %d (currently %d%%)' % (n, sub_scores[n]) for n in sub_struggling[:5]]
        report.append('  Still learning: %s.' % ', '.join(r))
    
    # Priority recommendations
    report.append('')
    report.append('RECOMMENDED ORDER OF STUDY:')
    # Find the weakest operation
    op_progress = [
        ('Times Tables (x)', len(mult_passed), mult_struggling, mult_not_started),
        ('Division (÷)', len(div_passed), div_struggling, div_not_started),
        ('Addition (+)', len(add_passed), add_struggling, add_not_started),
        ('Subtraction (−)', len(sub_passed), sub_struggling, sub_not_started),
    ]
    op_progress.sort(key=lambda x: x[1])
    for rank, (opname, p, st, ns) in enumerate(op_progress, 1):
        if p == 15:
            report.append('  %d. %s - COMPLETE!' % (rank, opname))
        elif p == 0 and not st:
            report.append('  %d. %s - Not started yet. Begin here!' % (rank, opname))
        elif st:
            report.append('  %d. %s - Priority. Focus on: %s.' % (rank, opname, ', '.join('table %d' % n for n in st[:4])))
        else:
            report.append('  %d. %s - Almost there! %d tables to go.' % (rank, opname, 15-p))
    
    # Top priorities - specific tables
    priority_tables = []
    for scores, name in [(mult_scores, 'Times Tables'), (div_scores, 'Division'), (add_scores, 'Addition'), (sub_scores, 'Subtraction')]:
        for t in struggling_tables(scores):
            priority_tables.append((scores[t], t, name))
    priority_tables.sort()
    
    if priority_tables:
        report.append('')
        report.append('MOST urgent focus areas:')
        for score, tbl, opname in priority_tables[:6]:
            report.append('  Table %s in %s is at %d percent - needs extra practice!' % (tbl, opname, score))
    
    # Study plan
    report.append('')
    report.append('SUGGESTED WEEKLY STUDY PLAN:')
    report.append('  Monday: 15 minutes on weakest operation. Use flashcards or Maths Man game.')
    report.append('  Tuesday: 15 minutes on second weakest. Use Target Shoot game for speed.')
    report.append('  Wednesday: 10 minutes quick revision of problem tables.')
    report.append('  Thursday: 15 minutes on third weakest operation.')
    report.append('  Friday: 15 minutes - mix of all weak areas. Reward with Math Snake game!')
    report.append('  Saturday: Free choice - any game or activity they enjoy.')
    report.append('  Sunday: Rest day or very light 5-minute review.')
    report.append('  Tip: Short 10-15 minute daily sessions are more effective than one long session per week.')
    
    # How parents can help
    report.append('')
    report.append('HOW YOU CAN HELP AS A PARENT:')
    if mult_struggling:
        report.append('  Times Tables: Ask %s random %d and %d multiplication questions during car journeys or dinner.' % (child_name, mult_struggling[0], mult_struggling[0] if len(mult_struggling) > 1 else mult_struggling[0] + 1))
    if div_struggling:
        report.append('  Division: Use real-life examples like sharing %d sweets between %d friends.' % (div_struggling[0] * 3, div_struggling[0]))
    if add_struggling:
        report.append('  Addition: Play adding games with household objects - count buttons, stairs, fruit.')
    if sub_struggling:
        report.append('  Subtraction: Practice taking away with toys or snacks.')
    report.append('  Praise effort, not just correct answers - this builds maths confidence.')
    report.append('  Celebrate each time a table reaches 80 percent - this earns a new badge!')
    report.append('  Keep sessions fun and pressure-free. Forced practice backfires.')
    
    # Motivational close
    report.append('')
    if pct >= 75:
        report.append('%s is making fantastic progress! Only a few more tables to go. Keep up the brilliant work!' % child_name)
    elif pct >= 50:
        report.append('%s is over halfway there! Steady daily practice will get them to mastery soon.' % child_name)
    elif pct >= 25:
        report.append('%s has made a solid start. Regular short practice sessions are the key to fast progress.' % child_name)
    else:
        report.append('%s is just beginning their maths journey. Every expert was once a beginner - let us get started!' % child_name)
    
    if day_streak >= 7:
        report.append('Amazing: %s has a %d-day learning streak! That consistency is building real maths skills.' % (child_name, day_streak))
    
    return jsonify({'advice': ' '.join(report)})

# ============ TTS ENDPOINT (edge-tts) ============
@app.route('/api/tts', methods=['POST'])
def api_tts():
    try:
        import tempfile, os, asyncio, edge_tts
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'en-GB-RyanNeural')
        if not text:
            return jsonify({'error': 'no text'}), 400

        async def generate():
            comm = edge_tts.Communicate(text=text, voice=voice)
            tmp = os.path.join(tempfile.gettempdir(), 'mq_tts.mp3')
            await comm.save(tmp)
            with open(tmp, 'rb') as f:
                return f.read()

        mp3_data = asyncio.run(generate())
        return Response(mp3_data, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ STRIPE PAYMENT ROUTES ============

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    """Buy page — capture email and redirect to Stripe Checkout."""
    if not STRIPE_AVAILABLE:
        return render_template('buy.html', error="Payment system is being set up. Please try again soon.")
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or '@' not in email:
            return render_template('buy.html', error="Please enter a valid email address.")
        
        # Generate a unique access code for this purchase
        access_code = 'MQ' + str(uuid.uuid4())[:8].upper()
        
        base_url = request.url_root.rstrip('/')
        success_url = f"{base_url}/payment/success?session_id={'{CHECKOUT_SESSION_ID}'}"
        cancel_url = f"{base_url}/buy"
        
        try:
            result = stripe_payment.create_checkout_session(
                email=email,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            stripe_payment.save_pending_payment(result['id'], email, access_code)
            return redirect(result['url'])
        except Exception as e:
            logging.error(f"Stripe error: {e}")
            return render_template('buy.html', error=f"Payment error: {str(e)}. Please try again.")
    
    return render_template('buy.html')


@app.route('/payment/success', methods=['GET'])
def payment_success():
    """Page shown after successful Stripe payment."""
    session_id = request.args.get('session_id', '')
    email = request.args.get('email', '')
    
    if session_id and not email:
        pending = stripe_payment.get_pending_payment(session_id)
        if pending:
            email = pending.get('email', '')
    
    return render_template('payment_success.html',
                         email=email or session_id,
                         session_id=session_id)


@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Stripe webhook — fires when payment is confirmed. Sends access code automatically."""
    if not STRIPE_AVAILABLE:
        return jsonify({'error': 'Stripe not configured'}), 400
    
    payload = request.get_data()
    sig = request.headers.get('stripe-signature', request.headers.get('Stripe-Signature', ''))
    
    try:
        event = stripe_payment.construct_webhook_event(payload, sig)
    except Exception as e:
        logging.error(f"Webhook verification failed: {e}")
        return jsonify({'error': str(e)}), 400
    
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        session_id = session_obj.get('id', '')
        buyer_email = (session_obj.get('customer_email', '') or
                       session_obj.get('customer_details', {}).get('email', ''))
        
        pending = stripe_payment.get_pending_payment(session_id)
        if pending and buyer_email:
            access_code = pending.get('access_code', '')
            if access_code:
                stripe_payment.send_access_code_email(buyer_email, access_code)
                # Register code in DB
                try:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute('INSERT OR IGNORE INTO access_codes (code, used) VALUES (%s, 0)', (access_code,))
                    conn.commit()
                    conn.close()
                except Exception as db_err:
                    logging.error(f"DB error: {db_err}")
                stripe_payment.remove_pending_payment(session_id)
                logging.info(f"Access code {access_code} sent to {buyer_email}")
    
    return jsonify({'received': True})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
