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
# 0. 全國大學區域分類 & 雲科大專屬科系清單 (全面去學院化)
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

YUNTECH_ALL_DEPTS = [
    "不限科系/共同通識核心",
    "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系", "化學工程與材料工程系",
    "環境與安全衛生工程系", "工程科技菁英班",
    "工業設計系", "視覺傳達設計系", "數位媒體設計系", "創意生活設計系", "建築與室內設計系", "跨域整合設計學士學位學程",
    "企業管理系", "財務金融系", "會計系", "資訊管理系", "工業工程與管理系", "國際管理學士學位學程",
    "應用外語系", "文化資產維護系",
    "前瞻學士學位學程", "產業科技學士學位學程"
]


# ==========================================
# 1. 資料庫初始化
# ==========================================
def init_db():
    try:
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
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


# AI 根據書名關鍵字智慧判定推薦科系
def auto_classify_book(name, description):
    text = (name + " " + description).lower()
    dept = "不限科系/共同通識核心"
    cat = "書籍"

    if "講義" in text or "筆記" in text or "考古題" in text:
        cat = "學術講義"
    elif "計算機" in text or "平板" in text or "工程計算機" in text:
        cat = "3C配件"

    mapping = {
        "資訊工程系": ["程式", "python", "java", "演算法", "資料結構", "網頁", "資工", "作業系統"],
        "電機工程系": ["電路", "電子學", "電磁", "訊號", "電機", "電力"],
        "機械工程系": ["熱力", "流體", "靜力", "動力", "機械", "繪圖"],
        "化學工程與材料工程系": ["有機化學", "普化", "化工", "材料工程", "質能均衡"],
        "營建工程系": ["土木", "營建", "結構學", "測量學", "混凝土"],
        "視覺傳達設計系": ["視覺", "色彩", "排版", "視傳", "平面設計"],
        "數位媒體設計系": ["動畫", "遊戲", "特效", "剪輯", "數媒", "3dsmax"],
        "工業設計系": ["工設", "產品設計", "模型", "人因工程"],
        "建築與室內設計系": ["建築史", "室內設計", "空間規劃", "透視圖"],
        "企業管理系": ["管理學", "行銷", "企管", "組織行為"],
        "財務金融系": ["投資", "金融", "財金", "證券"],
        "會計系": ["會計", "審計", "成管會", "稅務"],
        "資訊管理系": ["資管", "資料庫", "mis", "系統分析"],
        "應用外語系": ["英文", "多益", "toeic", "聽力", "應外"],
        "文化資產維護系": ["文資", "古蹟", "歷史", "修復"]
    }

    for dp, keywords in mapping.items():
        if any(word in text for word in keywords):
            dept = dp
            break

    return cat, dept


init_db()

# ==========================================
# 2. Session 狀態
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'user_uni' not in st.session_state:
    st.session_state.user_uni = ""
# 預設首頁進入「課本挖寶市集」
if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "🔍 課本挖寶市集"


def login_user(student_id, password):
    try:
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT university FROM users WHERE student_id = ? AND password = ?", (student_id, password))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except:
        return None


def register_user(student_id, password, university, line_id):
    try:
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
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
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else "未填寫"
    except:
        return "未填寫"


def update_user_line(student_id, new_line):
    try:
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET line_id = ? WHERE student_id = ?", (new_line, student_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_coins(student_id):
    try:
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0
    except:
        return 0


