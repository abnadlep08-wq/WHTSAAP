import sqlite3
import logging
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import threading
import time
import os
import re
استيراد عشوائي
استيراد سلسلة
استيراد smtplib
من مكتبة البريد الإلكتروني MIME.text استورد MIMEText
من مكتبة البريد الإلكتروني MIME.multipart استورد MIMEMultipart
from functools import wraps
من datetime استورد datetime و timedelta

# ====== إعدادات التسجيل ======
logging.basicConfig (​
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s' ,
    مستوى التسجيل. معلومات
)
logger = logging.getLogger ( __ name__ )

# ====== إعدادات البوت ======
TELEGRAM_TOKEN = '8556747289:AAGhbOEYXkeC7_kQYQtzOKny8usWSlKpMqI'
اسم المستخدم الإداري = '@x_f7x'
ADMIN_PASSWORD = '@x_f7x'
ADMIN_USER_IDS = [ ]

# ====== قارورة التحضير ======
app = Flask ( __name__ )
app.secret_key = ' x_f7x_secret_key_2024 '
app.config [ 'SESSION_TYPE' ] = ' filesystem'

# ====== إعداد قاعدة البيانات ======
def  setup_database ( ) :
    """إعداد قاعدة البيانات من جديد"""
    conn = sqlite3.connect ( 'banned.db ' )
    c = conn.cursor ( )
    
    #حذف القوائم القديمة إذا كانت موجودة
    ج. تنفيذ ( "DROP TABLE IF EXISTS ban_numbers" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS admins" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS report_logs" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS email_reports" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS payments" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS subscriptions" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS users" )
    ج. تنفيذ ( "DROP TABLE IF EXISTS settings" )
    
    # إنشاء قواعد البيانات من جديد
    ج. تنفيذ ( '''إنشاء جدول الأرقام المحظورة
                 (الرقم النص المفتاح الأساسي،
                  نص السبب،
                  ممنوع بواسطة نص،
                  التاريخ النصي،
                  report_count INTEGER DEFAULT 1)''' )
    
    ج. تنفيذ ( '''إنشاء جدول المسؤولين
                 (user_id TEXT PRIMARY KEY,
                  اسم المستخدم نص،
                  تمت الإضافة بواسطة نص،
                  التاريخ (نص)''' )
    
    ج. تنفيذ ( '''إنشاء جدول سجلات_التقارير
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  نص رقمي،
                  نص الإجراء،
                  تم التنفيذ بواسطة نص،
                  التاريخ النصي،
                  platform TEXT DEFAULT 'telegram')''' )
    
    ج. تنفيذ ( '''إنشاء جدول email_reports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  number TEXT,
                  email TEXT,
                  subject TEXT,
                  message TEXT,
                  count INTEGER DEFAULT 1,
                  status TEXT DEFAULT 'pending',
                  sent_by TEXT,
                  date TEXT,
                  completed_date TEXT)''')
    
    c.execute('''CREATE TABLE payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  username TEXT,
                  amount REAL,
                  method TEXT,
                  transaction_id TEXT,
                  status TEXT DEFAULT 'pending',
                  date TEXT,
                  completed_date TEXT)''')
    
    c.execute('''CREATE TABLE subscriptions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT UNIQUE,
                  username TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  status TEXT DEFAULT 'active',
                  reports_limit INTEGER DEFAULT 100,
                  reports_used INTEGER DEFAULT 0,
                  price REAL,
                  payment_id INTEGER)''')
    
    c.execute('''CREATE TABLE users
                 (user_id TEXT PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  email TEXT,
                  phone TEXT,
                  join_date TEXT,
                  reports_count INTEGER DEFAULT 0,
                  subscription_status TEXT DEFAULT 'inactive')''')
    
    c.execute('''CREATE TABLE settings
                 (key TEXT PRIMARY KEY,
                  value TEXT,
                  updated_by TEXT,
                  updated_date TEXT)''')
    
    # إعدادات النظام
    default_settings = [
        ('report_price', '5.0'),
        ('subscription_required', 'false'),
        ('email_enabled', 'false'),
        ('smtp_server', 'smtp.gmail.com'),
        ('smtp_port', '587'),
        ('smtp_email', ''),
        ('smtp_password', ''),
        ('whatsapp_abuse_email', 'abuse@support.whatsapp.com'),
        ('max_reports_per_day', '100'),
        ('min_report_count', '1'),
        ('max_report_count', '1000')
    ]
    
    for key, value in default_settings:
        c.execute("INSERT OR REPLACE INTO settings (key, value, updated_date) VALUES (?, ?, ?)",
                  (key, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    print("✅ تم إعداد قاعدة البيانات بنجاح")

# تشغيل إعداد قاعدة البيانات
setup_database()

# ====== الاتصال بقاعدة البيانات ======
conn = sqlite3.connect('banned.db', check_same_thread=False)
c = conn.cursor()

# ====== قوالب HTML مدمجة ======
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>واتساب شيلد - تسجيل الدخول</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Tajawal', 'Segoe UI', Tahoma, sans-serif;
        }
        body {
            background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-box {
            background: rgba(255, 255, 255, 0.95);
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 450px;
        }
        h1 {
            color: #1a2a6c;
            margin-bottom: 30px;
            text-align: center;
            font-size: 32px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e1e1;
            border-radius: 12px;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #1a2a6c;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #1a2a6c, #b21f1f);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .alert {
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 15px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
        }
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🛡️ واتساب شيلد</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label>👤 اسم المستخدم</label>
                <input type="text" name="username" placeholder="أدخل اسم المستخدم" required>
            </div>
            <div class="form-group">
                <label>🔑 كلمة المرور</label>
                <input type="password" name="password" placeholder="أدخل كلمة المرور" required>
            </div>
            <button type="submit">تسجيل الدخول</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>واتساب شيلد - لوحة التحكم</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Tajawal', 'Segoe UI', Tahoma, sans-serif;
        }
        body {
            background: #f0f2f5;
        }
        .container {
            display: flex;
            min-height: 100vh;
        }
        .sidebar {
            width: 280px;
            background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%);
            color: white;
            padding: 30px 20px;
        }
        .sidebar h2 {
            margin-bottom: 40px;
            font-size: 24px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255,255,255,0.2);
        }
        .sidebar a {
            display: block;
            color: white;
            text-decoration: none;
            padding: 15px 20px;
            margin-bottom: 5px;
            border-radius: 12px;
            transition: all 0.3s;
        }
        .sidebar a:hover {
            background: rgba(255,255,255,0.1);
        }
        .main-content {
            flex: 1;
            padding: 30px;
        }
        .header {
            background: white;
            padding: 25px 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        .stat-number {
            font-size: 42px;
            font-weight: 700;
            color: #1a2a6c;
            margin-top: 10px;
        }
        .recent-section {
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background: #f8f9fa;
            padding: 15px;
            text-align: right;
            font-weight: 600;
            color: #1a2a6c;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        .badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>🛡️ واتساب شيلد</h2>
            <a href="/admin/dashboard">🏠 الرئيسية</a>
            <a href="/admin/banned">🚫 الأرقام المحظورة</a>
            <a href="/admin/add">➕ إضافة رقم</a>
            <a href="/admin/admins">👥 المشرفين</a>
            <a href="/admin/email-reports">📧 بلاغات البريد</a>
            <a href="/admin/subscriptions">💳 الاشتراكات</a>
            <a href="/admin/payments">💰 المدفوعات</a>
            <a href="/admin/settings">⚙️ الإعدادات</a>
            <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
        </div>
        
        <div class="main-content">
            <div class="header">
                <div>
                    <h1 style="color: #1a2a6c;">مرحباً، {{ admin_username }}</h1>
                    <p style="color: #666; margin-top: 5px;">{{ now }}</p>
                </div>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}" style="padding: 15px; border-radius: 12px; margin-bottom: 20px; background: {% if category == 'success' %}#d4edda{% else %}#f8d7da{% endif %}; color: {% if category == 'success' %}#155724{% else %}#721c24{% endif %};">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3 style="color: #666;">🚫 الأرقام المحظورة</h3>
                    <div class="stat-number">{{ stats.total_banned }}</div>
                </div>
                <div class="stat-card">
                    <h3 style="color: #666;">👥 المشرفين</h3>
                    <div class="stat-number">{{ stats.total_admins }}</div>
                </div>
                <div class="stat-card">
                    <h3 style="color: #666;">📧 بلاغات البريد</h3>
                    <div class="stat-number">{{ stats.total_email_reports }}</div>
                </div>
                <div class="stat-card">
                    <h3 style="color: #666;">💳 الاشتراكات</h3>
                    <div class="stat-number">{{ stats.total_subscriptions }}</div>
                </div>
            </div>
            
            <div class="recent-section">
                <h3 style="color: #1a2a6c;">📋 آخر الأرقام المحظورة</h3>
                <table>
                    <thead>
                        <tr>
                            <th>الرقم</th>
                            <th>السبب</th>
                            <th>عدد البلاغات</th>
                            <th>تم بواسطة</th>
                            <th>التاريخ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for ban in recent_bans %}
                        <tr>
                            <td><strong>{{ ban[0] }}</strong></td>
                            <td>{{ ban[1][:40] + '...' if ban[1]|length > 40 else ban[1] }}</td>
                            <td><span class="badge badge-success">{{ ban[4] if ban[4] else 1 }}</span></td>
                            <td>{{ ban[2] }}</td>
                            <td>{{ ban[3] }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center; color: #666;">لا توجد أرقام محظورة</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="recent-section">
                <h3 style="color: #1a2a6c;">📋 آخر بلاغات البريد</h3>
                <table>
                    <thead>
                        <tr>
                            <th>الرقم</th>
                            <th>البريد</th>
                            <th>عدد البلاغات</th>
                            <th>الحالة</th>
                            <th>التاريخ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for report in recent_email_reports %}
                        <tr>
                            <td>{{ report[1] }}</td>
                            <td>{{ report[2] }}</td>
                            <td><span class="badge badge-success">{{ report[5] }}</span></td>
                            <td>
                                {% if report[6] == 'completed' %}
                                <span class="badge badge-success">✅ تم</span>
                                {% elif report[6] == 'pending' %}
                                <span class="badge badge-warning">⏳ قيد الانتظار</span>
                                {% else %}
                                <span class="badge badge-danger">❌ فشل</span>
                                {% endif %}
                            </td>
                            <td>{{ report[8] }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center; color: #666;">لا توجد بلاغات بريد</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''

BANNED_LIST_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>الأرقام المحظورة</title>
    <style>
        * { font-family: 'Tajawal', sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f0f2f5; display: flex; }
        .sidebar { width: 280px; background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%); color: white; padding: 30px; min-height: 100vh; }
        .main-content { flex: 1; padding: 30px; }
        .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin-bottom: 5px; border-radius: 12px; }
        .sidebar a:hover { background: rgba(255,255,255,0.1); }
        .search-box { width: 100%; padding: 15px; border: 2px solid #e1e1e1; border-radius: 12px; margin-bottom: 20px; }
        table { width: 100%; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        th { background: #1a2a6c; color: white; padding: 15px; }
        td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
        .btn { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; text-decoration: none; color: white; }
        .btn-danger { background: #dc3545; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="margin-bottom: 30px;">🛡️ واتساب شيلد</h2>
        <a href="/admin/dashboard">🏠 الرئيسية</a>
        <a href="/admin/banned">🚫 الأرقام المحظورة</a>
        <a href="/admin/add">➕ إضافة رقم</a>
        <a href="/admin/admins">👥 المشرفين</a>
        <a href="/admin/email-reports">📧 بلاغات البريد</a>
        <a href="/admin/subscriptions">💳 الاشتراكات</a>
        <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
    </div>
    
    <div class="main-content">
        <h1 style="color: #1a2a6c; margin-bottom: 30px;">🚫 الأرقام المحظورة</h1>
        
        <form method="GET" style="margin-bottom: 20px;">
            <input type="text" name="search" class="search-box" placeholder="🔍 بحث برقم الهاتف أو السبب..." value="{{ search }}">
        </form>
        
        <p style="margin-bottom: 15px;">إجمالي: {{ total }} رقم</p>
        
        <table>
            <thead>
                <tr>
                    <th>الرقم</th>
                    <th>السبب</th>
                    <th>عدد البلاغات</th>
                    <th>تم بواسطة</th>
                    <th>التاريخ</th>
                    <th>الإجراءات</th>
                </tr>
            </thead>
            <tbody>
                {% for ban in banned %}
                <tr>
                    <td><strong>{{ ban[0] }}</strong></td>
                    <td>{{ ban[1] }}</td>
                    <td><span style="background: #d4edda; color: #155724; padding: 5px 10px; border-radius: 20px;">{{ ban[4] if ban[4] else 1 }}</span></td>
                    <td>{{ ban[2] }}</td>
                    <td>{{ ban[3] }}</td>
                    <td>
                        <a href="/admin/unban/{{ ban[0] }}" class="btn btn-danger" onclick="return confirm('هل أنت متأكد؟')">إلغاء الحظر</a>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="6" style="text-align: center; color: #666;">لا توجد أرقام محظورة</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

ADD_BAN_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إضافة رقم محظور</title>
    <style>
        * { font-family: 'Tajawal', sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f0f2f5; display: flex; }
        .sidebar { width: 280px; background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%); color: white; padding: 30px; min-height: 100vh; }
        .main-content { flex: 1; padding: 30px; }
        .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin-bottom: 5px; border-radius: 12px; }
        .sidebar a:hover { background: rgba(255,255,255,0.1); }
        .form-card { background: white; padding: 40px; border-radius: 20px; max-width: 600px; margin: 0 auto; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 600; }
        input, textarea { width: 100%; padding: 15px; border: 2px solid #e1e1e1; border-radius: 12px; font-size: 16px; }
        input:focus, textarea:focus { outline: none; border-color: #1a2a6c; }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #1a2a6c, #0f1a3d); color: white; border: none; border-radius: 12px; font-size: 18px; font-weight: 700; cursor: pointer; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="margin-bottom: 30px;">🛡️ واتساب شيلد</h2>
        <a href="/admin/dashboard">🏠 الرئيسية</a>
        <a href="/admin/banned">🚫 الأرقام المحظورة</a>
        <a href="/admin/add">➕ إضافة رقم</a>
        <a href="/admin/admins">👥 المشرفين</a>
        <a href="/admin/email-reports">📧 بلاغات البريد</a>
        <a href="/admin/subscriptions">💳 الاشتراكات</a>
        <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
    </div>
    
    <div class="main-content">
        <div class="form-card">
            <h1 style="color: #1a2a6c; margin-bottom: 30px; text-align: center;">➕ إضافة رقم محظور</h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}" style="padding: 15px; border-radius: 12px; margin-bottom: 20px; background: {% if category == 'success' %}#d4edda{% else %}#f8d7da{% endif %}; color: {% if category == 'success' %}#155724{% else %}#721c24{% endif %};">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="form-group">
                    <label>📱 رقم الهاتف</label>
                    <input type="text" name="number" placeholder="مثال: 966501234567" required>
                </div>
                <div class="form-group">
                    <label>📋 سبب الحظر</label>
                    <textarea name="reason" rows="4" placeholder="أدخل سبب حظر هذا الرقم..." required></textarea>
                </div>
                <div class="form-group">
                    <label>📊 عدد البلاغات</label>
                    <input type="number" name="report_count" value="1" min="1" max="1000" placeholder="عدد البلاغات">
                </div>
                <button type="submit">إضافة الرقم</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

ADMINS_LIST_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>قائمة المشرفين</title>
    <style>
        * { font-family: 'Tajawal', sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f0f2f5; display: flex; }
        .sidebar { width: 280px; background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%); color: white; padding: 30px; min-height: 100vh; }
        .main-content { flex: 1; padding: 30px; }
        .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin-bottom: 5px; border-radius: 12px; }
        .sidebar a:hover { background: rgba(255,255,255,0.1); }
        table { width: 100%; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        th { background: #1a2a6c; color: white; padding: 15px; }
        td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
        .btn { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; text-decoration: none; color: white; }
        .btn-danger { background: #dc3545; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="margin-bottom: 30px;">🛡️ واتساب شيلد</h2>
        <a href="/admin/dashboard">🏠 الرئيسية</a>
        <a href="/admin/banned">🚫 الأرقام المحظورة</a>
        <a href="/admin/add">➕ إضافة رقم</a>
        <a href="/admin/admins">👥 المشرفين</a>
        <a href="/admin/email-reports">📧 بلاغات البريد</a>
        <a href="/admin/subscriptions">💳 الاشتراكات</a>
        <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
    </div>
    
    <div class="main-content">
        <h1 style="color: #1a2a6c; margin-bottom: 30px;">👥 قائمة المشرفين</h1>
        
        <table>
            <thead>
                <tr>
                    <th>معرف المستخدم</th>
                    <th>اسم المستخدم</th>
                    <th>تمت الإضافة بواسطة</th>
                    <th>التاريخ</th>
                    <th>الإجراءات</th>
                </tr>
            </thead>
            <tbody>
                {% for admin in admins %}
                <tr>
                    <td><code>{{ admin[0] }}</code></td>
                    <td>{{ admin[1] }}</td>
                    <td>{{ admin[2] }}</td>
                    <td>{{ admin[3] }}</td>
                    <td>
                        {% if admin[1] != '@x_f7x' %}
                        <a href="/admin/admins/remove/{{ admin[0] }}" class="btn btn-danger" onclick="return confirm('هل أنت متأكد من إزالة هذا المشرف؟')">إزالة</a>
                        {% else %}
                        <span style="color: #666;">المطور</span>
                        {% endif %}
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" style="text-align: center; color: #666;">لا يوجد مشرفين</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

# ====== دوال قاعدة البيانات ======
def get_setting(key, default=None):
    """الحصول على إعداد من قاعدة البيانات"""
    try:
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = c.fetchone()
        return result[0] if result else default
    except:
        return default

def update_setting(key, value, updated_by='system'):
    """تحديث إعداد في قاعدة البيانات"""
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT OR REPLACE INTO settings (key, value, updated_by, updated_date) VALUES (?, ?, ?, ?)",
                  (key, value, updated_by, date))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        return False

def add_banned_number(number, reason, banned_by, report_count=1):
    """إضافة رقم محظور إلى قاعدة البيانات مع عدد البلاغات"""
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT OR REPLACE INTO banned_numbers (number, reason, banned_by, date, report_count) VALUES (?, ?, ?, ?, ?)",
                  (number, reason, banned_by, date, report_count))
        conn.commit()
        add_log(number, f"Banned: {reason} ({report_count} reports)", banned_by)
        return True
    except Exception as e:
        logger.error(f"Error adding banned number: {e}")
        return False

def remove_banned_number(number):
    """إزالة رقم من قائمة المحظورين"""
    try:
        c.execute("DELETE FROM banned_numbers WHERE number = ?", (number,))
        conn.commit()
        add_log(number, "Unbanned", "System")
        return True
    except Exception as e:
        logger.error(f"Error removing banned number: {e}")
        return False

def get_banned_numbers():
    """الحصول على قائمة الأرقام المحظورة"""
    try:
        c.execute("SELECT number, reason, banned_by, date, report_count FROM banned_numbers ORDER BY date DESC")
        return c.fetchall()
    except Exception as e:
        logger.error(f"Error getting banned numbers: {e}")
        return []

def add_admin(user_id, username, added_by):
    """إضافة أدمن جديد"""
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT OR REPLACE INTO admins (user_id, username, added_by, date) VALUES (?, ?, ?, ?)",
                  (str(user_id), username, added_by, date))
        conn.commit()
        if str(user_id) not in ADMIN_USER_IDS:
            ADMIN_USER_IDS.append(str(user_id))
        add_log(user_id, f"Added as admin by {added_by}", added_by)
        return True
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return False

def remove_admin(user_id):
    """إزالة أدمن"""
    try:
        c.execute("DELETE FROM admins WHERE user_id = ?", (str(user_id),))
        conn.commit()
        if str(user_id) in ADMIN_USER_IDS:
            ADMIN_USER_IDS.remove(str(user_id))
        add_log(user_id, "Removed as admin", "System")
        return True
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        return False

def get_admins():
    """الحصول على قائمة الأدمن"""
    try:
        c.execute("SELECT user_id, username, added_by, date FROM admins ORDER BY date DESC")
        return c.fetchall()
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return []

def add_log(number, action, performed_by):
    """إضافة سجل جديد"""
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO report_logs (number, action, performed_by, date) VALUES (?, ?, ?, ?)",
                  (number, action, performed_by, date))
        conn.commit()
    except Exception as e:
        logger.error(f"Error adding log: {e}")

