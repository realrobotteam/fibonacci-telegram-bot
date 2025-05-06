import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot.db')
        self.create_tables()
        
    def create_tables(self):
        """ایجاد جداول مورد نیاز"""
        cursor = self.conn.cursor()
        
        # جدول تراکنش‌ها
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
        ''')
        
        # جدول بودجه‌ها
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            period TEXT NOT NULL,
            date TEXT NOT NULL
        )
        ''')
        
        self.conn.commit()
        
    def add_transaction(self, transaction: Dict):
        """افزودن تراکنش جدید"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO transactions (user_id, amount, category, type, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            transaction['user_id'],
            transaction['amount'],
            transaction['category'],
            transaction['type'],
            transaction['description'],
            transaction['date']
        ))
        self.conn.commit()
        
    def get_monthly_transactions(self, user_id: int, month: int, year: int) -> List[Dict]:
        """دریافت تراکنش‌های ماه"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM transactions
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
        ORDER BY date DESC
        ''', (user_id, f"{month:02d}", str(year)))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'user_id': row[1],
                'amount': row[2],
                'category': row[3],
                'type': row[4],
                'description': row[5],
                'date': row[6]
            })
            
        return transactions
        
    def get_period_transactions(self, user_id: int, period: str) -> List[Dict]:
        """دریافت تراکنش‌های دوره"""
        cursor = self.conn.cursor()
        
        if period == 'month':
            cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND date >= datetime('now', '-1 month')
            ORDER BY date DESC
            ''', (user_id,))
        elif period == 'week':
            cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND date >= datetime('now', '-7 days')
            ORDER BY date DESC
            ''', (user_id,))
        else:  # year
            cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND date >= datetime('now', '-1 year')
            ORDER BY date DESC
            ''', (user_id,))
            
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'user_id': row[1],
                'amount': row[2],
                'category': row[3],
                'type': row[4],
                'description': row[5],
                'date': row[6]
            })
            
        return transactions
        
    def set_budget(self, budget: Dict):
        """تنظیم بودجه"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO budgets (user_id, category, amount, period, date)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            budget['user_id'],
            budget['category'],
            budget['amount'],
            budget['period'],
            budget['date']
        ))
        self.conn.commit()
        
    def get_budget(self, user_id: int, category: str, period: str) -> Optional[Dict]:
        """دریافت بودجه"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM budgets
        WHERE user_id = ? AND category = ? AND period = ?
        ORDER BY date DESC
        LIMIT 1
        ''', (user_id, category, period))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'category': row[2],
                'amount': row[3],
                'period': row[4],
                'date': row[5]
            }
        return None
        
    def get_category_expenses(self, user_id: int, category: str, period: str) -> List[Dict]:
        """دریافت هزینه‌های یک دسته‌بندی"""
        cursor = self.conn.cursor()
        
        if period == 'month':
            cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND category = ? AND type = 'expense'
            AND date >= datetime('now', '-1 month')
            ORDER BY date DESC
            ''', (user_id, category))
        elif period == 'week':
            cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND category = ? AND type = 'expense'
            AND date >= datetime('now', '-7 days')
            ORDER BY date DESC
            ''', (user_id, category))
        else:  # year
            cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND category = ? AND type = 'expense'
            AND date >= datetime('now', '-1 year')
            ORDER BY date DESC
            ''', (user_id, category))
            
        expenses = []
        for row in cursor.fetchall():
            expenses.append({
                'id': row[0],
                'user_id': row[1],
                'amount': row[2],
                'category': row[3],
                'type': row[4],
                'description': row[5],
                'date': row[6]
            })
            
        return expenses
        
    def __del__(self):
        """بستن اتصال به دیتابیس"""
        self.conn.close() 