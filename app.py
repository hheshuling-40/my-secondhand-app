import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與現代化版面
st.set_page_config(page_title="Campus Market | 全國大學生智慧市集", page_icon="🛍️", layout="wide")

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
        background: linear-gradient(135deg, #06C755 0%, #05b34c 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        text-align: center;
        padding: 10px;
        display: inline-block;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(6, 199, 85, 0.15);
        transition: all 0.2s ease;
        font-size: 14px;
        margin-top: 5px;
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
# 0. 常數地圖設定 與 乾淨重置資料庫
# ==========================================
DB_NAME = 'streamlit_campus_market_v105_privacy.db'

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
            id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT NOT NULL, university TEXT NOT NULL,
            item_name TEXT NOT NULL, place TEXT NOT NULL, contact_location TEXT NOT NULL, 
            description TEXT, finder_id TEXT NOT NULL, image_base64 TEXT, status TEXT DEFAULT '招領中'
        )
    ''')

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO users (student_id, name, password, university, line_id, green_coins, email) 
            VALUES ('A66666666', '王小明', '1234', '國立雲林科技大學', 'yuntech_cool', 150, 'a66666666@yuntech.edu.tw')
        """)
    except Exception as e:
        pass

    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 狀態管理與核心隱私安全函式
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "🔍 探索雜貨市集"


# 💡 核心安全修改：將隱私遮罩符號改為 "O" 避免個資外洩
def mask_user_name(name_str):
    if not name_str or name_str == '同學':
        return "同學"
    length = len(name_str)
    if length == 2:
        return name_str[0] + "O"
    elif length == 3:
        return name_str[0] + "O" + name_str[2]
    elif length >= 4:
        return name_str[0] + "O" + name_str[-1]
    return name_str


def get_seller_masked_name(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT name FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    real_name = res[0] if res else "同學"
    return mask_user_name(real_name)


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
    st.markdown('<div class="main-title">🎓 Campus Market 全国大學生智慧市集</div>', unsafe_allow_html=True)
    st.write("已啟用多校學號防撞保護與個資隱私 O 字遮罩機制。")

    mode = st.radio("請選擇操作項目：", ["🔑 同學登入", "📝 新同學註冊帳號", "❓ 忘記密碼"], horizontal=True)

    if mode == "🔑 同學登入":
        with st.form("login_form"):
            log_reg = st.selectbox("請選取您的學校區域", list(REGION_UNIVERSITY_MAP.keys()))
            log_uni = st.selectbox("請選取您的就讀學校", REGION_UNIVERSITY_MAP[log_reg])
            sid = st.text_input("學號", placeholder="請輸入學號")
            pas = st.text_input("密碼", type="password", placeholder="請輸入密碼")
            if st.form_submit_button("登入市集"):
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
                    st.error("❌ 學校、學號或密碼輸入錯誤，請重新確認！")

    elif mode == "📝 新同學註冊帳號":
        st.subheader("填寫校園註冊資料")
        reg_name = st.text_input("您的真實姓名/稱呼 *", placeholder="外在公開會自動進行安全 O 字遮罩處理")
        reg_sid = st.text_input("註冊學號 *")
        reg_email = st.text_input("學校聯絡電子郵件 *")
        reg_reg = st.selectbox("學校區域 *", list(REGION_UNIVERSITY_MAP.keys()))
        reg_uni = st.selectbox("所屬大學 *", REGION_UNIVERSITY_MAP[reg_reg])
        reg_line = st.text_input("LINE ID *")
        reg_pass = st.text_input("設定系統密碼 *", type="password")

        if st.button("提交註冊並領取 100 幣 🪙"):
            if not reg_name or not reg_sid or not reg_email or not reg_pass:
                st.error("請完整填寫所有必填欄位！")
            else:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO users (student_id, name, password, university, line_id, green_coins, email) VALUES (?, ?, ?, ?, ?, 100, ?)",
                        (reg_sid, reg_name, reg_pass, reg_uni, reg_line, reg_email))
                    conn.commit()
                    conn.close()
                    st.success("🎉 註冊成功！快切換到「同學登入」吧！")
                except:
                    st.error("在該校中此學號已被註冊過。")

    elif mode == "❓ 忘記密碼":
        st.info("忘記密碼功能請洽各校系統管理員。")

# ==========================================
# 4. 主功能區 (登入成功解鎖)
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    current_name = st.session_state.user_name

    with st.sidebar:
        st.markdown("### 🧑‍🎓 攤主名片")
        st.markdown(f"歡迎回來，**{current_name}** 同學！👋")
        st.write(f"學校｜**{current_uni}**")
        st.write(f"學號｜**{current_student}**")
        st.metric(label="我的環保集點幣", value=f"{get_coins(current_student, current_uni)} 🪙")
        if st.button("🚪 登出市集", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="main-title">🛍 Honor 全國智慧服務選單</div>', unsafe_allow_html=True)
    st.write("---")

    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
    with row1_c1:
        if st.button("🔍 探索雜貨市集\n(購買與私訊賣家)",
                     use_container_width=True): st.session_state.current_menu = "🔍 探索雜貨市集"
    with row1_c2:
        if st.button("🚀 AI 智慧上架\n(上傳物資賺綠幣)",
                     use_container_width=True): st.session_state.current_menu = "🚀 AI 智慧上架"
    with row1_c3:
        if st.button("🎁 綠幣集點福利社\n(免費換超商點心)",
                     use_container_width=True): st.session_state.current_menu = "🎁 綠幣集點福利社"
    with row1_c4:
        if st.button("📍 失物招領中心\n(全台大學聯防網)",
                     use_container_width=True): st.session_state.current_menu = "📍 失物招領中心"

    st.write("---")

    # ------------------------------------------
    # 功能 1: 探索雜貨市集
    # ------------------------------------------
    if st.session_state.current_menu == "🔍 探索雜貨市集":
        st.subheader("🪐 全國二手物資流通池")
        f1, f2 = st.columns(2)
        with f1:
            search_cat = st.selectbox("📦 物品分類項目", PRODUCT_CATEGORIES)
        with f2:
            search_dept = st.selectbox("🎓 適用科系篩選", ["全部科系"] + YUNTECH_ALL_DEPTS)

        conn = sqlite3.connect(DB_NAME)
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

                        # 💡 核心修改：透過 O 字遮罩函式保護賣家姓名
                        masked_seller_name = get_seller_masked_name(row['seller_id'])
                        st.write(f"👤 **一手賣家：** {masked_seller_name} 同學 (誠信認證)")

                        seller_line = get_user_line(row['seller_id'])
                        st.markdown(
                            f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 聯絡賣家 LINE</a>',
                            unsafe_allow_html=True)

                        if row['shipping_method'] == "7-11 賣貨便" and row['shipping_link']:
                            st.markdown(
                                f'<a href="{row["shipping_link"]}" target="_blank" style="background-color:#E60012;color:white;padding:6px 12px;text-decoration:none;border-radius:6px;display:block;text-align:center;font-weight:bold;margin-top:10px;">🏪 直達 7-11 賣貨便</a>',
                                unsafe_allow_html=True)

                        if st.button("🛒 確定下單購買", key=f"buy_{row['id']}", use_container_width=True):
                            if row['seller_id'] == current_student and row['university'] == current_uni:
                                st.error("不能買自己的物品")
                            else:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                             (current_student, row['id']))
                                conn.commit()
                                conn.close()
                                modify_coins(current_student, current_uni, 20)
                                st.balloons()
                                st.success("🎉 下單成功！商品已成功售出。")
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 2: AI 智慧上架
    # ------------------------------------------
    elif st.session_state.current_menu == "🚀 AI 智慧上架":
        st.subheader("🏪 多元物資快速上架櫃檯")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱", placeholder="例如：微積分課本")
            p_price = st.number_input("欲售金額 (TWD)", min_value=0, value=100)
            p_shipping = st.selectbox("🚚 運送形式", ["校園面交", "7-11 賣貨便", "全家好賣+"])
            p_link = st.text_input("🔗 網頁賣場連結 (選填)")
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

                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        'INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, seller_id, image_base64) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (p_name, p_price, "生活雜物", current_uni, "不限科系/共同通識核心", p_desc, p_shipping, p_link,
                         current_student, b64_str))
                    conn.commit()
                    conn.close()
                    modify_coins(current_student, current_uni, 10)
                    st.success("🎉 上架成功！")
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利社
    # ------------------------------------------
    elif st.session_state.current_menu == "🎁 綠幣集點福利社":
        st.subheader("🪙 環保低碳集點福利社")
        user_coins = get_coins(current_student, current_uni)
        st.info(f"當前可用積點： {user_coins} 🪙")

        gifts = [
            {"name": "全家 77乳加巧克力 🍫", "cost": 30},
            {"name": "校園影印店 50元抵用券 📑", "cost": 60}
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
                        modify_coins(current_student, current_uni, -g['cost'])
                        v_code = f"CM-{random.randint(100000, 999999)}"
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                            (current_student, g['name'], v_code, "2026-06"))
                        conn.commit()
                        conn.close()
                        st.balloons()
                        st.success("🎉 兌換成功！序號已生成。")
                    else:
                        st.error("點數不足")
            st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 4: 📍 全國大學生失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "📍 失物招領中心":
        st.subheader("📍 全國大學生聯防失物招領中心")

        search_region = st.selectbox("🌐 請選擇欲查詢的台灣區域篩選失物",
                                     ["全部區域", "北部地區", "中部地區", "南部地區", "東部與離島"])

        m_tab1, m_tab2 = st.tabs(["🔍 招領佈告欄", "➕ 發布失物通報"])

        with m_tab1:
            conn = sqlite3.connect(DB_NAME)
            if search_region == "全部區域":
                query = "SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中'"
                df_lost = pd.read_sql_query(query, conn)
            else:
                query = "SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND region=?"
                df_lost = pd.read_sql_query(query, conn, params=(search_region,))
            conn.close()

            if df_lost.empty:
                st.info("💡 目前該區域暫無失物招領公告。")
            else:
                for idx, row in df_lost.iterrows():
                    # 💡 核心修改：透過 O 字遮罩函式保護拾獲者姓名
                    masked_finder_name = get_seller_masked_name(row['finder_id'])

                    st.markdown(f"""
                    <div class="lost-card">
                        <h5>🔍 【{row['region']} · {row['university']}】{row['item_name']}</h5>
                        <p style='margin:2px 0;'>📍 <b>拾獲地點：</b>{row['place']}</p>
                        <p style='margin:2px 0; color:#e67e22;'>🏢 <b>認領與暫存位置：</b>{row['contact_location']}</p>
                        <p style='margin:2px 0; color:#7f8c8d;'>👤 <b>善心拾獲人：</b>{masked_finder_name} 同學</p>
                        <small>外觀備註說明：{row['description']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    if row['image_base64']:
                        st.image(row['image_base64'], caption="遺失物實體現場照", width=250)

                    if st.button("✨ 物歸原主（撤除公告）", key=f"res_{row['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("UPDATE lost_found SET status='已認領' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.success("🎉 功德無量！已順利撤除公告。")
                        time.sleep(0.5)
                        st.rerun()

        with m_tab2:
            st.write("#### ➕ 填寫失物通報單（發布可現賺 15 點環保綠幣 🪙）")
            with st.form("lost_form", clear_on_submit=True):
                l_reg = st.selectbox("拾獲物品所在區域 *", list(REGION_UNIVERSITY_MAP.keys()))
                l_uni = st.selectbox("拾獲物品所屬學校 *", REGION_UNIVERSITY_MAP[l_reg])
                l_name = st.text_input("失物名稱 *", placeholder="例如：AirPods 左耳 / 學生證")
                l_place = st.text_input("詳細拾獲位置 *", placeholder="例如：綜大 1 樓飲水機旁")
                l_contact = st.text_input("目前暫存領取地點 *", placeholder="例如：生輔組 / 某某系辦櫃檯")
                l_desc = st.text_area("外觀、顏色等特徵備註")
                l_file = st.file_uploader("📸 上傳失物實體照（選填）", type=['png', 'jpg', 'jpeg'])

                if st.form_submit_button("📢 發布全台聯防公告"):
                    if l_name and l_place and l_contact:
                        lost_b64 = ""
                        if l_file is not None:
                            img = Image.open(l_file).convert("RGB")
                            img.thumbnail((300, 300))
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG")
                            lost_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO lost_found (region, university, item_name, place, contact_location, description, finder_id, image_base64) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (l_reg, l_uni, l_name, l_place, l_contact, l_desc, current_student, lost_b64))
                        conn.commit()
                        conn.close()

                        modify_coins(current_student, current_uni, 15)
                        st.balloons()
                        st.success("🎉 聯防公告發布成功！外在顯示已自動套用 O 字個資隱私保護。")
                        time.sleep(1)
                        st.rerun()