def get_logs(limit=50):
    """الحصول على آخر السجلات"""
    try:
        c.execute("SELECT id, number, action, performed_by, date FROM report_logs ORDER BY date DESC LIMIT ?", (limit,))
        return c.fetchall()
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return []

def add_email_report(number, email, subject, message, count, sent_by):
    """إضافة بلاغ بريد جديد"""
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO email_reports 
                     (number, email, subject, message, count, sent_by, date) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (number, email, subject, message, count, sent_by, date))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        logger.error(f"Error adding email report: {e}")
        return None

def get_email_reports(limit=50):
    """الحصول على بلاغات البريد"""
    try:
        c.execute("SELECT * FROM email_reports ORDER BY date DESC LIMIT ?", (limit,))
        return c.fetchall()
    except Exception as e:
        logger.error(f"Error getting email reports: {e}")
        return []

def update_email_report_status(report_id, status):
    """تحديث حالة بلاغ البريد"""
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE email_reports SET status = ?, completed_date = ? WHERE id = ?",
                  (status, date, report_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating email report status: {e}")
        return False

def validate_phone_number(number):
    """التحقق من صحة رقم الهاتف"""
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, number) is not None

def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def search_banned_numbers(query):
    """البحث في الأرقام المحظورة"""
    try:
        c.execute("SELECT number, reason, banned_by, date, report_count FROM banned_numbers WHERE number LIKE ? OR reason LIKE ? ORDER BY date DESC", 
                  (f'%{query}%', f'%{query}%'))
        return c.fetchall()
    except Exception as e:
        logger.error(f"Error searching banned numbers: {e}")
        return []

