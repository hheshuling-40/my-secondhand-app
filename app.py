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
# 1. 資料庫初始化 (新增學校與科系欄位)
# ==========================================
def init_db():
    conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
    cursor = conn.cursor()

    # 用戶資料表 (student_id 作為主鍵)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            university TEXT NOT NULL,       -- 所屬學校
            green_coins INTEGER DEFAULT 100
        )
    ''')

    # 商品書本資料表 (新增大學、科系欄位)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,         -- 書籍 / 3C配件 / 學術講義
            university TEXT NOT NULL,       -- 書籍適用大學
            department TEXT NOT NULL,       -- 書籍適用科系
            description TEXT,
            status TEXT DEFAULT '上架中', 
            is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0,
            image_base64 TEXT,
            seller_id TEXT NOT NULL,
            buyer_id TEXT
        )
    ''')
    conn.commit()
    conn.close()


# AI 智慧科系與分類判定
def auto_classify_book(name, description):
    text = (name + " " + description).lower()

    # 判定大類別
    cat = "書籍"
    if "計算機" in text or "平板" in text or "計算機" in text:
        cat = "3C配件"
    elif "講義" in text or "筆記" in text or "考古題" in text:
        cat = "學術講義"

    # 判定科系
    dept = "不限科系/通識核心"
    dept_keywords = {
        "資訊工程/資管系": ["程式", "python", "java", "演算法", "資料結構", "網頁", "計算機概論", "計概", "ai",
                            "機器學習", "資安"],
        "電機/電子/自動化": ["電路", "電子學", "電磁", "訊號", "控制", "半導體", "工數", "工程數學"],
        "機械/土木/營建": ["力學", "材料力學", "流體", "熱力学", "繪圖", "cad", "工程圖學", "結構"],
        "化學/化工/材料": ["有機化學", "普化", "化工", "分析化學", "熱力學", "週期表"],
        "企業管理/財金/商管": ["經濟學", "會計", "統計學", "行銷", "管理學", "財務", "期貨", "投資"],
        "應用外語/文史哲": ["英文", "多益", "toeic", "文學", "哲學", "日文", "歷史", "翻譯"],
        "設計/建築/數位媒體": ["視覺", "色彩", "立體設計", "建築史", "排版", "photoshop", "插畫", "ui", "ux"]
    }

    for dept_name, keywords in dept_keywords.items():
        if any(word in text for word in keywords):
            dept = dept_name
            break

    # 如果包含共同必修
    if "微積分" in text or "普通物理" in text or "普物" in text or "國文" in text:
        dept = "不限科系/通識核心"

    return cat, dept


init_db()

# ==========================================
# 2. Session 狀態管理
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'user_uni' not in st.session_state:
    st.session_state.user_uni = ""


def login_user(student_id, password):
    conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT university FROM users WHERE student_id = ? AND password = ?", (student_id, password))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None


def register_user(student_id, password, university):
    try:
        conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (student_id, password, university, green_coins) VALUES (?, ?, ?, 100)",
                       (student_id, password, university))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_coins(student_id):
    conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(student_id, amount):
    conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ?", (amount, student_id))
    conn.commit()
    conn.close()


# ==========================================
# 3. 系統入口：學號與學校登入介面
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 全國大學二手教科書 AI 交流平台")
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
                    st.success(f"🎉 歡迎 {uni_found} 的同學 ({login_sid}) 登入系統！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 學號或密碼錯誤，請重新確認。")

    with auth_tab2:
        with st.form("register_form"):
            reg_sid = st.text_input("註冊學號", placeholder="請輸入您的學校學號")
            reg_uni = st.selectbox("選擇您的所屬大學", UNIVERSITY_LIST)
            reg_pass = st.text_input("設定系統密碼", type="password", placeholder="請牢記密碼")
            btn_reg = st.form_submit_button("註冊並領取 100 綠幣獎勵 🪙")

            if btn_reg:
                if not reg_sid or not reg_pass:
                    st.warning("學號與密碼為必填欄位！")
                elif register_user(reg_sid, reg_pass, reg_uni):
                    st.success(f"🎉 註冊成功！歡迎加入，請切換至登入分頁。")
                else:
                    st.error("❌ 該學號已存在，請直接登入。")

