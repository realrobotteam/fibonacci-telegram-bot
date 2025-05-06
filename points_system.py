import sqlite3
from datetime import datetime, timedelta
import os

class PointsSystem:
    def __init__(self):
        self.db_path = 'points.db'
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # جدول کاربران
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id INTEGER PRIMARY KEY,
                     points INTEGER DEFAULT 100,
                     last_reset_date TEXT,
                     referral_code TEXT UNIQUE)''')
        
        # جدول رفرال‌ها
        c.execute('''CREATE TABLE IF NOT EXISTS referrals
                    (referrer_id INTEGER,
                     referred_id INTEGER,
                     date TEXT,
                     FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                     FOREIGN KEY (referred_id) REFERENCES users(user_id))''')
        
        conn.commit()
        conn.close()

    def get_user_points(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی وجود کاربر
        c.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            # اگر کاربر وجود نداشت، آن را با امتیاز پیش‌فرض ایجاد کن
            c.execute('INSERT INTO users (user_id, points, last_reset_date) VALUES (?, 100, ?)',
                     (user_id, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            return 100
        
        c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 100

    def deduct_points(self, user_id, amount=5):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی و ریست امتیازات روزانه
        self._check_daily_reset(user_id)
        
        # بررسی وجود کاربر
        c.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            # اگر کاربر وجود نداشت، آن را با امتیاز پیش‌فرض ایجاد کن
            c.execute('INSERT INTO users (user_id, points, last_reset_date) VALUES (?, 100, ?)',
                     (user_id, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
        
        # کسر امتیاز
        c.execute('UPDATE users SET points = points - ? WHERE user_id = ? AND points >= ?',
                 (amount, user_id, amount))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def add_referral_points(self, referrer_id, referred_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی اینکه آیا این رفرال قبلاً ثبت شده است
        c.execute('SELECT 1 FROM referrals WHERE referred_id = ?', (referred_id,))
        if c.fetchone():
            conn.close()
            return False
        
        # اضافه کردن امتیاز به دعوت‌کننده
        c.execute('UPDATE users SET points = points + 50 WHERE user_id = ?', (referrer_id,))
        
        # ثبت رفرال
        c.execute('INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)',
                 (referrer_id, referred_id, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
        return True

    def _check_daily_reset(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT last_reset_date FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if not result or result[0] != today:
            c.execute('''INSERT OR REPLACE INTO users (user_id, points, last_reset_date)
                        VALUES (?, 100, ?)''', (user_id, today))
            conn.commit()
        
        conn.close()

    def generate_referral_code(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # تولید کد رفرال منحصر به فرد
        import uuid
        referral_code = str(uuid.uuid4())[:8]
        
        c.execute('UPDATE users SET referral_code = ? WHERE user_id = ?',
                 (referral_code, user_id))
        
        conn.commit()
        conn.close()
        return referral_code

    def get_referral_code(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if not result or not result[0]:
            referral_code = self.generate_referral_code(user_id)
        else:
            referral_code = result[0]
        
        conn.close()
        return referral_code 