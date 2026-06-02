import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time
import re
import streamlit.components.v1 as components

# 設定網頁標題與網頁自動配置
st.set_page_config(page_title="Campus Market | 全國大學生智慧市集", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 UI 樣式配置 (包含仿蝦皮標籤頁與卡片)
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
        box-shadow: 0 4px 12px rgba(6, 199, 85, 0.15);
        transition: all 0.2s ease;
        font-size: 14px;
        margin-top: 5px;
    }
    .emap-btn {
        background: linear-gradient(135deg, #4dabf7 0%, #228be6 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        text-align: center;
        padding: 10px 0;
        display: block;
        width: 100%;
        box-sizing: border-box;
        text-decoration: none;
        font-size: 14px;
        margin-bottom: 15px;
    }
    .stButton>button {
        height: 60px !important;
        font-size: 14px !important;
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
    .gift-grid-card {
        background: #ffffff; 
        border-radius: 16px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); 
        overflow: hidden; 
        border: 1px solid #eef2f5;
        margin-bottom: 25px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .gift-img {
        width: 100%;
        height: 160px;
        object-fit: cover;
    }
    .gift-body {
        padding: 15px;
    }
    .mission-box {
        background: linear-gradient(135deg, #fff4e6 0%, #fff9db 100%);
        border: 1px solid #ffd43b;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    .mission-title {
        font-size: 14px;
        font-weight: bold;
        color: #d9480f;
        margin-bottom: 4px;
    }
    .checkout-box {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dee2e6;
        margin: 15px 0;
    }
    .checkout-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
        font-size: 14px;
        color: #495057;
    }
    .checkout-total {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed #ced4da;
        font-size: 18px;
        font-weight: bold;
        color: #212529;
    }
    @media (max-width: 768px) {
        .product-card { flex-direction: column !important; align-items: flex-start !important; padding: 15px; }
        .prod-img-container { max-width: 100% !important; width: 100% !important; text-align: center; }
        .prod-img-container img { max-height: 180px; object-fit: contain; }
        .prod-info-container { width: 100%; }
        .prod-action-container { width: 100%; text-align: left !important; border-top: 1px dashed #e9ecef; padding-top: 10px; margin-top: 5px; }
        .stButton>button { width: 100% !important; height: 55px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 基礎資料庫與地理常數設定
# ==========================================
DB_NAME = 'streamlit_campus_market_v118_final.db'

CAMPUS_TYPE_MAP = {
    "公立學校": ["國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學", "國立成功大學",
                 "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學", "國立雲林科技大學", "國立臺灣科技大學",
                 "國立臺北科技大學", "國立臺北大學"],
    "私立學校": ["輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學", "靜宜大學", "長庚大學",
                 "元智大學", "銘傳大學", "實踐大學", "世新大學"]
}
CAMPUS_LABELS = list(CAMPUS_TYPE_MAP.keys())

EMAP_URLS = {
    "7-11 統一超商": "https://emap.pcsc.com.tw/",
    "全家便利商店": "https://www.family.com.tw/Marketing/zh/Map",
    "萊爾富 Hi-Life": "https://www.hilife.com.tw/storeInquiry_street.aspx",
    "OK Mart": "https://www.okmart.com.tw/convenient_shopSearch"
}

# 🚀 需求 1：真實超商編號大數據對應字典（輸入編號自動查名稱與地址）
REAL_STORE_CODE_DATABASE = {
    # 7-11真實門市
    "131421": "雲科大門市 (雲林縣斗六市大學路三段123號)",
    "934211": "斗六門市 (雲林縣斗六市民生路200號)",
    "115234": "台大門市 (台北市大安區羅斯福路四段1號)",
    "194821": "新復興門市 (台北市大安區復興南路二段151巷30號)",
    "124115": "政大門市 (台北市文山區指南路二段65號)",
    "231452": "逢甲門市 (台中市西屯區文華路100號)",
    "162534": "成大門市 (台南市東區勝利路119號)",
    "181245": "交大門市 (新竹市東區大學路1001號)",
    # 全家真實門市
    "016542": "全家 雲科店 (雲林縣斗六市大學路三段123-1號)",
    "018442": "全家 台大長興店 (台北市大安區長興街82號)",
    "012445": "全家 政大新光店 (台北市文山區萬壽路11號)",
    "015521": "全家 逢甲大學店 (台中市西屯區逢甲路28號)",
    "019942": "全家 中興大學店 (台中市南區興大路145號)"
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
            buy_count INTEGER DEFAULT 0, report_count INTEGER DEFAULT 0,
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
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO users (student_id, name, password, university, line_id, green_coins, email, buy_count, report_count) VALUES ('A66666666', '王小明', '1234', '國立雲林科技大學', 'yuntech_cool', 500, 'a66666666@yuntech.edu.tw', 3, 1)")
    except:
        pass
    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 狀態管理與輔助安全函式
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "探索二手市集"


def mask_user_name(name_str):
    if not name_str or name_str == '同學': return "同學"
    length = len(name_str)
    if length == 2: return name_str[0] + "O"
    return name_str[0] + "O" + name_str[-1] if length >= 3 else name_str


def get_seller_masked_name(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT name FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return mask_user_name(res[0] if res else "同學")


def get_user_line(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else "未填寫"


def get_user_mission_data(student_id, university):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT green_coins, buy_count, report_count FROM users WHERE student_id = ? AND university = ?",
                       (student_id, university)).fetchone()
    conn.close()
    return res if res else (0, 0, 0)


def modify_coins(student_id, university, amount):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ? AND university = ?",
                 (amount, student_id, university))
    conn.commit()
    conn.close()


def increment_mission_counter(student_id, university, field):
    conn = sqlite3.connect(DB_NAME)
    conn.execute(f"UPDATE users SET {field} = {field} + 1 WHERE student_id = ? AND university = ?",
                 (student_id, university))
    conn.commit()
    conn.close()


# ==========================================
# 3. 登入 / 註冊區
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 Campus Market 全國大學生智慧市集</div>', unsafe_allow_html=True)
    mode = st.radio("請選擇操作項目：", ["🔑 同學登入", "📝 新同學註冊帳號", "❓ 忘記密碼"], horizontal=True)

    if mode == "🔑 同學登入":
        log_type = st.selectbox("請選擇體系類型", CAMPUS_LABELS)
        log_uni = st.selectbox("請選取您的就讀學校", CAMPUS_TYPE_MAP[log_type])
        with st.form("login_form"):
            sid = st.text_input("學號")
            pas = st.text_input("密碼", type="password")
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
                    st.error("❌ 帳密或學校選擇錯誤！")
    elif mode == "📝 新同學註冊帳號":
        reg_name = st.text_input("真實姓名/稱呼 *")
        reg_sid = st.text_input("註冊學號 *")
        reg_email = st.text_input("學校信箱 *")
        reg_type = st.selectbox("學校體系 *", CAMPUS_LABELS)
        reg_uni = st.selectbox("所屬大學 *", CAMPUS_TYPE_MAP[reg_type])
        reg_line = st.text_input("LINE ID *")
        reg_pass = st.text_input("設定系統密碼 *", type="password")
        if st.button("提交註冊"):
            if reg_name and reg_sid and reg_email and reg_pass:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO users (student_id, name, password, university, line_id, green_coins, email, buy_count, report_count) VALUES (?, ?, ?, ?, ?, 100, ?, 0, 0)",
                        (reg_sid, reg_name, reg_pass, reg_uni, reg_line, reg_email))
                    conn.commit()
                    conn.close()
                    st.success("🎉 註冊成功，請切換至登入！")
                except:
                    st.error("學號已被註冊。")
    elif mode == "❓ 忘記密碼":
        st.info("請洽校園網管人員。")

# ==========================================
# 4. 主功能區
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    current_name = st.session_state.user_name

    user_coins, buy_cnt, report_cnt = get_user_mission_data(current_student, current_uni)
    total_actions = buy_cnt + report_cnt

    with st.sidebar:
        st.markdown(f"### 🧑‍🎓 {current_name} ({current_uni})")
        st.metric(label="我的環保集點幣", value=f"{user_coins} 🪙")

        # 🚀 需求 3：精簡版抽獎區（字數精簡優化）
        st.markdown(f"""
        <div class="mission-box">
            <div class="mission-title">🎡 滿 5 次解鎖幸運抽獎</div>
            <span style="font-size:13px; color:#495057;">當前進度：<b>{total_actions} / 5</b> 次</span>
        </div>
        """, unsafe_allow_html=True)

        if total_actions >= 5:
            @st.dialog("🎁 幸運抽獎中獎確認")
            def lucky_draw_dialog():
                st.write("### 🎰 點擊按鈕啟動轉盤")
                if st.button("🌟 開始抽獎", use_container_width=True, type="primary"):
                    with st.spinner("抽獎中..."):
                        time.sleep(1.0)
                    prize_pool = ["50 點綠幣 🪙", "100 點綠幣 🪙", "超商 35元點心折價券 🍰", "免運通關券 🚚"]
                    won_prize = random.choice(prize_pool)
                    st.balloons()
                    st.success(f"🎊 恭喜抽中：【{won_prize}】！")

                    if "綠幣" in won_prize:
                        modify_coins(current_student, current_uni, 50 if "50" in won_prize else 100)
                    else:
                        v_code = f"DRAW-{random.randint(100000, 999999)}"
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, ?, '未使用')",
                            (current_student, f"【抽獎】{won_prize}", v_code, "2026-06-02"))
                        conn.commit()
                        conn.close()

                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "UPDATE users SET buy_count = 0, report_count = 0 WHERE student_id = ? AND university = ?",
                        (current_student, current_uni))
                    conn.commit()
                    conn.close()
                    time.sleep(2.0)
                    st.rerun()


            if st.button("🔥 立即抽獎", type="primary", use_container_width=True): lucky_draw_dialog()

        st.markdown("---")
        st.markdown("### 📊 我的交易與物資清單")

        conn = sqlite3.connect(DB_NAME)
        my_selling = pd.read_sql_query("SELECT id, name, price FROM products WHERE seller_id = ? AND status = '上架中'",
                                       conn, params=(current_student,))
        my_sales = pd.read_sql_query(
            "SELECT name, price, status, final_trade_info FROM products WHERE seller_id = ? AND (status = 'Ref售出' OR status = '已售出')",
            conn, params=(current_student,))
        my_buys = pd.read_sql_query("SELECT name, price, university, final_trade_info FROM products WHERE buyer_id = ?",
                                    conn, params=(current_student,))

        # 🚀 需求 2：仿蝦皮「未核銷」與「已核銷/已使用」分頁顯示
        my_vouchers_active = pd.read_sql_query(
            "SELECT gift_name, code, timestamp FROM vouchers WHERE student_id = ? AND status = '未使用'", conn,
            params=(current_student,))
        my_vouchers_used = pd.read_sql_query(
            "SELECT gift_name, code, timestamp FROM vouchers WHERE student_id = ? AND status = '已使用'", conn,
            params=(current_student,))
        conn.close()

        with st.expander(f"🏪 在售物品 ({len(my_selling)})"):
            for _, r in my_selling.iterrows():
                if st.button(f"🛑 下架 {r['name']} (${r['price']:.0f})", key=f"del_{r['id']}", use_container_width=True):
                    conn = sqlite3.connect(DB_NAME);
                    conn.execute("UPDATE products SET status = '已下架' WHERE id = ?", (r['id'],));
                    conn.commit();
                    conn.close()
                    st.rerun()

        with st.expander(f"🤝 售出紀錄 ({len(my_sales)})"):
            for _, r in my_sales.iterrows():
                st.markdown(f"<div class='record-box'><b>{r['name']}</b><br>{r['final_trade_info']}</div>",
                            unsafe_allow_html=True)

        with st.expander(f"📦 買進紀錄 ({len(my_buys)})"):
            for _, r in my_buys.iterrows():
                st.markdown(
                    f"<div class='record-box' style='background:#eef9ff;'><b>{r['name']}</b><br>{r['final_trade_info']}</div>",
                    unsafe_allow_html=True)

        # 🚀 仿蝦皮禮券分類介面
        with st.expander(f"🎫 我的優惠券明細"):
            shopee_tab1, shopee_tab2 = st.tabs(
                [f"可使用 ({len(my_vouchers_active)})", f"已使用 ({len(my_vouchers_used)})"])

            with shopee_tab1:
                if my_vouchers_active.empty: st.caption("暫無有效優惠券。")
                for _, r in my_vouchers_active.iterrows():
                    st.markdown(f"""
                    <div style="background-color:#fff5f5; border-left: 4px solid #ff6b6b; padding:8px; margin-bottom:5px; border-radius:6px; font-size:12px;">
                        <b>{r['gift_name']}</b><br><span style="color:#e64980; font-family:monospace; font-weight:bold;">序號: {r['code']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with shopee_tab2:
                if my_vouchers_used.empty: st.caption("無已使用或已失效禮券。")
                for _, r in my_vouchers_used.iterrows():
                    st.markdown(f"""
                    <div style="background-color:#f1f3f5; border-left: 4px solid #868e96; padding:8px; margin-bottom:5px; border-radius:6px; font-size:12px; opacity: 0.7;">
                        <del><b>{r['gift_name']}</b></del> <span style="color:#868e96;">[已套用核銷]</span><br>
                        <span style="font-family:monospace; color:#868e96;">序號: {r['code']}</span>
                    </div>
                    """, unsafe_allow_html=True)

        if st.button("🚪 登出市集", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="main-title">🛍 全國大學生智慧市集</div>', unsafe_allow_html=True)
    st.write("---")

    b_cols = st.columns(5)
    menus = ["探索二手市集", "智慧物資上架", "綠幣集點福利", "失物招領中心", "盲盒專區"]
    for idx, m in enumerate(menus):
        with b_cols[idx]:
            if st.button(m, use_container_width=True): st.session_state.current_menu = m

    st.write("---")

    # ------------------------------------------
    # 功能 1: 探索二手市集
    # ------------------------------------------
    if st.session_state.current_menu == "探索二手市集":
        st.subheader("🪐 全國二手物資流通池")
        f1, f2 = st.columns(2)
        with f1:
            search_cat = st.selectbox("📦 物品分類項目", PRODUCT_CATEGORIES)
        with f2:
            search_dept = st.selectbox("🎓 適用科系篩選", ["全部科系"] + YUNTECH_ALL_DEPTS)

        conn = sqlite3.connect(DB_NAME)
        query = "SELECT id, image_base64, name, price, category, university, department, description, shipping_method, shipping_link, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"
        params = []
        if search_cat != "全部類型": query += " AND category = ?"; params.append(search_cat)
        if search_dept != "全部科系": query += " AND department = ?"; params.append(search_dept)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()


        @st.dialog("🔍 商品詳情與下單")
        def show_product_details_dialog(prod_data):
            st.write(f"### {prod_data['name']}")
            if prod_data['image_base64']: st.image(prod_data['image_base64'], use_container_width=True)

            c_a, c_b = st.columns(2)
            with c_a:
                st.write(f"🏫 **學校：** {prod_data['university']}")
                st.write(f"💰 **售價：** ${prod_data['price']:.0f} 元")
            with c_b:
                st.write(f"🚚 **預設：** {prod_data['shipping_method']}")
                st.write(f"👤 **賣家：** {get_seller_masked_name(prod_data['seller_id'])} 同學")

            st.markdown("---")
            buyer_ship_choice = st.selectbox("請選擇配送管道",
                                             ["四大超商取貨", "使用賣家提供的 賣貨便/好賣+ 網址", "預約校園面交"])
            input_voucher_code = st.text_input("🎫 優惠券 / 免運通關券序號（選填）", placeholder="例如：DRAW-XXXXXX")

            base_shipping_fee = 60 if buyer_ship_choice == "四大超商取貨" else 0
            is_free_shipping = False
            voucher_name_applied = ""
            voucher_db_id = None

            if input_voucher_code.strip():
                conn = sqlite3.connect(DB_NAME)
                check_v = conn.execute(
                    "SELECT id, gift_name FROM vouchers WHERE student_id = ? AND code = ? AND status = '未使用'",
                    (current_student, input_voucher_code.strip())).fetchone()
                conn.close()
                if check_v:
                    voucher_db_id = check_v[0]
                    voucher_name_applied = check_v[1]
                    if "免運" in voucher_name_applied: is_free_shipping = True

            final_shipping_fee = 0 if is_free_shipping else base_shipping_fee
            total_cost = prod_data['price'] + final_shipping_fee

            st.markdown("#### 💵 結帳金額明細")
            voucher_discount_text = f"<span style='color:#e64980;'>-${base_shipping_fee} (已套用免運券)</span>" if is_free_shipping else f"${base_shipping_fee} 元"
            st.markdown(f"""
            <div class="checkout-box">
                <div class="checkout-row"><span>商品金額</span><span>${prod_data['price']:.0f} 元</span></div>
                <div class="checkout-row"><span>物流運費</span><span>{voucher_discount_text}</span></div>
                <div class="checkout-total"><span>總金額</span><span style="color:#06C755;">${total_cost:.0f} 元</span></div>
            </div>
            """, unsafe_allow_html=True)

            final_memo_output = ""
            form_valid = False

            if buyer_ship_choice == "使用賣家提供的 賣貨便/好賣+ 網址":
                if prod_data['shipping_link'] and prod_data['shipping_link'].strip():
                    st.markdown(f'<a href="{prod_data["shipping_link"]}" target="_blank">👉 點我打開外部賣場下單</a>',
                                unsafe_allow_html=True)
                    final_memo_output = f"[外部連結] {prod_data['shipping_link']}"
                    form_valid = True
                else:
                    st.warning("⚠️ 賣家未附連結，請點下方按鈕用 LINE 聯繫。")
                    final_memo_output = "[外部連結] 待敲定"
                    form_valid = True

            elif buyer_ship_choice == "四大超商取貨":
                st.markdown("### 📍 超商門市編號智慧查詢系統")
                chain_choice = st.selectbox("選擇超商體系", list(EMAP_URLS.keys()))
                st.markdown(
                    f'<a href="{EMAP_URLS[chain_choice]}" target="_blank" class="emap-btn">🌐 開啟官方【{chain_choice}】電子地圖查詢</a>',
                    unsafe_allow_html=True)

                # 🚀 需求 1：輸入店號秒查店名中文功能核心
                raw_store_input = st.text_input("📋 請輸入 5~6 位數「超商門市編號」",
                                                placeholder="請隨意輸入測試：115234（台大）、016542（雲科）、231452（逢甲）")

                user_store_final = ""
                if raw_store_input.strip():
                    clean_input = raw_store_input.strip()
                    code_match = re.search(r'\d{5,6}', clean_input)

                    if code_match:
                        input_code = code_match.group()

                        # 比對真實超商大數據
                        if input_code in REAL_STORE_CODE_DATABASE:
                            matched_details = REAL_STORE_CODE_DATABASE[input_code]
                            user_store_final = f"[{chain_choice}] {matched_details} [店號: {input_code}]"

                            st.markdown(f"""
                            <div style="background-color: #ebfbee; border-left: 5px solid #40c057; padding: 10px; border-radius: 8px; margin: 8px 0;">
                                <span style="color: #2b8a3e; font-weight: bold;">🎯 智慧店號識別成功：</span><br>
                                <span style="color: #2b8a3e; font-size: 13px;">{user_store_final}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            form_valid = True
                        else:
                            # 字典內沒有時，仍保留彈性給使用者自填
                            name_match = re.sub(r'\d+', '', clean_input).replace("門市", "").strip()
                            store_title = name_match if name_match else "自填門市"
                            user_store_final = f"[{chain_choice}] {store_title} (店號: {input_code})"
                            st.info(f"📋 已辨識店號為 `{input_code}`，請確保配送資訊無誤。")
                            form_valid = True
                    elif len(clean_input) >= 2:
                        user_store_final = f"[{chain_choice}] {clean_input}門市 (店號: 未輸入)"
                        st.warning("⚠️ 建議填入數字店號，物流配送會更精確喔！")
                        form_valid = True

                b_name = st.text_input("收件人真實姓名")
                b_phone = st.text_input("收件人手機號碼")
                if user_store_final and b_name and b_phone and form_valid:
                    final_memo_output = f"{user_store_final} (收件人:{b_name}, 電話:{b_phone})"
                else:
                    form_valid = False

            elif buyer_ship_choice == "預約校園面交":
                meet_memo = st.text_input("面交時間地點")
                if meet_memo:
                    final_memo_output = f"[面交] {meet_memo}"
                    form_valid = True

            s_line = get_user_line(prod_data['seller_id'])
            st.markdown(
                f'<a href="https://line.me/ti/p/~{s_line}" target="_blank" class="line-btn">💬 私訊賣家 LINE</a>',
                unsafe_allow_html=True)

            if form_valid:
                if st.button("🚀 確定送出訂單", use_container_width=True, type="primary"):
                    if prod_data['seller_id'] == current_student:
                        st.error("不能買自己的物品！")
                    else:
                        if voucher_db_id is not None:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("UPDATE vouchers SET status = '已使用' WHERE id = ?", (voucher_db_id,))
                            conn.commit();
                            conn.close()
                            final_memo_output += f" (已扣除禮券：{voucher_name_applied})"

                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "UPDATE products SET status = '已售出', buyer_id = ?, final_trade_info = ? WHERE id = ?",
                            (current_student, final_memo_output, prod_data['id']))
                        conn.commit();
                        conn.close()
                        increment_mission_counter(current_student, current_uni, "buy_count")
                        st.success("🎉 下單成功！已計入您的抽獎進度。")
                        time.sleep(1.0);
                        st.rerun()
            else:
                st.button("🔒 請完整填寫物流資訊以解鎖按鈕", use_container_width=True, disabled=True)


        if df.empty:
            st.info("💡 目前市集尚無寶物在售。")
        else:
            for index, row in df.iterrows():
                img_html = f"<img src='{row['image_base64']}' style='width:100%; border-radius:12px; height:130px; object-fit:cover;' />" if \
                row[
                    'image_base64'] else "<div style='background-color:#f1f3f5;height:120px;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#adb5bd;font-size:13px;'>📦 暫無商品照</div>"
                st.markdown(f"""
                <div class="product-card">
                    <div class="prod-img-container">{img_html}</div>
                    <div class="prod-info-container">
                        <h4 style="margin:0 0 4px 0;">{row['name']}</h4>
                        <p style="margin:2px 0; font-size:12px; color:#6c757d;">🏫 學校：{row['university']} | 👤 賣家：{get_seller_masked_name(row['seller_id'])} 同學</p>
                    </div>
                    <div class="prod-action-container"><div class="price-tag">${row['price']:.0f}</div></div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔍 查看並下單（品名：{row['name']}）", key=f"view_{row['id']}",
                             use_container_width=True): show_product_details_dialog(row)

    # ------------------------------------------
    # 功能 2: 智慧物資上架
    # ------------------------------------------
    elif st.session_state.current_menu == "智慧物資上架":
        st.subheader("🏪 多元物資快速上架")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱")
            p_price = st.number_input("欲售金額", min_value=0, value=100)
            p_shipping = st.selectbox("🚚 運送形式", ["校園面交", "7-11 賣貨便", "全家好賣+"])
            p_link = st.text_input("🔗 第三方賣場網址（選填）")
            p_desc = st.text_area("物況說明")
            p_file = st.file_uploader("📸 實體商品照", type=['png', 'jpg', 'jpeg'])
            if st.form_submit_button("🚀 發布至校園市集"):
                if p_name and p_desc:
                    b64_str = ""
                    if p_file:
                        img = Image.open(p_file).convert("RGB");
                        img.thumbnail((300, 300));
                        buffered = io.BytesIO();
                        img.save(buffered, format="JPEG")
                        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        'INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, seller_id, image_base64) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (p_name, p_price, "生活雜物", current_uni, "不限科系/共同通識核心", p_desc, p_shipping, p_link,
                         current_student, b64_str))
                    conn.commit();
                    conn.close()
                    modify_coins(current_student, current_uni, 10)
                    st.success("🎉 上架成功！已獲得 10 點綠色低碳積幣。")
                    time.sleep(0.5);
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利
    # ------------------------------------------
    elif st.session_state.current_menu == "綠幣集點福利":
        st.subheader("🪙 綠幣集點福利社")
        gifts = [
            {"name": "全家 77乳加巧克力 🍫", "cost": 30,
             "img": "https://images.unsplash.com/photo-1548907040-4baa42d10919?w=400&q=80"},
            {"name": "免運通關券 🚚", "cost": 40,
             "img": "https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=400&q=80"}
        ]
        cols = st.columns(2)
        for idx, g in enumerate(gifts):
            with cols[idx % 2]:
                st.markdown(
                    f'<div class="gift-grid-card"><img class="gift-img" src="{g["img"]}"><div class="gift-body"><h5>{g["name"]}</h5><p>🪙 {g["cost"]} 綠幣</p></div></div>',
                    unsafe_allow_html=True)
                if st.button("馬上兌換", key=f"g_{idx}", use_container_width=True):
                    if user_coins >= g['cost']:
                        modify_coins(current_student, current_uni, -g['cost'])
                        v_code = f"CM-{random.randint(100000, 999999)}"
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, ?, '未使用')",
                            (current_student, g['name'], v_code, "2026-06-02"))
                        conn.commit();
                        conn.close()
                        st.balloons();
                        st.success("🎉 兌換成功！已收納至左側折價券。");
                        time.sleep(0.5);
                        st.rerun()
                    else:
                        st.error("❌ 餘額不足。")

    # ------------------------------------------
    # 功能 4: 失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "失物招領中心":
        st.subheader("📍 大學生失物招領中心")
        t1, t2 = st.tabs(["🔍 招領佈告欄", "➕ 發布失物通報"])
        with t1:
            conn = sqlite3.connect(DB_NAME);
            df_local = pd.read_sql_query(
                "SELECT id, item_name, place, contact_location, finder_id FROM lost_found WHERE status='招領中' AND university=?",
                conn, params=(current_uni,));
            conn.close()
            if df_local.empty: st.info("💡 目前校內暫無失物公告。")
            for idx, row in df_local.iterrows():
                st.markdown(
                    f'<div class="lost-card"><h5>🔍 {row["item_name"]}</h5><p>📍 地點：{row["place"]}</p><p>🏢 領取處：{row["contact_location"]}</p></div>',
                    unsafe_allow_html=True)
                if st.button("✨ 順利領回 (撤除)", key=f"res_l_{row['id']}", use_container_width=True):
                    conn = sqlite3.connect(DB_NAME);
                    conn.execute("UPDATE lost_found SET status='已認領' WHERE id=?", (row['id'],));
                    conn.commit();
                    conn.close();
                    st.rerun()
        with t2:
            with st.form("lost_form", clear_on_submit=True):
                l_name = st.text_input("拾獲物名稱")
                l_place = st.text_input("拾獲地點")
                l_contact = st.text_input("暫存保管位置")
                if st.form_submit_button("📢 廣播發布"):
                    if l_name and l_place and l_contact:
                        conn = sqlite3.connect(DB_NAME);
                        conn.execute(
                            "INSERT INTO lost_found (region, university, item_name, place, contact_location, description, finder_id, image_base64) VALUES ('台灣', ?,?,?,?,?,?,?)",
                            (current_uni, l_name, l_place, l_contact, "", current_student, ""));
                        conn.commit();
                        conn.close()
                        increment_mission_counter(current_student, current_uni, "report_count")
                        st.success("🎉 回報完成！");
                        time.sleep(0.5);
                        st.rerun()

    # ------------------------------------------
    # 功能 5: 盲盒專區
    # ------------------------------------------
    elif st.session_state.current_menu == "盲盒專區":
        blind_box_html = """
        <html><body style="background:#f8f9fa; display:flex; justify-content:center; align-items:center;"><div style="background:#111; color:#fff; padding:40px; border-radius:20px; text-align:center; width:300px;"><h3>CAMPUS BLIND BOX</h3><h1 style="margin:20px 0; font-size:60px;">?</h1><button onclick="alert('✨ 恭喜抽中驚喜福袋！')" style="padding:10px 20px; background:#fff; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">購買盲盒 ($150)</button></div></body></html>
        """
        components.html(blind_box_html, height=350)