# ==========================================
# 4. 主程式功能（登入後解鎖）
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni

    # 側邊欄個人資訊
    with st.sidebar:
        st.title("📚 我的書香帳戶")
        st.write(f"🏫 學校：**{current_uni}**")
        st.write(f"👤 學號：**{current_student}**")
        coins = get_coins(current_student)
        st.metric(label="我的環保綠幣", value=f"{coins} 🪙")
        st.write("---")
        if st.button("🚪 登出系統", color="red"):
            st.session_state.logged_in = False
            st.session_state.student_id = ""
            st.session_state.user_uni = ""
            st.rerun()
        st.write("---")
        st.caption("🌱 平台小知識：\n傳承一本二手書，平均能為地球減少約 1.2 公斤的造紙與印刷碳排放物！")

    # 功能分頁 (新增科系與大學交叉搜尋)
    tab1, tab2, tab3, tab4 = st.tabs(["🛍️ 全國跨校市集挖寶", "🏪 智慧快速上架", "🎰 綠幣幸運抽獎", "📋 我的交易與書單"])

    # ------------------------------------------
    # TAB 1: 跨校市集挖寶 (核心升級：大學+科系精準搜尋)
    # ------------------------------------------
    with tab1:
        st.header("🌍 全國大學二手書交流市集")
        st.write("透過精準定位學校與科系，輕鬆找到教授指定的必修教科書！")

        # 篩選核心控制台
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_uni = st.selectbox("🏫 依大學篩選", ["全部大學"] + UNIVERSITY_LIST, index=UNIVERSITY_LIST.index(
                current_uni) + 1 if current_uni in UNIVERSITY_LIST else 0)
        with col_f2:
            search_dept = st.selectbox("🎓 依適用科系篩選", ["全部科系"] + DEPARTMENT_LIST)
        with col_f3:
            search_cat = st.selectbox("📦 物品類型", ["全部類型", "書籍", "3C配件", "學術講義"])

        # 從資料庫撈取尚未售出的書籍
        conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
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
            st.info("💡 哇！目前這個校系組合還沒有對應的書籍上架，快當第一個開拓者吧！")
        else:
            # 高質感圖文卡片清單
            for index, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1.2, 3, 1])
                    with c1:
                        if row['image_base64'] and row['image_base64'].startswith("data:image"):
                            st.image(row['image_base64'], width=140)
                        else:
                            st.write("📖 暫無書本外觀照")
                    with c2:
                        st.subheader(f"[{row['id']}] {row['name']}")
                        st.write(f"📝 **書況/筆記描述:** {row['description']}")
                        st.caption(f"🏫 學校: **{row['university']}** |  🎓 適用科系: **{row['department']}**")
                        st.caption(f"🏷️ 分類: {row['category']}  |  👤 賣家學號: {row['seller_id']}")
                    with c3:
                        st.write(f"### 💰 ${row['price']:,.0f}")
                        st.success("🟢 在售中")
                    st.write("---")

        # 交易控制台 (下單後直接下架消失)
        st.write("### 🛒 快速結帳與議價控制台")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            target_id = st.number_input("欲交易的書本 ID", min_value=1, step=1, key="bk_id")
        with col_t2:
            offer_price = st.number_input("出價金額 (向 AI 賣家砍價)", min_value=0, step=20, key="bk_offer")

        with col_t3:
            if st.button("🛍️ 確認原價購買", use_container_width=True):
                conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()

                if res and res[2] == '上架中':
                    if res[1] == current_student:
                        st.error("❌ 您不能購買自己上架的教科書！")
                    else:
                        cursor.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                       (current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 20)
                        st.success(f"🎉 成功購入《{res[0]}》！該書已從跨校市集自動下架！")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("找不到該商品或該書已被學弟妹買走下架囉！")
                conn.close()

        with col_t4:
            if st.button("💬 與 AI 賣家智慧砍價", use_container_width=True):
                conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, price, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()

                if res and res[3] == '上架中':
                    p_name, orig_price, seller_sid = res[0], res[1], res[2]
                    if seller_sid == current_student:
                        st.error("❌ 別跟自己的東西玩心理戰！")
                    elif offer_price < orig_price * 0.5:
                        st.error(f"🤖 AI賣家：這本原價可是 ${orig_price} 耶！出 ${offer_price} 太扯了，拒絕交易！😡")
                    elif offer_price >= orig_price * 0.8:
                        cursor.execute("UPDATE products SET status = '已售出', price = ?, buyer_id = ? WHERE id = ?",
                                       (offer_price, current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 25)
                        st.success(f"🤖 AI賣家：成交！看在同校系傳承的份上，以 ${offer_price} 元成交，書本已下架！")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.warning(f"🤖 AI賣家：不行啦，各退一步 ${(orig_price + offer_price) / 2:.0f} 元要不要？")
                else:
                    st.error("該書無法議價（可能已被下架）。")
                conn.close()

    # ------------------------------------------
    # TAB 2: 智慧快速上架 (新增選學校與科系)
    # ------------------------------------------
    with tab2:
        st.header("🏪 教科書智慧環保上架中心")
        st.write("輸入書名與描述，AI 系統會**自動幫您媒合推薦最符合的群組科系**，幫你省下大把時間！")

        with st.form("book_upload_form", clear_on_submit=True):
            p_name = st.text_input("書名 / 物品名稱", placeholder="例如：精簡微積分 第九版 Metric Version")
            p_price = st.number_input("欲售價格 (元)", min_value=0, value=250)

            # 自由選擇這本書適用於哪間大學！預設自動帶入賣家自己的學校
            p_uni = st.selectbox("🏫 這本書適用於哪間大學？", UNIVERSITY_LIST,
                                 index=UNIVERSITY_LIST.index(current_uni) if current_uni in UNIVERSITY_LIST else 0)

            p_desc = st.text_area("詳細物況/內頁劃記/教授姓名",
                                  placeholder="林老師大一必修用書，內頁只有少量鉛筆劃記，無破損...")
            p_file = st.file_uploader("📸 上傳書本實體封面照", type=['png', 'jpg', 'jpeg'])
            is_blind = st.checkbox("打包成「知識盲盒」（名稱圖片會被隱藏，直接投入盲盒抽獎機中）")

            submitted = st.form_submit_button("🚀 啟動 AI 判定並確認上架")

            if submitted:
                if p_name and p_desc:
                    b64_str = ""
                    if p_file is not None:
                        img = Image.open(p_file)
                        img.thumbnail((300, 300))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                    # 核心亮點：AI 自動判定類型與適合科系
                    category, department = auto_classify_book(p_name, p_desc)
                    carbon_saving = 1200.0 + random.randint(50, 300)  # 教科書循環平均減碳重

                    conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO products (name, price, category, university, department, description, is_blindbox, carbon_saving, image_base64, seller_id) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                    p_name, p_price, category, p_uni, department, p_desc, 1 if is_blind else 0, carbon_saving, b64_str,
                    current_student))
                    conn.commit()
                    conn.close()

                    modify_coins(current_student, 10)
                    st.success(f"🎉 上架成功！【AI 推薦指引】：自動精準分類至 👉「{department}」👈")
                    st.info(f"🌿 知識傳承成功！本次二手循環預估為地球省下 {carbon_saving:,.0f} 克的碳排放。")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("書名與物況描述不可空白！")

    # ------------------------------------------
    # TAB 3: 綠幣幸運抽獎 (維持盲盒娛樂性)
    # ------------------------------------------
    with tab3:
        st.header("🎰 綠色校園福利社")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🎯 課業歐趴大轉盤")
            st.write("每次抽獎消耗 **20 綠幣**")
            if st.button("🎰 點我轉動輪盤"):
                if get_coins(current_student) >= 20:
                    modify_coins(current_student, -20)
                    prizes = ["學辦免費美式咖啡券 ☕", "校園影印店 50 元折價券 📑", "期末歐趴糖 🍬",
                              "下學期必中籤幸運符 🍀"]
                    st.success(f"🎉 恭喜中獎！你獲得了：【{random.choice(prizes)}】")
                else:
                    st.error("❌ 你的綠幣不足 20 枚！")

        with col_g2:
            st.subheader("📦 跨校誠信知識盲盒")
            st.write("用一口價 **$150 元** 隨機抽取各校學長姐留下來的「神秘二手用書」！")
            if st.button("🔮 支付 150 元開啟知識盲盒"):
                conn = sqlite3.connect('streamlit_national_books.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.