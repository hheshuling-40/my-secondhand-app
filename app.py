import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time
import re  # 導入正則表達式，用於超商與有效期限格式防錯
import streamlit.components.v1 as components

# 設定網頁標題與網頁自動配置
st.set_page_config(page_title="Campus Market | 全國大學生智慧市集", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 RWD 響應式視覺優化 UI (含抽獎與結帳面板)
# ==========================================
st.markdown("""<style>
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
        background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        text-align: center;
        padding: 12px 0;
        display: block;
        width: 100%;
        box-sizing: border-box;
        text-decoration: none;
        font-size: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(255, 102, 0, 0.2);
        transition: transform 0.2s;
    }
    .emap-btn:hover {
        transform: scale(1.02);
        color: #ffffff !important;
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
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    .mission-title {
        font-size: 14px;
        font-weight: bold;
        color: #d9480f;
        margin-bottom: 6px;
    }
    /* 費用結帳明細面板 */
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
        .product-card {
            flex-direction: column !important;
            align-items: flex-start !important;
            padding: 15px;
        }
        .prod-img-container {
            max-width: 100% !important;
            width: 100% !important;
            text-align: center;
        }
        .prod-img-container img {
            max-height: 180px;
            object-fit: contain;
        }
        .prod-info-container {
            width: 100%;
        }
        .prod-action-container {
            width: 100%;
            text-align: left !important;
            border-top: 1px dashed #e9ecef;
            padding-top: 10px;
            margin-top: 5px;
        }
        .stButton>button {
            width: 100% !important;
            height: 55px !important;
        }
    }
</style>""", unsafe_allow_html=True)

# ==========================================
# 0. 地理大數據與基礎設定
# ==========================================
DB_NAME = 'streamlit_campus_market_v116_perfect_taiwan_fixed.db'
CAMPUS_TYPE_MAP = {
    "公立學校": [
        "國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學",
        "國立成功大學", "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學",
        "國立雲林科技大學", "國立臺灣科技大學", "國立臺北科技大學", "國立臺北大學"
    ],
    "私立學校": [
        "輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學",
        "靜宜大學", "長庚大學", "元智大學", "銘傳大學", "實踐大學", "世新大學"
    ]
}
CAMPUS_LABELS = list(CAMPUS_TYPE_MAP.keys())

# 100% 真實的四大超商地圖入口
EMAP_URLS = {
    "7-11 統一超商": "https://emap.pcsc.com.tw/",
    "全家便利商店": "https://www.family.com.tw/Marketing/zh/Map",
    "萊爾富 Hi-Life": "https://www.hilife.com.tw/storeInquiry_street.aspx",
    "OK Mart": "https://www.okmart.com.tw/convenient_shopSearch"
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

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN buy_count INTEGER DEFAULT 0")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN report_count INTEGER DEFAULT 0")
    except:
        pass

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
        cursor.execute("""
            INSERT OR IGNORE INTO users (student_id, name, password, university, line_id, green_coins, email, buy_count, report_count) 
            VALUES ('A66666666', '王小明', '1234', '國立雲林科技大學', 'yuntech_cool', 500, 'a66666666@yuntech.edu.tw', 3, 1)
        """)
    except:
        pass

    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 狀態管理與安全核心
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "探索二手市集"

# 💳 建立信用卡有效期限專用的動態監聽快取狀態
if 'expiry_input' not in st.session_state: st.session_state.expiry_input = ""


def mask_user_name(name_str):
    if not name_str or name_str == '同學': return "同學"
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
        reg_name = st.text_input("您的真實姓名/稱呼 *")
        reg_sid = st.text_input("註冊學號 *")
        reg_email = st.text_input("學校聯絡電子郵件 *")
        reg_type = st.selectbox("學校體系類型 *", CAMPUS_LABELS)
        reg_uni = st.selectbox("所屬大學 *", CAMPUS_TYPE_MAP[reg_type])
        reg_line = st.text_input("LINE ID *")
        reg_pass = st.text_input("設定系統密碼 *", type="password")

        if st.button("提交註冊並領取 100 幣 🪙"):
            if not reg_name or not reg_sid or not reg_email or not reg_pass:
                st.error("請完整填寫所有必填欄位！")
            else:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO users (student_id, name, password, university, line_id, green_coins, email, buy_count, report_count) VALUES (?, ?, ?, ?, ?, 100, ?, 0, 0)",
                        (reg_sid, reg_name, reg_pass, reg_uni, reg_line, reg_email))
                    conn.commit()
                    conn.close()
                    st.success("🎉 註冊成功！快切換到「同學登入」吧！")
                except:
                    st.error("在該校中此學號已被註冊過。")

    elif mode == "❓ 忘記密碼":
        st.info("忘記密碼功能請洽各校系統管理員。")

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
        st.markdown("### 🧑‍🎓 攤主名片")
        st.markdown(f"歡迎回來，**{current_name}** 同學！👋")
        st.write(f"學校｜**{current_uni}**")
        st.write(f"學號｜**{current_student}**")
        st.metric(label="我的環保集點幣", value=f"{user_coins} 🪙")

        st.markdown('---')
        st.markdown("<small style='color: #7048e8; font-weight: bold;'>🛠️ 測試快捷速推面板</small>",
                    unsafe_allow_html=True)
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("模擬購買 +1", key="test_buy_btn", use_container_width=True):
                increment_mission_counter(current_student, current_uni, "buy_count")
                st.rerun()
        with col_t2:
            if st.button("模擬通報 +1", key="test_rep_btn", use_container_width=True):
                increment_mission_counter(current_student, current_uni, "report_count")
                st.rerun()

        st.markdown('---')
        st.markdown(f"""
        <div class="mission-box">
            <div class="mission-title">🎁 活躍校園滿額抽獎</div>
            <span style="font-size:12px; color:#5c5f62;">已買二手物：<b>{buy_cnt} 次</b></span><br>
            <span style="font-size:12px; color:#5c5f62;">已回報失物：<b>{report_cnt} 次</b></span><br>
            <div style="margin-top:8px; font-size:13px; font-weight:bold; color:#e8590c;">
                總計次數：{total_actions} 次 (滿 5 次即可抽獎)
            </div>
        </div>
        """, unsafe_allow_html=True)

        if total_actions >= 5:
            st.warning(f"🎉 恭喜！您已符合解鎖抽獎條件！(目前可抽 {total_actions // 5} 次)")


            @st.dialog("🎁 滿5次社群貢獻：校園幸運大抽獎")
            def lucky_draw_dialog():
                st.markdown("### 🎡 恭喜觸發限時福利抽獎")
                st.write("系統檢測到您在 Campus Market 累計交易與招領通報已達標！點擊下方按鈕啟動轉盤：")

                if st.button("🎰 開始抽獎", use_container_width=True, type="primary"):
                    with st.spinner("轉盤瘋狂旋轉中...🌀"):
                        time.sleep(1.5)

                    prize_pool = [
                        "50 點綠幣 🪙", "100 點綠幣 🪙", "全家 35元微波點心折價券 🍰",
                        "學辦特調冰美式咖啡 ☕", "期末歐趴糖一包 🍬", "免運通關券 🚚"
                    ]
                    won_prize = random.choice(prize_pool)
                    st.balloons()
                    st.success(f"🎊 恭喜抽中：【{won_prize}】！")

                    if "50 點綠幣" in won_prize:
                        modify_coins(current_student, current_uni, 50)
                    elif "100 點綠幣" in won_prize:
                        modify_coins(current_student, current_uni, 100)
                    else:
                        v_code = f"DRAW-{random.randint(100000, 999999)}"
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, ?, '未使用')",
                            (current_student, f"【抽獎贏得】{won_prize}", v_code, "2026-06-02"))
                        conn.commit()
                        conn.close()
                    st.info("💡 實體獎勵換領序號已同步保存至下方的福利商品清單中。")

                    conn = sqlite3.connect(DB_NAME)
                    rem_to_deduct = 5
                    if buy_cnt >= rem_to_deduct:
                        conn.execute(
                            "UPDATE users SET buy_count = buy_count - 5 WHERE student_id = ? AND university = ?",
                            (current_student, current_uni))
                    else:
                        rem_to_deduct -= buy_cnt
                        conn.execute(
                            "UPDATE users SET buy_count = 0, report_count = report_count - ? WHERE student_id = ? AND university = ?",
                            (rem_to_deduct, current_student, current_uni))
                    conn.commit()
                    conn.close()
                    time.sleep(3.0)
                    st.rerun()


            if st.button("🔥 點我立刻抽獎", type="primary", use_container_width=True):
                lucky_draw_dialog()

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
        my_vouchers = pd.read_sql_query("SELECT gift_name, code, timestamp, status FROM vouchers WHERE student_id = ?",
                                        conn, params=(current_student,))
        conn.close()

        with st.expander(f"🏪 我正在賣的商品 ({len(my_selling)})"):
            if my_selling.empty:
                st.caption("目前沒有在售物品。")
            else:
                for _, r in my_selling.iterrows():
                    col_pname, col_pbtn = st.columns([2, 1])
                    with col_pname:
                        st.markdown(f"**{r['name']}**<br><small style='color:green;'>售價: ${r['price']:.0f}</small>",
                                    unsafe_allow_html=True)
                    with col_pbtn:
                        if st.button("🛑 下架", key=f"del_{r['id']}", use_container_width=True, type="secondary"):
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("UPDATE products SET status = '已下架' WHERE id = ?", (r['id'],))
                            conn.commit()
                            conn.close()
                            st.toast(f"✅ 「{r['name']}」已成功移除！")
                            time.sleep(0.5)
                            st.rerun()

        with st.expander(f"🤝 我已售出的商品 ({len(my_sales)})"):
            if my_sales.empty:
                st.caption("目前尚無售出物資紀錄。")
            else:
                for _, r in my_sales.iterrows():
                    st.markdown(f"""
                    <div class="record-box">
                        <b>{r['name']}</b> <span style="color:green;">[{r['status']}]</span><br>
                        金額：${r['price']:.0f}<br>
                        🤝 交易與寄送資料：{r['final_trade_info']}
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander(f"📦 我買進的商品 ({len(my_buys)})"):
            if my_buys.empty:
                st.caption("目前尚無購買物資紀錄。")
            else:
                for _, r in my_buys.iterrows():
                    st.markdown(f"""
                    <div class="record-box" style="background-color:#eef9ff;">
                        <b>{r['name']}</b><br>
                        金額：${r['price']:.0f} | 來源：{r['university']}<br>
                        🤝 配送方式：{r['final_trade_info']}
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander(f"🎁 我兌換的福利商品 ({len(my_vouchers)})"):
            if my_vouchers.empty:
                st.caption("目前尚無點心兌換紀錄。")
            else:
                for _, r in my_vouchers.iterrows():
                    color_status = "#868e96" if r['status'] == "已使用" else "#e64980"
                    st.markdown(f"""
                    <div class="record-box" style="background-color:#fff5f5; border-left: 3px solid #ff6b6b;">
                        <b>{r['gift_name']}</b> <small>[{r['status']}]</small><br>
                        <span style="color:{color_status}; font-family:monospace; font-weight:bold; font-size:14px;">序號：{r['code']}</span><br>
                        <small style="color:#868e96;">時間：{r['timestamp']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 登出市集", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="main-title">🛍 全國大學生智慧市集</div>', unsafe_allow_html=True)
    st.write("---")

    row1_c1, row1_c2, row1_c3, row1_c4, row1_c5 = st.columns([1, 1, 1, 1, 1])
    with row1_c1:
        if st.button("探索二手市集", use_container_width=True): st.session_state.current_menu = "探索二手市集"
    with row1_c2:
        if st.button("智慧物資上架", use_container_width=True): st.session_state.current_menu = "智慧物資上架"
    with row1_c3:
        if st.button("綠幣集點福利", use_container_width=True): st.session_state.current_menu = "綠幣集點福利"
    with row1_c4:
        if st.button("失物招領中心", use_container_width=True): st.session_state.current_menu = "失物招領中心"
    with row1_c5:
        if st.button("🎁 盲盒專區", use_container_width=True): st.session_state.current_menu = "盲盒專區"

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
        if search_cat != "全部類型":
            query += " AND category = ?"
            params.append(search_cat)
        if search_dept != "全部科系":
            query += " AND department = ?"
            params.append(search_dept)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()


        @st.dialog("🔍 商品詳情與下單")
        def show_product_details_dialog(prod_data):
            st.write(f"### {prod_data['name']}")
            if prod_data['image_base64']:
                st.image(prod_data['image_base64'], use_container_width=True)

            c_a, c_b = st.columns(2)
            with c_a:
                st.write(f"🏫 **出物校園：** {prod_data['university']}")
                st.write(f"💰 **物資售價：** ${prod_data['price']:.0f} 元")
            with c_b:
                st.write(f"🚚 **原定寄送：** {prod_data['shipping_method']}")
                st.write(f"👤 **認證賣家：** {get_seller_masked_name(prod_data['seller_id'])} 同學")

            st.info(f"💡 **商品描述：**\n{prod_data['description']}")
            st.markdown("---")

            buyer_ship_choice = st.selectbox("請選擇配送管道",
                                             ["四大超商取貨", "使用賣家提供的 賣貨便/好賣+ 網址", "預約校園面交"])

            # 🎫 序號輸入欄位
            input_voucher_code = st.text_input("🎫 優惠券 / 免運通關券序號（選填）", placeholder="例如：DRAW-XXXXXX")

            # ==================================================
            # 💳 智慧型金流：卡片有效期限自動加「/」核心邏輯
            # ==================================================
            st.markdown("#### 💳 擔保支付信用卡資訊")
            col_card1, col_card2 = st.columns([2, 1])
            with col_card1:
                st.text_input("卡片號碼", placeholder="XXXX XXXX XXXX XXXX", max_chars=19)

            with col_card2:
                # 讀取快取中的輸入內容
                raw_expiry = st.text_input(
                    "有效期限 (MM/YY) *",
                    value=st.session_state.expiry_input,
                    placeholder="MM/YY",
                    max_chars=5,
                    key="expiry_widget"
                )

                # 核心防錯：過濾掉非數字的字元
                digits_only = re.sub(r'\D', '', raw_expiry)

                # 關鍵邏輯：當輸入滿兩個數字，且目前快取還沒有斜線時，自動組裝加上 "/"
                if len(digits_only) >= 2:
                    formatted_expiry = f"{digits_only[:2]}/{digits_only[2:4]}"
                else:
                    formatted_expiry = digits_only

                # 如果格式化後的結果與目前組件的值不同，立刻同步更新快取並重整畫面
                if formatted_expiry != raw_expiry:
                    st.session_state.expiry_input = formatted_expiry
                    st.rerun()

                # 驗證格式長度是否合規 (例如 12/28 長度必須等於 5)
                is_expiry_valid = len(formatted_expiry) == 5
                if formatted_expiry and not is_expiry_valid:
                    st.caption("<small style='color:red;'>格式需為 4 位數字，如 12/28</small>", unsafe_allow_html=True)

            # 💡 基礎運費計算
            base_shipping_fee = 60
            if buyer_ship_choice == "預約校園面交" or buyer_ship_choice == "使用賣家提供的 賣貨便/好賣+ 網址":
                base_shipping_fee = 0

            # 驗證輸入的序號是否能免運
            is_free_shipping = False
            voucher_name_applied = ""
            voucher_db_id = None

            if input_voucher_code.strip() != "":
                conn = sqlite3.connect(DB_NAME)
                check_v = conn.execute(
                    "SELECT id, gift_name FROM vouchers WHERE student_id = ? AND code = ? AND status = '未使用'",
                    (current_student, input_voucher_code.strip())).fetchone()
                conn.close()
                if check_v:
                    voucher_db_id = check_v[0]
                    voucher_name_applied = check_v[1]
                    if "免運" in voucher_name_applied:
                        is_free_shipping = True

            final_shipping_fee = 0 if is_free_shipping else base_shipping_fee
            total_cost = prod_data['price'] + final_shipping_fee

            # 💡 費用明細面板給買家確認
            st.markdown("#### 💵 結帳金額明細確認")
            if buyer_ship_choice == "使用賣家提供的 賣貨便/好賣+ 網址":
                st.markdown(f"""
                <div class="checkout-box">
                    <div class="checkout-row"><span>商品本體金額</span><span>${prod_data['price']:.0f} 元</span></div>
                    <div class="checkout-row"><span>物流寄送費用</span><span style="color:#868e96;">以賣家外部連結為準</span></div>
                    <div class="checkout-total"><span>預計應付總額</span><span>${prod_data['price']:.0f} 元 + 運費</span></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                voucher_discount_text = f"<span style='color:#e64980;'>-${base_shipping_fee} (已套用 {voucher_name_applied})</span>" if is_free_shipping else f"${base_shipping_fee} 元"
                st.markdown(f"""
                <div class="checkout-box">
                    <div class="checkout-row"><span>商品本體金額</span><span>${prod_data['price']:.0f} 元</span></div>
                    <div class="checkout-row"><span>物流寄送費用</span><span>{voucher_discount_text}</span></div>
                    <div class="checkout-total"><span>最終應付總額</span><span style="color:#06C755;">${total_cost:.0f} 元</span></div>
                </div>
                """, unsafe_allow_html=True)

            final_memo_output = ""
            form_valid = False  # 用於物流熔斷器

            # 填寫對應的物流表單資料
            if buyer_ship_choice == "使用賣家提供的 賣貨便/好賣+ 網址":
                if prod_data['shipping_link'] and prod_data['shipping_link'].strip() != "":
                    st.markdown(f"""
                    <div style="background:#eef9ff; padding:12px; border-radius:8px; border-left:4px solid #007bff; margin-bottom:10px;">
                        <a href="{prod_data['shipping_link']}" target="_blank" style="font-weight:bold; color:#007bff; text-decoration:underline;">👉 點我打開賣家外部賣場下單</a>
                    </div>
                    """, unsafe_allow_html=True)
                    final_memo_output = f"[賣貨便/好賣+] 買家已導向連結：{prod_data['shipping_link']}"
                    form_valid = True
                else:
                    st.warning("⚠️ 賣家上架時未附連結，請透過下方 LINE 聯繫賣家開單。")
                    final_memo_output = "[賣貨便/好賣+] 待聯絡開單"
                    form_valid = True

            elif buyer_ship_choice == "四大超商取貨":
                st.markdown("### 📍 100% 真實超商數據查詢與對接")
                st.caption("為避免舊資料與關店錯誤，請切換至要寄送的超商，開啟官方地圖複製店名/店號貼回。")

                # 選擇超商體系
                chain_choice = st.selectbox("選擇欲寄送的超商系統", list(EMAP_URLS.keys()))
                target_url = EMAP_URLS[chain_choice]

                # 炫酷的電子地圖彈出按鈕
                st.markdown(
                    f'<a href="{target_url}" target="_blank" class="emap-btn">🌐 點我開啟官方【{chain_choice}】真實地圖查店號</a>',
                    unsafe_allow_html=True)

                # 輸入真實超商欄位
                raw_store_input = st.text_input("📋 貼上或輸入官方查詢到的門市名稱或店號",
                                                placeholder="例如：台大門市 或 115234")
                user_store_final = ""

                # AI 物流大師防錯格式過濾器
                if raw_store_input.strip():
                    clean_input = raw_store_input.strip()
                    store_code_match = re.search(r'\d{5,6}', clean_input)
                    store_name_match = re.sub(r'\d+', '', clean_input).replace("門市", "").replace("()", "").replace(
                        "（）", "").strip()

                    if store_code_match and len(store_name_match) >= 2:
                        user_store_final = f"[{chain_choice}] {store_name_match}門市 (店號: {store_code_match.group()})"
                        st.success(f"⚡ **AI 真實物流防錯校正成功：** `{user_store_final}`")
                        form_valid = True
                    elif store_code_match:
                        user_store_final = f"[{chain_choice}] 未知門市 (店號: {store_code_match.group()})"
                        st.warning(
                            f"⚠️ 已偵測到真實店號 `{store_code_match.group()}`，建議連同「門市名稱」一起打更安全喔！")
                        form_valid = True
                    elif len(clean_input) >= 2:
                        user_store_final = f"[{chain_choice}] {clean_input}門市 (店號: 待補)"
                        st.warning(f"⚠️ 已收到門市名稱 `{clean_input}`，但缺少 5~6 位數字店號，可能導致賣家寄件時混淆。")
                        form_valid = True
                    else:
                        st.error("❌ 格式不夠完整！請至少輸入真實門市名稱或 5~6 位數店號。")

                final_memo_output = user_store_final

            elif buyer_ship_choice == "預約校園面交":
                meet_place = st.text_input("📍 請輸入預約面交的地點", placeholder="例如：工程一館正門口、學餐全家前")
                meet_time = st.text_input("⏰ 請輸入期望的面交時間區段", placeholder="例如：每週二三中午12:00-13:00")
                if meet_place.strip() and meet_time.strip():
                    final_memo_output = f"[校園面交] 地點: {meet_place.strip()} | 時間: {meet_time.strip()}"
                    form_valid = True
                else:
                    st.caption("ℹ️ 請完整輸入期望的面交地點與時間以解鎖下單。")

            st.write("---")

            # 🚀 熔斷阻擋機制：除了超商物流必須合法外，有效期限也必須完整輸入（長度=5），才會啟用下單按鈕
            button_disabled = not (form_valid and is_expiry_valid)

            if st.button("🛒 確認付費並送出訂單", use_container_width=True, type="primary", disabled=button_disabled):
                conn = sqlite3.connect(DB_NAME)
                if voucher_db_id:
                    conn.execute("UPDATE vouchers SET status = '已使用' WHERE id = ?", (voucher_db_id,))

                conn.execute("UPDATE products SET status = '已售出', buyer_id = ?, final_trade_info = ? WHERE id = ?",
                             (current_student, final_memo_output, prod_data['id']))
                conn.commit()
                conn.close()

                # 計入活躍社群進度
                increment_mission_counter(current_student, current_uni, "buy_count")

                st.success("🎉 下單成功！系統已安全儲存此筆訂單！此善舉已計入活躍滿額抽獎進度。")

                # 重設有效期限快取狀態
                st.session_state.expiry_input = ""
                time.sleep(1.0)
                st.rerun()


        if df.empty:
            st.info("💡 目前在此篩選條件下尚無上架二手物品，歡迎切換其他分類或率先上架！")
        else:
            for _, row in df.iterrows():
                st.markdown(f"""
                <div class="product-card">
                    <div class="prod-img-container">
                        <img src="{row['image_base64'] if row['image_base64'] else 'https://via.placeholder.com/150'}" style="width:100%; border-radius:10px; max-height:130px; object-fit:cover;">
                    </div>
                    <div class="prod-info-container">
                        <span style="background:#eef9ff; color:#007bff; font-size:11px; font-weight:bold; padding:3px 8px; border-radius:20px;">{row['category']}</span>
                        <span style="background:#fff4e6; color:#d9480f; font-size:11px; font-weight:bold; padding:3px 8px; border-radius:20px; margin-left:5px;">{row['university']}</span>
                        <h4 style="margin:8px 0 4px 0; color:#212529;">{row['name']}</h4>
                        <p style="font-size:13px; color:#868e96; margin:0; line-height:1.4;">適用：{row['department']}<br>簡介：{row['description']}</p>
                    </div>
                    <div class="prod-action-container">
                        <div class="price-tag">${row['price']:.0f}</div>
                        <small style="color:#868e96; display:block; margin-bottom:8px;">原定管道: {row['shipping_method']}</small>
                """, unsafe_allow_html=True)

                if st.button("🔍 查看與購買", key=f"view_{row['id']}", use_container_width=True):
                    show_product_details_dialog(row)

                seller_line = get_user_line(row['seller_id'])
                if seller_line and seller_line != "未填寫":
                    st.markdown(
                        f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 聯絡賣家 LINE</a>',
                        unsafe_allow_html=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 2: 智慧物資上架
    # ------------------------------------------
    elif st.session_state.current_menu == "智慧物資上架":
        st.subheader("📤 快速發布校園物資")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱 *", placeholder="請填寫清晰的商品名稱，例如：微積分課本(修訂版)")
            p_price = st.number_input("期望售價 (元) *", min_value=0, max_value=999999, value=50, step=10)
            p_cat = st.selectbox("物品大類項目 *", PRODUCT_CATEGORIES[1:])
            p_dept = st.selectbox("最適用推薦科系 *", YUNTECH_ALL_DEPTS)
            p_desc = st.text_area("詳細描述說明 *", placeholder="請說明新舊狀態、缺陷或特別約定...")

            p_ship = st.selectbox("偏好的預設寄送管道", ["校園面交", "四大超商取貨", "提供 賣貨便/好賣+ 外部連結"])
            p_link = st.text_input("外部賣場下單連結 (若選外部連結才需填寫)",
                                   placeholder="https://myship.7-11.com.tw/...")

            p_file = st.file_uploader("上傳實體精美照片 (選填)", type=["jpg", "png", "jpeg"])

            if st.form_submit_button("立即安全上架"):
                if not p_name or not p_desc:
                    st.error("請填寫商品名稱與商品詳細描述說明！")
                else:
                    b64_str = ""
                    if p_file:
                        img = Image.open(p_file)
                        img.thumbnail((400, 400))
                        buf = io.BytesIO()
                        img_format = p_file.type.split("/")[-1].upper()
                        img_format = "JPEG" if img_format == "JPG" else img_format
                        img.save(buf, format=img_format)
                        b64_str = f"data:{p_file.type};base64," + base64.b64encode(buf.getvalue()).decode()

                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, image_base64, seller_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (p_name, p_price, p_cat, current_uni, p_dept, p_desc, p_ship, p_link, b64_str, current_student))
                    conn.commit()
                    conn.close()
                    st.success("🎉 商品已成功安全上架到全國流通池！")
                    time.sleep(0.5)
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利
    # ------------------------------------------
    elif st.session_state.current_menu == "綠幣集點福利":
        st.subheader("🪙 環保集點幣：校園點心福利社")
        st.write(f"目前可用點數：**{user_coins} 🪙**（可透過註冊、購買、失物招領通報獲得）")

        gifts = [
            {"name": "超商 35 元微波點心兌換券", "cost": 150,
             "img": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=400"},
            {"name": "學辦特調熱美式咖啡(大杯)", "cost": 200,
             "img": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400"},
            {"name": "期末限定高分歐趴糖袋", "cost": 100,
             "img": "https://images.unsplash.com/photo-1581798459219-318e76aecc7b?w=400"},
            {"name": "智慧物流免運通關券", "cost": 250,
             "img": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400"}
        ]

        g_cols = st.columns(4)
        for idx, g in enumerate(gifts):
            with g_cols[idx]:
                st.markdown(f"""
                <div class="gift-grid-card">
                    <img src="{g['img']}" class="gift-img">
                    <div class="gift-body">
                        <h5 style="margin:0 0 8px 0; color:#212529;">{g['name']}</h5>
                        <p style="color:#ae3ec9; font-weight:bold; margin:0 0 12px 0;">兌換價: {g['cost']} 🪙</p>
                    </div>
                """, unsafe_allow_html=True)

                if st.button(f"立即兌換", key=f"gift_{idx}", use_container_width=True):
                    if user_coins >= g['cost']:
                        v_code = f"COIN-{random.randint(100000, 999999)}"
                        modify_coins(current_student, current_uni, -g['cost'])

                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, ?, '未使用')",
                            (current_student, g['name'], v_code, "2026-06-02"))
                        conn.commit()
                        conn.close()

                        st.success(f"🎉 成功兌換！序號為：{v_code} (已存至左側清單)")
                        time.sleep(1.0)
                        st.rerun()
                    else:
                        st.error("❌ 您的環保集點幣不夠喔！快去購買物資或回報失物吧！")
                st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 4: 失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "失物招領中心":
        st.subheader("🔍 校園失物尋找與招領通報")

        tab1, tab2 = st.tabs(["📋 目前校內待領失物", "📢 發布拾獲新通報"])
        with tab1:
            conn = sqlite3.connect(DB_NAME)
            lost_df = pd.read_sql_query(
                "SELECT id, item_name, place, contact_location, description, finder_id, image_base64 FROM lost_found WHERE university = ? AND status = '招領中'",
                conn, params=(current_uni,))
            conn.close()

            if lost_df.empty:
                st.caption("✨ 太棒了！本校目前沒有待領失物，大家都好好保管了財產！")
            else:
                for _, r in lost_df.iterrows():
                    st.markdown(f"""
                    <div class="lost-card">
                        <h4>🎁 拾獲：{r['item_name']}</h4>
                        <p style="margin:5px 0; font-size:13px;">
                            📍 拾獲地點：<b>{r['place']}</b> | 📦 暫存/認領聯絡處：<b>{r['contact_location']}</b><br>
                            📝 物品特徵描述：{r['description']}<br>
                            👤 善心通報人：{get_seller_masked_name(r['finder_id'])} 同學
                        </p>
                    """, unsafe_allow_html=True)
                    if r['image_base64']:
                        st.image(r['image_base64'], width=200)
                    if st.button("✅ 我是失主，已前往成功認領", key=f"claim_{r['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("UPDATE lost_found SET status = '已認領' WHERE id = ?", (r['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("🎉 恭喜物歸原主！誠實是美德！")
                        time.sleep(0.5)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("##### 填寫拾獲失物資訊 (發布成功可獲得 50 綠幣 🪙)")
            l_name = st.text_input("拾獲物品名稱 *", placeholder="例如：黑色AirPods耳機、藍色保溫杯")
            l_place = st.text_input("拾獲詳細地點 *", placeholder="例如：管一B120教室課桌內、學餐沙發區")
            l_contact = st.text_input("目前暫存/認領聯絡處 *", placeholder="例如：請私訊我LINE、已交給生輔組")
            l_desc = st.text_area("補充描述/特徵說明", placeholder="外殼有黃色貓咪貼紙、大約八成新...")
            l_file = st.file_uploader("失物照片存證 (選填)", type=["jpg", "png", "jpeg"], key="lost_file")

            if st.button("確認發布招領通報"):
                if not l_name or not l_place or not l_contact:
                    st.error("請完整填寫拾獲物名稱、地點與聯絡處！")
                else:
                    lost_b64 = ""
                    if l_file:
                        img = Image.open(l_file)
                        img.thumbnail((300, 300))
                        buf = io.BytesIO()
                        fmt = l_file.type.split("/")[-1].upper().replace("JPG", "JPEG")
                        img.save(buf, format=fmt)
                        lost_b64 = f"data:{l_file.type};base64," + base64.b64encode(buf.getvalue()).decode()

                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO lost_found (region, university, item_name, place, contact_location, description, finder_id, image_base64) VALUES (?,?,?,?,?,?,?,?)",
                        ("台灣", current_uni, l_name, l_place, l_contact, l_desc, current_student, lost_b64))
                    conn.commit()
                    conn.close()

                    increment_mission_counter(current_student, current_uni, "report_count")

                    st.success("🎉 成功發布公告！此善舉已計入活躍滿額抽獎進度。")
                    time.sleep(0.5)
                    st.rerun()

    # ------------------------------------------
    # 功能 5: 盲盒專區 ($150 / 次)
    # ------------------------------------------
    elif st.session_state.current_menu == "盲盒專區":
        prizes = ["神秘高級大專生福袋", "星巴克 150元電子即享券", "超商免運通行證", "1TB 高速行動硬碟"]
        blind_box_html = f"""
        <html>
        <body style="background:#f8f9fa; display:flex; justify-content:center; align-items:center;">
            <div style="background:#111; color:#fff; padding:40px; border-radius:20px; text-align:center; width:300px;">
                <h3>CAMPUS BLIND BOX</h3>
                <h1 style="margin:20px 0; font-size:60px;">?</h1>
                <button onclick="alert('✨ 恭喜抽中：{random.choice(prizes)}！')" style="padding:10px 20px; border-radius:10px; border:none; cursor:pointer; font-weight:bold; background:#fff; color:#111;">開箱盲盒 ($150)</button>
            </div>
        </body>
        </html>
        """
        components.html(blind_box_html, height=300)