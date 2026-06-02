import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io

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
# 1. 資料庫智慧初始化 (強制防錯版)
# ==========================================
def init_db():
    try:
        # 使用全新的資料庫名稱，防止舊的壞檔卡住
        conn = sqlite3.connect('streamlit_national_books_v4.db', check_same_thread=False)
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
        # 預先塞入一個測試帳號 (雲科學號)，密碼 1234
        cursor.execute(
            "INSERT OR IGNORE INTO users (student_id, password, university, green_coins) VALUES ('B11321123', '1234', '國立雲林科技大學', 100)")
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"資料庫初始化失敗，錯誤原因: {e}")


def auto_classify_book(name, description):
    text = (name + " " + description).lower()
    cat = "書籍"
    if "講義" in text or "筆記" in text or "考古題" in text:
        cat = "學術講義"
    elif "計算機" in text or "平板" in text or "耳機" in text:
        cat = "3C配件"

    dept = "不限科系/通識核心"
    dept_keywords = {
        "資訊工程/資管系": ["程式", "python", "java", "演算法", "資料結構", "網頁", "計概", "ai", "資安", "資管"],
        "電機/電子/自動化": ["電路", "電子學", "電磁", "訊號", "控制", "工數", "工程數學"],
        "機械/土木/營建": ["力學", "流體", "熱力学", "繪圖", "cad", "工程圖學", "營建"],
        "化學/化工/材料": ["有機化學", "普化", "化工", "材料", "化學"],
        "企業管理/財金/商管": ["經濟學", "會計", "統計學", "行銷", "管理學", "財務", "企管"],
        "應用外語/文史哲": ["英文", "多益", "toeic", "文學", "哲學", "日文", "外語"],
        "設計/建築/數位媒體": ["視覺", "色彩", "排版", "photoshop", "建築史", "ui", "ux", "設計"]
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
# 2. Session 狀態與核心操作
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'user_uni' not in st.session_state:
    st.session_state.user_uni = ""


def login_user(student_id, password):
    try:
        conn = sqlite3.connect('streamlit_national_books_v4.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT university FROM users WHERE student_id = ? AND password = ?", (student_id, password))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except:
        return None


def register_user(student_id, password, university):
    try:
        conn = sqlite3.connect('streamlit_national_books_v4.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (student_id, password, university, green_coins) VALUES (?, ?, ?, 100)",
                       (student_id, password, university))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_coins(student_id):
    try:
        conn = sqlite3.connect('streamlit_national_books_v4.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0
    except:
        return 0


def modify_coins(student_id, amount):
    try:
        conn = sqlite3.connect('streamlit_national_books_v4.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ?", (amount, student_id))
        conn.commit()
        conn.close()
    except:
        pass


# ==========================================
# 3. 畫面渲染：登入 / 註冊系統
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 全國大學二手教科書 AI 智慧交流平台")
    st.subheader("開學挖寶、畢業減碳，直達各校系必修用書")

    auth_tab1, auth_tab2 = st.tabs(["🔑 同學登入", "📝 新同學註冊"])

    with auth_tab1:
        with st.form("login_form"):
            login_sid = st.text_input("請輸入學號", placeholder="例如：B11321123")
            login_pass = st.text_input("請輸入密碼", type="password", placeholder="請輸入密碼")
            btn_login = st.form_submit_button("立即進入市集")
            if btn_login:
                uni_found = login_user(login_sid, login_pass)
                if uni_found:
                    st.session_state.logged_in = True
                    st.session_state.student_id = login_sid
                    st.session_state.user_uni = uni_found
                    st.success(f"🎉 歡迎 {uni_found} 同學 ({login_sid}) 登入！請點擊下方按鈕重新整理畫面。")
                    st.button("進入大廳 🚀")
                else:
                    st.error("❌ 學號或密碼錯誤。（提示：可使用學號 B11321123 密碼 1234 進行測試）")

    with auth_tab2:
        with st.form("register_form"):
            reg_sid = st.text_input("註冊學號", placeholder="請輸入學號")
            reg_uni = st.selectbox("選擇您的所屬大學", UNIVERSITY_LIST, index=0)
            reg_pass = st.text_input("設定系統密碼", type="password")
            btn_reg = st.form_submit_button("註冊並領取 100 綠幣 🪙")
            if btn_reg:
                if not reg_sid or not reg_pass:
                    st.warning("欄位不可為空白！")
                elif register_user(reg_sid, reg_pass, reg_uni):
                    st.success("🎉 註冊成功！請切換至【同學登入】分頁進行登入。")
                else:
                    st.error("❌ 該學號已存在。")

# ==========================================
# 4. 主功能區 (登入後解鎖)
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni

    # 側邊欄個人資訊
    with st.sidebar:
        st.title("📚 我的書香帳戶")
        st.write(f"🏫 學校：**{current_uni}**")
        st.write(f"👤 學號：**{current_student}**")
        st.metric(label="我的環保綠幣", value=f"{get_coins(current_student)} 🪙")
        st.write("---")
        if st.button("🚪 登出系統", color="red"):
            st.session_state.logged_in = False
            st.session_state.student_id = ""
            st.session_state.user_uni = ""
            st.button("確認登出")

    tab1, tab2, tab3, tab4 = st.tabs(["🛍️ 全國跨校市集挖寶", "🏪 智慧快速上架", "🎰 綠幣幸運抽獎", "📋 我的交易與書單"])

    # ------------------------------------------
    # TAB 1: 跨校市集挖寶
    # ------------------------------------------
    with tab1:
        st.header("🌍 全國大學二手書交流市集")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_uni = st.selectbox("🏫 依大學篩選", ["全部大學"] + UNIVERSITY_LIST, index=UNIVERSITY_LIST.index(
                current_uni) + 1 if current_uni in UNIVERSITY_LIST else 0)
        with col_f2:
            search_dept = st.selectbox("🎓 依適用科系篩選", ["全部科系"] + DEPARTMENT_LIST)
        with col_f3:
            search_cat = st.selectbox("📦 物品類型", ["全部類型", "書籍", "3C配件", "學術講義"])

        conn = sqlite3.connect('streamlit_national_books_v4.db', check_same_thread=False)
        query = "SELECT id, image_base64, name, price, category, university, department, description, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"
        if search_uni != "全部大學":
            query += f" AND university = '{search_uni}'"
        if search_dept != "全部科系":
            query += f" AND department = '{search_dept}'"
        if search_cat != "全部類型":
            query += f" AND category = '{search_cat}'"

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            st.info("💡 哇！目前這個校系組合還沒有對應的書籍在售，快去【智慧快速上架】當第一個人吧！")