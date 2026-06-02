import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與圖示
st.set_page_config(page_title="🎓 全國大學二手教科書 AI 智慧交流平台", page_icon="📚", layout="wide")

# ==========================================
# 0. 全國大學與科系常用清單定義
# ==========================================
UNIVERSITY_LIST = [
    "國立雲林科技大學", "國立台灣大學", "國立成功大學", "國立清華大學", "國立陽明交通大學",
    "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學", "國立臺北科技大學",
    "國立台灣科技大學", "逢甲大學", "淡江大學", "輔仁大學", "東吳大學", "其他大學"
]

DEPARTMENT_LIST = [
    "不限科系/通識核心", "資訊工程/資管系", "電機/電子/自動化", "機械/土木/營建",
    "化學/化工/材料", "企業管理/財金/商管", "應用外語/文史哲", "設計/建築/數位媒體"
]


# ==========================================
# 1. 資料庫初始化 (使用同一個 V3 資料庫避免衝突)
# ==========================================
def init_db():
    conn = sqlite3.connect('streamlit_national_books_v3.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            university TEXT NOT NULL,
            green_coins INTEGER DEFAULT 100
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            university TEXT NOT NULL,
            department TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT '上架中', 
            is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0,
            image_base64 TEXT,
            seller_id TEXT NOT NULL,
            buyer_id TEXT
        )
    ''')
    conn.commit()
    conn.close()


def auto_classify_book(name, description):
    text = (name + " " + description).lower()
    cat = "書籍"
    if "講義" in text or "筆記" in text or "考古題" in text:
        cat = "學術講義"
    elif "計算機" in text or "平板" in text:
        cat = "3C配件"

    dept = "不限科系/通識核心"
    dept_keywords = {
        "資訊工程/資管系": ["程式", "python", "java", "演算法", "資料結構", "網頁", "計概", "ai", "資安"],
        "電機/電子/自動化": ["電路", "電子學", "電磁", "訊號", "控制", "工數", "工程數學"],
        "機械/土木/營建": ["力學", "流體", "熱力学", "繪圖", "cad", "工程圖學"],
        "化學/化工/材料": ["有機化學", "普化", "化工", "材料"],
        "企業管理/財金/商管": ["經濟學", "會計", "統計學", "行銷", "管理學", "財務"],
        "應用外語/文史哲": ["英文", "多益", "toeic", "文學", "哲學", "日文"],
        "設計/建築/數位媒體": ["視覺", "色彩", "排版", "photoshop", "建築史", "ui", "ux"]
    }
    for dept_name, keywords in dept_keywords.items():
        if any(word in text for word in keywords):
            dept = dept_name
            break
    if "微積分" in text or "普通物理" in text or "國文" in text:
        dept = "不限科系/通識核心"
    return cat, dept


init_db()

# ==========================================
# 2. Session 狀態與資料庫核心操作
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'user_uni' not in st.session_state:
    st.session_state.user_uni = ""


def login_user(student_id, password):
    conn = sqlite3.connect('streamlit_national_books_v3.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT university FROM users WHERE student_id = ? AND password = ?", (student_id, password))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None


def register_user(student_id, password, university):
    try:
        conn = sqlite3.connect('streamlit_national_books_v3.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (student_id, password, university, green_coins) VALUES (?, ?, ?, 100)",
                       (student_id, password, university))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_coins(student_id):
    conn = sqlite3.connect('streamlit_national_books_v3.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(student_id, amount):
    conn = sqlite3.connect('streamlit_national_books_v3.db', check_same_thread=False)
    cursor = conn.cursor()