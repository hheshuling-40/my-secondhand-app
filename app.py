import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與圖示
st.set_page_config(page_title="AI 智慧二手環保多用戶市集", page_icon="🌱", layout="wide")


# ==========================================
# 1. 資料庫初始化 (新增用戶表與賣家/買家關聯)
# ==========================================
def init_db():
    conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
    cursor = conn.cursor()

    # 用戶資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            green_coins INTEGER DEFAULT 100
        )
    ''')

    # 商品表 (新增 seller 和 buyer 欄位)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT '上架中', -- 上架中 / 已售出
            is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0,
            image_base64 TEXT,
            seller TEXT NOT NULL,          -- 誰上架的
            buyer TEXT                     -- 誰買走的
        )
    ''')
    conn.commit()
    conn.close()


def auto_classify(name, description):
    text = (name + " " + description).lower()
    keywords = {
        '3C電子': ['手機', '電腦', '平板', '耳機', '充電', 'apple', 'asus', '滑鼠', '鍵盤', '螢幕', '相機', 'switch',
                   'ps5'],
        '書籍': ['書', '課本', '小說', '漫畫', '教材', '筆記', '閱讀', '文學', '原文書'],
        '衣物': ['衣服', '外套', '褲子', '裙子', '鞋', '帽子', '襯衫', '穿搭', '全新', '二手衣', 't恤'],
        '生活用品': ['水杯', '保溫杯', '收納', '椅子', '桌子', '風扇', '檯燈', '洗面乳', '雨傘', '背包']
    }
    scores = {cat: sum(1 for w in words if w in text) for cat, words in keywords.items()}
    best_cat = max(scores, key=scores.get)
    return '生活用品' if scores[best_cat] == 0 else best_cat


init_db()

# ==========================================
# 2. 登入與 Session 狀態管理
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""


# 資料庫用戶操作函數
def login_user(username, password):
    conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    res = cursor.fetchone()
    conn.close()
    return res is not None


def register_user(username, password):
    try:
        conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, green_coins) VALUES (?, ?, 100)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_coins(username):
    conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT green_coins FROM users WHERE username = ?", (username,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(username, amount):
    conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET green_coins = green_coins + ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()


# ==========================================
# 3. 登入/註冊 介面渲染
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 歡迎來到 AI 二手綠色市集")
    st.subheader("請先登入或註冊您的環保帳號")

    auth_tab1, auth_tab2 = st.tabs(["🔑 使用者登入", "📝 新用戶註冊"])

    with auth_tab1:
        with st.form("login_form"):
            login_user_input = st.text_input("帳號 (Username)", placeholder="請輸入您的帳號")
            login_pass_input = st.text_input("密碼 (Password)", type="password", placeholder="請輸入您的密碼")
            btn_login = st.form_submit_button("立即登入")

            if btn_login:
                if login_user(login_user_input, login_pass_input):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user_input
                    st.success(f"🎉 歡迎回來，{login_user_input}！正在進入市集...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，請再試一次。")

    with auth_tab2:
        with st.form("register_form"):
            reg_user_input = st.text_input("設定新帳號", placeholder="限英文或數字")
            reg_pass_input = st.text_input("設定新密碼", type="password", placeholder="請牢記您的密碼")
            btn_reg = st.form_submit_button("註冊並領取 100 綠幣 🪙")

            if btn_reg:
                if not reg_user_input or not reg_pass_input:
                    st.warning("請填寫完整的帳號與密碼！")
                elif register_user(reg_user_input, reg_pass_input):
                    st.success("🎉 註冊成功！預送 100 綠幣已到帳，請切換至登入頁籤登入。")
                else:
                    st.error("❌ 該帳號名稱已被註冊，請換一個名字。")

