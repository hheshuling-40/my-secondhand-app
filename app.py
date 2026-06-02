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
# 0. 全國大學（依北中南東區域分類）與科系常用清單
# ==========================================
REGION_UNIVERSITY_MAP = {
    "北部地區": [
        "國立台灣大學", "國立清華大學", "國立陽明交通大學", "國立臺北科技大學",
        "國立台灣科技大學", "國立中央大學", "國立政治大學", "淡江大學",
        "輔仁大學", "東吳大學", "銘傳大學", "中原大學", "其他北部大學"
    ],
    "中部地區": [
        "國立雲林科技大學", "國立中興大學", "逢甲大學", "東海大學",
        "中國醫藥大學", "靜宜大學", "大葉大學", "國立彰化師範大學", "其他中部大學"
    ],
    "南部地區": [
        "國立成功大學", "國立中山大學", "國立中正大學", "國立高雄科技大學",
        "國立屏東科技大學", "義守大學", "長榮大學", "其他南部大學"
    ],
    "東部與離島": [
        "國立東華大學", "國立宜蘭大學", "國立台東大學", "慈濟大學", "其他東部離島大學"
    ]
}

# 攤平成一個完整的清單，方便資料庫比對與舊資料相容
ALL_UNIVERSITIES = []
for unis in REGION_UNIVERSITY_MAP.values():
    ALL_UNIVERSITIES.extend(unis)

DEPARTMENT_LIST = [
    "不限科系/通識核心", "資訊工程/資管系", "電機/電子/自動化", "機械/土木/營建",
    "化學/化工/材料", "企業管理/財金/商管", "應用外語/文史哲", "設計/建築/數位媒體"
]


# ==========================================
# 1. 資料庫智慧初始化
# ==========================================
def init_db():
    try:
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
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
        # 預先塞入雲科大測試帳號
        cursor.execute(
            "INSERT OR IGNORE INTO users (student_id, password, university, line_id, green_coins) VALUES ('B11321123', '1234', '國立雲林科技大學', 'yuntech_cool', 100)")
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"資料庫初始化失敗，錯誤原因: {e}")


def auto_classify_book(name, description):
    text = (name + " " + description).lower()
    cat = "書籍"
    if "講義" in text or "筆記" in text or "考古題" in text:
        cat = "學術講義"
    elif "計算機" in text or "平板" in text or "耳機" in text:
        cat = "3C配件"

    dept = "不限科系/通識核心"
    dept_keywords = {
        "資訊工程/資管系": ["程式", "python", "java", "演算法", "資料結構", "網頁", "計概", "ai", "資安", "資管"],
        "電機/電子/自動化": ["電路", "電子學", "電磁", "訊號", "控制", "工數", "工程數學"],
        "機械/土木/營建": ["力學", "流體", "熱力学", "繪圖", "cad", "工程圖學", "營建"],
        "化學/化工/材料": ["有機化學", "普化", "化工", "材料", "化學"],
        "企業管理/財金/商管": ["經濟學", "會計", "統計學", "行銷", "管理學", "財務", "企管"],
        "應用外語/文史哲": ["英文", "多益", "toeic", "文學", "哲學", "日文", "外語"],
        "設計/建築/數位媒體": ["視覺", "色彩", "排版", "photoshop", "建築史", "ui", "ux", "設計"]
    }
    for dept_name, keywords in dept_keywords.items():
        if any(word in text for word in keywords):
            dept = dept_name
            break
    if "微積分" in text or "普通物理" in text or "國文" in text:
        dept = "不限科系/通識核心"
    return cat, dept


init_db()

# ==========================================
# 2. Session 狀態與核心操作
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'user_uni' not in st.session_state:
    st.session_state.user_uni = ""


def login_user(student_id, password):
    try:
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT university FROM users WHERE student_id = ? AND password = ?", (student_id, password))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except:
        return None


def register_user(student_id, password, university, line_id):
    try:
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
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
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else "未填寫"
    except:
        return "未填寫"