def load_admins():
    """تحميل قائمة الأدمن من قاعدة البيانات"""
    global ADMIN_USER_IDS
    try:
        c.execute("SELECT user_id FROM admins")
        ADMIN_USER_IDS = [str(row[0]) for row in c.fetchall()]
        
        # إضافة المطور إذا لم يكن موجوداً
        developer_id = "7342085811"
        if developer_id not in ADMIN_USER_IDS:
            add_admin(developer_id, "@x_f7x", "System")
            ADMIN_USER_IDS.append(developer_id)
    except Exception as e:
        logger.error(f"Error loading admins: {e}")
        ADMIN_USER_IDS = ["7342085811"]

# تحميل الأدمن
load_admins()

# ====== دوال البريد الإلكتروني ======
def send_whatsapp_abuse_report(number, reason, count=1):
    """إرسال بلاغ واتساب عبر البريد الإلكتروني"""
    try:
        smtp_server = get_setting('smtp_server', 'smtp.gmail.com')
        smtp_port = int(get_setting('smtp_port', '587'))
        smtp_email = get_setting('smtp_email', '')
        smtp_password = get_setting('smtp_password', '')
        abuse_email = get_setting('whatsapp_abuse_email', 'abuse@support.whatsapp.com')
        
        if not smtp_email or not smtp_password:
            logger.warning("SMTP credentials not configured")
            return False
        
        subject = f"Report: Suspicious Phone Number {number}"
        
        body = f"""
        WhatsApp Abuse Report
        
        Phone Number: {number}
        Reason: {reason}
        Report Count: {count}
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        This number is engaging in suspicious/spam activities.
        Please investigate and take appropriate action.
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = abuse_email
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def send_bulk_whatsapp_reports(number, reason, count, sent_by):
    """إرسال بلاغات متعددة لواتساب"""
    report_id = add_email_report(number, get_setting('whatsapp_abuse_email', 'abuse@support.whatsapp.com'), 
                                 f"Report: {number}", reason, count, sent_by)
    
    if not report_id:
        return False
    
    success_count = 0
    for i in range(count):
        if send_whatsapp_abuse_report(number, reason, i+1):
            success_count += 1
        time.sleep(0.5)  # تجنب الحظر
    
    if success_count == count:
        update_email_report_status(report_id, 'completed')
    elif success_count > 0:
        update_email_report_status(report_id, 'partial')
    else:
        update_email_report_status(report_id, 'failed')
    
    return success_count

# ====== ديكوراتور التحقق من الأدمن ======
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ====== دوال البوت ======
def start(update: Update, context: CallbackContext):
    """معالج أمر /start مع أزرار ملونة"""
    keyboard = [
        [
            InlineKeyboardButton("📱 الإبلاغ عن رقم", callback_data="report_number"),
            InlineKeyboardButton("📧 بلاغ عبر البريد", callback_data="email_report")
        ],
        [
            InlineKeyboardButton("🔍 التحقق من رقم", callback_data="check_number"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
        ],
        [
            InlineKeyboardButton("👥 المشرفين", callback_data="admins"),
            InlineKeyboardButton("❓ المساعدة", callback_data="help")
        ],
        [
            InlineKeyboardButton("💎 صـلي علـى الـنبـي ﷺ", callback_data="prayer"),
            InlineKeyboardButton("🛡️ الاشتراكات", callback_data="subscriptions")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "✨ *بوت واتساب شيلد - نظام الحماية المتكامل* ✨\n\n"
        "🛡️ *أهلاً بك في أقوى نظام للإبلاغ عن الأرقام المزعجة*\n\n"
        "📌 *اختر الخدمة التي تريدها من الأزرار أدناه:*\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

def help_command(update: Update, context: CallbackContext):
    """معالج أمر /help"""
    help_text = (
        "📚 *مساعدة البوت*\n\n"
        "*الأوامر المتاحة:*\n"
        "/start - القائمة الرئيسية\n"
        "/ban <رقم> <سبب> - إبلاغ سريع\n"
        "/check <رقم> - تحقق من رقم\n"
        "/stats - إحصائيات\n"
        "/admins - قائمة المشرفين\n\n"
        "*خدمات البوت:*\n"
        "• بلاغات تلقائية لواتساب\n"
        "• بلاغات عبر البريد الإلكتروني\n"
        "• نظام اشتراكات متكامل\n\n"
        "👨‍💻 *المطور:* @x_f7x"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def button_callback(update: Update, context: CallbackContext):
    """معالج الضغط على الأزرار"""
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name
    
    if query.data == "prayer":
        keyboard = [
            [InlineKeyboardButton("🤍 اللهم صل وسلم على نبينا محمد ﷺ", callback_data="prayer_again")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "🤍 *اللهم صل وسلم وبارك على سيدنا محمد ﷺ*\n\n"
            "🌸 جزاك الله خيراً 🌸",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "prayer_again":
        keyboard = [
            [InlineKeyboardButton("🤍 اللهم صل وسلم على نبينا محمد ﷺ", callback_data="prayer_again")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "🤍 *اللهم صل وسلم وبارك على سيدنا محمد ﷺ*\n\n"
            "🌸 جزاك الله خيراً 🌸\n"
            "💎 صدقة جارية 💎",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "back_to_main":
        keyboard = [
            [
                InlineKeyboardButton("📱 الإبلاغ عن رقم", callback_data="report_number"),
                InlineKeyboardButton("📧 بلاغ عبر البريد", callback_data="email_report")
            ],
            [
                InlineKeyboardButton("🔍 التحقق من رقم", callback_data="check_number"),
                InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
            ],
            [
                InlineKeyboardButton("👥 المشرفين", callback_data="admins"),
                InlineKeyboardButton("❓ المساعدة", callback_data="help")
            ],
            [
                InlineKeyboardButton("💎 صـلي علـى الـنبـي ﷺ", callback_data="prayer"),
                InlineKeyboardButton("🛡️ الاشتراكات", callback_data="subscriptions")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "✨ *بوت واتساب شيلد - نظام الحماية المتكامل* ✨\n\n"
            "🛡️ *أهلاً بك في أقوى نظام للإبلاغ عن الأرقام المزعجة*\n\n"
            "📌 *اختر الخدمة التي تريدها من الأزرار أدناه:*",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "report_number":
        if user_id not in ADMIN_USER_IDS:
            subscription_required = get_setting('subscription_required', 'false')
            if subscription_required == 'true':
                c.execute("SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' AND end_date > ?", 
                         (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                sub = c.fetchone()
                if not sub:
                    query.edit_message_text(
                        "❌ *عذراً، تحتاج إلى اشتراك فعال لاستخدام هذه الخدمة*\n\n"
                        "💰 سعر الاشتراك: {} دولار\n"
                        "📋 للاشتراك تواصل مع المطور: @x_f7x".format(get_setting('report_price', '5')),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
        
        query.edit_message_text(
            "📝 *أرسل رقم الهاتف مع السبب*\n\n"
            "📌 *مثال:*\n"
            "`966501234567 هذا الرقم يرسل رسائل مزعجة`\n\n"
            "⚠️ *يمكنك أيضاً تحديد عدد البلاغات*\n"
            "مثال: `966501234567 | هذا الرقم مزعج | 10`",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for_report'] = True
    
    elif query.data == "email_report":
        if user_id not in ADMIN_USER_IDS:
            subscription_required = get_setting('subscription_required', 'false')
            if subscription_required == 'true':
                c.execute("SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' AND end_date > ?", 
                         (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                sub = c.fetchone()
                if not sub:
                    query.edit_message_text(
                        "❌ *عذراً، تحتاج إلى اشتراك فعال لاستخدام هذه الخدمة*\n\n"
                        "💰 سعر الاشتراك: {} دولار\n"
                        "📋 للاشتراك تواصل مع المطور: @x_f7x".format(get_setting('report_price', '5')),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
        
        query.edit_message_text(
            "📧 *نظام البلاغات عبر البريد الإلكتروني*\n\n"
            "1️⃣ *أرسل الرقم*\n"
            "2️⃣ *السبب*\n"
            "3️⃣ *عدد البلاغات*\n\n"
            "📌 *مثال:*\n"
            "`966501234567 | هذا الرقم مزعج | 50`\n\n"
            "⚠️ *الحد الأقصى: 1000 بلاغ في المرة الواحدة*",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for_email_report'] = True
    
    elif query.data == "check_number":
        query.edit_message_text(
            "🔍 *أرسل رقم الهاتف للتحقق*\n\n"
            "📌 *مثال:*\n"
            "`966501234567`",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for_check'] = True
    
    elif query.data == "stats":
        total_banned = c.execute("SELECT COUNT(*) FROM banned_numbers").fetchone()[0]
        total_reports = c.execute("SELECT SUM(report_count) FROM banned_numbers").fetchone()[0] or 0
        total_admins = c.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        total_email = c.execute("SELECT COUNT(*) FROM email_reports").fetchone()[0]
        
        stats_message = (
            "📊 *إحصائيات النظام*\n\n"
            f"🚫 الأرقام المحظورة: {total_banned}\n"
            f"📋 إجمالي البلاغات: {total_reports}\n"
            f"📧 بلاغات البريد: {total_email}\n"
            f"👥 المشرفين: {total_admins}\n\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        query.edit_message_text(stats_message, parse_mode=ParseMode.MARKDOWN)
    
    elif query.data == "admins":
        admins_list = get_admins()
        if not admins_list:
            query.edit_message_text("📋 لا يوجد مشرفين حالياً")
            return
        
        message = "👥 *قائمة المشرفين:*\n\n"
        for admin in admins_list[:10]:
            message += f"• {admin[1]} - (ID: `{admin[0]}`)\n"
        query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
    
    elif query.data == "help":
        help_command(update, context)
    
    elif query.data == "subscriptions":
        c.execute("SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' AND end_date > ?", 
                 (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        sub = c.fetchone()
        
        if sub:
            reports_used = sub[7]
            reports_limit = sub[6]
            end_date = sub[4]
            remaining = reports_limit - reports_used
            
            message = (
                "✅ *اشتراكك الحالي:*\n\n"
                f"📅 ينتهي في: {end_date}\n"
                f"📊 البلاغات المستخدمة: {reports_used}/{reports_limit}\n"
                f"📈 المتبقي: {remaining} بلاغ\n\n"
                "✨ شكراً لاشتراكك!"
            )
        else:
            message = (
                "💳 *نظام الاشتراكات*\n\n"
                f"💰 سعر الاشتراك: {get_setting('report_price', '5')} دولار\n"
                "📊 100 بلاغ شهرياً\n"
                "📧 بلاغات بريد غير محدودة\n"
                "⚡ أولوية في المعالجة\n\n"
                "📋 للاشتراك تواصل مع المطور: @x_f7x"
            )
        query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)

def handle_message(update: Update, context: CallbackContext):
    """معالج الرسائل النصية"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    text = update.message.text
    
    if context.user_data.get('waiting_for_report'):
        try:
            if '|' in text:
                parts = text.split('|')
                number = parts[0].strip()
                reason = parts[1].strip()
                report_count = int(parts[2].strip()) if len(parts) > 2 else 1
            else:
                words = text.split()
                number = words[0]
                reason = ' '.join(words[1:]) if len(words) > 1 else "لا يوجد سبب"
                report_count = 1
            
            if not validate_phone_number(number):
                update.message.reply_text("❌ رقم غير صالح")
                del context.user_data['waiting_for_report']
                return
            
            max_count = int(get_setting('max_report_count', '1000'))
            if report_count > max_count:
                report_count = max_count
            
            if add_banned_number(number, reason, f"@{username}", report_count):
                update.message.reply_text(
                    f"✅ *تم الإبلاغ بنجاح*\n\n"
                    f"📱 الرقم: `{number}`\n"
                    f"📋 السبب: {reason}\n"
                    f"📊 عدد البلاغات: {report_count}\n"
                    f"👤 بواسطة: @{username}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text("❌ حدث خطأ")
        except Exception as e:
            update.message.reply_text(f"❌ خطأ: {str(e)}")
        del context.user_data['waiting_for_report']
    
    elif context.user_data.get('waiting_for_email_report'):
        try:
            parts = text.split('|')
            if len(parts) < 2:
                update.message.reply_text("❌ الصيغة غير صحيحة. استخدم: الرقم | السبب | عدد البلاغات")
                del context.user_data['waiting_for_email_report']
                return
            
            number = parts[0].strip()
            reason = parts[1].strip()
            report_count = int(parts[2].strip()) if len(parts) > 2 else 1
            
            if not validate_phone_number(number):
                update.message.reply_text("❌ رقم غير صالح")
                del context.user_data['waiting_for_email_report']
                return
            
            max_reports = int(get_setting('max_report_count', '1000'))
            if report_count > max_reports:
                report_count = max_reports
                update.message.reply_text(f"⚠️ تم تعديل العدد إلى {max_reports} (الحد الأقصى)")
            
            update.message.reply_text(f"📧 جاري إرسال {report_count} بلاغ عبر البريد...")
            
            success_count = send_bulk_whatsapp_reports(number, reason, report_count, f"@{username}")
            
            if success_count:
                update.message.reply_text(
                    f"✅ *تم إرسال البلاغات بنجاح*\n\n"
                    f"📱 الرقم: `{number}`\n"
                    f"📋 السبب: {reason}\n"
                    f"📊 تم الإرسال: {success_count}/{report_count}\n"
                    f"📧 عبر: {get_setting('whatsapp_abuse_email', 'abuse@support.whatsapp.com')}",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                if success_count >= 10:
                    add_banned_number(number, reason, f"@{username}", success_count)
            else:
                update.message.reply_text("❌ فشل إرسال البلاغات. تأكد من إعدادات البريد في لوحة التحكم")
                
        except Exception as e:
            update.message.reply_text(f"❌ خطأ: {str(e)}")
        del context.user_data['waiting_for_email_report']
    
    elif context.user_data.get('waiting_for_check'):
        number = text.strip()
        if validate_phone_number(number):
            c.execute("SELECT * FROM banned_numbers WHERE number = ?", (number,))
            result = c.fetchone()
            if result:
                update.message.reply_text(
                    f"⚠️ *الرقم محظور*\n\n"
                    f"📱 الرقم: `{result[0]}`\n"
                    f"📋 السبب: {result[1]}\n"
                    f"📊 البلاغات: {result[4]}\n"
                    f"👤 بواسطة: {result[2]}\n"
                    f"📅 التاريخ: {result[3]}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text(
                    f"✅ *الرقم آمن*\n\n`{number}`\nغير موجود في قاعدة البيانات",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.message.reply_text("❌ رقم غير صالح")
        del context.user_data['waiting_for_check']

def ban(update: Update, context: CallbackContext):
    """معالج أمر /ban"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    
    if user_id not in ADMIN_USER_IDS:
        update.message.reply_text("❌ هذا الأمر متاح فقط للمشرفين")
        return
    
    if not context.args:
        update.message.reply_text("❌ الاستخدام: /ban <رقم> <سبب>")
        return
    
    number = context.args[0]
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "لا يوجد سبب"
    
    if not validate_phone_number(number):
        update.message.reply_text("❌ رقم غير صالح")
        return
    
    if add_banned_number(number, reason, f"@{username}"):
        update.message.reply_text(f"✅ تم حظر {number}")
    else:
        update.message.reply_text("❌ حدث خطأ")

def check(update: Update, context: CallbackContext):
    """معالج أمر /check"""
    if not context.args:
        update.message.reply_text("❌ الاستخدام: /check <رقم>")
        return
    
    number = context.args[0]
    c.execute("SELECT * FROM banned_numbers WHERE number = ?", (number,))
    result = c.fetchone()
    
    if result:
        update.message.reply_text(f"⚠️ محظور: {result[0]}\nالسبب: {result[1]}")
    else:
        update.message.reply_text(f"✅ آمن: {number}")

def stats(update: Update, context: CallbackContext):
    """معالج أمر /stats"""
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_USER_IDS:
        update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    total_banned = c.execute("SELECT COUNT(*) FROM banned_numbers").fetchone()[0]
    total_reports = c.execute("SELECT SUM(report_count) FROM banned_numbers").fetchone()[0] or 0
    total_admins = c.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
    total_email = c.execute("SELECT COUNT(*) FROM email_reports").fetchone()[0]
    
    update.message.reply_text(
        f"📊 الإحصائيات\n\n"
        f"محظور: {total_banned}\n"
        f"بلاغات: {total_reports}\n"
        f"بريد: {total_email}\n"
        f"مشرفين: {total_admins}"
    )

def admins(update: Update, context: CallbackContext):
    """معالج أمر /admins"""
    admins_list = get_admins()
    if not admins_list:
        update.message.reply_text("📋 لا يوجد مشرفين")
        return
    
    message = "👥 المشرفين:\n"
    for admin in admins_list[:10]:
        message += f"\n• {admin[1]}"
    update.message.reply_text(message)

def add_admin_command(update: Update, context: CallbackContext):
    """معالج أمر /addadmin"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    
    if f"@{username}" != ADMIN_USERNAME:
        update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    if not context.args or len(context.args) < 2:
        update.message.reply_text("❌ الاستخدام: /addadmin <user_id> <username>")
        return
    
    new_id = context.args[0]
    new_username = f"@{context.args[1]}"
    
    if add_admin(new_id, new_username, username):
        update.message.reply_text(f"✅ تم إضافة {new_username}")
    else:
        update.message.reply_text("❌ حدث خطأ")

# ====== صفحات Flask ======
@app.route('/')
def index():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """صفحة تسجيل الدخول"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('تم تسجيل الدخول', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('بيانات غير صحيحة', 'danger')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """لوحة التحكم الرئيسية"""
    try:
        stats = {
            'total_banned': c.execute("SELECT COUNT(*) FROM banned_numbers").fetchone()[0],
            'total_admins': c.execute("SELECT COUNT(*) FROM admins").fetchone()[0],
            'total_email_reports': c.execute("SELECT COUNT(*) FROM email_reports").fetchone()[0],
            'total_subscriptions': c.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
        }
    except:
        stats = {'total_banned': 0, 'total_admins': 0, 'total_email_reports': 0, 'total_subscriptions': 0}
    
    recent_bans = get_banned_numbers()[:10]
    recent_email_reports = get_email_reports(10)
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        stats=stats,
        recent_bans=recent_bans,
        recent_email_reports=recent_email_reports,
        admin_username=session.get('admin_username'),
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/admin/banned')
@admin_required
def banned_list():
    """صفحة الأرقام المحظورة"""
    search = request.args.get('search', '')
    
    if search:
        all_bans = search_banned_numbers(search)
    else:
        all_bans = get_banned_numbers()
    
    return render_template_string(
        BANNED_LIST_TEMPLATE,
        banned=all_bans[:50],
        search=search,
        total=len(all_bans)
    )

@app.route('/admin/unban/<number>')
@admin_required
def unban_number(number):
    """إلغاء حظر رقم"""
    if remove_banned_number(number):
        flash(f'تم إلغاء حظر {number}', 'success')
    else:
        flash('حدث خطأ', 'danger')
    return redirect(url_for('banned_list'))

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_ban():
    """إضافة رقم محظور"""
    if request.method == 'POST':
        number = request.form.get('number')
        reason = request.form.get('reason')
        report_count = int(request.form.get('report_count', 1))
        
        if validate_phone_number(number):
            if add_banned_number(number, reason, 'Web Panel', report_count):
                flash(f'تم إضافة {number} مع {report_count} بلاغ', 'success')
                return redirect(url_for('banned_list'))
            else:
                flash('حدث خطأ', 'danger')
        else:
            flash('رقم غير صالح', 'danger')
    
    return render_template_string(ADD_BAN_TEMPLATE)

@app.route('/admin/admins')
@admin_required
def admin_list():
    """صفحة المشرفين"""
    admins = get_admins()
    return render_template_string(ADMINS_LIST_TEMPLATE, admins=admins)

@app.route('/admin/admins/remove/<user_id>')
@admin_required
def remove_admin_route(user_id):
    """إزالة مشرف"""
    if remove_admin(user_id):
        flash('تم إزالة المشرف', 'success')
    else:
        flash('حدث خطأ', 'danger')
    return redirect(url_for('admin_list'))

@app.route('/admin/logout')
def admin_logout():
    """تسجيل الخروج"""
    session.clear()
    flash('تم تسجيل الخروج', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/email-reports')
@admin_required
def email_reports():
    """صفحة بلاغات البريد"""
    reports = get_email_reports(100)
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>بلاغات البريد</title>
        <style>
            * { font-family: 'Tajawal', sans-serif; }
            body { background: #f0f2f5; display: flex; }
            .sidebar { width: 280px; background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%); color: white; padding: 30px; min-height: 100vh; }
            .main-content { flex: 1; padding: 30px; }
            .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin-bottom: 5px; border-radius: 12px; }
            .sidebar a:hover { background: rgba(255,255,255,0.1); }
            table { width: 100%; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
            th { background: #1a2a6c; color: white; padding: 15px; }
            td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
            .badge-success { background: #d4edda; color: #155724; padding: 5px 10px; border-radius: 20px; }
            .badge-warning { background: #fff3cd; color: #856404; padding: 5px 10px; border-radius: 20px; }
            .badge-danger { background: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 20px; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2 style="margin-bottom: 30px;">🛡️ واتساب شيلد</h2>
            <a href="/admin/dashboard">🏠 الرئيسية</a>
            <a href="/admin/banned">🚫 الأرقام المحظورة</a>
            <a href="/admin/add">➕ إضافة رقم</a>
            <a href="/admin/admins">👥 المشرفين</a>
            <a href="/admin/email-reports">📧 بلاغات البريد</a>
            <a href="/admin/subscriptions">💳 الاشتراكات</a>
            <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
        </div>
        <div class="main-content">
            <h1 style="color: #1a2a6c; margin-bottom: 30px;">📧 بلاغات البريد الإلكتروني</h1>
            <table>
                <thead>
                    <tr>
                        <th>الرقم</th>
                        <th>البريد</th>
                        <th>الموضوع</th>
                        <th>عدد البلاغات</th>
                        <th>الحالة</th>
                        <th>التاريخ</th>
                        <th>تم بواسطة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for report in reports %}
                    <tr>
                        <td><strong>{{ report[1] }}</strong></td>
                        <td>{{ report[2] }}</td>
                        <td>{{ report[3][:30] }}{% if report[3]|length > 30 %}...{% endif %}</td>
                        <td><span class="badge-success">{{ report[5] }}</span></td>
                        <td>
                            {% if report[6] == 'completed' %}
                            <span class="badge-success">✅ تم</span>
                            {% elif report[6] == 'pending' %}
                            <span class="badge-warning">⏳ قيد الانتظار</span>
                            {% elif report[6] == 'partial' %}
                            <span class="badge-warning">⚠️ جزئي</span>
                            {% else %}
                            <span class="badge-danger">❌ فشل</span>
                            {% endif %}
                        </td>
                        <td>{{ report[8] }}</td>
                        <td>{{ report[7] }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="7" style="text-align: center; color: #666;">لا توجد بلاغات بريد</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    ''', reports=reports)

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    """صفحة الإعدادات"""
    if request.method == 'POST':
        # إعدادات عامة
        update_setting('report_price', request.form.get('report_price', '5'), session.get('admin_username'))
        update_setting('subscription_required', request.form.get('subscription_required', 'false'), session.get('admin_username'))
        
        # إعدادات البريد
        update_setting('smtp_server', request.form.get('smtp_server', 'smtp.gmail.com'), session.get('admin_username'))
        update_setting('smtp_port', request.form.get('smtp_port', '587'), session.get('admin_username'))
        update_setting('smtp_email', request.form.get('smtp_email', ''), session.get('admin_username'))
        update_setting('smtp_password', request.form.get('smtp_password', ''), session.get('admin_username'))
        update_setting('whatsapp_abuse_email', request.form.get('whatsapp_abuse_email', 'abuse@support.whatsapp.com'), session.get('admin_username'))
        
        # حدود البلاغات
        update_setting('max_reports_per_day', request.form.get('max_reports_per_day', '100'), session.get('admin_username'))
        update_setting('max_report_count', request.form.get('max_report_count', '1000'), session.get('admin_username'))
        
        flash('تم حفظ الإعدادات', 'success')
        return redirect(url_for('admin_settings'))
    
    settings = {
        'report_price': get_setting('report_price', '5'),
        'subscription_required': get_setting('subscription_required', 'false'),
        'smtp_server': get_setting('smtp_server', 'smtp.gmail.com'),
        'smtp_port': get_setting('smtp_port', '587'),
        'smtp_email': get_setting('smtp_email', ''),
        'smtp_password': get_setting('smtp_password', ''),
        'whatsapp_abuse_email': get_setting('whatsapp_abuse_email', 'abuse@support.whatsapp.com'),
        'max_reports_per_day': get_setting('max_reports_per_day', '100'),
        'max_report_count': get_setting('max_report_count', '1000')
    }
    
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>الإعدادات</title>
        <style>
            * { font-family: 'Tajawal', sans-serif; }
            body { background: #f0f2f5; display: flex; }
            .sidebar { width: 280px; background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%); color: white; padding: 30px; min-height: 100vh; }
            .main-content { flex: 1; padding: 30px; }
            .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin-bottom: 5px; border-radius: 12px; }
            .sidebar a:hover { background: rgba(255,255,255,0.1); }
            .form-card { background: white; padding: 40px; border-radius: 20px; max-width: 800px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
            input, select { width: 100%; padding: 12px; border: 2px solid #e1e1e1; border-radius: 10px; font-size: 14px; }
            input:focus, select:focus { outline: none; border-color: #1a2a6c; }
            button { padding: 15px 30px; background: linear-gradient(135deg, #1a2a6c, #0f1a3d); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; }
            button:hover { transform: translateY(-2px); }
            h3 { color: #1a2a6c; margin: 30px 0 20px; border-bottom: 2px solid #1a2a6c; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2 style="margin-bottom: 30px;">🛡️ واتساب شيلد</h2>
            <a href="/admin/dashboard">🏠 الرئيسية</a>
            <a href="/admin/banned">🚫 الأرقام المحظورة</a>
            <a href="/admin/add">➕ إضافة رقم</a>
            <a href="/admin/admins">👥 المشرفين</a>
            <a href="/admin/email-reports">📧 بلاغات البريد</a>
            <a href="/admin/subscriptions">💳 الاشتراكات</a>
            <a href="/admin/settings">⚙️ الإعدادات</a>
            <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
        </div>
        
        <div class="main-content">
            <div class="form-card">
                <h1 style="color: #1a2a6c; margin-bottom: 30px;">⚙️ إعدادات النظام</h1>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div style="padding: 15px; border-radius: 10px; margin-bottom: 20px; background: {% if category == 'success' %}#d4edda{% else %}#f8d7da{% endif %}; color: {% if category == 'success' %}#155724{% else %}#721c24{% endif %};">
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <h3>💰 إعدادات الاشتراكات</h3>
                    <div class="form-group">
                        <label>سعر الاشتراك (دولار)</label>
                        <input type="number" name="report_price" value="{{ settings.report_price }}" step="0.01" min="0">
                    </div>
                    <div class="form-group">
                        <label>الاشتراك إجباري</label>
                        <select name="subscription_required">
                            <option value="true" {% if settings.subscription_required == 'true' %}selected{% endif %}>نعم</option>
                            <option value="false" {% if settings.subscription_required == 'false' %}selected{% endif %}>لا</option>
                        </select>
                    </div>
                    
                    <h3>📧 إعدادات البريد</h3>
                    <div class="form-group">
                        <label>خادم SMTP</label>
                        <input type="text" name="smtp_server" value="{{ settings.smtp_server }}">
                    </div>
                    <div class="form-group">
                        <label>منفذ SMTP</label>
                        <input type="text" name="smtp_port" value="{{ settings.smtp_port }}">
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني</label>
                        <input type="email" name="smtp_email" value="{{ settings.smtp_email }}" placeholder="your-email@gmail.com">
                    </div>
                    <div class="form-group">
                        <label>كلمة المرور</label>
                        <input type="password" name="smtp_password" value="{{ settings.smtp_password }}" placeholder="App Password">
                    </div>
                    <div class="form-group">
                        <label>بريد واتساب للبلاغات</label>
                        <input type="email" name="whatsapp_abuse_email" value="{{ settings.whatsapp_abuse_email }}">
                    </div>
                    
                    <h3>📊 حدود البلاغات</h3>
                    <div class="form-group">
                        <label>الحد الأقصى للبلاغات اليومية</label>
                        <input type="number" name="max_reports_per_day" value="{{ settings.max_reports_per_day }}" min="1" max="10000">
                    </div>
                    <div class="form-group">
                        <label>الحد الأقصى للبلاغات في المرة الواحدة</label>
                        <input type="number" name="max_report_count" value="{{ settings.max_report_count }}" min="1" max="10000">
                    </div>
                    
                    <button type="submit">💾 حفظ الإعدادات</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''', settings=settings)

@app.route('/admin/subscriptions')
@admin_required
def subscriptions():
    """صفحة الاشتراكات"""
    try:
        c.execute("SELECT * FROM subscriptions ORDER BY start_date DESC")
        subs = c.fetchall()
    except:
        subs = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>الاشتراكات</title>
        <style>
            * { font-family: 'Tajawal', sans-serif; }
            body { background: #f0f2f5; display: flex; }
            .sidebar { width: 280px; background: linear-gradient(180deg, #1a2a6c 0%, #0f1a3d 100%); color: white; padding: 30px; min-height: 100vh; }
            .main-content { flex: 1; padding: 30px; }
            .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin-bottom: 5px; border-radius: 12px; }
            .sidebar a:hover { background: rgba(255,255,255,0.1); }
            table { width: 100%; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
            th { background: #1a2a6c; color: white; padding: 15px; }
            td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
            .badge-success { background: #d4edda; color: #155724; padding: 5px 10px; border-radius: 20px; }
            .badge-danger { background: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 20px; }
            .form-card { background: white; padding: 30px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
            .form-group { margin-bottom: 15px; }
            input { padding: 10px; border: 2px solid #e1e1e1; border-radius: 8px; width: 100%; }
            .btn { padding: 10px 20px; background: #1a2a6c; color: white; border: none; border-radius: 8px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2 style="margin-bottom: 30px;">🛡️ واتساب شيلد</h2>
            <a href="/admin/dashboard">🏠 الرئيسية</a>
            <a href="/admin/banned">🚫 الأرقام المحظورة</a>
            <a href="/admin/add">➕ إضافة رقم</a>
            <a href="/admin/admins">👥 المشرفين</a>
            <a href="/admin/email-reports">📧 بلاغات البريد</a>
            <a href="/admin/subscriptions">💳 الاشتراكات</a>
            <a href="/admin/settings">⚙️ الإعدادات</a>
            <a href="/admin/logout" style="background: #dc3545; margin-top: 50px;">🚪 تسجيل الخروج</a>
        </div>
        
        <div class="main-content">
            <h1 style="color: #1a2a6c; margin-bottom: 30px;">💳 الاشتراكات</h1>
            
            <div class="form-card">
                <h3 style="color: #1a2a6c; margin-bottom: 20px;">➕ إضافة اشتراك جديد</h3>
                <form action="/admin/add-subscription" method="POST">
                    <div class="form-group">
                        <label>معرف المستخدم</label>
                        <input type="text" name="user_id" placeholder="123456789" required>
                    </div>
                    <div class="form-group">
                        <label>اسم المستخدم</label>
                        <input type="text" name="username" placeholder="@username" required>
                    </div>
                    <div class="form-group">
                        <label>السعر (دولار)</label>
                        <input type="number" name="price" value="{{ settings.report_price }}" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>حد البلاغات</label>
                        <input type="number" name="reports_limit" value="100" min="1" required>
                    </div>
                    <button type="submit" class="btn">إضافة اشتراك</button>
                </form>
            </div>
            
            <h3 style="color: #1a2a6c; margin: 30px 0 20px;">📋 قائمة الاشتراكات</h3>
            <table>
                <thead>
                    <tr>
                        <th>المستخدم</th>
                        <th>تاريخ البداية</th>
                        <th>تاريخ النهاية</th>
                        <th>السعر</th>
                        <th>البلاغات</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for sub in subs %}
                    <tr>
                        <td>{{ sub[2] }}</td>
                        <td>{{ sub[3] }}</td>
                        <td>{{ sub[4] }}</td>
                        <td>{{ sub[8] }} $</td>
                        <td>{{ sub[7] }}/{{ sub[6] }}</td>
                        <td>
                            {% if sub[5] == 'active' %}
                            <span class="badge-success">✅ نشط</span>
                            {% else %}
                            <span class="badge-danger">❌ منتهي</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" style="text-align: center; color: #666;">لا توجد اشتراكات</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    ''', subs=subs, settings={'report_price': get_setting('report_price', '5')})

@app.route('/admin/add-subscription', methods=['POST'])
@admin_required
def add_subscription_route():
    """إضافة اشتراك جديد"""
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    price = float(request.form.get('price', 5))
    reports_limit = int(request.form.get('reports_limit', 100))
    
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute('''INSERT OR REPLACE INTO subscriptions 
                     (user_id, username, start_date, end_date, price, reports_limit, reports_used, status) 
                     VALUES (?, ?, ?, ?, ?, ?, 0, 'active')''',
                  (str(user_id), username, date, end_date, price, reports_limit))
        conn.commit()
        
        flash(f'✅ تم إضافة اشتراك لـ {username}', 'success')
    except Exception as e:
        logger.error(f"Error adding subscription: {e}")
        flash('❌ حدث خطأ أثناء إضافة الاشتراك', 'danger')
    
    return redirect(url_for('subscriptions'))

# ====== تشغيل البوت ======
def run_bot():
    """تشغيل بوت التليجرام"""
    try:
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # إضافة معالجات الأوامر
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("ban", ban))
        dp.add_handler(CommandHandler("check", check))
        dp.add_handler(CommandHandler("stats", stats))
        dp.add_handler(CommandHandler("admins", admins))
        dp.add_handler(CommandHandler("addadmin", add_admin_command))
        
        # إضافة معالج الأزرار
        dp.add_handler(CallbackQueryHandler(button_callback))
        
        # إضافة معالج الرسائل
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        logger.info("✅ Bot started successfully!")
        updater.start_polling()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")

# ====== تشغيل التطبيق ======
if __name__ == '__main__':
    print("=" * 60)
    print("🛡️  واتساب شيلد - نظام البلاغات المتكامل")
    print("=" * 60)
    
    # تشغيل البوت
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    print("\n✅ تم تشغيل البوت ولوحة التحكم!")
    print("📱 البوت: @your_bot_username")
    print("🌐 لوحة التحكم: http://localhost:5000")
    print("👤 اسم المستخدم: @x_f7x")
    print("🔑 كلمة المرور: @x_f7x")
    print("=" * 60)
    
    # تشغيل Flask
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
