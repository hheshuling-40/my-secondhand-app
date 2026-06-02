import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與網頁自動配置
st.set_page_config(page_title="Campus Market | 全國大學生智慧市集", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 RWD 響應式視覺優化 UI
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
        margin-bottom: 5px;
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
        box-shadow: 0 4px 12px rgba(6, 199, 85, 0.15);
        transition: all 0.2s ease;
        font-size: 14px;
        margin-top: 5px;
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 全台大專院校完整地圖 (已去除括號與數量)
# ==========================================
DB_NAME = 'streamlit_campus_market_v109_trade_fix.db'

CAMPUS_TYPE_MAP = {
    "公立學校": [
        "國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學",
        "國立成功大學", "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學",
        "國立臺灣科技大學", "國立臺北科技大學", "國立雲林科技大學", "國立屏東科技大學", "國立虎尾科技大學",
        "國立高雄科技大學", "國立臺北大學", "國立臺灣海洋大學", "國立彰化師範大學", "國立高雄師範大學",
        "國立東華大學", "國立暨南國際大學", "國立臺東大學", "國立宜蘭大學", "國立聯合大學",
        "國立臺南大學", "國立臺北教育大學", "國立臺中教育大學", "國立臺灣藝術大學", "國立臺北藝術大學",
        "國立臺灣體育運動大學", "國立體育大學", "國立金門大學", "國立澎湖科技大學", "國立勤益科技大學",
        "國立臺北商業大學", "國立臺中科技大學", "國立臺北護理健康大學", "國立高雄餐旅大學", "國立臺灣戲曲學院",
        "臺北市立大學", "國立防衛大學", "國立空中大學", "高雄市立空中大學", "國立臺東專科學校",
        "國立警察大學", "中央警察大學"
    ],
    "私立學校": [
        "輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學",
        "靜宜大學", "長庚大學", "元智大學", "中華大學", "大葉大學", "華梵大學",
        "義守大學", "銘傳大學", "實踐大學", "世新大學", "真理大學", "東海大學",
        "高雄醫學大學", "中國醫藥大學", "中山醫學大學", "台北醫學大學", "長榮大學",
        "南華大學", "玄奘大學", "佛光大學", "明道大學", "亞洲大學", "開南大學",
        "台灣首府大學", "康寧大學", "大同大學", "南台科技大學", "崑山科技大學",
        "嘉南藥理大學", "樹德科技大學", "龍華科技大學", "輔英科技大學", "明志科技大學",
        "聖約翰科技大學", "嶺東科技大學", "中國科技大學", "中台科技大學", "台南應用科技大學",
        "遠東科技大學", "元培醫事科技大學", "景文科技大學", "中華醫事科技大學", "萬能科技大學",
        "建國科技大學", "高苑科技大學", "大仁科技大學", "文藻外語大學", "正修科技大學",
        "朝陽科技大學", "弘光科技大學", "健行科技大學", "僑光科技大學", "明新科技大學",
        "東南科技大學", "德明財經科技大學", "致理科技大學", "醒吾科技大學", "亞東科技大學",
        "台北城市科技大學", "環球科技大學", "修平科技大學", "中華科技大學", "育達科技大學",
        "美和科技大學", "吳鳳科技大學", "臺灣神學研究學院", "法鼓文理學院", "中信金融管理學院",
        "馬偕醫學院", "基督書院", "台北海洋科技大學", "宏國德霖科技大學", "長庚科技大學",
        "黎明技術學院", "東方設計大學", "南榮科技大學", "崇右影藝科技大學", "和春技術學院",
        "大漢技術學院", "慈濟科技大學", "慈濟大學"
    ]
}

YUNTECH_ALL_DEPTS = ["不限科系/共同通識核心", "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系",
                     "工業設計系", "視覺傳達設計系", "數位媒體設計系", "企業管理系", "資訊管理系", "應用外語系"]
PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件", "體育用品", "學術講義"]


# ==========================================
# 1. 資料庫基礎建設 (新增實際交易備註欄位)
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
            final_trade_info TEXT DEFAULT '' -- 儲存買家最後填寫的交易詳情與面交管道
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
    st.write("已解鎖全台139所大專院校，並啟用行動裝置 RWD 佈局與個資 O 字遮罩機制。")

    mode = st.radio("請選擇操作項目：", ["🔑 同學登入", "📝 新同學註冊帳號", "❓ 忘記密碼"], horizontal=True)

    if mode == "🔑 同學登入":
        with st.form("login_form"):
            log_type = st.selectbox("請選擇體系類型", list(CAMPUS_TYPE_MAP.keys()))
            log_uni = st.selectbox("請選取您的就讀學校", CAMPUS_TYPE_MAP[log_type])
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
        reg_type = st.selectbox("學校體系類型 *", list(CAMPUS_TYPE_MAP.keys()))
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

    # ------------------------------------------
    # 側邊欄新增：我的交易紀錄（解決買賣家看不見訂單的問題）
    # ------------------------------------------
    with st.sidebar:
        st.markdown("### 🧑‍🎓 攤主名片")
        st.markdown(f"歡迎回來，**{current_name}** 同學！👋")
        st.write(f"學校｜**{current_uni}**")
        st.write(f"學號｜**{current_student}**")
        st.metric(label="我的環保集點幣", value=f"{get_coins(current_student, current_uni)} 🪙")

        st.markdown("---")
        st.markdown("### 📊 我的交易清單")

        # 讀取交易資料
        conn = sqlite3.connect(DB_NAME)
        my_sales = pd.read_sql_query(
            "SELECT name, price, status, final_trade_info FROM products WHERE seller_id = ? AND status = '已售出'",
            conn, params=(current_student,))
        my_buys = pd.read_sql_query("SELECT name, price, university, final_trade_info FROM products WHERE buyer_id = ?",
                                    conn, params=(current_student,))
        conn.close()

        with st.expander(f"🏪 我賣出的商品 ({len(my_sales)})"):
            if my_sales.empty:
                st.caption("目前尚無售出物資紀錄。")
            else:
                for _, r in my_sales.iterrows():
                    st.markdown(f"""
                    <div class="record-box">
                        <b>{r['name']}</b> <span style="color:#green;">[已售出]</span><br>
                        金額：${r['price']:.0f}<br>
                        🤝 交易細節：{r['final_trade_info']}
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
                        🤝 協商方式：{r['final_trade_info']}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 登出市集", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="main-title">🛍 Honor 全國智慧服務選單</div>', unsafe_allow_html=True)
    st.write("---")

    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns([1, 1, 1, 1])
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
    # 功能 1: 探索雜貨市集 (結合詳細視窗與重構交易流程)
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


        # 定义詳細視窗與交易細節填寫對話框
        @st.dialog("🔍 商品完整詳情與敲定交易方式")
        def show_product_details_dialog(prod_data):
            st.write(f"### {prod_data['name']}")
            if prod_data['image_base64']:
                st.image(prod_data['image_base64'], use_container_width=True)

            c_a, c_b = st.columns(2)
            with c_a:
                st.write(f"🏫 **出校園：** {prod_data['university']}")
                st.write(f"💰 **物資售價：** ${prod_data['price']:.0f} 元")
            with c_b:
                st.write(f"🚚 **原定寄送：** {prod_data['shipping_method']}")
                st.write(f"👤 **認證賣家：** {get_seller_masked_name(prod_data['seller_id'])} 同學")

            st.info(f"💡 **商品完整描述：**\n{prod_data['description']}")

            st.markdown("---")
            st.markdown("#### 🤝 步驟二：請填寫您與賣家敲定的交易模式")
            st.write("（此步驟不會扣除環保點數，資訊將會同步進入雙方的交易清單）")

            trade_choice = st.selectbox("選擇您要進行的實際管道",
                                        ["預約校園面交", "使用 7-11 賣貨便 / 好賣+", "其他寄送約定"])

            if trade_choice == "預約校園面交":
                trade_memo = st.text_input("填寫面交時間與地點 (例如：週三中午在雲科生活創意大樓門口)",
                                           placeholder="請輸入約定地點...")
            elif trade_choice == "使用 7-11 賣貨便 / 好賣+":
                trade_memo = st.text_input("填寫收件人姓名與店號（若賣家有提供網址，亦可貼上）",
                                           placeholder="請填寫收件資訊...")
            else:
                trade_memo = st.text_input("備註說明", placeholder="請填寫其他物流或付款細節...")

            s_line = get_user_line(prod_data['seller_id'])
            st.markdown(
                f'<a href="https://line.me/ti/p/~{s_line}" target="_blank" class="line-btn">💬 先私訊賣家 LINE 敲定細節</a>',
                unsafe_allow_html=True)

            if st.button("🚀 確定送出訂單（不扣幣，移入雙方清單）", use_container_width=True, type="primary"):
                if prod_data['seller_id'] == current_student:
                    st.error("不能購買自己上架的商品！")
                elif not trade_memo:
                    st.error("請填寫交易詳情再送出，方便賣家為您出貨與接洽。")
                else:
                    final_info_string = f"[{trade_choice}] {trade_memo}"
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "UPDATE products SET status = '已售出', buyer_id = ?, final_trade_info = ? WHERE id = ?",
                        (current_student, final_info_string, prod_data['id']))
                    conn.commit()
                    conn.close()
                    st.success("🎉 訂單發送成功！您可以在側邊欄的「我的交易清單」中隨時查閱。")
                    time.sleep(1.5)
                    st.rerun()


        if df.empty:
            st.info("💡 目前市集商場尚無寶物在售。")
        else:
            for index, row in df.iterrows():
                img_html = f"<img src='{row['image_base64']}' style='width:100%; border-radius:12px; object-fit:cover;' />" if \
                row[
                    'image_base64'] else "<div style='background-color:#f1f3f5;height:120px;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#adb5bd;font-size:13px;'>📦 暫無商品照</div>"
                masked_seller_name = get_seller_masked_name(row['seller_id'])

                st.markdown(f"""
                <div class="product-card">
                    <div class="prod-img-container">{img_html}</div>
                    <div class="prod-info-container">
                        <h4 style="margin:0 0 8px 0; color:#212529;">{row['name']}</h4>
                        <p style="margin:2px 0; font-size:13px; color:#6c757d;">🏫 學校：{row['university']}</p>
                        <p style="margin:2px 0; font-size:13px; color:#6c757d;">🚚 預期運送：{row['shipping_method']}</p>
                        <p style="margin:8px 0 0 0; font-size:13px; color:#06C755;">👤 <b>賣家：</b>{masked_seller_name} 同學 (誠信認證)</p>
                    </div>
                    <div class="prod-action-container">
                        <div class="price-tag">${row['price']:.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 點選檢視與下單
                if st.button(f"🔍 點此看詳細規格或下單流程（品名：{row['name']}）", key=f"view_{row['id']}",
                             use_container_width=True):
                    show_product_details_dialog(row)

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
            st.markdown(f"""
            <div style="background:#ffffff; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.02); margin-bottom:12px;">
                <h5 style="margin:0 0 5px 0;">{g['name']}</h5>
                <p style="margin:0; color:#06C755; font-weight:bold;">所需點數：{g['cost']} 點</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("確認兌換", key=f"g_{idx}", use_container_width=True):
                if user_coins >= g['cost']:
                    modify_coins(current_student, current_uni, -g['cost'])
                    v_code = f"CM-{random.randint(100000, 999999)}"
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                                 (current_student, g['name'], v_code, "2026-06"))
                    conn.commit()
                    conn.close()
                    st.balloons()
                    st.success(f"🎉 兌換成功！您的核銷序號為：{v_code}")
                else:
                    st.error("點數不足")

    # ------------------------------------------
    # 功能 4: 📍 全國大學生失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "📍 失物招領中心":
        st.subheader("📍 全國大學生聯防失物招領中心")

        m_tab1, m_tab2 = st.tabs(["🔍 招領佈告欄", "➕ 發布失物通報"])

        with m_tab1:
            sub_tab_local, sub_tab_national = st.tabs([f"🏫 本校公告 ({current_uni})", "🌐 全台跨校聯防"])

            # 1. 本校專屬分頁
            with sub_tab_local:
                conn = sqlite3.connect(DB_NAME)
                query_local = "SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND university=?"
                df_local = pd.read_sql_query(query_local, conn, params=(current_uni,))
                conn.close()

                if df_local.empty:
                    st.info(f"💡 目前 {current_uni} 暫無校內失物招領公告。")
                else:
                    for idx, row in df_local.iterrows():
                        masked_finder_name = get_seller_masked_name(row['finder_id'])
                        st.markdown(f"""
                        <div class="lost-card" style="border-left: 5px solid #2ecc71; background-color: #fafffa;">
                            <h5>🔍 【本校專區】{row['item_name']}</h5>
                            <p style='margin:2px 0; font-size:13px;'>📍 <b>拾獲地點：</b>{row['place']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#e67e22;'>🏢 <b>認領與暫存位置：</b>{row['contact_location']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#7f8c8d;'>👤 <b>善心拾獲人：</b>{masked_finder_name} 同學</p>
                            <small>外觀備註說明：{row['description']}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        if row['image_base64']: st.image(row['image_base64'], caption="遺失物實體現場照", width=220)

                        if st.button("✨ 本校物歸原主（撤除公告）", key=f"res_local_{row['id']}",
                                     use_container_width=True):
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("UPDATE lost_found SET status='已認領' WHERE id=?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.success("🎉 功德無量！已順利撤除校內公告。")
                            time.sleep(0.5)
                            st.rerun()

            # 2. 跨校聯防分頁
            with sub_tab_national:
                st.write("🌐 篩選其他學校的失物看板：")
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    nat_type = st.selectbox("學校體系篩選", list(CAMPUS_TYPE_MAP.keys()))
                with c_t2:
                    search_nat_uni = st.selectbox("特定學校篩選",
                                                  ["全部學校"] + [u for u in CAMPUS_TYPE_MAP[nat_type] if
                                                                  u != current_uni])

                conn = sqlite3.connect(DB_NAME)
                if search_nat_uni == "全部學校":
                    placeholders = ','.join(['?'] * len(CAMPUS_TYPE_MAP[nat_type]))
                    query_nat = f"SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND university != ? AND university IN ({placeholders})"
                    params = [current_uni] + CAMPUS_TYPE_MAP[nat_type]
                    df_nat = pd.read_sql_query(query_nat, conn, params=params)
                else:
                    query_nat = "SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND university = ?"
                    df_nat = pd.read_sql_query(query_nat, conn, params=(search_nat_uni,))
                conn.close()

                if df_nat.empty:
                    st.info("💡 目前所選之其他大學暫無失物招領公告。")
                else:
                    for idx, row in df_nat.iterrows():
                        masked_finder_name = get_seller_masked_name(row['finder_id'])
                        st.markdown(f"""
                        <div class="lost-card">
                            <h5>🔍 【{row['university']}】{row['item_name']}</h5>
                            <p style='margin:2px 0; font-size:13px;'>📍 <b>拾獲地點：</b>{row['place']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#e67e22;'>🏢 <b>認領與暫存位置：</b>{row['contact_location']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#7f8c8d;'>👤 <b>善心拾獲人：</b>{masked_finder_name} 同學</p>
                            <small>外觀備註說明：{row['description']}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        if row['image_base64']: st.image(row['image_base64'], caption="遺失物實體現場照", width=220)

                        if st.button("✨ 跨校物歸原主（撤除公告）", key=f"res_nat_{row['id']}", use_container_width=True):
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
                l_type = st.selectbox("拾獲物品學校體系 *", list(CAMPUS_TYPE_MAP.keys()))
                l_uni = st.selectbox("拾獲物品所屬學校 *", CAMPUS_TYPE_MAP[l_type])
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
                            (l_type, l_uni, l_name, l_place, l_contact, l_desc, current_student, lost_b64))
                        conn.commit()
                        conn.close()

                        modify_coins(current_student, current_uni, 15)
                        st.balloons()
                        st.success("🎉 聯防公告發布成功！外在顯示已自動套用 O 字個資隱私保護。")
                        time.sleep(1)
                        st.rerun()