# ==========================================
# 4. 主程式介面 (登入後才會顯示)
# ==========================================
else:
    current_user = st.session_state.username

    # 側邊欄狀態顯示 (Sidebar)
    with st.sidebar:
        st.title("🍀 我的環保帳戶")
        st.write(f"👤 當前登入：**{current_user}**")
        coins = get_coins(current_user)
        st.metric(label="我的環保綠幣", value=f"{coins} 🪙")
        st.write("---")

        if st.button("🚪 登出帳號", color="red"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        st.write("---")
        st.caption("💡 秘笈提示：\n1. 上架寶貝賺 10 綠幣\n2. 正常購買賺 20 綠幣\n3. 綠幣可以用來抽大獎或開盲盒！")

    # 網頁主要分頁設計 (Tabs)
    tab1, tab2, tab3, tab4 = st.tabs(["🛍️ 買家互動市集", "🏪 賣家智慧中心", "🎰 綠幣遊戲與盲盒", "📋 我的交易紀錄"])

    # ------------------------------------------
    # TAB 1: 買家市集 (新增自動下架邏輯)
    # ------------------------------------------
    with tab1:
        st.header("🌍 循環經濟綠色市集")

        col_f1, _ = st.columns([2, 2])
        with col_f1:
            filter_cat = st.selectbox("類別篩選", ['全部商品', '3C電子', '書籍', '衣物', '生活用品'])

        # 關鍵創新：SQL 語法加上 `status = '上架中'`，被買走的商品會直接從這裡「下架消失」！
        conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
        query = f"SELECT id, image_base64, name, price, category, description, carbon_saving, seller FROM products WHERE is_blindbox = 0 AND status = '上架中'"
        if filter_cat != '全部商品':
            query += f" AND category = '{filter_cat}'"

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            st.info("目前市集沒有此類別的在售商品，快去隔壁分頁上架一些寶貝吧！")
        else:
            # 渲染漂亮的圖文卡片
            for index, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 3, 1])
                    with c1:
                        if row['image_base64'] and row['image_base64'].startswith("data:image"):
                            st.image(row['image_base64'], width=120)
                        else:
                            st.write("📷 暫無圖片")
                    with c2:
                        st.subheader(f"[{row['id']}] {row['name']}")
                        st.write(f"**描述:** {row['description']}")
                        st.caption(
                            f"🏷️ 分類: {row['category']}  |  👤 賣家: {row['seller']}  |  🌱 減碳貢獻: {row['carbon_saving']:,.0f} 克")
                    with c3:
                        st.write(f"### 💰 ${row['price']:,.0f}")
                        st.success("🟢 在售中")
                    st.write("---")

        # 交易控制台
        st.write("### 🛒 互動交易控制台")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            target_id = st.number_input("輸入要交易的商品 ID", min_value=1, step=1, key="market_id")
        with col_t2:
            offer_price = st.number_input("我的出價 (砍價用)", min_value=0, step=50, key="market_offer")

        with col_t3:
            if st.button("🛍️ 原價下單購買", use_container_width=True):
                conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, seller, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()

                if res and res[2] == '上架中':
                    if res[1] == current_user:
                        st.error("❌ 您不能購買自己上架的商品！")
                    else:
                        # 標記為已售出、記錄買家，並進行「下架」
                        cursor.execute("UPDATE products SET status = '已售出', buyer = ? WHERE id = ?",
                                       (current_user, target_id))
                        conn.commit()
                        modify_coins(current_user, 20)  # 買家賺 20 綠幣
                        st.success(f"🎉 成功購買「{res[0]}」！該商品已從市集下架！")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("商品不存在、或已經被其他人捷足先登下架囉！")
                conn.close()

        with col_t4:
            if st.button("💬 向 AI 賣家砍價", use_container_width=True):
                conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT name, price, seller, status FROM products WHERE id = ? AND is_blindbox = 0",
                               (target_id,))
                res = cursor.fetchone()

                if res and res[3] == '上架中':
                    p_name, orig_price, seller_name = res[0], res[1], res[2]
                    if seller_name == current_user:
                        st.error("❌ 您不能跟自己的商品砍價！")
                    elif offer_price < orig_price * 0.5:
                        st.error(f"🤖 AI賣家：價格太低了！出 ${offer_price} 是在開玩笑嗎？拒絕交易！😡")
                    elif offer_price >= orig_price * 0.8:
                        # 砍價成功，記錄買家，並下架
                        cursor.execute("UPDATE products SET status = '已售出', price = ?, buyer = ? WHERE id = ?",
                                       (offer_price, current_user, target_id))
                        conn.commit()
                        modify_coins(current_user, 25)
                        st.success(f"🤖 AI賣家：看在你想做環保的份上，【成交！】以 ${offer_price} 元賣給你！商品已成功下架！")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.warning(f"🤖 AI賣家：底線是 ${(orig_price + offer_price) / 2:.0f} 元，低於這數字免談！")
                else:
                    st.error("無法對該商品進行砍價（商品可能已被下架）。")
                conn.close()

    # ------------------------------------------
    # TAB 2: 賣家中心
    # ------------------------------------------
    with tab2:
        st.header("🏪 賣家智慧上架中心")

        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("商品名稱", placeholder="例如：極新二手機械鍵盤")
            p_price = st.number_input("預售價格 (元)", min_value=0, value=500)
            p_desc = st.text_area("商品詳細描述", placeholder="購入約半年，功能皆正常...")
            p_file = st.file_uploader("📸 上傳商品實體照片", type=['png', 'jpg', 'jpeg'])
            is_blind = st.checkbox("打包成「誠信盲盒」（名稱和圖片將在一般市集隱藏，由盲盒機專屬抽取）")

            submitted = st.form_submit_button("🚀 確認發布上架 (AI智慧算碳)")

            if submitted:
                if p_name and p_desc:
                    b64_str = ""
                    if p_file is not None:
                        img = Image.open(p_file)
                        img.thumbnail((300, 300))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                    category = auto_classify(p_name, p_desc)
                    carbon_weights = {'3C電子': 15000.0, '書籍': 1200.0, '衣物': 4500.0, '生活用品': 2000.0}
                    carbon_saving = carbon_weights.get(category, 2000.0) + random.randint(-100, 300)

                    conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
                    cursor = conn.cursor()
                    # 寫入資料庫時，自動帶入當前的登入用戶 `current_user` 為賣家
                    cursor.execute('''
                        INSERT INTO products (name, price, category, description, is_blindbox, carbon_saving, image_base64, seller) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                    p_name, p_price, category, p_desc, 1 if is_blind else 0, carbon_saving, b64_str, current_user))
                    conn.commit()
                    conn.close()

                    modify_coins(current_user, 10)  # 賣家賺 10 綠幣
                    st.success(f"🎉 上架成功！【AI 判定類別】：{category} | 🎁 獲得 10 綠幣獎勵！")
                    st.info(f"🌿 本次綠色循環預計為地球減少了 {carbon_saving:,.0f} 克的碳排放！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("請確認名稱與商品描述皆已填寫！")

    # ------------------------------------------
    # TAB 3: 遊戲化變現專區 (抽到盲盒也會自動下架)
    # ------------------------------------------
    with tab3:
        st.header("🎰 綠色環保變現遊戲場")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🎯 幸運綠幣大轉盤")
            st.write("每次抽獎消耗 **20 綠幣**")
            if st.button("🎰 點我開始瘋狂旋轉"):
                if get_coins(current_user) >= 20:
                    modify_coins(current_user, -20)
                    prizes = ["超商 50 元大禮券 🎫", "蝦皮免運券 🚚", "星巴克買一送一券 ☕", "謝謝參與，再創環保 🍃"]
                    time_sim = random.choice(prizes)
                    st.success(f"🎉 恭喜中獎！你獲得了：【{time_sim}】")
                else:
                    st.error("❌ 你的綠幣不足 20 枚！")

        with col_g2:
            st.subheader("📦 誠信盲盒抽獎機")
            st.write("用一口價 **$150 元** 隨機開箱神秘商品")
            if st.button("🔮 支付 150 元開啟隨機盲盒"):
                conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, image_base64, seller FROM products WHERE is_blindbox = 1 AND status = '上架中'")
                blind_items = cursor.fetchall()

                # 過濾掉自己的盲盒，不能抽到自己的東西
                valid_blind_items = [item for item in blind_items if item[4] != current_user]

                if not valid_blind_items:
                    st.warning("📦 目前盲盒池裡沒有其他人的商品喔！")
                else:
                    chosen = random.choice(valid_blind_items)
                    # 抽中後，標記為已售出、寫入買家、進行下架
                    cursor.execute("UPDATE products SET status = '已售出', buyer = ? WHERE id = ?",
                                   (current_user, chosen[0]))
                    conn.commit()
                    st.balloons()
                    st.success(f"🎁 盲盒成功開箱！！你抽中了：\n\n**物品名稱:** {chosen[1]}\n\n**描述細節:** {chosen[2]}")
                    if chosen[3] and chosen[3].startswith("data:image"):
                        st.image(chosen[3], width=200)
                conn.close()

    # ------------------------------------------
    # TAB 4: 個人專屬交易紀錄 (查看被下架的商品去哪了)
    # ------------------------------------------
    with tab4:
        st.header("📋 我的個人交易清單")

        conn = sqlite3.connect('streamlit_auction_v2.db', check_same_thread=False)

        st.subheader("🛍️ 我買到的寶貝 (已被市集下架)")
        df_buy = pd.read_sql_query(
            f"SELECT id, name, price, category, seller, status FROM products WHERE buyer = '{current_user}'", conn)
        if df_buy.empty:
            st.write("您目前還沒有買過東西喔。")
        else:
            st.dataframe(df_buy, use_container_width=True, hide_index=True)

        st.subheader("🏪 我賣出的/上架的寶貝紀錄")
        df_sell = pd.read_sql_query(
            f"SELECT id, name, price, category, status, buyer FROM products WHERE seller = '{current_user}'", conn)
        if df_sell.empty:
            st.write("您目前還沒有上架過任何東西。")
        else:
            st.dataframe(df_sell, use_container_width=True, hide_index=True)

        conn.close()