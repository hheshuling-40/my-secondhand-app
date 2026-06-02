import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與圖示
st.set_page_config(page_title="🎓 全國大學校園 AI 智慧二手生活市集", page_icon="🛍️", layout="wide")

# 自訂 LINE 官方帳號視覺風格 CSS
st.markdown("""
<style>
    /* 美化 LINE 綠色快捷按鈕 */
    .line-btn {
        background-color: #06C755 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        text-align: center;
        padding: 12px;
        display: block;
        text-decoration: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .line-btn:hover {
        background-color: #05b34c !important;
        color: white !important;
    }
    /* 強化按鈕文字排版，使其更像圖文選單方格 */
    .stButton>button {
        height: 70px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: 2px solid #06C755 !important;
        background-color: #ffffff !important;
        color: #333333 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stButton>button:hover {
        background-color: #f4fff7 !important;
        border-color: #05b34c !important;
        color: #06C755 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 全國大學與雲科大專屬科系地圖
# ==========================================
REGION_UNIVERSITY_MAP = {
    "中部地區": [
        "國立雲林科技大學", "國立中興大學", "逢甲大學", "東海大學",
        "中國醫藥大學", "靜宜大學", "大葉大學", "國立彰化師範大學", "其他中部大學"
    ],
    "北部地區": [
        "國立台灣大學", "國立清華大學", "國立陽明交通大學", "國立臺北科技大學",
        "國立台灣科技大學", "國立中央大學", "國立政治大學", "淡江大學",
        "輔仁大學", "東吳大學", "其他北部大學"
    ],
    "南部地區": [
        "國立成功大學", "國立中山大學", "國立中正大學", "國立高雄科技大學",
        "國立屏東科技大學", "義守大學", "其他南部大學"
    ],
    "東部與離島": [
        "國立東華大學", "國立宜蘭大學", "國立台東大學", "其他東部離島大學"
    ]
}

# 雲科大所有系所（若非書籍，可選不限科系/共同通識核心）
YUNTECH_ALL_DEPTS = [
    "不限科系/共同通識核心",
    "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系", "化學工程與材料工程系",
    "環境與安全衛生工程系", "工程科技菁英班",
    "工業設計系", "視覺傳達設計系", "數位媒體設計系", "創意生活設計系", "建築與室內設計系", "跨域整合設計學士學位學程",
    "企業管理系", "財務金融系", "會計系", "資訊管理系", "工業工程與管理系", "國際管理學士學位學程",
    "應用外語系", "文化資產維護系",
    "前瞻學士學位學程", "產業科技學士學位學程"
]

# 恢復全方位商品分類
PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件", "體育用品", "學術講義"]


# ==========================================
# 1. 資料庫初始化
# ==========================================
def init_db():
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                student_id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                university TEXT NOT NULL,
                line_id TEXT DEFAULT '未填寫',
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
        cursor.execute(
            "INSERT OR IGNORE INTO users (student_id, password, university, line_id, green_coins) VALUES ('B11321123', '1234', '國立雲林科技大學', 'yuntech_cool', 100)")
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"資料庫初始化失敗: {e}")


# AI 全方位商品類別與科系智慧判定
def auto_classify_item(name, description):
    text = (name + " " + description).lower()

    # 預設分類
    cat = "生活雜物"
    dept = "不限科系/共同通識核心"

    # 1. 判定物品大類
    if any(w in text for w in ["書", "課本", "精裝", "修訂版", "版"]):
        cat = "書籍"
    elif any(w in text for w in ["計算機", "行動電源", "耳機", "充電", "ipad", "iphone", "滑鼠", "鍵盤", "線"]):
        cat = "3C配件"
    elif any(w in text for w in ["衣服", "褲子", "外套", "鞋", "帽子", "背包", "飾品"]):
        cat = "服飾配件"
    elif any(w in text for w in ["球", "球拍", "健身", "啞鈴", "球鞋", "運動"]):
        cat = "體育用品"
    elif any(w in text for w in ["講義", "筆記", "考古題", "列印"]):
        cat = "學術講義"
    elif any(w in text for w in ["檯燈", "風扇", "衣架", "椅子", "桌子", "床墊", "宿舍"]):
        cat = "生活雜物"

    # 2. 如果是書籍或講義，進一步判定雲科大科系關鍵字
    if cat in ["書籍", "學術講義"]:
        mapping = {
            "資訊工程系": ["程式", "python", "java", "演算法", "資料結構", "網頁", "資工", "作業系統"],
            "電機工程系": ["電路", "電子學", "電磁", "訊號", "電機", "電力"],
            "機械工程系": ["熱力", "流體", "靜力", "動力", "機械", "工程圖学"],
            "化學工程與材料工程系": ["有機化學", "普化", "化工", "材料工程"],
            "營建工程系": ["土木", "營建", "結構學", "混凝土"],
            "視覺傳達設計系": ["視覺", "色彩", "排版", "視傳", "平面設計"],
            "數位媒體設計系": ["動畫", "遊戲", "特效", "剪輯", "數媒"],
            "工業設計系": ["工設", "產品設計", "模型"],
            "企業管理系": ["管理學", "行銷", "企管"],
            "財務金融系": ["投資", "金融", "財金"],
            "會計系": ["會計", "審計", "稅務"],
            "資訊管理系": ["資管", "資料庫", "mis"],
            "應用外語系": ["英文", "多益", "toeic", "應外"]
        }
        for dp, keywords in mapping.items():
            if any(word in text for word in keywords):
                dept = dp
                break

    return cat, dept


init_db()

# ==========================================
# 2. Session 狀態與帳戶操作
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'user_uni' not in st.session_state:
    st.session_state.user_uni = ""
if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "🔍 校園雜貨市集"


def login_user(student_id, password):
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT university FROM users WHERE student_id = ? AND password = ?", (student_id, password))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except:
        return None


def register_user(student_id, password, university, line_id):
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (student_id, password, university, line_id, green_coins) VALUES (?, ?, ?, ?, 100)",
            (student_id, password, university, line_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_user_line(student_id):
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else "未填寫"
    except:
        return "未填寫"


def update_user_line(student_id, new_line):
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET line_id = ? WHERE student_id = ?", (new_line, student_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_coins(student_id):
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0
    except:
        return 0


def modify_coins(student_id, amount):
    try:
        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ?", (amount, student_id))
        conn.commit()
        conn.close()
    except:
        pass


# ==========================================
# 3. 登入 / 註冊系統
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 全國大學校園 AI 智慧二手生活市集")
    st.subheader("生活用品、3C配件、學長姐教科書，一應俱全")

    auth_tab1, auth_tab2 = st.tabs(["🔑 同學登入", "📝 新同學註冊"])

    with auth_tab1:
        with st.form("login_form"):
            login_sid = st.text_input("請輸入學號", placeholder="例如：B11321123")
            login_pass = st.text_input("請輸入密碼", type="password")
            btn_login = st.form_submit_button("進入二手市集")

            if btn_login:
                uni_found = login_user(login_sid, login_pass)
                if uni_found:
                    st.session_state.logged_in = True
                    st.session_state.student_id = login_sid
                    st.session_state.user_uni = uni_found
                    st.success(f"🎉 歡迎 {uni_found} 同學 ({login_sid}) 登入！正在跳轉...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 學號或密碼錯誤。（測試學號: B11321123 密碼: 1234）")

    with auth_tab2:
        reg_sid = st.text_input("註冊學號 *", placeholder="請輸入學號")
        reg_reg = st.selectbox("選擇學校所在區域 *", list(REGION_UNIVERSITY_MAP.keys()))
        reg_uni = st.selectbox("選擇您的所屬大學 *", REGION_UNIVERSITY_MAP[reg_reg])
        reg_line = st.text_input("輸入您的 LINE ID (面交聯絡使用) *", placeholder="例如：line12345")
        reg_pass = st.text_input("設定系統密碼 *", type="password")

        if st.button("註冊並領取 100 綠幣 🪙"):
            if not reg_sid or not reg_pass or not reg_line:
                st.warning("打 * 號欄位皆不可為空白！")
            elif register_user(reg_sid, reg_pass, reg_uni, reg_line):
                st.success("🎉 註冊成功！請切換至【同學登入】分頁進行登入。")
            else:
                st.error("❌ 該學號已存在。")

# ==========================================
# 4. 主功能區 (登入後解鎖)
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    my_line = get_user_line(current_student)

    default_region = "中部地區"
    for r, unis in REGION_UNIVERSITY_MAP.items():
        if current_uni in unis:
            default_region = r
            break

    with st.sidebar:
        st.title("🛍️ 我的市集帳戶")
        st.write(f"🏫 學校：**{current_uni}**")
        st.write(f"👤 學號：**{current_student}**")
        st.metric(label="我的綠色環保幣", value=f"{get_coins(current_student)} 🪙")
        st.write("---")
        st.subheader("💬 我的 LINE 聯絡設定")
        new_line_input = st.text_input("修改 LINE ID:", value=my_line)
        if st.button("💾 儲存 LINE 設定"):
            if update_user_line(current_student, new_line_input):
                st.success("LINE ID 已成功更新！")
                time.sleep(0.5)
                st.rerun()
        st.write("---")
        if st.button("🚪 登出系統", type="primary"):
            st.session_state.logged_in = False
            st.session_state.student_id = ""
            st.session_state.user_uni = ""
            st.rerun()

    # ------------------------------------------
    # 🔥 全方位二手市集：精美 6 大功能圖文選單面板
    # ------------------------------------------
    st.write("### 📱 雲科大 × 全國校園二手物資智慧交流選單")

    row1_c1, row1_c2, row1_c3 = st.columns(3)
    row2_c1, row2_c2, row2_c3 = st.columns(3)

    with row1_c1:
        if st.button("🔍 校園雜貨市集\n(挖寶各式生活好物)", use_container_width=True):
            st.session_state.current_menu = "🔍 校園雜貨市集"
    with row1_c2:
        if st.button("🚀 AI 智慧上架\n(衣服雜物課本一鍵賣)", use_container_width=True):
            st.session_state.current_menu = "🚀 AI 智慧上架"
    with row1_c3:
        if st.button("📜 我的拍賣攤位\n(管理上下架與買賣)", use_container_width=True):
            st.session_state.current_menu = "📜 我的拍賣攤位"

    with row2_c1:
        if st.button("🎁 綠幣好康福利\n(歐趴轉盤與誠信盲盒)", use_container_width=True):
            st.session_state.current_menu = "🎁 綠幣好康福利"
    with row2_c2:
        # 一鍵跳轉聯絡功能
        st.markdown(
            f'<a href="https://line.me/ti/p/~{my_line}" target="_blank" class="line-btn">💬 快速開啟 LINE 視窗 (測試對話)</a>',
            unsafe_allow_html=True)
    with row2_c3:
        # 校園常見安全面交地圖
        st.markdown(
            '<a href="https://maps.google.com" target="_blank" class="line-btn">📍 校園安全面交點 (推薦：圖書館/活動中心)</a>',
            unsafe_allow_html=True)

    st.write("---")
    st.success(f"📌 當前功能視窗：**{st.session_state.current_menu}**")

    # ------------------------------------------
    # 功能 1: 校園雜貨市集 (全方位物品篩選)
    # ------------------------------------------
    if st.session_state.current_menu == "🔍 校園雜貨市集":
        st.header("🌍 全國大學校園二手物資市集")

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            search_region = st.selectbox("📍 選擇學校區域", ["全部區域"] + list(REGION_UNIVERSITY_MAP.keys()),
                                         index=list(REGION_UNIVERSITY_MAP.keys()).index(default_region) + 1)
        with col_f2:
            if search_region == "全部區域":
                search_uni = st.selectbox("🏫 選擇大學", ["全部大學"])
            else:
                available_unis = REGION_UNIVERSITY_MAP[search_region]
                default_uni_idx = available_unis.index(current_uni) + 1 if current_uni in available_unis else 0
                search_uni = st.selectbox("🏫 選擇大學", ["該區全部大學"] + available_unis, index=default_uni_idx)
        with col_f3:
            search_cat = st.selectbox("📦 物品大類項目", PRODUCT_CATEGORIES)
        with col_f4:
            search_dept = st.selectbox("🎓 適用科系篩選 (選填，多用於書籍)", ["全部科系"] + YUNTECH_ALL_DEPTS)

        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        query = "SELECT id, image_base64, name, price, category, university, department, description, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"

        if search_region != "全部區域":
            if search_uni == "該區全部大學":
                uni_tuples = str(tuple(REGION_UNIVERSITY_MAP[search_region])).replace(',)', ')')
                query += f" AND university IN {uni_tuples}"
            else:
                query += f" AND university = '{search_uni}'"
        if search_cat != "全部類型":
            query += f" AND category = '{search_cat}'"
        if search_dept != "全部科系":
            query += f" AND department = '{search_dept}'"

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            st.info("💡 哇！目前這個分類還沒有寶物在售，快去【AI 智慧上架】清空個人空位吧！")
        else:
            for index, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1.2, 3, 1])
                    with c1:
                        if row['image_base64'] and row['image_base64'].startswith("data:image"):
                            st.image(row['image_base64'], width=130)
                        else:
                            st.write("📦 暫無商品實體照")
                    with c2:
                        st.subheader(f"[{row['id']}] {row['name']}")
                        st.write(f"📝 **物品狀況描述:** {row['description']}")
                        st.caption(f"🏫 學校: **{row['university']}** | 🎓 相關科系: **{row['department']}**")
                        st.caption(f"🏷️ 商品分類: **{row['category']}** | 👤 賣家同學學號: {row['seller_id']}")
                    with c3:
                        st.write(f"### 💰 ${row['price']:,.0f}")
                        st.success("🟢 上架在售中")
                    st.write("---")

        # 結帳與即時議價控制台
        st.write("### 🛒 快速購買與 AI 議價控制台")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            target_id = st.number_input("欲交易的二手物品 ID", min_value=1, step=1, key="bk_id")
        with col_t2:
            offer_price = st.number_input("出價金額 (向 AI 賣家砍價)", min_value=0, step=20, key="bk_offer")

        with col_t3:
            if st.button("🛍️ 確認原價購買", use_container_width=True):
                conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()
                if res and res[2] == '上架中':
                    if res[1] == current_student:
                        st.error("❌ 您不能購買自己拍賣的物品！")
                    else:
                        seller_sid = res[1]
                        seller_line = get_user_line(seller_sid)
                        cursor.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                       (current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 20)

                        st.balloons()
                        st.success(f"🎉 成功購入《{res[0]}》！")
                        st.markdown(f"### 💬 請立即點擊下方綠色按鈕直接跳轉 LINE 與賣家同學私訊面交：")
                        st.markdown(
                            f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 一鍵開啟 LINE 聯絡賣家 (ID: {seller_line})</a>',
                            unsafe_allow_html=True)
                else:
                    st.error("商品不存在或已被買走囉！")
                conn.close()

        with col_t4:
            if st.button("💬 與 AI 賣家智慧砍價", use_container_width=True):
                conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, price, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()
                if res and res[3] == '上架中':
                    p_name, orig_price, seller_sid = res[0], res[1], res[2]
                    if seller_sid == current_student:
                        st.error("❌ 別跟自己的商品玩心理戰！")
                    elif offer_price < orig_price * 0.5:
                        st.error(f"🤖 AI賣家：原價 ${orig_price} 砍到 ${offer_price} 太狠了，拒絕交易！😡")
                    elif offer_price >= orig_price * 0.8:
                        seller_line = get_user_line(seller_sid)
                        cursor.execute("UPDATE products SET status = '已售出', price = ?, buyer_id = ? WHERE id = ?",
                                       (offer_price, current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 25)

                        st.success(f"🤖 AI賣家：可以接受！以優惠價 ${offer_price} 元成交！")
                        st.markdown(f"### 💬 議價成功！點擊下方綠色按鈕直接跳轉至 LINE 預約面交：")
                        st.markdown(
                            f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 一鍵開啟 LINE 聯絡賣家 (ID: {seller_line})</a>',
                            unsafe_allow_html=True)
                    else:
                        st.warning(f"🤖 AI賣家：這價格虧太多，各退一步 ${(orig_price + offer_price) / 2:.0f} 元我就賣！")
                else:
                    st.error("該物件目前無法進行議價。")
                conn.close()

    # ------------------------------------------
    # 功能 2: AI 智慧上架 (全方位物品)
    # ------------------------------------------
    elif st.session_state.current_menu == "🚀 AI 智慧上架":
        st.header("🏪 全方位二手物品智慧上架中心")
        st.write(
            "輸入拍賣名稱與細節描述，AI 將自動為您歸類**「商品大類項目」**；如果是課本書籍，還會精確判定**「適用科系」**！")

        p_name = st.text_input("拍賣物資名稱", placeholder="例如：捷安特腳踏車 / 微積分第九版 / 宿舍小冰箱")
        p_price = st.number_input("欲售價格 (元)", min_value=0, value=150)
        p_reg = st.selectbox("🏫 選擇該物品主要交貨的大學區域", list(REGION_UNIVERSITY_MAP.keys()),
                             index=list(REGION_UNIVERSITY_MAP.keys()).index(default_region))
        p_uni = st.selectbox("🏫 適用/面交之目標大學？", REGION_UNIVERSITY_MAP[p_reg])
        p_desc = st.text_area("詳細物況/使用痕跡/規格說明",
                              placeholder="請輸入描述，例如：用了一學期、功能正常、無內頁劃記...")
        p_file = st.file_uploader("📸 上傳商品實體狀況照", type=['png', 'jpg', 'jpeg'])
        is_blind = st.checkbox("打包成「誠信盲盒」（名稱與圖片會被隱藏，直接投入盲盒抽獎池中）")

        if st.button("🚀 啟動 AI 智慧判定並發布上架"):
            if p_name and p_desc:
                b64_str = ""
                if p_file is not None:
                    img = Image.open(p_file)
                    img.thumbnail((300, 300))
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                # 執行 AI 智慧大類與科系判定
                category, target_dept = auto_classify_item(p_name, p_desc)
                carbon_saving = 800.0 + random.randint(50, 400)

                conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO products (name, price, category, university, department, description, is_blindbox, carbon_saving, image_base64, seller_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                p_name, p_price, category, p_uni, target_dept, p_desc, 1 if is_blind else 0, carbon_saving, b64_str,
                current_student))
                conn.commit()
                conn.close()

                modify_coins(current_student, 10)
                st.success(
                    f"🎉 上架發布成功！\n\n🤖 【AI 智慧判定歸類結果】:\n\n📦 物品大類：**{category}** \n\n🎓 關聯系所：**{target_dept}**")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("拍賣物品名稱與物況描述不可空白！")

    # ------------------------------------------
    # 功能 3: 綠幣好康福利
    # ------------------------------------------
    elif st.session_state.current_menu == "🎁 綠幣好康福利":
        st.header("🎰 綠色校園福利與誠信盲盒抽獎")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🎯 課業歐趴大轉盤")
            if st.button("🎰 消耗 20 綠幣轉動輪盤"):
                if get_coins(current_student) >= 20:
                    modify_coins(current_student, -20)
                    prizes = ["學辦免費美式咖啡券 ☕", "校園影印店 50 元折價券 📑", "期末歐趴糖 🍬",
                              "下學期必中籤幸運符 🍀"]
                    st.success(f"🎉 恭喜中獎！你獲得了：【{random.choice(prizes)}】")
                else:
                    st.error("❌ 您的環保綠幣不足 20 枚！")

        with col_g2:
            st.subheader("📦 跨校誠信物資盲盒")
            if st.button("🔮 支付 150 元隨機開啟一箱盲盒"):
                conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, image_base64, seller_id, university FROM products WHERE is_blindbox = 1 AND status = '上架中'")
                blind_items = cursor.fetchall()
                valid_blind_items = [item for item in blind_items if item[4] != current_student]

                if not valid_blind_items:
                    st.warning("📦 目前盲盒池裡暫時沒有其他同學投入的二手盲盒。")
                else:
                    chosen = random.choice(valid_blind_items)
                    seller_sid = chosen[4]
                    seller_line = get_user_line(seller_sid)

                    cursor.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                   (current_student, chosen[0]))
                    conn.commit()

                    st.success(
                        f"🎁 成功開箱！你抽中了來自【{chosen[5]}】同學投入的驚喜盲盒：\n\n**物品名稱:** {chosen[1]}\n\n**細節描述:** {chosen[2]}")
                    st.markdown(f"### 💬 點擊下方綠色按鈕跳轉 LINE 與原物主約定面交：")
                    st.markdown(
                        f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 一鍵開啟 LINE 聯絡賣家 (ID: {seller_line})</a>',
                        unsafe_allow_html=True)
                    if chosen[3] and chosen[3].startswith("data:image"):
                        st.image(chosen[3], width=200)
                    st.balloons()
                conn.close()

    # ------------------------------------------
    # 功能 4: 我的拍賣攤位 (交易歷史紀錄)
    # ------------------------------------------
    elif st.session_state.current_menu == "📜 我的拍賣攤位":
        st.header("📋 我的個人拍賣攤位與買賣清單")

        st.subheader("🛍️ 我成功掏寶買到的二手資產")
        st.caption("💡 點擊下方清單中賣家的 LINE ID 即可隨時私訊聯絡約面交。")

        conn = sqlite3.connect('streamlit_campus_market_v12.db', check_same_thread=False)
        query_buy = f'''
            SELECT p.id as 物品ID, p.name as 物品名稱, p.price as 價格, p.category as 分類, p.university as 來源學校, 
                   p.seller_id as 賣家學號, u.line_id as 賣家LINE_ID
            FROM products p
            LEFT JOIN users u ON p.seller_id = u.student_id
            WHERE p.buyer_id = '{current_student}'
        '''
        df_buy = pd.read_sql_query(query_buy, conn)
        if df_buy.empty:
            st.write("您目前還沒有買過任何商品喔。")
        else:
            st.dataframe(df_buy, use_container_width=True, hide_index=True)

        st.subheader("🏪 我賣出/上架的個人攤位紀錄")
        query_sell = f'''
            SELECT p.id as 物品ID, p.name as 物品名稱, p.price as 價格, p.category as 分類, p.university as 投放大學, 
                   p.status as 狀態, p.buyer_id as 買家學號, u.line_id as 買家LINE_ID
            FROM products p
            LEFT JOIN users u ON p.buyer_id = u.student_id
            WHERE p.seller_id = '{current_student}'
        '''
        df_sell = pd.read_sql_query(query_sell, conn)
        if df_sell.empty:
            st.write("您目前還沒有上架過任何個人二手商品。")
        else:
            st.dataframe(df_sell, use_container_width=True, hide_index=True)

        conn.close()