def update_user_line(student_id, new_line):
    try:
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET line_id = ? WHERE student_id = ?", (new_line, student_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_coins(student_id):
    try:
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0
    except:
        return 0


def modify_coins(student_id, amount):
    try:
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ?", (amount, student_id))
        conn.commit()
        conn.close()
    except:
        pass


# ==========================================
# 3. 畫面渲染：登入 / 註冊系統
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 全國大學二手教科書 AI 智慧交流平台")
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
                    st.success(f"🎉 歡迎 {uni_found} 同學 ({login_sid}) 登入！正在跳轉...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 學號或密碼錯誤。（提示：可使用學號 B11321123 密碼 1234 進行測試）")

    with auth_tab2:
        # 註冊表單：不使用 st.form 以確保北中南東下拉連動能即時觸發
        reg_sid = st.text_input("註冊學號 *", placeholder="請輸入學號")

        # 級聯選擇：先選區域，再選大學
        reg_reg = st.selectbox("選擇學校所在區域 *", list(REGION_UNIVERSITY_MAP.keys()))
        reg_uni = st.selectbox("選擇您的所屬大學 *", REGION_UNIVERSITY_MAP[reg_reg])

        reg_line = st.text_input("輸入您的 LINE ID (以便買家後續面交聯絡) *", placeholder="例如：line12345")
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

    # 判斷目前使用者的學校在哪個區域，設定市集的預設選單
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
        if st.button("🚪 登出系統", color="red"):
            st.session_state.logged_in = False
            st.session_state.student_id = ""
            st.session_state.user_uni = ""
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["🛍️ 全國跨校市集挖寶", "🏪 智慧快速上架", "🎰 綠幣幸運抽獎", "📋 我的交易與書單"])

    # ------------------------------------------
    # TAB 1: 跨校市集挖寶 (支援北中南東區域級聯篩選)
    # ------------------------------------------
    with tab1:
        st.header("🌍 全國大學二手書交流市集")

        # 頂部多條件連動篩選區
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            search_region = st.selectbox("📍 選擇學校區域", ["全部區域"] + list(REGION_UNIVERSITY_MAP.keys()),
                                         index=list(REGION_UNIVERSITY_MAP.keys()).index(default_region) + 1)
        with col_f2:
            if search_region == "全部區域":
                search_uni = st.selectbox("🏫 選擇大學", ["全部大學"])
            else:
                # 取得該區域的大學，並預設選到同學自己的學校
                available_unis = REGION_UNIVERSITY_MAP[search_region]
                default_uni_idx = available_unis.index(current_uni) + 1 if current_uni in available_unis else 0
                search_uni = st.selectbox("🏫 選擇大學", ["該區全部大學"] + available_unis, index=default_uni_idx)
        with col_f3:
            search_dept = st.selectbox("🎓 依適用科系篩選", ["全部科系"] + DEPARTMENT_LIST)
        with col_f4:
            search_cat = st.selectbox("📦 物品類型", ["全部類型", "書籍", "3C配件", "學術講義"])

        # SQL 資料庫智慧動態撈取
        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        query = "SELECT id, image_base64, name, price, category, university, department, description, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"

        # 區域與學校組合邏輯篩選
        if search_region != "全部區域":
            if search_uni == "該區全部大學":
                # 串接該區所有的大學名稱放到 SQL IN 中
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
            st.info("💡 哇！目前這個校系區域組合還沒有對應的書籍在售，快去【智慧快速上架】當第一個人吧！")
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
                        st.caption(f"🏫 學校: **{row['university']}** |  🎓 科系: **{row['department']}**")
                        st.caption(f"🏷️ 分類: {row['category']}  |  👤 賣家同學: {row['seller_id']}")
                    with c3:
                        st.write(f"### 💰 ${row['price']:,.0f}")
                        st.success("🟢 在售中")
                    st.write("---")

        # 交易控制台
        st.write("### 🛒 快速結帳與議價控制台")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            target_id = st.number_input("欲交易的書本 ID", min_value=1, step=1, key="bk_id")
        with col_t2:
            offer_price = st.number_input("出價金額 (向 AI 賣家砍價)", min_value=0, step=20, key="bk_offer")

        with col_t3:
            if st.button("🛍️ 確認原價購買", use_container_width=True):
                conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
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
                        st.success(f"🎉 成功購入《{res[0]}》！商品已從市集下架！")
                        st.markdown(f"### 💬 請立即加賣家學長姐的 LINE 預約面交：")
                        st.info(f"👤 **賣家學號:** {seller_sid} \n\n 🆔 **賣家 LINE ID:** {seller_line}")
                        st.markdown(f"[點我快速開啟 LINE 加好友](https://line.me/ti/p/~{seller_line})")

                        if st.button("確認並重整市集頁面"):
                            st.rerun()
                else:
                    st.error("商品不存在或已被買走下架囉！")
                conn.close()

        with col_t4:
            if st.button("💬 與 AI 賣家智慧砍價", use_container_width=True):
                conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, price, seller_id, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()
                if res and res[3] == '上架中':
                    p_name, orig_price, seller_sid = res[0], res[1], res[2]
                    if seller_sid == current_student:
                        st.error("❌ 別跟自己的商品玩心理戰！")
                    elif offer_price < orig_price * 0.5:
                        st.error(f"🤖 AI賣家：這本原價 ${orig_price} 耶！出 ${offer_price} 太少，拒絕交易！😡")
                    elif offer_price >= orig_price * 0.8:
                        seller_line = get_user_line(seller_sid)
                        cursor.execute("UPDATE products SET status = '已售出', price = ?, buyer_id = ? WHERE id = ?",
                                       (offer_price, current_student, target_id))
                        conn.commit()
                        modify_coins(current_student, 25)

                        st.success(f"🤖 AI賣家：成交！以 ${offer_price} 元出售並成功下架！")
                        st.markdown(f"### 💬 議價成功！請立即加賣家 LINE 預約面交：")
                        st.info(f"👤 **賣家學號:** {seller_sid} \n\n 🆔 **賣家 LINE ID:** {seller_line}")
                        st.markdown(f"[點我快速開啟 LINE 加好友](https://line.me/ti/p/~{seller_line})")

                        if st.button("收下划算二手書，重整市集"):
                            st.rerun()
                    else:
                        st.warning(f"🤖 AI賣家：不行啦，各退一步 ${(orig_price + offer_price) / 2:.0f} 元要不要？")
                else:
                    st.error("該書目前無法議價。")
                conn.close()

    # ------------------------------------------
    # TAB 2: 智慧快速上架 (亦改為北中南東級聯選擇學校)
    # ------------------------------------------
    with tab2:
        st.header("🏪 教科書智慧環保上架中心")
        st.write("輸入書名，系統將經由 AI 自動為您推薦適合的「群組科系」分類！")

        p_name = st.text_input("書名 / 物品名稱", placeholder="例如：精簡微積分 第九版 Metric Version")
        p_price = st.number_input("欲售價格 (元)", min_value=0, value=250)

        # 上架學校選擇也同步改為 區域 -> 學校
        p_reg = st.selectbox("🏫 選擇該書適用學校的區域", list(REGION_UNIVERSITY_MAP.keys()),
                             index=list(REGION_UNIVERSITY_MAP.keys()).index(default_region))
        p_uni = st.selectbox("🏫 這本書適用於哪間大學？", REGION_UNIVERSITY_MAP[p_reg])

        p_desc = st.text_area("詳細物況/內頁劃記/教授姓名", placeholder="微積分必修用書，內頁只有少量鉛筆劃記...")
        p_file = st.file_uploader("📸 上傳書本實體封面照", type=['png', 'jpg', 'jpeg'])
        is_blind = st.checkbox("打包成「知識盲盒」（名稱圖片會被隱藏，直接投入盲盒抽獎機中）")

        if st.button("🚀 啟動 AI 判定並確認上架"):
            if p_name and p_desc:
                b64_str = ""
                if p_file is not None:
                    img = Image.open(p_file)
                    img.thumbnail((300, 300))
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                category, department = auto_classify_book(p_name, p_desc)
                carbon_saving = 1200.0 + random.randint(50, 300)

                conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
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
                st.success(f"🎉 上架成功！【AI 自動判定科系】：👉「{department}」👈！")
                time.sleep(1)
                st.rerun()
            else:
                st.error("書名與物況描述不可空白！")

    # ------------------------------------------
    # TAB 3: 綠幣幸運抽獎
    # ------------------------------------------
    with tab3:
        st.header("🎰 綠色校園福利社")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🎯 課業歐趴大轉盤")
            if st.button("🎰 點我轉動輪盤 (消耗 20 綠幣)"):
                if get_coins(current_student) >= 20:
                    modify_coins(current_student, -20)
                    prizes = ["學辦免費美式咖啡券 ☕", "校園影印店 50 元折價券 📑", "期末歐趴糖 🍬",
                              "下學期必中籤幸運符 🍀"]
                    st.success(f"🎉 恭喜中獎！你獲得了：【{random.choice(prizes)}】")
                else:
                    st.error("❌ 你的綠幣不足 20 枚！")

        with col_g2:
            st.subheader("📦 跨校誠信知識盲盒")
            if st.button("🔮 支付 150 元開啟知識盲盒"):
                conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, image_base64, seller_id, university FROM products WHERE is_blindbox = 1 AND status = '上架中'")
                blind_items = cursor.fetchall()
                valid_blind_items = [item for item in blind_items if item[4] != current_student]

                if not valid_blind_items:
                    st.warning("📦 目前盲盒池裡沒有其他同學的盲盒。")
                else:
                    chosen = random.choice(valid_blind_items)
                    seller_sid = chosen[4]
                    seller_line = get_user_line(seller_sid)

                    cursor.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                   (current_student, chosen[0]))
                    conn.commit()

                    st.success(
                        f"🎁 成功開箱！你抽中了來自【{chosen[5]}】學長姐的珍藏：\n\n**書名:** {chosen[1]}\n\n**細節:** {chosen[2]}")
                    st.info(
                        f"📢 盲盒開箱完畢！請加學長姐 LINE 面交：\n\n👤 **賣家學號:** {seller_sid} | 🆔 **LINE ID:** {seller_line}")
                    if chosen[3] and chosen[3].startswith("data:image"):
                        st.image(chosen[3], width=200)
                    st.balloons()

                    if st.button("收下盲盒並記錄"):
                        st.rerun()
                conn.close()

    # ------------------------------------------
    # TAB 4: 個人書產交易清單
    # ------------------------------------------
    with tab4:
        st.header("📋 我的個人校園交易清單")

        st.subheader("🛍️ 我成功挖寶買到的書籍 (已自動從市集下架)")
        st.caption("💡 溫馨提示：這裡可以直接隨時查詢對方的 LINE 喔！")

        conn = sqlite3.connect('streamlit_national_books_v7.db', check_same_thread=False)
        query_buy = f'''
            SELECT p.id as 書本ID, p.name as 書名, p.price as 價格, p.university as 來源大學, 
                   p.department as 適用科系, p.seller_id as 賣家學號, u.line_id as 賣家LINE_ID
            FROM products p
            LEFT JOIN users u ON p.seller_id = u.student_id
            WHERE p.buyer_id = '{current_student}'
        '''
        df_buy = pd.read_sql_query(query_buy, conn)
        if df_buy.empty:
            st.write("您目前還沒有買過書籍喔。")
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
            st.write("您目前還沒有上架過任何書籍。")
        else:
            st.dataframe(df_sell, use_container_width=True, hide_index=True)

        conn.close()