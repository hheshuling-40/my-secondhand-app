import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與網頁自動配置
st.set_page_config(page_title="Campus Market", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 UI 視覺優化
# ==========================================
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-title {
        font-size: clamp(22px, 4vw, 30px);
        font-weight: 800;
        color: #212529;
        margin-bottom: 20px;
    }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    .product-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
        display: flex;
        flex-direction: row;
        gap: 20px;
        align-items: center;
        cursor: pointer;
    }
    .prod-img-container {
        flex: 1.2;
        min-width: 120px;
        max-width: 200px;
    }
    .prod-info-container {
        flex: 3;
    }
    .prod-action-container {
        flex: 1.5;
        text-align: right;
        min-width: 150px;
    }
    .line-btn {
        background: linear-gradient(135deg, #06C755 0%, #05b34c 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        text-align: center;
        padding: 10px;
        display: block;
        text-decoration: none;
        font-size: 14px;
        margin-top: 5px;
    }
    .emap-btn {
        background: linear-gradient(135deg, #212529 0%, #343a40 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        text-align: center;
        padding: 8px 16px;
        display: inline-block;
        text-decoration: none;
        font-size: 13px;
        margin-bottom: 10px;
    }
    .stButton>button {
        height: 50px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
    }
    .lost-card {
        background-color: #fff9db;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #fcc419;
        margin-bottom: 15px;
    }
    .price-tag {
        font-size: 26px;
        font-weight: 700;
        color: #212529;
        margin-bottom: 5px;
    }
    .record-box {
        background: #f1f3f5;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 地理大數據與基礎設定
# ==========================================
DB_NAME = 'streamlit_campus_market_v116_perfect_taiwan_fixed.db'

# 簡化體系名稱，移除括號贅字
CAMPUS_TYPE_MAP = {
    "公立學校": [
        "國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學",
        "國立成功大學", "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學",
        "國立臺灣科技大學", "國立臺北科技大學", "國立雲林科技大學", "國立屏東科技大學", "國立虎尾科技大學"
    ],
    "私立學校": [
        "輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學",
        "靜宜大學", "長庚大學", "元智大學", "中華大學", "大葉大學", "華梵大學"
    ]
}

CAMPUS_LABELS = list(CAMPUS_TYPE_MAP.keys())

EMAP_URLS = {
    "7-11": "https://emap.pcsc.com.tw/",
    "全家": "https://www.family.com.tw/Marketing/zh/Map",
    "萊爾富": "https://www.hilife.com.tw/storeInquiry_street.aspx",
    "OK": "https://www.okmart.com.tw/convenient_shopSearch"
}

PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件"]


# ==========================================
# 1. 資料庫基礎建設
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT NOT NULL, name TEXT DEFAULT '同學', password TEXT NOT NULL, university TEXT NOT NULL, 
            line_id TEXT DEFAULT '未填寫', green_coins INTEGER DEFAULT 100, email TEXT DEFAULT '',
            PRIMARY KEY (student_id, university)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, category TEXT NOT NULL,
            university TEXT NOT NULL, department TEXT NOT NULL, description TEXT, shipping_method TEXT DEFAULT '校園面交',
            shipping_link TEXT DEFAULT '', status TEXT DEFAULT '上架中', is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0, image_base64 TEXT, seller_id TEXT NOT NULL, buyer_id TEXT,
            final_trade_info TEXT DEFAULT ''
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL, gift_name TEXT NOT NULL, 
            code TEXT NOT NULL, status TEXT DEFAULT '未使用', timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lost_found (
            id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT NOT NULL, university TEXT NOT NULL,
            item_name TEXT NOT NULL, place TEXT NOT NULL, contact_location TEXT NOT NULL, 
            description TEXT, finder_id TEXT NOT NULL, image_base64 TEXT, status TEXT DEFAULT '招領中'
        )
    ''')
    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 狀態管理
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "探索二手市集"


def get_seller_masked_name(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT name FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else "同學"


def get_user_line(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else "未填寫"


def get_coins(student_id, university):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT green_coins FROM users WHERE student_id = ? AND university = ?",
                       (student_id, university)).fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(student_id, university, amount):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ? AND university = ?",
                 (amount, student_id, university))
    conn.commit()
    conn.close()


# ==========================================
# 3. 登入 / 註冊區
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🛍 Campus Market 全國大學生智慧市集</div>', unsafe_allow_html=True)

    mode = st.radio("操作項目", ["登入", "註冊", "忘記密碼"], horizontal=True)

    if mode == "登入":
        log_type = st.selectbox("體系類型", CAMPUS_LABELS)
        log_uni = st.selectbox("就讀學校", CAMPUS_TYPE_MAP[log_type])

        with st.form("login_form"):
            sid = st.text_input("學號")
            pas = st.text_input("密碼", type="password")
            if st.form_submit_button("登入"):
                conn = sqlite3.connect(DB_NAME)
                res = conn.execute(
                    "SELECT university, name FROM users WHERE student_id = ? AND password = ? AND university = ?",
                    (sid, pas, log_uni)).fetchone()
                conn.close()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.student_id = sid
                    st.session_state.user_uni = res[0]
                    st.session_state.user_name = res[1]
                    st.rerun()
                else:
                    st.error("輸入錯誤")

    elif mode == "註冊":
        reg_name = st.text_input("姓名")
        reg_sid = st.text_input("學號")
        reg_email = st.text_input("電子郵件")
        reg_type = st.selectbox("學校體系", CAMPUS_LABELS)
        reg_uni = st.selectbox("所屬大學", CAMPUS_TYPE_MAP[reg_type])
        reg_line = st.text_input("LINE ID")
        reg_pass = st.text_input("密碼", type="password")

        if st.button("註冊"):
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.execute(
                    "INSERT INTO users (student_id, name, password, university, line_id, green_coins, email) VALUES (?, ?, ?, ?, ?, 100, ?)",
                    (reg_sid, reg_name, reg_pass, reg_uni, reg_line, reg_email))
                conn.commit()
                conn.close()
                st.success("註冊成功")
            except:
                st.error("註冊失敗")

    elif mode == "忘記密碼":
        st.info("請洽系統管理員。")

# ==========================================
# 4. 主功能區
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    current_name = st.session_state.user_name

    with st.sidebar:
        st.markdown(f"### 🧑‍🎓 {current_name} 同學")
        st.write(f"學校｜{current_uni}")
        st.metric(label="我的綠幣", value=f"{get_coins(current_student, current_uni)} 🪙")
        if st.button("🚪 登出", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="main-title">🛍 Campus Market</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("二手市集", use_container_width=True): st.session_state.current_menu = "探索二手市集"
    with c2:
        if st.button("物資上架", use_container_width=True): st.session_state.current_menu = "智慧物資上架"
    with c3:
        if st.button("綠幣福利", use_container_width=True): st.session_state.current_menu = "綠幣集點福利"
    with c4:
        if st.button("失物招領", use_container_width=True): st.session_state.current_menu = "失物招領中心"

    st.write("---")

    # 二手市集
    if st.session_state.current_menu == "探索二手市集":
        search_cat = st.selectbox("分類項目", PRODUCT_CATEGORIES)

        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM products WHERE status = '上架中'", conn)
        conn.close()


        @st.dialog("🔍 商品詳情")
        def show_product_details_dialog(prod_data):
            st.write(f"### {prod_data['name']}")
            st.write(f"價格：${prod_data['price']:.0f} 元 | 學校：{prod_data['university']}")

            # 精簡配送選項
            buyer_ship_choice = st.selectbox("配送管道", ["超商取貨", "賣貨便/好賣+", "校園面交"])
            final_memo_output = ""

            if buyer_ship_choice == "賣貨便/好賣+":
                if prod_data['shipping_link']:
                    st.markdown(f"[👉 點我前往外部賣場]({prod_data['shipping_link']})")
                    final_memo_output = f"賣貨便下單：{prod_data['shipping_link']}"
                else:
                    st.warning("賣家未提供連結，請用 LINE 聯繫。")
                    final_memo_output = "待開賣場"

            elif buyer_ship_choice == "超商取貨":
                chain_choice = st.selectbox("選擇超商", ["7-11", "全家", "萊爾富", "OK"])
                target_url = EMAP_URLS.get(chain_choice, "https://www.google.com")
                st.markdown(f'[🌐 開啟電子地圖]({target_url})', unsafe_allow_html=True)

                user_store_input = st.text_input("門市名稱/店號")
                b_name = st.text_input("收件人姓名")
                b_phone = st.text_input("手機號碼")
                if user_store_input and b_name and b_phone:
                    final_memo_output = f"[{chain_choice}] {user_store_input} ({b_name}/{b_phone})"

            elif buyer_ship_choice == "校園面交":
                meet_memo = st.text_input("面交時間/地點")
                if meet_memo:
                    final_memo_output = f"面交：{meet_memo}"

            if st.button("確認下單", use_container_width=True, type="primary"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("UPDATE products SET status = '已售出', buyer_id = ?, final_trade_info = ? WHERE id = ?",
                             (current_student, final_memo_output, prod_data['id']))
                conn.commit()
                conn.close()
                st.success("下單成功！")
                time.sleep(1)
                st.rerun()


        for idx, row in df.iterrows():
            st.markdown(f"""
            <div class="product-card">
                <div class="prod-info-container">
                    h4>{row['name']}</h4>
                    <p style="color:#6c757d; font-size:13px;">🏫 {row['university']} | 🚚 {row['shipping_method']}</p>
                </div>
                <div class="prod-action-container"><div class="price-tag">${row['price']:.0f}</div></div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("查看詳情", key=f"v_{row['id']}", use_container_width=True):
                show_product_details_dialog(row)

    # 物資上架
    elif st.session_state.current_menu == "智慧物資上架":
        st.subheader("物資快速上架")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱")
            p_price = st.number_input("售價", min_value=0, value=100)
            p_shipping = st.selectbox("運送形式", ["校園面交", "7-11 賣貨便", "全家好賣+"])
            p_link = st.text_input("賣場連結(選填)")
            p_desc = st.text_area("說明")

            if st.form_submit_button("上架商品"):
                if p_name:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        'INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, seller_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (p_name, p_price, "生活雜物", current_uni, "不限科系", p_desc, p_shipping, p_link,
                         current_student))
                    conn.commit()
                    conn.close()
                    st.success("上架成功")
                    st.rerun()

    # 綠幣福利
    elif st.session_state.current_menu == "綠幣集點福利":
        st.subheader("點數福利社")
        st.info(f"當前點數：{get_coins(current_student, current_uni)} 🪙")
        if st.button("兌換 77乳加巧克力 (30點)"):
            if get_coins(current_student, current_uni) >= 30:
                modify_coins(current_student, current_uni, -30)
                st.success("兌換成功")
                st.rerun()
            else:
                st.error("點數不足")

    # 失物招領中心
    elif st.session_state.current_menu == "失物招領中心":
        st.subheader("失物招領中心")
        t1, t2 = st.tabs(["招領看板", "發布公告"])

        with t1:
            conn = sqlite3.connect(DB_NAME)
            df_lost = pd.read_sql_query("SELECT * FROM lost_found WHERE status='招領中'", conn)
            conn.close()
            for _, row in df_lost.iterrows():
                st.markdown(f"""
                <div class="lost-card">
                    <h5>🔍 {row['item_name']} ({row['university']})</h5>
                    <p>地點：{row['place']} | 認領處：{row['contact_location']}</p>
                </div>
                """, unsafe_allow_html=True)

        with t2:
            # 建立連動選擇，移除幾所的贅字
            l_type = st.selectbox("選擇體系", CAMPUS_LABELS, key="lost_type")
            l_uni = st.selectbox("選擇學校", CAMPUS_TYPE_MAP[l_type], key="lost_uni")

            with st.form("lost_form", clear_on_submit=True):
                l_name = st.text_input("失物名稱")
                l_place = st.text_input("拾獲位置")
                l_contact = st.text_input("領取地點")
                l_desc = st.text_area("備註說明")

                # 統一精簡改為「發布公告」
                if st.form_submit_button("發布公告"):
                    if l_name and l_place and l_contact:
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO lost_found (region, university, item_name, place, contact_location, description, finder_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (l_type, l_uni, l_name, l_place, l_contact, l_desc, current_student))
                        conn.commit()
                        conn.close()
                        st.success("公告已發布！")
                        time.sleep(0.5)
                        st.rerun()