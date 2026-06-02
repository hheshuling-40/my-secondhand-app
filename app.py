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
# 🎨 網美級極簡高質感 UI 視覺工程 (CSS)
# ==========================================
st.markdown("""
<style>
    /* 全域字體與背景柔化 */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* 頂部主標題美化 */
    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #212529;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 16px;
        color: #6c757d;
        margin-bottom: 25px;
    }

    /* LINE 快捷功能按鈕 - 現代化極簡風 */
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
    .line-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.1);
        color: #ffffff !important;
    }

    /* 綠色專屬 LINE 按鈕 */
    .line-green-btn {
        background: linear-gradient(135deg, #06C755 0%, #05b34c 100%) !important;
        color: white !important;
    }

    /* 6大功能選單按鈕美化 */
    .stButton>button {
        height: 65px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        border: none !important;
        background-color: #ffffff !important;
        color: #495057 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background-color: #f1f3f5 !important;
        color: #06C755 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.06);
    }
    .stButton>button:active {
        transform: translateY(0px);
    }

    /* 商品網格卡片樣式 */
    .product-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    .product-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        transform: translateY(-3px);
    }

    /* 價格大字美化 */
    .price-tag {
        font-size: 24px;
        font-weight: 700;
        color: #212529;
        font-family: 'Courier New', Courier, monospace;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 地圖與常數設定
# ==========================================
REGION_UNIVERSITY_MAP = {
    "中部地區": ["國立雲林科技大學", "國立中興大學", "逢甲大學", "東海大學", "國立彰化師範大學"],
    "北部地區": ["國立台灣大學", "國立清華大學", "國立陽明交通大學", "國立臺北科技大學"],
    "南部地區": ["國立成功大學", "國立中山大學", "國立中正大學", "國立高雄科技大學"],
    "東部與離島": ["國立東華大學", "國立宜蘭大學"]
}

YUNTECH_ALL_DEPTS = [
    "不限科系/共同通識核心", "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系",
    "化學工程與材料工程系", "環境與安全衛生工程系", "工業設計系", "視覺傳達設計系", "數位媒體設計系",
    "創意生活設計系", "建築與室內設計系", "企業管理系", "財務金融系", "會計系", "資訊管理系", "應用外語系"
]

PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件", "體育用品", "學術講義"]


# ==========================================
# 1. 資料庫基礎建設
# ==========================================
def init_db():
    conn = sqlite3.connect('streamlit_campus_market_v14.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY, password TEXT NOT NULL, university TEXT NOT NULL, line_id TEXT DEFAULT '未填寫', green_coins INTEGER DEFAULT 100
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
    cursor.execute("INSERT OR IGNORE INTO users VALUES ('B11321123', '1234', '國立雲林科技大學', 'yuntech_cool', 120)")
    conn.commit()
    conn.close()


def auto_classify_item(name, description):
    text = (name + " " + description).lower()
    cat, dept = "生活雜物", "不限科系/共同通識核心"
    if any(w in text for w in ["書", "課本", "版"]):
        cat = "書籍"
    elif any(w in text for w in ["計算機", "耳機", "行動電源", "充電", "ipad", "iphone", "滑鼠", "鍵盤"]):
        cat = "3C配件"
    elif any(w in text for w in ["衣服", "褲子", "鞋", "外套", "襯衫"]):
        cat = "服飾配件"
    elif any(w in text for w in ["球", "拍", "運動", "健身"]):
        cat = "體育用品"
    elif any(w in text for w in ["講義", "筆記", "考古題"]):
        cat = "學術講義"
    return cat, dept


init_db()

# ==========================================
# 2. 狀態管理
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "🔍 探索雜貨市集"


def get_user_line(student_id):
    conn = sqlite3.connect('streamlit_campus_market_v14.db')
    res = conn.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else "未填寫"


def get_coins(student_id):
    conn = sqlite3.connect('streamlit_campus_market_v14.db')
    res = conn.execute("SELECT green_coins FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(student_id, amount):
    conn = sqlite3.connect('streamlit_campus_market_v14.db')
    conn.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ?", (amount, student_id))
    conn.commit()
    conn.close()


# ==========================================
# 3. 歡迎與登入區 (極簡美化)
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 Campus Market</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">全台大學生專屬・AI智慧二手物資集點交流平台</div>', unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 快速登入", "📝 註冊帳號"])
    with auth_tab1:
        with st.form("login"):
            sid = st.text_input("學號", "B11321123", placeholder="請輸入學號")
            pas = st.text_input("密碼", "1234", type="password", placeholder="請輸入密碼")
            if st.form_submit_button("進入市集空間"):
                conn = sqlite3.connect('streamlit_campus_market_v14.db')
                res = conn.execute("SELECT university FROM users WHERE student_id = ? AND password = ?",
                                   (sid, pas)).fetchone()
                conn.close()
                if res:
                    st.session_state.logged_in, st.session_state.student_id, st.session_state.user_uni = True, sid, res[
                        0]
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤，請再試一次。")

# ==========================================
# 4. 主商務後台系統
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    my_line = get_user_line(current_student)

    # 側邊欄改為乾淨的小型名片卡
    with st.sidebar:
        st.markdown("### 🧑‍🎓 同學個人名片")
        st.write(f"學校｜**{current_uni}**")
        st.write(f"學號｜**{current_student}**")
        st.metric(label="我的環保集點幣", value=f"{get_coins(current_student)} 🪙")
        st.write("---")
        if st.button("🚪 登出市集", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 📱 頂部滿版大氣 6 大核心圖文操控面板
    st.markdown('<div class="main-title">🛍️ 智慧校園市集選單</div>', unsafe_allow_html=True)
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
        if st.button("📜 我的拍賣攤位\n(查看買賣紀錄/上下架)",
                     use_container_width=True): st.session_state.current_menu = "📜 我的拍賣攤位"
    with row2_c1:
        if st.button("🎁 綠幣集點福利社\n(免費換超商零食好禮)",
                     use_container_width=True): st.session_state.current_menu = "🎁 綠幣集點福利社"
    with row2_c2:
        st.markdown(
            f'<a href="https://line.me/ti/p/~{my_line}" target="_blank" class="line-btn line-green-btn">💬 一鍵測試 LINE 聯絡</a>',
            unsafe_allow_html=True)
    with row2_c3:
        st.markdown('<a href="https://maps.google.com" target="_blank" class="line-btn">📍 查詢校園安全面交點</a>',
                    unsafe_allow_html=True)

    st.write("---")

    # ------------------------------------------
    # 功能 1: 探索雜貨市集 (精美卡片式佈局)
    # ------------------------------------------
    if st.session_state.current_menu == "🔍 探索雜貨市集":
        st.subheader("🪐 校園二手物資流通池")

        # 篩選欄優雅精簡化
        f1, f2, f3 = st.columns(3)
        with f1:
            search_region = st.selectbox("📌 限定區域", ["全部區域"] + list(REGION_UNIVERSITY_MAP.keys()))
        with f2:
            search_cat = st.selectbox("📦 物品分類項目", PRODUCT_CATEGORIES)
        with f3:
            search_dept = st.selectbox("🎓 適用科系", ["全部科系"] + YUNTECH_ALL_DEPTS)

        conn = sqlite3.connect('streamlit_campus_market_v14.db')
        query = "SELECT id, image_base64, name, price, category, university, department, description, shipping_method, shipping_link, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            st.info("💡 目前市集空空如也，歡迎點選上方【🚀 AI 智慧上架】成為第一個攤主！")
        else:
            for index, row in df.iterrows():
                # 使用 HTML div 結構與 Streamlit 區塊完美融合成精美卡片
                st.markdown(f'<div class="product-card">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1.2, 3, 1.5])
                with c1:
                    if row['image_base64']:
                        st.image(row['image_base64'], use_container_width=True)
                    else:
                        st.markdown(
                            "<div style='background-color:#f1f3f5;height:120px;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#adb5bd;font-size:14px;'>📦 暫無商品照</div>",
                            unsafe_allow_html=True)
                with c2:
                    st.markdown(f"#### {row['name']}")
                    st.caption(f"🏫 學校：{row['university']}  |  🏷️ 分類：{row['category']}")
                    st.markdown(f"🚚 配送與支付管道：**`{row['shipping_method']}`**")
                with c3:
                    st.markdown(f'<div class="price-tag">${row['price']:.0f}</div>', unsafe_allow_html=True)

                    # 精美抽屜式詳情查看區，決定要買再點開
                    with st.expander("🔍 查看細節與點此購買", expanded=False):
                        st.write(f"💡 **物況詳細說明：**")
                        st.info(row['description'] if row['description'] else "賣家很懶，沒有留下備註。")
                        st.write(f"🎓 **關聯科系：** {row['department']} | **上架同學：** {row['seller_id']}")

                        if row['shipping_method'] == "7-11 賣貨便" and row['shipping_link']:
                            st.markdown(
                                f'<a href="{row["shipping_link"]}" target="_blank" style="background-color:#E60012;color:white;padding:8px 12px;text-decoration:none;border-radius:8px;display:block;text-align:center;font-weight:bold;margin-bottom:10px;">🏪 前往 7-11 賣貨便下單與付款</a>',
                                unsafe_allow_html=True)

                        if st.button("🛒 確定下單購買", key=f"buy_{row['id']}", use_container_width=True):
                            if row['seller_id'] == current_student:
                                st.error("❌ 無法購買自己上架的物品")
                            else:
                                conn = sqlite3.connect('streamlit_campus_market_v14.db')
                                conn.execute("UPDATE products SET status = '已售出', buyer_id = ? WHERE id = ?",
                                             (current_student, row['id']))
                                conn.commit()
                                conn.close()
                                modify_coins(current_student, 20)  # 購買獲得集點點數
                                st.balloons()
                                st.success("🎉 下單成功！系統已為您保留該物資。")
                                seller_line = get_user_line(row['seller_id'])
                                st.markdown(
                                    f'<a href="https://line.me/ti/p/~{seller_line}" target="_blank" class="line-btn line-green-btn">💬 點我直接開啟 LINE 私訊賣家約交貨 (ID: {seller_line})</a>',
                                    unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 2: AI 智慧上架 (簡單俐落)
    # ------------------------------------------
    elif st.session_state.current_menu == "🚀 AI 智慧上架":
        st.subheader("🏪 多元物資快速上架櫃檯")

        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱", placeholder="例如：微積分課本 / 捷安特九成新單車 / 藍牙耳機")
            p_price = st.number_input("欲售金額 (TWD)", min_value=0, value=100, step=50)

            p_shipping = st.selectbox("🚚 運送與收款形式", ["校園面交", "7-11 賣貨便", "全家好賣+", "郵寄寄送"])
            p_link = st.text_input("🔗 賣貨便/好賣+ 賣場連結 (選填)",
                                   placeholder="若上方選擇賣貨便，可在此貼上生成好的下單網址")

            p_desc = st.text_area("詳盡物況描述", placeholder="例如：使用過一學期、有微小擦傷、功能皆完全正常...")
            p_file = st.file_uploader("📸 上傳實體外觀照 (可選)", type=['png', 'jpg', 'jpeg'])

            if st.form_submit_button("🚀 發布至校園市集並累積點數"):
                if p_name and p_desc:
                    b64_str = ""
                    if p_file is not None:
                        img = Image.open(p_file).convert("RGB")
                        img.thumbnail((300, 300))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                    category, target_dept = auto_classify_item(p_name, p_desc)

                    conn = sqlite3.connect('streamlit_campus_market_v14.db')
                    conn.execute('''
                        INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, seller_id) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                    p_name, p_price, category, current_uni, target_dept, p_desc, p_shipping, p_link, current_student))
                    conn.commit()
                    conn.close()

                    modify_coins(current_student, 10)  # 上架集點
                    st.success(f"🎉 物品已成功上架！AI 偵測其屬於【{category}】，並已自動歸檔。")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("請填寫物品名稱與基本物況描述！")

    # ------------------------------------------
    # 功能 3: 綠幣集點福利社 (乾淨大方)
    # ------------------------------------------
    elif st.session_state.current_menu == "🎁 綠幣集點福利社":
        st.subheader("🪙 環保低碳集點福利社")
        user_coins = get_coins(current_student)
        st.markdown(f"當前累積點數： **{user_coins}** 🪙 (上架物品可賺10點，購買物品可賺20點！)")
        st.write("---")

        gifts = [
            {"id": 1, "name": "全家 77乳加巧克力 🍫", "cost": 30},
            {"id": 2, "name": "校園影印店 50元全額現金抵用券 📑", "cost": 60},
            {"id": 3, "name": "學校咖啡廳 免費中杯拿鐵 ☕", "cost": 100},
            {"id": 4, "name": "期末ALL-PASS 歐趴糖福袋 🍬", "cost": 140}
        ]

        for g in gifts:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            gc1, gc2, gc3 = st.columns([3, 1, 1])
            with gc1:
                st.markdown(f"##### {g['name']}")
            with gc2:
                st.markdown(f"**{g['cost']} 點**")
            with gc3:
                if st.button("立即兌換", key=f"gift_{g['id']}", use_container_width=True):
                    if user_coins >= g['cost']:
                        modify_coins(current_student, -g['cost'])
                        st.balloons()
                        st.success(f"🎁 兌換成功！【{g['name']}】電子兌換券已派發，請至學辦出示畫面領取。")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("點數不足")
            st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 功能 4: 我的拍賣攤位 (極簡扁平化清單)
    # ------------------------------------------
    elif st.session_state.current_menu == "📜 我的拍賣攤位":
        st.subheader("📋 我的市集交易帳簿")

        conn = sqlite3.connect('streamlit_campus_market_v14.db')

        st.write("#### 🛍️ 我買進的二手物資")
        df_buy = pd.read_sql_query(
            f"SELECT id as 商品ID, name as 商品名稱, price as 金額, shipping_method as 配送管道, seller_id as 賣家學號 FROM products WHERE buyer_id = '{current_student}'",
            conn)
        if df_buy.empty:
            st.caption("目前暫無買入紀錄")
        else:
            st.dataframe(df_buy, use_container_width=True, hide_index=True)

        st.write("#### 🏪 我上架/售出的物品清單")
        df_sell = pd.read_sql_query(
            f"SELECT id as 商品ID, name as 商品名稱, price as 金額, status as 狀態, buyer_id as 買家學號 FROM products WHERE seller_id = '{current_student}'",
            conn)
        if df_sell.empty:
            st.caption("目前暫無上架紀錄")
        else:
            st.dataframe(df_sell, use_container_width=True, hide_index=True)

        conn.close()