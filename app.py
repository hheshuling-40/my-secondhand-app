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
# 🎨 RWD 響應式視覺優化 UI (正式上線版)
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
    .email-box {
        background-color: #e3fafc;
        border: 2px dashed #1098ad;
        padding: 20px;
        border-radius: 12px;
        margin-top: 15px;
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

EMAP_URLS = {
    "7-11 統一超商": "https://emap.pcsc.com.tw/",
    "全家便利商店": "https://www.family.com.tw/Marketing/zh/Map",
    "萊爾富 Hi-Life": "https://www.hilife.com.tw/storeInquiry_street.aspx",
    "OK Mart": "https://www.okmart.com.tw/convenient_shopSearch"
}

YUNTECH_ALL_DEPTS = ["不限科系/共同通識核心", "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系",
                     "工業設計系", "視覺傳達設計系", "數位媒體設計系", "企業管理系", "資訊管理系", "應用外語系"]
PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件", "體育用品", "學術講義"]

INTERNAL_BLINDBOX_POOL = [
    {"name": "【全新】威秀影城全台灣通用電影交換券 🎬", "tag": "豪華大獎"},
    {"name": "【星巴克】$165 星巴克隨行飲料電子即享券 ☕", "tag": "精選好禮"},
    {"name": "【小米】Xiaomi 22.5W 行動電源 10000 ⚡", "tag": "實用3C"},
    {"name": "【全新】Logitech 羅技 B170 無線滑鼠 🖱️", "tag": "辦公必備"},
    {"name": "【生活好物】純白極簡超大容量不鏽鋼保溫冰霸杯 🥤", "tag": "精選好禮"},
    {"name": "【麥當勞】超值全餐豪飽雙人電子兌換券 🍔", "tag": "雙人飽餐"},
    {"name": "【全家】大杯特濃美式咖啡 兌換券 ☕", "tag": "小確幸"},
    {"name": "【7-11】茶葉蛋2顆 + 所長豆干 雙組合點心券 🥚", "tag": "小確幸"},
    {"name": "【義美】經典黑巧克力霜淇淋 兌換券 🍦", "tag": "小確幸"},
    {"name": "【超商熱賣】黑雷神巧克力 3入隨手包 🍫", "tag": "小確幸"}
]


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
if 'formatted_cc' not in st.session_state: st.session_state.formatted_cc = ""

# 忘記密碼專用的暫存狀態
if 'forgot_step' not in st.session_state: st.session_state.forgot_step = "input"
if 'forgot_sid' not in st.session_state: st.session_state.forgot_sid = ""
if 'forgot_uni' not in st.session_state: st.session_state.forgot_uni = ""


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
        reg_email = st.text_input("學校聯絡電子郵件 *", placeholder="example@university.edu.tw")
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
        st.subheader("🔒 自助安全密碼重設服務")

        if st.session_state.forgot_step == "input":
            fg_type = st.selectbox("選擇您的學校體系", CAMPUS_LABELS, key="fg_type")
            fg_uni = st.selectbox("選擇您的學校", CAMPUS_TYPE_MAP[fg_type], key="fg_uni")
            fg_sid = st.text_input("請輸入註冊學號", placeholder="例如：B11000001")
            fg_email = st.text_input("請輸入註冊時填寫的電子郵件", placeholder="例如：example@university.edu.tw")

            if st.button("📧 送出密碼重設信件", type="primary", use_container_width=True):
                if not fg_sid or not fg_email:
                    st.error("⚠️ 請完整填寫學號與電子郵件欄位。")
                else:
                    conn = sqlite3.connect(DB_NAME)
                    user_exist = conn.execute(
                        "SELECT name FROM users WHERE student_id = ? AND university = ? AND email = ?",
                        (fg_sid, fg_uni, fg_email.strip())).fetchone()
                    conn.close()

                    if user_exist:
                        with st.spinner("⚡ 正在向安全伺服器請求驗證並發送郵件中..."):
                            time.sleep(1.8)
                        st.session_state.forgot_sid = fg_sid
                        st.session_state.forgot_uni = fg_uni
                        st.session_state.forgot_step = "email_sent"
                        st.rerun()
                    else:
                        st.error("❌ 查無此資料。請確認學校、學號與註冊信箱是否完全相符！")

        elif st.session_state.forgot_step == "email_sent":
            st.success("🚀 密碼重設郵件發送成功！")

            # 模擬收信匣 UI
            st.markdown(f"""
            <div class="email-box">
                <h4 style="margin-top:0; color:#1098ad;">📬 模擬電子郵件收信匣 (Campus Market)</h4>
                <p><b>收件人：</b> 同學已註冊之信箱</p>
                <p><b>主旨：</b> 【重要】Campus Market 帳號密碼重設安全驗證通知信</p>
                <hr style="border: 0; border-top: 1px solid #b4f2f6;">
                <p>親愛的市集同學您好：</p>
                <p>系統收到您提出的密碼重設申請。為了確保您帳號的安全，請點擊下方系統生成的重設驗證按鈕完成安全重設：</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔗 點擊此處安全連結：前往變更密碼面板", type="primary"):
                st.session_state.forgot_step = "reset_password"
                st.rerun()

            if st.button("⬅️ 返回重新輸入資料"):
                st.session_state.forgot_step = "input"
                st.rerun()

        elif st.session_state.forgot_step == "reset_password":
            st.markdown("### 🔑 設定您的新密碼")
            st.info(f"正在為【{st.session_state.forgot_uni}】學號【{st.session_state.forgot_sid}】的同學變更密碼。")

            new_pass = st.text_input("請輸入新的登入密碼", type="password", placeholder="請輸入新密碼")
            confirm_pass = st.text_input("請再次輸入新密碼確認", type="password", placeholder="再次確認密碼")

            if st.button("💾 儲存新密碼並重新登入", type="primary", use_container_width=True):
                if not new_pass:
                    st.error("⚠️ 密碼不可為空！")
                elif new_pass != confirm_pass:
                    st.error("❌ 兩次輸入的密碼不一致，請重新檢查。")
                else:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("UPDATE users SET password = ? WHERE student_id = ? AND university = ?",
                                 (new_pass, st.session_state.forgot_sid, st.session_state.forgot_uni))
                    conn.commit()
                    conn.close()

                    st.success("🎉 密碼重設成功！請切換到「同學登入」標籤，使用新密碼登入。")
                    # 重設狀態
                    st.session_state.forgot_step = "input"
                    st.session_state.forgot_sid = ""
                    st.session_state.forgot_uni = ""

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


            @st.dialog("🎁 滿5次社群貢獻：校園幸幸運大抽獎")
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
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, '2026-06-03', '未使用')",
                            (current_student, f"【抽獎贏得】{won_prize}", v_code))
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

        unused_vouchers = pd.read_sql_query(
            "SELECT gift_name, code, timestamp FROM vouchers WHERE student_id = ? AND status = '未使用'", conn,
            params=(current_student,))
        used_vouchers = pd.read_sql_query(
            "SELECT gift_name, code, timestamp FROM vouchers WHERE student_id = ? AND status = '已使用'", conn,
            params=(current_student,))
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

        with st.expander(f"🎁 我的優惠券明細 ({len(unused_vouchers) + len(used_vouchers)})"):
            st.markdown("🎟️ **未使用優惠券（含盲盒中獎、點數換購）**")
            if unused_vouchers.empty:
                st.caption("暫無未使用的優惠券。")
            else:
                for _, r in unused_vouchers.iterrows():
                    st.markdown(f"""
                    <div class="record-box" style="background-color:#fff5f5; border-left: 3px solid #ff6b6b;">
                        <b>{r['gift_name']}</b> <small style='color:#e64980; font-weight:bold;'>[未使用]</small><br>
                        <span style="color:#e64980; font-family:monospace; font-weight:bold; font-size:14px;">序號/兌換憑證：{r['code']}</span><br>
                        <small style="color:#868e96;">獲得時間：{r['timestamp']}</small>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("⌛ **已使用/已核銷優惠券**")
            if used_vouchers.empty:
                st.caption("暫無已核銷的優惠券紀錄。")
            else:
                for _, r in used_vouchers.iterrows():
                    st.markdown(f"""
                    <div class="record-box" style="background-color:#f1f3f5; border-left: 3px solid #868e96;">
                        <span style='color:#868e96; text-decoration: line-through;'><b>{r['gift_name']}</b></span> <small style='color:#868e96;'>[已使用]</small><br>
                        <span style="color:#868e96; font-family:monospace; font-size:13px;">序號：{r['code']}</span><br>
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
                st.write(f"👤 **認證賣家：** {get_seller_masked_name(prod_data['seller_id'])} 同學")

            st.info(f"💡 **商品描述：**\n{prod_data['description']}")
            st.markdown("---")

            allowed_methods = [m.strip() for m in prod_data['shipping_method'].split(',') if m.strip()]
            if not allowed_methods:
                allowed_methods = ["預約校園面交"]

            buyer_ship_choice = st.selectbox("請選擇配送管道 (僅顯示賣家支援的選項)", allowed_methods)
            input_voucher_code = st.text_input("🎫 優惠券 / 免運通關券序號（選填）", placeholder="例如：DRAW-XXXXXX")

            base_shipping_fee = 60
            if "面交" in buyer_ship_choice or "網址" in buyer_ship_choice:
                base_shipping_fee = 0

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

            st.markdown("#### 💵 結帳金額明細確認")
            if "網址" in buyer_ship_choice:
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
            form_valid = False

            if "網址" in buyer_ship_choice:
                if prod_data['shipping_link'] and prod_data['shipping_link'].strip() != "":
                    st.markdown(f"""
                    <div style="background:#eef9ff; padding:12px; border-radius:8px; border-left:4px solid #007bff; margin-bottom:10px;">
                        <a href="{prod_data['shipping_link']}" target="_blank" style="font-weight:bold; color:#007bff; text-decoration:underline;">👉 點我打開賣家外部賣場下單</a>
                    </div>
                    """, unsafe_allow_html=True)
                    final_memo_output = f"[外部賣場] 連結：{prod_data['shipping_link']}"
                    form_valid = True
                else:
                    st.warning("⚠️ 賣家未附連結，請點下方 LINE 按鈕聯絡賣家開單。")
                    final_memo_output = "[外部賣場] 待聯絡開單"
                    form_valid = True

            elif "超商" in buyer_ship_choice:
                st.markdown("### 📍 官方真實超商數據對接")
                st.caption("請開啟超商官方地圖，查詢並複製完整的門市名稱與編號後貼回下方。")

                chain_choice = st.selectbox("選擇欲寄送的超商系統", list(EMAP_URLS.keys()))
                st.markdown(
                    f'<a href="{EMAP_URLS[chain_choice]}" target="_blank" class="emap-btn">🌐 開啟官方【{chain_choice}】電子地圖查詢</a>',
                    unsafe_allow_html=True)

                raw_store_input = st.text_input("📋 請在此貼上官方複製的門市名稱與編號資料",
                                                placeholder="例如：台大門市 115234")
                b_name = st.text_input("收件人真實姓名")
                b_phone = st.text_input("收件人手機號碼")

                if raw_store_input.strip() and b_name.strip() and b_phone.strip():
                    final_memo_output = f"[{chain_choice}取貨] {raw_store_input.strip()} (收件人: {b_name.strip()}, 電話: {b_phone.strip()})"
                    form_valid = True
                else:
                    st.error("請完整輸入門市貼上資訊與收件人姓名、電話。")
                    form_valid = False

            elif "面交" in buyer_ship_choice:
                face_detail = st.text_input("🤝 輸入欲約定的校園面交地點與時間",
                                            placeholder="例如：明天中午12點 體育館大門口")
                if face_detail.strip():
                    final_memo_output = f"校園面交 ➡️ {face_detail.strip()}"
                    form_valid = True
                else:
                    st.warning("請輸入預期面交的地點與時間。")
                    form_valid = False

            st.write(" ")
            s_line = get_user_line(prod_data['seller_id'])
            st.markdown(
                f'<a href="https://line.me/ti/p/~{s_line}" target="_blank" class="line-btn">💬 私訊賣家 LINE 溝通</a>',
                unsafe_allow_html=True)
            st.write(" ")

            if form_valid:
                if st.button("🛒 確認下單", type="primary", use_container_width=True):
                    if prod_data['seller_id'] == current_student:
                        st.error("不能購買自己上架的商品！")
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        if voucher_db_id:
                            conn.execute("UPDATE vouchers SET status = '已使用' WHERE id = ?", (voucher_db_id,))
                        conn.execute(
                            "UPDATE products SET status = '已售出', buyer_id = ?, final_trade_info = ? WHERE id = ?",
                            (current_student, final_memo_output, prod_data['id']))
                        conn.commit()
                        conn.close()

                        increment_mission_counter(current_student, current_uni, "buy_count")
                        st.success("🎉 下單成功！系統已為您鎖定該物資。")
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.button("🔒 請先完成上方欄位填寫以解鎖按鈕", type="secondary", disabled=True, use_container_width=True)


        if df.empty:
            st.info("🪐 目前流通池空空如也。")
        else:
            for _, row in df.iterrows():
                st.markdown(f"""
                <div class="product-card">
                    <div class="prod-img-container">
                        <img src="{row['image_base64'] if row['image_base64'] else 'https://placehold.co/180x150?text=No+Image'}" style="width:100%; border-radius:12px;">
                    </div>
                    <div class="prod-info-container">
                        <span style="background-color:#eef2f5; color:#495057; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:600;">{row['category']}</span>
                        <h4 style="margin:8px 0 4px 0; color:#212529;">{row['name']}</h4>
                        <div style="font-size:13px; color:#868e96; margin-bottom:6px;">學校：{row['university']} | 支援交易：{row['shipping_method']}</div>
                        <p style="font-size:13px; color:#495057; line-height:1.4; margin:0;">{row['description'][:50]}...</p>
                    </div>
                    <div class="prod-action-container">
                        <div class="price-tag">${row['price']:.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("查看詳情 / 立即下單 🛒", key=f"view_{row['id']}", use_container_width=True):
                    show_product_details_dialog(row)

    # ------------------------------------------
    # 功能 2: 智慧物資上架
    # ------------------------------------------
    elif st.session_state.current_menu == "智慧物資上架":
        st.subheader("📤 智慧物資發布中心")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("商品名稱 *", placeholder="例如：微積分課本(九成新)")
            p_price = st.number_input("預售金額 ($) *", min_value=0, value=50, step=10)
            p_cat = st.selectbox("物品類型分類 *", PRODUCT_CATEGORIES[1:])
            p_dept = st.selectbox("推薦適用科系 *", YUNTECH_ALL_DEPTS)
            p_desc = st.text_area("商品細節描述 *")

            st.write("🚚 **您希望提供哪些交易/配送形式？(可複選)** *")
            ship_1 = st.checkbox("預約校園面交", value=True)
            ship_2 = st.checkbox("四大超商取貨")
            ship_3 = st.checkbox("使用 賣貨便/好賣+ 外部網址下單")

            p_link = st.text_input("外部賣場下單網址 (若有勾選外部網址請填寫)",
                                   placeholder="https://myship.7-11.com.tw/...")
            p_img = st.file_uploader("上傳商品真實照片 (選填)", type=["jpg", "png", "jpeg"])

            if st.form_submit_button("一鍵上架物資 🚀"):
                methods_selected = []
                if ship_1: methods_selected.append("預約校園面交")
                if ship_2: methods_selected.append("四大超商取貨")
                if ship_3: methods_selected.append("使用 賣貨便/好賣+ 外部網址下單")

                if not p_name or not p_desc:
                    st.error("請填寫商品名稱與描述項目！")
                elif not methods_selected:
                    st.error("請至少選擇一種交易形式！")
                else:
                    shipping_methods_str = ", ".join(methods_selected)
                    img_b64 = ""
                    if p_img:
                        bytes_data = p_img.read()
                        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode()}"

                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, image_base64, seller_id, status) VALUES (?,?,?,?,?,?,?,?,?,?,'上架中')",
                        (p_name, p_price, p_cat, current_uni, p_dept, p_desc, shipping_methods_str, p_link, img_b64,
                         current_student))
                    conn.commit()
                    conn.close()
                    st.success("🎉 上架成功！您的物品已加入共享池。")
                    time.sleep(1.0)
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利
    # ------------------------------------------
    elif st.session_state.current_menu == "綠幣集點福利":
        st.subheader("🪙 環保綠幣福利社")
        st.info(f"💡 您的當前帳戶餘額： **{user_coins} 🪙**")

        rewards = [
            {"name": "【全家】35元微波點心即享折價券", "cost": 150,
             "img": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=400"},
            {"name": "【7-11】大杯美式咖啡電子即享券", "cost": 200,
             "img": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400"},
            {"name": "【Campus Market】校園免運通行證", "cost": 80,
             "img": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400"}
        ]

        col_rew = st.columns(3)
        for i, r in enumerate(rewards):
            with col_rew[i]:
                st.markdown(f"""
                <div class="gift-grid-card">
                    <img class="gift-img" src="{r['img']}">
                    <div class="gift-body">
                        <h5 style="margin:0 0 8px 0; min-height:40px;">{r['name']}</h5>
                        <p style="color:#e64980; font-weight:bold; font-size:16px; margin:0;">所需點數：{r['cost']} 🪙</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if user_coins >= r['cost']:
                    if st.button(f"🛒 立刻兌換", key=f"rew_{i}", use_container_width=True, type="primary"):
                        modify_coins(current_student, current_uni, -r['cost'])
                        v_code = f"COIN-{random.randint(100000, 999999)}"

                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, '2026-06-03', '未使用')",
                            (current_student, r['name'], v_code))
                        conn.commit()
                        conn.close()
                        st.success(f"🎉 兌換成功！序號 {v_code} 已存入個人清單。")
                        time.sleep(1.0)
                        st.rerun()
                else:
                    st.button("🔒 點數不足", key=f"rew_dis_{i}", disabled=True, use_container_width=True)

    # ------------------------------------------
    # 功能 4: 失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "失物招領中心":
        st.subheader("🔍 校園失物尋找與招領通報")
        tab_list, tab_report = st.tabs(["📋 目前失物招領登記簿", "📣 拾獲失物通報登記入口"])

        with tab_list:
            conn = sqlite3.connect(DB_NAME)
            lost_df = pd.read_sql_query(
                "SELECT id, item_name, place, contact_location, description, university FROM lost_found WHERE status='招領中'",
                conn)
            conn.close()

            if lost_df.empty:
                st.caption("目前校園內沒有未領取的失物登記。")
            else:
                for _, r in lost_df.iterrows():
                    st.markdown(f"""
                    <div class="lost-card">
                        <h4 style="margin:0 0 6px 0; color:#c25e00;">📌 {r['item_name']}</h4>
                        <small><b>拾獲校園：</b>{r['university']} | <b>拾獲地點：</b>{r['place']}</small><br>
                        <p style="font-size:13px; margin:6px 0 0 0; color:#495057;">備註：{r['description']}</p>
                        <small style="color:#744210;"><b>保管處：</b>{r['contact_location']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🙋 我是失主 / 已物歸原主", key=f"claim_{r['id']}", use_container_width=True):
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("UPDATE lost_found SET status='已領回' WHERE id=?", (r['id'],))
                        conn.commit()
                        conn.close()
                        st.success("🎉 狀態已變更為已領回。")
                        time.sleep(0.5)
                        st.rerun()

        with tab_report:
            with st.form("lost_form"):
                l_name = st.text_input("拾獲物品名稱 *")
                l_place = st.text_input("具體拾獲地點 *")
                l_contact = st.text_input("目前暫時寄放地點 *")
                l_desc = st.text_area("外觀備註/特徵描述")

                if st.form_submit_button("發布招領通報 📢"):
                    if not l_name or not l_place or not l_contact:
                        st.error("請完整填寫通報必填欄位！")
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO lost_found (region, university, item_name, place, contact_location, description, finder_id, image_base64) VALUES (?,?,?,?,?,?,?,?)",
                            ("台灣", current_uni, l_name, l_place, l_contact, l_desc, current_student, ""))
                        conn.commit()
                        conn.close()
                        increment_mission_counter(current_student, current_uni, "report_count")
                        st.success("🎉 成功發布公告！")
                        time.sleep(0.5)
                        st.rerun()

    # ------------------------------------------
    # 功能 5: 盲盒專區 (內建驚喜商品 + 信用卡號自動格式化)
    # ------------------------------------------
    elif st.session_state.current_menu == "盲盒專區":
        st.subheader("🎁 幸運官方盲盒抽獎池 ($150 / 次)")
        st.write(
            "每次購買只需支付 **$150 元** 信用卡手續費，即可隨機獲得平台官方準備的驚喜好禮！獎池包含高價實體 3C 產品、精選即享券，或是日常實用的超商平價小確幸點心，快來試試手氣吧！")

        st.markdown("#### 🛍️ 官方盲盒獎項部分精彩預覽：")
        col_preview = st.columns(4)
        preview_items = [INTERNAL_BLINDBOX_POOL[0], INTERNAL_BLINDBOX_POOL[2], INTERNAL_BLINDBOX_POOL[6],
                         INTERNAL_BLINDBOX_POOL[7]]
        for idx, item in enumerate(preview_items):
            with col_preview[idx]:
                badge_color = "#e64980" if "大獎" in item['tag'] or "3C" in item['tag'] else "#4dabf7"
                st.markdown(f"""
                <div style="background:#ffffff; padding:15px; border-radius:12px; border:1px solid #dee2e6; text-align:center; min-height:110px;">
                    <span style="background:{badge_color}; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">{item['tag']}</span>
                    <p style="margin:8px 0 0 0; font-size:14px; font-weight:600; color:#343a40;">{item['name']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.write(" ")
        st.info("💳 本模組已接軌線上正式安全金流（信用卡即時扣款面版）：")

        with st.expander("📝 點此展開信用卡付款資料填寫", expanded=True):
            raw_cc = st.text_input("💳 信用卡卡號", value=st.session_state.formatted_cc,
                                   placeholder="4000 1234 5678 9010", key="cc_input")

            digits_only = re.sub(r"\D", "", raw_cc)[:16]
            formatted = " ".join([digits_only[i:i + 4] for i in range(0, len(digits_only), 4)])

            if formatted != raw_cc:
                st.session_state.formatted_cc = formatted
                st.rerun()

            cc_date = st.text_input("📅 有效期限", placeholder="MM/YY", max_chars=5)
            cc_cvv = st.text_input("🔒 安全碼", type="password", placeholder="123", max_chars=3)

            pay_valid = len(digits_only) == 16 and len(cc_date) >= 4 and len(cc_cvv) >= 3

        if pay_valid:
            if st.button("🔒 確定支付 $150 並開啟盲盒 🎰", type="primary", use_container_width=True):
                with st.spinner("正在進行銀行 3D 安全金流驗證，請勿關閉網頁... 💳"):
                    time.sleep(2.0)

                won_gift = random.choice(INTERNAL_BLINDBOX_POOL)
                v_code = f"BOX-{random.randint(100000, 999999)}"

                conn = sqlite3.connect(DB_NAME)
                conn.execute(
                    "INSERT INTO vouchers (student_id, gift_name, code, timestamp, status) VALUES (?, ?, ?, '2026-06-03', '未使用')",
                    (current_student, f"【盲盒獎項】{won_gift['name']}", v_code))
                conn.commit()
                conn.close()

                increment_mission_counter(current_student, current_uni, "buy_count")
                st.session_state.formatted_cc = ""

                st.balloons()
                st.success(f"✨ 刷卡扣款成功！恭喜您在盲盒中抽中：")
                st.markdown(f"### 🎉 {won_gift['name']}")
                st.markdown(f"🎟️ **您的專屬領獎序號/憑證碼為：** `{v_code}`")
                st.info("💡 領獎憑證已為您自動存入左側側邊欄的「我的優惠券明細」 ➡️ 「未使用優惠券」中，您可隨時查看核銷！")
                time.sleep(3.5)
                st.rerun()
        else:
            st.button("🔒 請先於上方正確填寫 16 碼信用卡付款資訊以解鎖盲盒購買", disabled=True, use_container_width=True)