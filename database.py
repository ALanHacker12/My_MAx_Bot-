import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'volunteers.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            age INTEGER,
            is_adult BOOLEAN DEFAULT 0,
            registration_date TEXT,
            total_points INTEGER DEFAULT 0,
            help_count INTEGER DEFAULT 0,
            phone TEXT,
            city TEXT
        )
    ''')
    
    # Таблица отзывов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            feedback TEXT,
            created_at TEXT
        )
    ''')
    
    # Таблица добрых дел
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS good_deeds (
            deed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            deed_type TEXT,
            description TEXT,
            points INTEGER,
            photo_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            verified_at TEXT,
            verified_by INTEGER
        )
    ''')
    
    # Таблица семей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS families (
            family_id INTEGER PRIMARY KEY AUTOINCREMENT,
            adult_id INTEGER,
            child_id INTEGER,
            family_name TEXT,
            total_points INTEGER DEFAULT 0,
            created_date TEXT,
            FOREIGN KEY (adult_id) REFERENCES users (user_id),
            FOREIGN KEY (child_id) REFERENCES users (user_id)
        )
    ''')
    
    # Таблица истории баллов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            points INTEGER,
            reason TEXT,
            created_at TEXT
        )
    ''')
    
    # Таблица заявок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            phone TEXT,
            city TEXT,
            category TEXT,
            details TEXT,
            type TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            answered_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных готова")

def register_user(user_id, username, full_name, age=30, phone='', city=''):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    
    now = datetime.now().isoformat()
    
    if exists:
        cursor.execute('''
            UPDATE users SET username = ?, full_name = ?, age = ?, phone = ?, city = ?
            WHERE user_id = ?
        ''', (username, full_name, age, phone, city, user_id))
    else:
        is_adult = age >= 55
        cursor.execute('''
            INSERT INTO users (user_id, username, full_name, age, is_adult, registration_date, total_points, help_count, phone, city)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
        ''', (user_id, username, full_name, age, is_adult, now, phone, city))
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def add_feedback(user_id, username, full_name, feedback):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO feedback (user_id, username, full_name, feedback, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, feedback, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_feedback(limit=20):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM feedback 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_leaderboard(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT full_name, total_points, help_count 
        FROM users 
        WHERE total_points > 0
        ORDER BY total_points DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_points(user_id, points, reason):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET total_points = total_points + ?, help_count = help_count + 1
        WHERE user_id = ?
    ''', (points, user_id))
    cursor.execute('''
        INSERT INTO points_history (user_id, points, reason, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, points, reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_points_history(user_id, days=30):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT points, reason, created_at 
        FROM points_history 
        WHERE user_id = ? AND created_at > datetime('now', ?)
        ORDER BY created_at DESC
    ''', (user_id, f'-{days} days'))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_good_deed(user_id, deed_type, description, points, photo_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO good_deeds (user_id, deed_type, description, points, photo_id, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    ''', (user_id, deed_type, description, points, photo_id, datetime.now().isoformat()))
    deed_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return deed_id

def get_good_deeds(user_id, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM good_deeds 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def verify_deed(deed_id, verified_by, approved=True):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, points FROM good_deeds WHERE deed_id = ?', (deed_id,))
    deed = cursor.fetchone()
    
    if deed:
        status = 'verified' if approved else 'rejected'
        cursor.execute('''
            UPDATE good_deeds 
            SET status = ?, verified_at = ?, verified_by = ?
            WHERE deed_id = ?
        ''', (status, datetime.now().isoformat(), verified_by, deed_id))
        
        if approved:
            add_points(deed['user_id'], deed['points'], f"Доброе дело #{deed_id}")
    
    conn.commit()
    conn.close()
    return deed is not None

def create_family(adult_id, child_id, family_name=None):
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем возраст
    adult = get_user(adult_id)
    child = get_user(child_id)
    
    if not adult or not child:
        conn.close()
        return False, "Пользователь не найден"
    
    if not adult.get('is_adult'):
        conn.close()
        return False, "Взрослый участник должен быть старше 55 лет"
    
    child_age = child.get('age', 0)
    if child_age < 10 or child_age > 16:
        conn.close()
        return False, "Ребенок должен быть в возрасте 10-16 лет"
    
    family_name = family_name or f"Семья_{adult_id}_{child_id}"
    
    cursor.execute('''
        INSERT INTO families (adult_id, child_id, family_name, created_date)
        VALUES (?, ?, ?, ?)
    ''', (adult_id, child_id, family_name, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return True, "Семья успешно создана!"

def get_family(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, u1.full_name as adult_name, u2.full_name as child_name
        FROM families f
        JOIN users u1 ON f.adult_id = u1.user_id
        JOIN users u2 ON f.child_id = u2.user_id
        WHERE f.adult_id = ? OR f.child_id = ?
    ''', (user_id, user_id))
    family = cursor.fetchone()
    conn.close()
    return dict(family) if family else None

def get_family_leaderboard(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT family_name, total_points 
        FROM families 
        WHERE total_points > 0
        ORDER BY total_points DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_request(user_id, user_name, phone, city, category, details, req_type):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO requests (user_id, user_name, phone, city, category, details, type, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    ''', (user_id, user_name, phone, city, category, details, req_type, datetime.now().isoformat()))
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return request_id

def get_requests(status='pending', limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM requests 
        WHERE status = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (status, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_request_answered(request_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE requests 
        SET status = 'answered', answered_at = ?
        WHERE request_id = ?
    ''', (datetime.now().isoformat(), request_id))
    conn.commit()
    conn.close()