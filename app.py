import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io

# 設定網頁標題與圖示
st.set_page_config(page_title="AI 智慧二手綠色遊戲市集", page_icon="🌱", layout="wide")

# ==========================================
# 1. 資料庫初始化
# ==========================================
def init_db():
    conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT '上架中',
            is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0,
            image_base64 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_wallet (
            id INTEGER PRIMARY KEY,
            green_coins INTEGER DEFAULT 100
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO user_wallet (id, green_coins) VALUES (1, 100)")
    conn.commit()
    conn.close()

def auto_classify(name, description):
    text = (name + " " + description).lower()
    keywords = {
        '3C電子': ['手機', '電腦', '平板', '耳機', '充電', 'apple', 'asus', '滑鼠', '鍵盤', '螢幕', '相機', 'switch', 'ps5'],
        '書籍': ['書', '課本', '小說', '漫畫', '教材', '筆記', '閱讀', '文學', '原文書'],
        '衣物': ['衣服', '外套', '褲子', '裙子', '鞋', '帽子', '襯衫', '穿搭', '全新', '二手衣', 't恤'],
        '生活用品': ['水杯', '保溫杯', '收納', '椅子', '桌子', '風扇', '檯燈', '洗面乳', '雨傘', '背包']
    }
    scores = {cat: sum(1 for w in words if w in text) for cat, words in keywords.items()}
    best_cat = max(scores, key=scores.get)
    return '生活用品' if scores[best_cat] == 0 else best_cat

init_db()

# 錢包操作常規函數
def get_coins():
    conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT green_coins FROM user_wallet WHERE id = 1")
    coins = cursor.fetchone()[0]
    conn.close()
    return coins

def modify_coins(amount):
    conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_wallet SET green_coins = green_coins + ? WHERE id = 1", (amount,))
    conn.commit()
    conn.close()

# ==========================================
# 2. 側邊欄狀態顯示 (Sidebar)
# ==========================================
with st.sidebar:
    st.title("🍀 我的環保帳戶")
    coins = get_coins()
    st.metric(label="環保綠幣餘額", value=f"{coins} 🪙")
    st.write("---")
    st.caption("💡 秘笈提示：\n1. 上架寶貝賺 10 綠幣\n2. 正常購買賺 20 綠幣\n3. 綠幣可以用來抽大獎或開盲盒！")

# ==========================================
# 3. 網頁分頁設計 (Tabs)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🛍️ 買家互動市集", "🏪 賣家智慧中心", "🎰 綠幣遊戲與盲盒"])

# ------------------------------------------
# TAB 1: 買家市集
# ------------------------------------------
with tab1:
    st.header("🌍 循環經濟綠色市集")
    
    # 篩選控制
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_cat = st.selectbox("類別篩選", ['全部商品', '3C電子', '書籍', '衣物', '生活用品'])
    
    conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
    query = "SELECT id, image_base64, name, price, category, description, carbon_saving, status FROM products WHERE is_blindbox = 0"
    if filter_cat != '全部商品':
        query += f" AND category = '{filter_cat}'"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("目前市集空空如也，快去右邊的分頁上架一些寶貝吧！")
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
                    st.caption(f"🏷️ 分類: {row['category']}  |  🌱 減碳貢獻: {row['carbon_saving']:,.0f} 克")
                with c3:
                    st.write(f"### 💰 ${row['price']:,.0f}")
                    if row['status'] == '已售出':
                        st.error("🔴 已售出")
                    else:
                        st.success("🟢 上架中")
                st.write("---")
                
    # 交易控制台
    st.write("### 🛒 互動交易控制台")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        target_id = st.number_input("輸入要交易的商品 ID", min_value=1, step=1)
    with col_t2:
        offer_price = st.number_input("我的出價 (砍價用)", min_value=0, step=50)
        
    with col_t3:
        if st.button("🛍️ 原價下單購買", use_container_width=True):
            conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT name, status FROM products WHERE id = ? AND is_blindbox = 0", (target_id,))
            res = cursor.fetchone()
            if res and res[1] == '上架中':
                cursor.execute("UPDATE products SET status = '已售出' WHERE id = ?", (target_id,))
                conn.commit()
                modify_coins(20)
                st.success(f"🎉 成功購買「{res[0]}」！獲得 20 綠幣！網頁重整後更新狀態。")
                st.balloons()
            else:
                st.error("商品不存在或已被買走囉！")
            conn.close()
            
    with col_t4:
        if st.button("💬 向 AI 賣家砍價", use_container_width=True):
            conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT name, price, status FROM products WHERE id = ? AND is_blindbox = 0", (target_id,))
            res = cursor.fetchone()
            if res and res[2] == '上架中':
                p_name, orig_price = res[0], res[1]
                if offer_price < orig_price * 0.5:
                    st.error(f"🤖 AI賣家：價格太低了！出 ${offer_price} 是在開玩笑嗎？拒絕交易！😡")
                elif offer_price >= orig_price * 0.8:
                    cursor.execute("UPDATE products SET status = '進展成交', price = ? WHERE id = ?", (offer_price, target_id))
                    conn.commit()
                    modify_coins(25)
                    st.success(f"🤖 AI賣家：看在你想做環保的份上，【成交！】以 ${offer_price} 元賣給你！快去收件吧！")
                else:
                    st.warning(f"🤖 AI賣家：底線是 ${(orig_price + offer_price)/2:.0f} 元，低於這數字免談！")
            else:
                st.error("無法對該商品進行砍價。")
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
        
        # 支援圖片上傳
        p_file = st.file_uploader("📸 上傳商品實體照片", type=['png', 'jpg', 'jpeg'])
        
        is_blind = st.checkbox("打包成「誠信盲盒」（名稱和圖片將被隱藏，直接投入盲盒機）")
        
        submitted = st.form_submit_with_col_url = st.form_submit_button("🚀 確認發布上架 (AI智慧算碳)")
        
        if submitted:
            if p_name and p_desc:
                # 處理圖片轉成 Base64
                b64_str = ""
                if p_file is not None:
                    img = Image.open(p_file)
                    img.thumbnail((300, 300)) # 精簡網頁檔案大小
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
                
                category = auto_classify(p_name, p_desc)
                carbon_weights = {'3C電子': 15000.0, '書籍': 1200.0, '衣物': 4500.0, '生活用品': 2000.0}
                carbon_saving = carbon_weights.get(category, 2000.0) + random.randint(-100, 300)
                
                conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO products (name, price, category, description, is_blindbox, carbon_saving, image_base64) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (p_name, p_price, category, p_desc, 1 if is_blind else 0, carbon_saving, b64_str))
                conn.commit()
                conn.close()
                
                modify_coins(10)
                st.success(f"🎉 上架成功！【AI 判定類別】：{category} | 🎁 獲得 10 綠幣獎勵！")
                st.info(f"🌿 本次綠色循環預計為地球減少了 {carbon_saving:,.0f} 克的碳排放！感謝有你！")
            else:
                st.error("請確認名稱與商品描述皆已填寫！")