def modify_coins(student_id, amount):
    try:
        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
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
    st.title("🔐 全國大學二手教科書 AI 智慧交流平台")
    st.subheader("開學挖寶、畢業減碳，直達各校系必修用書")

    auth_tab1, auth_tab2 = st.tabs(["🔑 同學登入", "📝 新同學註冊"])

    with auth_tab1:
        with st.form("login_form"):
            login_sid = st.text_input("請輸入學號", placeholder="例如：B11321123")
            login_pass = st.text_input("請輸入密碼", type="password")
            btn_login = st.form_submit_button("立即進入市集")

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
                    st.error("❌ 學號或密碼錯誤。（提示：可使用學號 B11321123 密碼 1234 進行測試）")

    with auth_tab2:
        reg_sid = st.text_input("註冊學號 *", placeholder="請輸入學號")
        reg_reg = st.selectbox("選擇學校所在區域 *", list(REGION_UNIVERSITY_MAP.keys()))
        reg_uni = st.selectbox("選擇您的所屬大學 *", REGION_UNIVERSITY_MAP[reg_reg])
        reg_line = st.text_input("輸入您的 LINE ID (買家聯繫面交使用) *", placeholder="例如：line12345")
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

    # 側邊欄個人資訊
    with st.sidebar:
        st.title("📚 我的書香帳戶")
        st.write(f"🏫 學校：**{current_uni}**")
        st.write(f"👤 學號：**{current_student}**")
        st.metric(label="我的環保綠幣", value=f"{get_coins(current_student)} 🪙")
        st.write("---")
        st.subheader("💬 我的 LINE 聯絡設定")
        new_line_input = st.text_input("隨時修改我的 LINE ID:", value=my_line)
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
    # 🔥 二手書專屬：智慧圖文方格選單面板 (模擬 LINE 介面)
    # ------------------------------------------
    st.write("### 📱 雲科大 × 全國二手書 AI 智慧交流選單")

    row1_c1, row1_c2, row1_c3 = st.columns(3)
    row2_c1, row2_c2, row2_c3 = st.columns(3)

    with row1_c1:
        if st.button("🔍 課本挖寶市集\n(尋找各系必修書)", use_container_width=True):
            st.session_state.current_menu = "🔍 課本挖寶市集"
    with row1_c2:
        if st.button("🚀 AI 智慧上架\n(免手動極速賣書)", use_container_width=True):
            st.session_state.current_menu = "🚀 AI 智慧上架"
    with row1_c3:
        if st.button("📜 我的個人書產\n(追蹤買賣與歷史)", use_container_width=True):
            st.session_state.current_menu = "📜 我的個人書產"

    with row2_c1:
        if st.button("🎁 綠幣好康抽獎\n(歐趴糖與誠信盲盒)", use_container_width=True):
            st.session_state.current_menu = "🎁 綠幣好康抽獎"
    with row2_c2:
        # 模擬快速與賣家對話的跳轉
        st.markdown(
            f'<a href="https://line.me/ti/p/~{my_line}" target="_blank" class="line-btn">💬 快速開啟 LINE 視窗 (查看我自己的狀態)</a>',
            unsafe_allow_html=True)
    with row2_c3:
        # 校園常見安全面交點
        st.markdown(
            '<a href="https://maps.google.com" target="_blank" class="line-btn">📍 校園安全面交點 (推薦：圖書館前)</a>',
            unsafe_allow_html=True)

    st.write("---")
    st.success(f"📌 當前功能視窗：**{st.session_state.current_menu}**")

    # ------------------------------------------
    # 功能 1: 課本挖寶市集 (純科系篩選)
    # ------------------------------------------
    if st.session_state.current_menu == "🔍 課本挖寶市集":
        st.header("🌍 全國大學二手書交流市集")

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
            search_dept = st.selectbox("🎓 選擇適用科系", ["全部科系"] + YUNTECH_ALL_DEPTS)
        with col_f4:
            search_cat = st.selectbox("📦 物品類型", ["全部類型", "書籍", "3C配件", "學術講義"])

        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
        query = "SELECT id, image_base64, name, price, category, university, department, description, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"

        if search_region != "全部區域":
            if search_uni == "該區全部大學":
                uni_tuples = str(tuple(REGION_UNIVERSITY_MAP[search_region])).replace(',)', ')')
                query += f" AND university IN {uni_tuples}"
            else:
                query += f" AND university = '{search_uni}'"
        if search_dept != "全部科系":
            query += f" AND department = '{search_dept}'"
        if search_cat != "全部類型":
            query += f" AND category = '{search_cat}'"

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            st.info("💡 哇！目前這個組合還沒有對應的課本在售，快去【AI 智慧上架】造福學弟妹吧！")
        else:
            for index, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1.2, 3, 1])
                    with c1:
                        if row['image_base64'] and row['image_base64'].startswith("data:image"):
                            st.image(row['image_base64'], width=130)
                        else:
                            st.write("📖 暫無書本外觀照")
                    with c2:
                        st.subheader(f"[{row['id']}] {row['name']}")
                        st.write(f"📝 **書況描述:** {row['description']}")
                        st.caption(f"🏫 學校: **{row['university']}** | 🎓 適用系所: **{row['department']}**")
                        st.caption(f"🏷️ 分類: {row['category']} | 👤 賣家學長姐: {row['seller_id']}")
                    with c3:
                        st.write(f"### 💰 ${row['price']:,.0f}")
                        st.success("🟢 在售中")
                    st.write("---")

        # 結帳與即時議價控制台
        st.write("### 🛒 快速購買與 AI 議價控制台")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            target_id = st.number_input("欲交易的書本 ID", min_value=1, step=1, key="bk_id")
        with col_t2:
            offer_price = st.number_input("出價金額 (向 AI 賣家砍價)", min_value=0, step=20, key="bk_offer")

        with col_t3:
            if st.button("🛍️ 確認原價購買", use_container_width=True):
                conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()
                if res and res[2] == '上架中':
                    if res[1] == current_student:
                        st.error("❌ 您不能購買自己上架的書！")
                    else:
                        seller_sid = res[1]
                        seller_line = get_user_line(seller_sid)
                        cursor.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                       (current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 20)

                        st.balloons()
                        st.success(f"🎉 成功購入《{res[0]}》！")
                        st.markdown(f"### 💬 請立即點擊下方綠色按鈕跳轉 LINE 預約面交：")
                        st.markdown(
                            f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 開啟 LINE 聯絡賣家 (ID: {seller_line})</a>',
                            unsafe_allow_html=True)
                else:
                    st.error("商品不存在或已被買走下架囉！")
                conn.close()

        with col_t4:
            if st.button("💬 與 AI 賣家智慧砍價", use_container_width=True):
                conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, price, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()
                if res and res[3] == '上架中':
                    p_name, orig_price, seller_sid = res[0], res[1], res[2]
                    if seller_sid == current_student:
                        st.error("❌ 別跟自己的商品玩心理戰！")
                    elif offer_price < orig_price * 0.5:
                        st.error(f"🤖 AI賣家：原價 ${orig_price} 砍到 ${offer_price} 太誇張了，拒絕出價！😡")
                    elif offer_price >= orig_price * 0.8:
                        seller_line = get_user_line(seller_sid)
                        cursor.execute("UPDATE products SET status = '已售出', price = ?, buyer_id = ? WHERE id = ?",
                                       (offer_price, current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 25)

                        st.success(f"🤖 AI賣家：可以接受！以甜甜價 ${offer_price} 元成交！")
                        st.markdown(f"### 💬 議價成功！點擊下方綠色按鈕直接跳轉至 LINE 面交：")
                        st.markdown(
                            f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 開啟 LINE 聯絡賣家 (ID: {seller_line})</a>',
                            unsafe_allow_html=True)
                    else:
                        st.warning(f"🤖 AI賣家：這價格不行啦，各退一步 ${(orig_price + offer_price) / 2:.0f} 元我就賣！")
                else:
                    st.error("該書目前無法議價。")
                conn.close()

    # ------------------------------------------
    # 功能 2: AI 智慧上架
    # ------------------------------------------
    elif st.session_state.current_menu == "🚀 AI 智慧上架":
        st.header("🏪 教科書智慧環保上架中心")
        st.write("免去複雜的手動選擇！輸入書名與課文描述，AI 系統會自動為您精確分類對應的**「適用科系」**！")

        p_name = st.text_input("書名 / 物品名稱", placeholder="例如：精簡微積分 第九版 或 視覺傳達設計基礎")
        p_price = st.number_input("欲售價格 (元)", min_value=0, value=250)
        p_reg = st.selectbox("🏫 選擇該書適用學校的區域", list(REGION_UNIVERSITY_MAP.keys()),
                             index=list(REGION_UNIVERSITY_MAP.keys()).index(default_region))
        p_uni = st.selectbox("🏫 這本書適用於哪間大學？", REGION_UNIVERSITY_MAP[p_reg])
        p_desc = st.text_area("詳細物況/內頁劃記/教授姓名",
                              placeholder="請輸入描述，內含關鍵字（如：程式、會計、電路）能讓 AI 判定更準喔...")
        p_file = st.file_uploader("📸 上傳書本實體封面照", type=['png', 'jpg', 'jpeg'])
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

                # 執行 AI 智慧判定
                category, target_dept = auto_classify_book(p_name, p_desc)
                carbon_saving = 1200.0 + random.randint(50, 300)

                conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
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
                st.success(f"🎉 上架成功！\n\n🤖 【AI 智慧判定系統分類結果】 👉 推薦系所：**{target_dept}** 👈")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("書名與物況描述不可空白！")

    # ------------------------------------------
    # 功能 3: 綠幣好康抽獎
    # ------------------------------------------
    elif st.session_state.current_menu == "🎁 綠幣好康抽獎":
        st.header("🎰 綠色校園福利與盲盒抽獎")
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
            st.subheader("📦 跨校誠信知識盲盒")
            if st.button("🔮 支付 150 元隨機開啟一箱盲盒"):
                conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, image_base64, seller_id, university FROM products WHERE is_blindbox = 1 AND status = '上架中'")
                blind_items = cursor.fetchall()
                valid_blind_items = [item for item in blind_items if item[4] != current_student]

                if not valid_blind_items:
                    st.warning("📦 目前盲盒池裡暫時沒有其他同學投入的書籍盲盒。")
                else:
                    chosen = random.choice(valid_blind_items)
                    seller_sid = chosen[4]
                    seller_line = get_user_line(seller_sid)

                    cursor.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                   (current_student, chosen[0]))
                    conn.commit()

                    st.success(
                        f"🎁 成功開箱！你抽中了來自【{chosen[5]}】學長姐的珍藏書籍：\n\n**書名:** {chosen[1]}\n\n**細節描述:** {chosen[2]}")
                    st.markdown(f"### 💬 點擊下方綠色按鈕跳轉 LINE 與原書主面交：")
                    st.markdown(
                        f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn">💬 開啟 LINE 聯絡賣家 (ID: {seller_line})</a>',
                        unsafe_allow_html=True)
                    if chosen[3] and chosen[3].startswith("data:image"):
                        st.image(chosen[3], width=200)
                    st.balloons()
                conn.close()

    # ------------------------------------------
    # 功能 4: 我的個人書產 (交易紀錄)
    # ------------------------------------------
    elif st.session_state.current_menu == "📜 我的個人書產":
        st.header("📋 我的個人校園交易與資產清單")

        st.subheader("🛍️ 我成功挖寶買到的書籍")
        st.caption("💡 點擊下方清單中賣家的 LINE ID 即可隨時開啟對話面交。")

        conn = sqlite3.connect('streamlit_books_v11.db', check_same_thread=False)
        query_buy = f'''
            SELECT p.id as 書本ID, p.name as 書名, p.price as 價格, p.university as 來源大學, 
                   p.department as 適用科系, p.seller_id as 賣家學號, u.line_id as 賣家LINE_ID
            FROM products p
            LEFT JOIN users u ON p.seller_id = u.student_id
            WHERE p.buyer_id = '{current_student}'
        '''
        df_buy = pd.read_sql_query(query_buy, conn)
        if df_buy.empty:
            st.write("您目前還沒有買過任何二手書喔。")
        else:
            st.dataframe(df_buy, use_container_width=True, hide_index=True)

        st.subheader("🏪 我賣出/上架的書籍紀錄清單")
        query_sell = f'''
            SELECT p.id as 書本ID, p.name as 書名, p.price as 價格, p.university as 目標大學, 
                   p.department as 適用科系, p.status as 狀態, p.buyer_id as 買家學號, u.line_id as 買家LINE_ID
            FROM products p
            LEFT JOIN users u ON p.buyer_id = u.student_id
            WHERE p.seller_id = '{current_student}'
        '''
        df_sell = pd.read_sql_query(query_sell, conn)
        if df_sell.empty:
            st.write("您目前還沒有上架過任何書籍資產。")
        else:
            st.dataframe(df_sell, use_container_width=True, hide_index=True)

        conn.close()