import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與現代化版面
st.set_page_config(page_title="Campus Market | 校園智慧市集", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 視覺優化 UI
# ==========================================
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-title {
        font-size: 30px;
        font-weight: 800;
        color: #212529;
        margin-bottom: 5px;
    }
    .line-btn {
        background: linear-gradient(135deg, #111111 0%, #333333 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        text-align: center;
        padding: 14px;
        display: block;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
        margin-bottom: 15px;
        font-size: 15px;
    }
    .line-green-btn {
        background: linear-gradient(135deg, #06C755 0%, #05b34c 100%) !important;
        color: white !important;
    }
    .stButton>button {
        height: 65px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        border: none !important;
        background-color: #ffffff !important;
        color: #495057 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    .stButton>button:hover {
        background-color: #f1f3f5 !important;
        color: #06C755 !important;
    }
    .product-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    .lost-card {
        background-color: #fff9db;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #fcc419;
        margin-bottom: 15px;
    }
    .price-tag {
        font-size: 24px;
        font-weight: 700;
        color: #212529;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 常數地圖設定
# ==========================================
REGION_UNIVERSITY_MAP = {
    "中部地區": ["國立雲林科技大學", "國立中興大學", "逢甲大學", "東海大學"],
    "北部地區": ["國立台灣大學", "國立清華大學", "國立陽明交通大學"],
    "南部地區": ["國立成功大學", "國立中山大學", "國立中正大學"],
    "東部與離島": ["國立東華大學", "國立宜蘭大學"]
}
YUNTECH_ALL_DEPTS = ["不限科系/共同通識核心", "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系",
                     "工業設計系", "視覺傳達設計系", "數位媒體設計系", "企業管理系", "資訊管理系", "應用外語系"]
PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件", "體育用品", "學術講義"]


# ==========================================
# 1. 資料庫基礎建設 (全面升級至全新的 v18 版資料庫)
# ==========================================
def init_db():
    conn = sqlite3.connect('streamlit_campus_market_v18.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY, password TEXT NOT NULL, university TEXT NOT NULL, 
            line_id TEXT DEFAULT '未填寫', green_coins INTEGER DEFAULT 100, email TEXT DEFAULT ''
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, category TEXT NOT NULL,
            university TEXT NOT NULL, department TEXT NOT NULL, description TEXT, shipping_method TEXT DEFAULT '校園面交',
            shipping_link TEXT DEFAULT '', status TEXT DEFAULT '上架中', is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0, image_base64 TEXT, seller_id TEXT NOT NULL, buyer_id TEXT
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
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT NOT NULL, place TEXT NOT NULL, 
            contact_location TEXT NOT NULL, description TEXT, finder_id TEXT NOT NULL, status TEXT DEFAULT '招領中'
        )
    ''')
    # 💡 修正核心：明確定義 INSERT 的欄位順序，保證 SQLite 絕對不會出錯
    cursor.execute("""
        INSERT OR IGNORE INTO users (student_id, password, university, line_id, green_coins, email) 
        VALUES ('B11321123', 'A66666666', '國立雲林科技大學', 'yuntech_cool', 150, 'b11321123@yuntech.edu.tw')
    """)
    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 狀態管理與核心函式
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "🔍 探索雜貨市集"
if 'login_attempts' not in st.session_state: st.session_state.login_attempts = 0


def get_user_line(student_id):
    conn = sqlite3.connect('streamlit_campus_market_v18.db')
    res = conn.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else "未填寫"


def get_coins(student_id):
    conn = sqlite3.connect('streamlit_campus_market_v18.db')
    res = conn.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(student_id, amount):
    conn = sqlite3.connect('streamlit_campus_market_v18.db')
    conn.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ?", (amount, student_id))
    conn.commit()
    conn.close()


# ==========================================
# 3. 登入 / 註冊 / 忘記密碼驗證區
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 Campus Market</div>', unsafe_allow_html=True)
    st.write("全台大學生專屬・AI智慧二手物資與失物防護網")

    mode = st.radio("請選擇操作項目：", ["🔑 同學登入", "📝 新同學註冊帳號", "❓ 忘記密碼（安全重設）"], horizontal=True)

    if mode == "🔑 同學登入":
        with st.form("login_form"):
            sid = st.text_input("學號", placeholder="請輸入您的完整學號")
            pas = st.text_input("密碼", type="password", placeholder="請輸入密碼")
            if st.form_submit_button("登入市集"):
                conn = sqlite3.connect('streamlit_campus_market_v18.db')
                res = conn.execute("SELECT university FROM users WHERE student_id = ? AND password = ?",
                                   (sid, pas)).fetchone()
                conn.close()
                if res:
                    st.session_state.logged_in, st.session_state.student_id, st.session_state.user_uni = True, sid, res[
                        0]
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error(f"❌ 學號或密碼錯誤！(目前已連續錯誤 {st.session_state.login_attempts} 次)")

        if st.session_state.login_attempts >= 3:
            st.warning(
                "⚠️ 偵測到您已連續 3 次輸入錯誤密碼！建議您可以點擊上方單選鈕切換至「❓ 忘記密碼（安全重設）」，透過當初註冊的電子郵件進行身分認證並快速修改密碼。")

    elif mode == "📝 新同學註冊帳號":
        st.subheader("填寫校園註冊資料")
        reg_sid = st.text_input("註冊學號 *", placeholder="例如：B112XXXXX")
        reg_email = st.text_input("學校聯絡電子郵件 (忘記密碼安全憑證) *", placeholder="example@yuntech.edu.tw")
        reg_reg = st.selectbox("學校區域 *", list(REGION_UNIVERSITY_MAP.keys()))
        reg_uni = st.selectbox("所屬大學 *", REGION_UNIVERSITY_MAP[reg_reg])
        reg_line = st.text_input("LINE ID *", placeholder="方便買家聯絡您")
        reg_pass = st.text_input("設定系統密碼 *", type="password", placeholder="請妥善保管密碼")

        if st.button("提交註冊並領取 100 幣 🪙"):
            if not reg_sid or not reg_email or not reg_pass:
                st.error("請完整填寫必填欄位！")
            else:
                try:
                    conn = sqlite3.connect('streamlit_campus_market_v18.db')
                    conn.execute(
                        "INSERT INTO users (student_id, password, university, line_id, green_coins, email) VALUES (?, ?, ?, ?, 100, ?)",
                        (reg_sid, reg_pass, reg_uni, reg_line, reg_email))
                    conn.commit()
                    conn.close()
                    st.success("🎉 註冊成功！快切換到「同學登入」吧！")
                except:
                    st.error("此學號已被註冊過。")

    elif mode == "❓ 忘記密碼（安全重設）":
        st.subheader("🛡️ 忘記密碼：安全雙重認證機制")
        st.caption("為確保帳號資安，請提供原註冊學號與電子郵件。系統完全比對相符後，將會即時提供重設連結通道。")

        with st.form("forgot_form"):
            verify_sid = st.text_input("請輸入您的學號", placeholder="例如：B112XXXXX")
            verify_email = st.text_input("請輸入註冊時綁定的電子郵件", placeholder="example@yuntech.edu.tw")
            submit_verify = st.form_submit_button("🚀 發送更改密碼連結並進行身分雙重確認")

            if submit_verify:
                conn = sqlite3.connect('streamlit_campus_market_v18.db')
                user_data = conn.execute("SELECT password FROM users WHERE student_id = ? AND email = ?",
                                         (verify_sid, verify_email)).fetchone()
                conn.close()

                if user_data:
                    st.success("🟢 雙重認證成功！已成功確認是您本人。密碼修改重設通道已在下方開啟：")
                    st.session_state.verification_success = True
                else:
                    st.error("❌ 雙重認證失敗：學號與電子郵件不匹配，無法核發密碼更改通道！")
                    st.session_state.verification_success = False

        if st.session_state.get('verification_success', False):
            with st.form("new_password_form"):
                new_pwd = st.text_input("請輸入全新密碼", type="password", placeholder="請輸入新密碼")
                if st.form_submit_button("💾 確認更新密碼"):
                    if new_pwd:
                        conn = sqlite3.connect('streamlit_campus_market_v18.db')
                        conn.execute("UPDATE users SET password = ? WHERE student_id = ?", (new_pwd, verify_sid))
                        conn.commit()
                        conn.close()
                        st.success("🎉 密碼重設成功！請切換至「🔑 同學登入」重新進入市集。")
                        st.session_state.verification_success = False
                        st.session_state.login_attempts = 0
                    else:
                        st.warning("密碼不可為空")

# ==========================================
# 4. 主功能區 (登入成功解鎖)
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    my_line = get_user_line(current_student)

    with st.sidebar:
        st.markdown("### 🧑‍🎓 攤主名片")
        st.write(f"學校｜**{current_uni}**")
        st.write(f"學號｜**{current_student}**")
        st.metric(label="我的環保集點幣", value=f"{get_coins(current_student)} 🪙")
        if st.button("🚪 登出市集", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 功能操控面板
    st.markdown('<div class="main-title">🛍️ 智慧校園綜合服務選單</div>', unsafe_allow_html=True)
    st.write("---")

    row1_c1, row1_c2, row1_c3 = st.columns(3)
    row2_c1, row2_c2, row2_c3 = st.columns(3)

    with row1_c1:
        if st.button("🔍 探索雜貨市集\n(看詳情與購買商品)",
                     use_container_width=True): st.session_state.current_menu = "🔍 探索雜貨市集"
    with row1_c2:
        if st.button("🚀 AI 智慧上架\n(支援面交/7-11賣貨便)",
                     use_container_width=True): st.session_state.current_menu = "🚀 AI 智慧上架"
    with row1_c3:
        if st.button("📜 我的拍賣攤位\n(查看買賣與兌換券)",
                     use_container_width=True): st.session_state.current_menu = "📜 我的拍賣攤位"
    with row2_c1:
        if st.button("🎁 綠幣集點福利社\n(免費換超商零食好禮)",
                     use_container_width=True): st.session_state.current_menu = "🎁 綠幣集點福利社"
    with row2_c2:
        st.markdown(
            f'<a href="https://line.me/ti/p/~{my_line}" target="_blank" class="line-btn line-green-btn">💬 一鍵測試 LINE 聯絡</a>',
            unsafe_allow_html=True)
    with row2_c3:
        if st.button("📍 失物招領中心\n(全校失物公告與面交地圖)",
                     use_container_width=True): st.session_state.current_menu = "📍 失物招領中心"

    st.write("---")

    # ------------------------------------------
    # 功能 1: 探索雜貨市集
    # ------------------------------------------
    if st.session_state.current_menu == "🔍 探索雜貨市集":
        st.subheader("🪐 校園二手物資流通池")
        f1, f2 = st.columns(2)
        with f1:
            search_cat = st.selectbox("📦 物品分類項目", PRODUCT_CATEGORIES)
        with f2:
            search_dept = st.selectbox("🎓 適用科系篩選", ["全部科系"] + YUNTECH_ALL_DEPTS)

        conn = sqlite3.connect('streamlit_campus_market_v18.db')
        query = "SELECT id, image_base64, name, price, category, university, department, description, shipping_method, shipping_link, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            st.info("💡 目前市集商場尚無寶物在售。")
        else:
            for index, row in df.iterrows():
                st.markdown(f'<div class="product-card">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1.2, 3, 1.5])
                with c1:
                    if row['image_base64']:
                        st.image(row['image_base64'], use_container_width=True)
                    else:
                        st.markdown(
                            "<div style='background-color:#f1f3f5;height:100px;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#adb5bd;font-size:13px;'>📦 暫無商品照</div>",
                            unsafe_allow_html=True)
                with c2:
                    st.markdown(f"#### {row['name']}")
                    st.caption(f"🏫 學校：{row['university']} | 🚚 運送管道：{row['shipping_method']}")
                with c3:
                    st.markdown(f'<div class="price-tag">${row['price']:.0f}</div>', unsafe_allow_html=True)
                    with st.expander("🔍 查看細節與點此購買"):
                        st.write(f"💡 **物況描述：** {row['description']}")
                        if row['shipping_method'] == "7-11 賣貨便" and row['shipping_link']:
                            st.markdown(
                                f'<a href="{row["shipping_link"]}" target="_blank" style="background-color:#E60012;color:white;padding:6px 12px;text-decoration:none;border-radius:6px;display:block;text-align:center;font-weight:bold;margin-bottom:10px;">🏪 點此直達 7-11 賣貨便下單</a>',
                                unsafe_allow_html=True)
                        if st.button("🛒 確定下單購買", key=f"buy_{row['id']}", use_container_width=True):
                            if row['seller_id'] == current_student:
                                st.error("不能買自己的物品")
                            else:
                                conn = sqlite3.connect('streamlit_campus_market_v18.db')
                                conn.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                             (current_student, row['id']))
                                conn.commit()
                                conn.close()
                                modify_coins(current_student, 20)
                                st.balloons()
                                st.success("🎉 下單成功！商品已移入您的拍賣攤位。")
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 2: AI 智慧上架
    # ------------------------------------------
    elif st.session_state.current_menu == "🚀 AI 智慧上架":
        st.subheader("🏪 多元物資快速上架櫃檯")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱", placeholder="例如：微積分課本 / 藍牙耳機")
            p_price = st.number_input("欲售金額 (TWD)", min_value=0, value=100)
            p_shipping = st.selectbox("🚚 運送形式", ["校園面交", "7-11 賣貨便", "全家好賣+"])
            p_link = st.text_input("🔗 網頁賣場連結 (選填)", placeholder="若選賣貨便，可在此附上下單網址")
            p_desc = st.text_area("物況詳細說明")
            p_file = st.file_uploader("📸 上傳商品實體照", type=['png', 'jpg', 'jpeg'])

            if st.form_submit_button("🚀 發布至校園市集"):
                if p_name and p_desc:
                    b64_str = ""
                    if p_file is not None:
                        img = Image.open(p_file).convert("RGB")
                        img.thumbnail((300, 300))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                    text = (p_name + " " + p_desc).lower()
                    category, target_dept = "生活雜物", "不限科系/共同通識核心"
                    if any(w in text for w in ["書", "課本", "版"]):
                        category = "書籍"
                    elif any(w in text for w in ["計算機", "耳機", "充電", "iphone"]):
                        category = "3C配件"

                    conn = sqlite3.connect('streamlit_campus_market_v18.db')
                    conn.execute(
                        'INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, seller_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (p_name, p_price, category, current_uni, target_dept, p_desc, p_shipping, p_link,
                         current_student))
                    conn.commit()
                    conn.close()
                    modify_coins(current_student, 10)
                    st.success("🎉 上架成功！")
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利社
    # ------------------------------------------
    elif st.session_state.current_menu == "🎁 綠幣集點福利社":
        st.subheader("🪙 環保低碳集點福利社")
        user_coins = get_coins(current_student)
        st.info(f"當前點數： {user_coins} 🪙")

        gifts = [
            {"name": "全家 77乳加巧克力 🍫", "cost": 30},
            {"name": "校園影印店 50元抵用券 📑", "cost": 60},
            {"name": "學校咖啡廳 免費中杯拿鐵 ☕", "cost": 100}
        ]

        for idx, g in enumerate(gifts):
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            gc1, gc2, gc3 = st.columns([3, 1, 1])
            with gc1:
                st.write(f"##### {g['name']}")
            with gc2:
                st.write(f"**{g['cost']} 點**")
            with gc3:
                if st.button("確認兌換", key=f"g_{idx}", use_container_width=True):
                    if user_coins >= g['cost']:
                        modify_coins(current_student, -g['cost'])
                        v_code = f"CM-{random.randint(100000, 999999)}"
                        v_time = time.strftime("%Y-%m-%d %H:%M")

                        conn = sqlite3.connect('streamlit_campus_market_v18.db')
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                            (current_student, g['name'], v_code, v_time))
                        conn.commit()
                        conn.close()

                        st.balloons()
                        st.success(f"🎉 兌換成功！序號【{v_code}】已存入您的票券專區。")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("點數不足")
            st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 4: 我的拍賣攤位 & 電子票券紀錄視窗
    # ------------------------------------------
    elif st.session_state.current_menu == "📜 我的拍賣攤位":
        st.subheader("📋 My Dashboard")

        st.markdown("### 🎟️ 我的電子兌換券專區 (超商零食核銷紀錄)")
        conn = sqlite3.connect('streamlit_campus_market_v18.db')
        df_vouchers = pd.read_sql_query(
            f"SELECT id as 票券ID, gift_name as 獎品項目, code as 核銷電子序號, timestamp as 兌換時間, status as 狀態 FROM vouchers WHERE student_id = '{current_student}'",
            conn)
        if df_vouchers.empty:
            st.caption("目前尚無兌換紀錄，快去賺點數免費換點心吧！")
        else:
            st.dataframe(df_vouchers, use_container_width=True, hide_index=True)
            st.info("💡 領取指南：請至學校大樓辦公室出示上述「核銷電子序號」即可直接現場兌領！")

        st.write("---")
        st.write("#### 🛍️ 我買進的物品項目")
        df_buy = pd.read_sql_query(
            f"SELECT id as 商品ID, name as 商品名稱, price as 金額 FROM products WHERE buyer_id = '{current_student}'",
            conn)
        st.dataframe(df_buy, use_container_width=True, hide_index=True)
        conn.close()

    # ------------------------------------------
    # 功能 5: 📍 失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "📍 失物招領中心":
        st.subheader("📍 雲科大校園安全面交導航 × 🔍 全校失物招領服務中心")
        m_tab1, m_tab2 = st.tabs(["🔍 全校失物招領佈告欄", "📍 校園安全面交熱點指引"])

        with m_tab1:
            st.write("失物尋找與發布平台，同學撿到物資可以登記在這裡。")
            with st.expander("➕ 協助發布失物招領公告"):
                with st.form("lost_form", clear_on_submit=True):
                    l_name = st.text_input("物品名稱 *", placeholder="例如：學生證 / 藍牙耳機盒")
                    l_place = st.text_input("拾獲地點 *", placeholder="例如：圖書館三樓")
                    l_contact = st.text_input("目前暫存位置 (領取地點) *", placeholder="例如：圖書館櫃檯")
                    l_desc = st.text_area("外觀備註")
                    if st.form_submit_button("📢 上傳失物公告"):
                        if l_name and l_place and l_contact:
                            conn = sqlite3.connect('streamlit_campus_market_v18.db')
                            conn.execute(
                                "INSERT INTO lost_found (item_name, place, contact_location, description, finder_id) VALUES (?, ?, ?, ?, ?)",
                                (l_name, l_place, l_contact, l_desc, current_student))
                            conn.commit()
                            conn.close()
                            st.success("🎉 公告發布成功！")
                            time.sleep(0.5)
                            st.rerun()

            st.write("#### 🕵️ 當前校園招領中物件清單")
            conn = sqlite3.connect('streamlit_campus_market_v18.db')
            df_lost = pd.read_sql_query(
                "SELECT id as 公告ID, item_name as 遺失物品, place as 拾獲地點, contact_location as 前往此處領取, description as 外觀備註 FROM lost_found WHERE status='招領中'",
                conn)
            conn.close()

            if df_lost.empty:
                st.info("目前全校無失物公告。")
            else:
                for idx, row in df_lost.iterrows():
                    st.markdown(f"""
                    <div class="lost-card">
                        <h5>🔍 【招領中】{row['遺失物品']}</h5>
                        <p style='margin:2px 0;'>📍 <b>拾獲地點：</b>{row['拾獲地點']}</p>
                        <p style='margin:2px 0; color:#e67e22;'>🏢 <b>領取位置：</b>{row['前往此處領取']}</p>
                        <small>備註：{row['外觀備註']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("✨ 撤除已認領公告", key=f"res_{row['公告ID']}"):
                        conn = sqlite3.connect('streamlit_campus_market_v18.db')
                        conn.execute("UPDATE lost_found SET status='已認領' WHERE id=?", (row['公告ID'],))
                        conn.commit()
                        conn.close()
                        st.success("已完成認領！")
                        time.sleep(0.5)
                        st.rerun()

        with m_tab2:
            st.write("#### 🛡️ 雲科大推薦面交安全熱點指南")
            st.info("為了保障人身與財產安全，建議同學優先選在以下明亮且有監視器覆蓋的地方交貨：")
            st.markdown("""
            1. 📍 **雲科大圖書館大門迴廊前** (24小時錄影監控，首選)
            2. 📍 **學生活動中心便利超商門口休息區** (人潮眾多、明亮)
            3. 📍 **大禮堂正門口廣場** (視野開闊安全)
            """)