# ------------------------------------------
# TAB 3: 遊戲化變現專區
# ------------------------------------------
with tab3:
    st.header("🎰 綠色環保變現遊戲場")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("🎯 幸運綠幣大轉盤")
        st.write("每次抽獎消耗 **20 綠幣**，100% 機率獲得虛擬或實體合作免運券！")
        if st.button("🎰 點我開始瘋狂旋轉"):
            if get_coins() >= 20:
                modify_coins(-20)
                prizes = ["超商 50 元大禮券 🎫", "蝦皮免運券 🚚", "星巴克買一送一券 ☕", "謝謝參與，再創環保 🍃"]
                st.toast("輪盤正在發瘋似地旋轉...🌀")
                time_sim = random.choice(prizes)
                st.success(f"🎉 恭喜中獎！你獲得了：【{time_sim}】")
            else:
                st.error("❌ 你的綠幣不足 20 枚！快去買賣二手商品賺取吧！")
                
    with col_g2:
        st.subheader("📦 誠信盲盒抽獎機")
        st.write("用一口價 **$150 元** 隨機開箱其他賣家打包的神秘二手商品，拼人品的時候到了！")
        if st.button("🔮 支付 150 元開啟隨機盲盒"):
            conn = sqlite3.connect('streamlit_auction.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, image_base64 FROM products WHERE is_blindbox = 1 AND status = '上架中'")
            blind_items = cursor.fetchall()
            
            if not blind_items:
                st.warning("📦 目前盲盒機池子空了！快去賣家中心上架幾個盲盒吧！")
            else:
                chosen = random.choice(blind_items)
                cursor.execute("UPDATE products SET status = '已售出' WHERE id = ?", (chosen[0],))
                conn.commit()
                st.balloons()
                st.success(f"🎁 盲盒成功開箱！！你抽中了：\n\n**物品名稱:** {chosen[1]}\n\n**描述細節:** {chosen[2]}")
                if chosen[3] and chosen[3].startswith("data:image"):
                    st.image(chosen[3], caption="盲盒真實物品外觀", width=200)
            conn.close()