from telebot import types
from typing import Dict, List, Optional
import re
from datetime import datetime
import json
from .database import Database

class FinancialAssistant:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.categories = {
            'expenses': [
                'خوراک', 'پوشاک', 'مسکن', 'حمل و نقل', 'بهداشت و درمان',
                'تفریح', 'آموزش', 'قبوض', 'خرید', 'سایر'
            ],
            'income': [
                'حقوق', 'درآمد آزاد', 'سود سرمایه‌گذاری', 'هدیه', 'سایر'
            ]
        }
        
    async def show_menu(self, call: types.CallbackQuery):
        """نمایش منوی دستیار مالی"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💰 ثبت هزینه", callback_data="add_expense"),
            types.InlineKeyboardButton("💵 ثبت درآمد", callback_data="add_income")
        )
        markup.add(
            types.InlineKeyboardButton("📊 گزارش ماهانه", callback_data="monthly_report"),
            types.InlineKeyboardButton("📈 تحلیل هزینه‌ها", callback_data="expense_analysis")
        )
        markup.add(
            types.InlineKeyboardButton("🎯 بودجه‌بندی", callback_data="budgeting"),
            types.InlineKeyboardButton("📝 مدیریت تراکنش‌ها", callback_data="transaction_management")
        )
        markup.add(
            types.InlineKeyboardButton("⚙️ تنظیمات", callback_data="financial_settings"),
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main_menu")
        )
        
        await self.bot.edit_message_text(
            "💰 *دستیار مالی*\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    async def add_transaction(self, user_id: int, amount: float, category: str, 
                            transaction_type: str, description: str = "") -> Dict:
        """ثبت تراکنش جدید"""
        transaction = {
            'user_id': user_id,
            'amount': amount,
            'category': category,
            'type': transaction_type,
            'description': description,
            'date': datetime.now().isoformat()
        }
        
        # ذخیره در دیتابیس
        self.db.add_transaction(transaction)
        
        return transaction
        
    async def generate_monthly_report(self, user_id: int, month: int, year: int) -> Dict:
        """تولید گزارش ماهانه"""
        # دریافت تراکنش‌های ماه
        transactions = self.db.get_monthly_transactions(user_id, month, year)
        
        # محاسبه مجموع درآمد و هزینه
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        
        # محاسبه هزینه‌ها به تفکیک دسته‌بندی
        category_expenses = {}
        for transaction in transactions:
            if transaction['type'] == 'expense':
                category = transaction['category']
                if category not in category_expenses:
                    category_expenses[category] = 0
                category_expenses[category] += transaction['amount']
                
        # محاسبه نرخ پس‌انداز
        savings_rate = (total_income - total_expenses) / total_income if total_income > 0 else 0
        
        return {
            'month': month,
            'year': year,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'category_expenses': category_expenses,
            'savings_rate': savings_rate,
            'transactions': transactions
        }
        
    async def show_monthly_report(self, call: types.CallbackQuery, report: Dict):
        """نمایش گزارش ماهانه"""
        text = f"📊 *گزارش مالی {report['month']}/{report['year']}*\n\n"
        
        text += f"💰 *درآمد کل:* {report['total_income']:,.0f} تومان\n"
        text += f"💸 *هزینه کل:* {report['total_expenses']:,.0f} تومان\n"
        text += f"💵 *نرخ پس‌انداز:* {report['savings_rate']:.1%}\n\n"
        
        text += "📈 *هزینه‌ها به تفکیک دسته‌بندی:*\n"
        for category, amount in report['category_expenses'].items():
            percentage = amount / report['total_expenses'] if report['total_expenses'] > 0 else 0
            text += f"• {category}: {amount:,.0f} تومان ({percentage:.1%})\n"
            
        await self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
    async def analyze_expenses(self, user_id: int, period: str = 'month') -> Dict:
        """تحلیل هزینه‌ها"""
        # دریافت تراکنش‌های دوره
        transactions = self.db.get_period_transactions(user_id, period)
        
        # محاسبه آمار هزینه‌ها
        total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        avg_expense = total_expenses / len(transactions) if transactions else 0
        
        # تحلیل روند هزینه‌ها
        expense_trend = self.calculate_expense_trend(transactions)
        
        # پیشنهادات بهینه‌سازی
        recommendations = self.generate_recommendations(transactions)
        
        return {
            'period': period,
            'total_expenses': total_expenses,
            'average_expense': avg_expense,
            'expense_trend': expense_trend,
            'recommendations': recommendations
        }
        
    def calculate_expense_trend(self, transactions: List[Dict]) -> str:
        """محاسبه روند هزینه‌ها"""
        if not transactions:
            return "اطلاعات کافی موجود نیست"
            
        # محاسبه میانگین هزینه‌های اخیر
        recent_expenses = [t['amount'] for t in transactions[-5:] if t['type'] == 'expense']
        avg_recent = sum(recent_expenses) / len(recent_expenses) if recent_expenses else 0
        
        # محاسبه میانگین هزینه‌های قبلی
        old_expenses = [t['amount'] for t in transactions[:-5] if t['type'] == 'expense']
        avg_old = sum(old_expenses) / len(old_expenses) if old_expenses else 0
        
        if avg_recent > avg_old * 1.1:
            return "افزایش"
        elif avg_recent < avg_old * 0.9:
            return "کاهش"
        else:
            return "ثابت"
            
    def generate_recommendations(self, transactions: List[Dict]) -> List[str]:
        """تولید پیشنهادات بهینه‌سازی"""
        recommendations = []
        
        # تحلیل هزینه‌های غیرضروری
        unnecessary_expenses = self.identify_unnecessary_expenses(transactions)
        if unnecessary_expenses:
            recommendations.append(f"کاهش هزینه‌های غیرضروری: {unnecessary_expenses}")
            
        # تحلیل هزینه‌های تکراری
        recurring_expenses = self.identify_recurring_expenses(transactions)
        if recurring_expenses:
            recommendations.append(f"بهینه‌سازی هزینه‌های تکراری: {recurring_expenses}")
            
        # پیشنهاد پس‌انداز
        savings_recommendation = self.generate_savings_recommendation(transactions)
        if savings_recommendation:
            recommendations.append(savings_recommendation)
            
        return recommendations
        
    def identify_unnecessary_expenses(self, transactions: List[Dict]) -> str:
        """شناسایی هزینه‌های غیرضروری"""
        # این تابع در واقعیت باید منطق پیچیده‌تری داشته باشد
        return "هزینه‌های تفریحی و خریدهای غیرضروری"
        
    def identify_recurring_expenses(self, transactions: List[Dict]) -> str:
        """شناسایی هزینه‌های تکراری"""
        # این تابع در واقعیت باید منطق پیچیده‌تری داشته باشد
        return "قبوض و اشتراک‌ها"
        
    def generate_savings_recommendation(self, transactions: List[Dict]) -> str:
        """تولید پیشنهاد پس‌انداز"""
        # این تابع در واقعیت باید منطق پیچیده‌تری داشته باشد
        return "پیشنهاد می‌شود 20% از درآمد ماهانه را پس‌انداز کنید"
        
    async def set_budget(self, user_id: int, category: str, amount: float, 
                        period: str = 'month') -> Dict:
        """تنظیم بودجه"""
        budget = {
            'user_id': user_id,
            'category': category,
            'amount': amount,
            'period': period,
            'date': datetime.now().isoformat()
        }
        
        # ذخیره در دیتابیس
        self.db.set_budget(budget)
        
        return budget
        
    async def check_budget(self, user_id: int, category: str, period: str = 'month') -> Dict:
        """بررسی وضعیت بودجه"""
        # دریافت بودجه
        budget = self.db.get_budget(user_id, category, period)
        if not budget:
            return {'error': 'بودجه تنظیم نشده است'}
            
        # دریافت هزینه‌های دوره
        expenses = self.db.get_category_expenses(user_id, category, period)
        total_expenses = sum(e['amount'] for e in expenses)
        
        # محاسبه درصد مصرف بودجه
        budget_usage = total_expenses / budget['amount'] if budget['amount'] > 0 else 0
        
        return {
            'budget': budget,
            'total_expenses': total_expenses,
            'budget_usage': budget_usage,
            'remaining': budget['amount'] - total_expenses
        }
        
    async def show_budget_status(self, call: types.CallbackQuery, status: Dict):
        """نمایش وضعیت بودجه"""
        text = "🎯 *وضعیت بودجه*\n\n"
        
        if 'error' in status:
            text += f"❌ {status['error']}"
        else:
            text += f"📌 *دسته‌بندی:* {status['budget']['category']}\n"
            text += f"💰 *بودجه:* {status['budget']['amount']:,.0f} تومان\n"
            text += f"💸 *هزینه شده:* {status['total_expenses']:,.0f} تومان\n"
            text += f"💵 *میزان مصرف:* {status['budget_usage']:.1%}\n"
            text += f"📊 *مانده:* {status['remaining']:,.0f} تومان\n\n"
            
            # نمایش وضعیت
            if status['budget_usage'] > 1:
                text += "⚠️ *هشدار:* بودجه بیش از حد مصرف شده است"
            elif status['budget_usage'] > 0.8:
                text += "⚠️ *هشدار:* نزدیک به پایان بودجه هستید"
            else:
                text += "✅ *وضعیت:* بودجه در وضعیت مطلوب است"
                
        await self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        ) 