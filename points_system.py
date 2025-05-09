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
        
        # بررسی و به‌روز‌رسانی ساختار دیتابیس برای پشتیبانی از فرمت تاریخ و زمان جدید
        self._update_database_structure()
        
        conn.commit()
        conn.close()

    def _update_database_structure(self):
        """
        به‌روز‌رسانی ساختار دیتابیس برای استفاده از فرمت تاریخ و زمان کامل
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی داده‌های موجود و تبدیل فرمت تاریخ قدیمی به فرمت جدید
        c.execute('SELECT user_id, last_reset_date FROM users')
        rows = c.fetchall()
        
        for user_id, last_reset_date in rows:
            if last_reset_date and ' ' not in last_reset_date:
                # اگر فرمت تاریخ قدیمی است (فقط تاریخ بدون زمان)
                try:
                    # تبدیل به فرمت جدید با زمان 00:00:00
                    date_obj = datetime.strptime(last_reset_date, '%Y-%m-%d')
                    new_date_format = date_obj.strftime('%Y-%m-%d 00:00:00')
                    
                    c.execute('UPDATE users SET last_reset_date = ? WHERE user_id = ?',
                             (new_date_format, user_id))
                except Exception as e:
                    print(f"Error updating date format for user {user_id}: {e}")
        
        conn.commit()
        conn.close()

    def get_user_points(self, user_id):
        """
        دریافت امتیاز کاربر و در صورت گذشت 24 ساعت، ریست امتیاز به 100
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        print(f"Getting points for user {user_id}")
        # ابتدا بررسی کنید که آیا باید امتیازات ریست شوند
        self._check_daily_reset(user_id)
        
        # بررسی وجود کاربر
        c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if not result:
            # اگر کاربر وجود نداشت، آن را با امتیاز پیش‌فرض ایجاد کن
            current_time = datetime.now()
            c.execute('INSERT INTO users (user_id, points, last_reset_date) VALUES (?, 100, ?)',
                     (user_id, current_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            print(f"Created new user {user_id} with 100 points")
            return 100
        
        points = result[0] if result else 100
        print(f"User {user_id} has {points} points")
        conn.close()
        return points

    def deduct_points(self, user_id, amount=5):
        """
        کسر امتیاز از کاربر
        """
        print(f"Attempting to deduct {amount} points from user {user_id}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی و ریست امتیازات روزانه
        self._check_daily_reset(user_id)
        
        # بررسی وجود کاربر
        c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if not result:
            print(f"User {user_id} not found, creating new user")
            # اگر کاربر وجود نداشت، آن را با امتیاز پیش‌فرض ایجاد کن
            current_time = datetime.now()
            c.execute('INSERT INTO users (user_id, points, last_reset_date) VALUES (?, 100, ?)',
                     (user_id, current_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            current_points = 100
        else:
            current_points = result[0]
            print(f"Current points for user {user_id}: {current_points}")
        
        if current_points >= amount:
            # اجرای کوئری کسر امتیاز
            print(f"Executing SQL UPDATE query: UPDATE users SET points = points - {amount} WHERE user_id = {user_id}")
            c.execute('UPDATE users SET points = points - ? WHERE user_id = ?',
                     (amount, user_id))
            rows_affected = c.rowcount
            print(f"SQL query affected {rows_affected} rows")
            success = rows_affected > 0
            print(f"Points deduction {'successful' if success else 'failed'}")
        else:
            print(f"Not enough points. Current: {current_points}, Required: {amount}")
            success = False
        
        # نمایش امتیاز کاربر بعد از کسر
        c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        after_result = c.fetchone()
        if after_result:
            print(f"Points after deduction: {after_result[0]}")
        else:
            print("Error: User not found after deduction!")
        
        conn.commit()
        conn.close()
        return success

    def add_referral_points(self, referrer_id, referred_id):
        """
        اضافه کردن امتیاز رفرال به کاربر دعوت‌کننده
        """
        # جلوگیری از دعوت خود کاربر
        if referrer_id == referred_id:
            print(f"User {referrer_id} tried to refer themselves")
            return False
            
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی اینکه آیا این رفرال قبلاً ثبت شده است
        c.execute('SELECT 1 FROM referrals WHERE referred_id = ?', (referred_id,))
        if c.fetchone():
            print(f"User {referred_id} was already referred by someone")
            conn.close()
            return False
            
        # بررسی اینکه آیا کاربر دعوت شده از قبل وجود دارد (برای جلوگیری از سوءاستفاده)
        c.execute('SELECT 1 FROM users WHERE user_id = ? AND points > 0', (referred_id,))
        if c.fetchone():
            print(f"User {referred_id} already exists and has been active before")
            conn.close()
            return False
        
        # محاسبه تعداد کل دعوت‌های موفق کاربر برای پاداش پلکانی
        c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (referrer_id,))
        referral_count = c.fetchone()[0]
        
        # امتیاز پایه برای دعوت
        base_points = 50
        
        # محاسبه امتیاز بر اساس تعداد دعوت‌های قبلی - سیستم پاداش پلکانی 10 مرحله‌ای
        bonus_points = 0
        
        if referral_count >= 100:  # بیش از 100 دعوت
            bonus_points = 950  # مجموع 1000 امتیاز
        elif referral_count >= 80:  # بیش از 80 دعوت
            bonus_points = 750  # مجموع 800 امتیاز
        elif referral_count >= 60:  # بیش از 60 دعوت
            bonus_points = 550  # مجموع 600 امتیاز
        elif referral_count >= 50:  # بیش از 50 دعوت
            bonus_points = 450  # مجموع 500 امتیاز
        elif referral_count >= 40:  # بیش از 40 دعوت
            bonus_points = 350  # مجموع 400 امتیاز
        elif referral_count >= 30:  # بیش از 30 دعوت
            bonus_points = 250  # مجموع 300 امتیاز
        elif referral_count >= 20:  # بیش از 20 دعوت
            bonus_points = 150  # مجموع 200 امتیاز
        elif referral_count >= 15:  # بیش از 15 دعوت
            bonus_points = 100  # مجموع 150 امتیاز
        elif referral_count >= 10:  # بیش از 10 دعوت
            bonus_points = 70  # مجموع 120 امتیاز
        elif referral_count >= 5:  # بیش از 5 دعوت
            bonus_points = 30  # مجموع 80 امتیاز
        
        total_points = base_points + bonus_points
        
        # اضافه کردن امتیاز به دعوت‌کننده
        c.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (total_points, referrer_id,))
        
        # ثبت رفرال
        current_time = datetime.now()
        c.execute('INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)',
                 (referrer_id, referred_id, current_time.strftime('%Y-%m-%d %H:%M:%S')))
        
        print(f"User {referrer_id} successfully referred user {referred_id} and got {total_points} points (base: {base_points}, bonus: {bonus_points})")
        conn.commit()
        conn.close()
        return total_points

    def _check_daily_reset(self, user_id):
        """
        بررسی و ریست امتیازات روزانه
        این تابع هر بار که کاربر ربات را باز می‌کند بررسی می‌کند که آیا 24 ساعت از آخرین بازدید گذشته است
        اگر بله، امتیاز کاربر به 100 تنظیم می‌شود
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT last_reset_date, points FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        current_time = datetime.now()
        
        if not result:
            # اگر کاربر وجود ندارد، آن را با امتیاز پیش‌فرض ایجاد کن
            c.execute('''INSERT INTO users (user_id, points, last_reset_date)
                        VALUES (?, 100, ?)''', (user_id, current_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            print(f"User {user_id} created with 100 points at {current_time}")
        else:
            # بررسی آیا 24 ساعت از آخرین ریست گذشته است
            last_reset = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S' if ' ' in result[0] else '%Y-%m-%d')
            current_points = result[1]
            
            if current_time - last_reset >= timedelta(hours=24):
                # بیش از 24 ساعت گذشته است، امتیازات را ریست کن
                c.execute('''UPDATE users SET points = 100, last_reset_date = ? 
                           WHERE user_id = ?''', (current_time.strftime('%Y-%m-%d %H:%M:%S'), user_id))
                conn.commit()
                print(f"User {user_id} points reset to 100 at {current_time} (previous: {current_points})")
        
        conn.close()

    def generate_referral_code(self, user_id):
        """
        تولید کد رفرال منحصر به فرد برای کاربر
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # تولید کد رفرال منحصر به فرد
        import uuid
        referral_code = str(uuid.uuid4())[:8]
        
        print(f"Generating new referral code {referral_code} for user {user_id}")
        
        # بررسی تکراری بودن کد
        c.execute('SELECT 1 FROM users WHERE referral_code = ?', (referral_code,))
        while c.fetchone():
            # اگر کد تکراری بود، یک کد جدید تولید کن
            referral_code = str(uuid.uuid4())[:8]
            print(f"Referral code was duplicate, regenerated: {referral_code}")
            c.execute('SELECT 1 FROM users WHERE referral_code = ?', (referral_code,))
        
        c.execute('UPDATE users SET referral_code = ? WHERE user_id = ?',
                 (referral_code, user_id))
        
        conn.commit()
        conn.close()
        return referral_code

    def get_referral_code(self, user_id):
        """
        دریافت کد رفرال کاربر یا تولید کد جدید اگر کد قبلی وجود نداشته باشد
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # ابتدا اطمینان حاصل می‌کنیم که کاربر وجود دارد
        c.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            # ایجاد کاربر جدید با امتیاز پیش‌فرض
            current_time = datetime.now()
            c.execute('INSERT INTO users (user_id, points, last_reset_date) VALUES (?, 100, ?)',
                     (user_id, current_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            print(f"Created new user {user_id} for referral code generation")
            
        # دریافت کد رفرال کاربر
        c.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if not result or not result[0]:
            # اگر کد رفرال نداشت، یک کد جدید تولید کن
            referral_code = self.generate_referral_code(user_id)
            print(f"Generated new referral code for user {user_id}: {referral_code}")
        else:
            referral_code = result[0]
            print(f"Retrieved existing referral code for user {user_id}: {referral_code}")
        
        conn.close()
        return referral_code

    def debug_user(self, user_id):
        """
        نمایش اطلاعات دیباگ برای یک کاربر
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # بررسی وجود کاربر
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if result:
            print(f"User {user_id} exists in database:")
            print(f"Points: {result[1]}")
            print(f"Last reset: {result[2]}")
            print(f"Referral code: {result[3]}")
        else:
            print(f"User {user_id} does not exist in database")
        
        conn.close()
        return result

    def get_user_referral_stats(self, user_id):
        """
        دریافت آمار دعوت‌های کاربر
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # تعداد کل دعوت‌های موفق
        c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
        total_referrals = c.fetchone()[0]
        
        # امتیاز کسب شده از دعوت‌ها (تخمینی)
        estimated_points = 0
        if total_referrals > 0:
            # محاسبه امتیاز برای هر دعوت با در نظر گرفتن سیستم پاداش پلکانی 10 مرحله‌ای
            for i in range(1, total_referrals + 1):
                if i > 100:
                    estimated_points += 1000  # 50 پایه + 950 بونوس
                elif i > 80:
                    estimated_points += 800   # 50 پایه + 750 بونوس
                elif i > 60:
                    estimated_points += 600   # 50 پایه + 550 بونوس
                elif i > 50:
                    estimated_points += 500   # 50 پایه + 450 بونوس
                elif i > 40:
                    estimated_points += 400   # 50 پایه + 350 بونوس
                elif i > 30:
                    estimated_points += 300   # 50 پایه + 250 بونوس
                elif i > 20:
                    estimated_points += 200   # 50 پایه + 150 بونوس
                elif i > 15:
                    estimated_points += 150   # 50 پایه + 100 بونوس
                elif i > 10:
                    estimated_points += 120   # 50 پایه + 70 بونوس
                elif i > 5:
                    estimated_points += 80    # 50 پایه + 30 بونوس
                else:
                    estimated_points += 50    # 50 پایه
        
        # دعوت‌های اخیر (5 مورد آخر)
        c.execute('''SELECT referred_id, date FROM referrals 
                   WHERE referrer_id = ? 
                   ORDER BY date DESC LIMIT 5''', (user_id,))
        recent_referrals = c.fetchall()
        
        conn.close()
        
        return {
            'total': total_referrals,
            'estimated_points': estimated_points,
            'recent': recent_referrals
        }
        
    def get_top_referrers(self, limit=10):
        """
        دریافت لیست کاربران برتر از نظر تعداد دعوت
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT referrer_id, COUNT(*) as count 
                   FROM referrals 
                   GROUP BY referrer_id 
                   ORDER BY count DESC 
                   LIMIT ?''', (limit,))
        
        top_referrers = c.fetchall()
        conn.close()
        
        return top_referrers 