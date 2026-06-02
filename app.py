import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime

# ==========================================
# 1. 頁面基礎設定 (RWD 響應式優化)
# ==========================================
st.set_page_config(
    page_title="CampusMarket | 大學生智慧二手市集",
    page_icon="🎒",
    layout="wide",  # 寬螢幕模式，在手機與電腦上會自動縮放
    initial_sidebar_state="expanded"
)

# 使用自訂 CSS 強化行動裝置（RWD）的視覺體驗
st.markdown("""
<style>
    .product-card {
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #ffffff;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .price-tag {
        color: #ff4b4b;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .status-badge {
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.8rem;
    }
    .status-sold {
        background-color: #6c757d;
        color: white;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SQLite 資料庫初始化與防錯機制
# ==========================================
DB_FILE = "campus_market.db"


def get_db_connection():
    """建立資料庫連線，並確保回傳正確的連線物件"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        st.error(f"資料庫連線失敗: {e}")
        return None


def init_db():
    """初始化資料庫表格 (如果不存在則建立)"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # 商品表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price INTEGER NOT NULL,
                category TEXT,
                description TEXT,
                seller TEXT,
                status TEXT DEFAULT '上架中',
                created_at TEXT
            )
        """)
        # 訂單與抽獎表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                buyer TEXT,
                phone TEXT,
                lucky_number INTEGER,
                order_time TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.commit()
        conn.close()


# 執行初始化
init_db()

# ==========================================
# 3. 側邊導覽列 (Sidebar)
# ==========================================
st.sidebar.title("🎒 大學生二手市集")
st.sidebar.subheader("導覽選單")
page = st.sidebar.radio("請選擇頁面：", ["📜 瀏覽市集", "📤 上架二手商品", "🎉 幸運抽獎活動", "⚙️ 後台數據管理"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **RWD 提示：** 在手機上觀看時，可以點擊左上角的 `>` 展開或收合此選單。")

# ==========================================
# 4. 主要頁面邏輯
# ==========================================

# ---- 頁面 A：瀏覽市集 ----
if page == "📜 瀏覽市集":
    st.title("📜 現正上架中的二手寶物")
    st.caption("即時尋找學長姐留下來的教科書、3C、生活好物！")

    conn = get_db_connection()
    if conn:
        # 讀取所有上架中的商品
        df_products = pd.read_sql_query("SELECT * FROM products WHERE status = '上架中' ORDER BY id DESC", conn)
        conn.close()

        if df_products.empty:
            st.info("目前市集空空如也，快去當第一個上架的人吧！")
        else:
            # 類別篩選功能 (防錯：若無資料則給預設值)
            categories = ["全部"] + list(df_products['category'].unique())
            selected_cat = st.selectbox("🔍 依分類篩選：", categories)

            if selected_cat != "全部":
                filtered_df = df_products[df_products['category'] == selected_cat]
            else:
                filtered_df = df_products

            # 採用 RWD 網格佈局 (電腦 3 欄，手機自動往下排)
            cols = st.columns(3)
            for index, row in filtered_df.iterrows():
                with cols[index % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                        <h3>{row['title']}</h3>
                        <p><span class="status-badge">{row['category']}</span></p>
                        <p class="price-tag">${row['price']}</p>
                        <p style="color: #666; font-size: 0.9rem;">🎒 賣家：{row['seller']}</p>
                        <p style="font-size: 0.95rem;">{row['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # 購買按鈕與彈出視窗設計
                    with st.expander(f"🛒 購買 {row['title']}"):
                        with st.form(key=f"buy_form_{row['id']}"):
                            buyer_name = st.text_input("你的稱呼/姓名", key=f"name_{row['id']}")
                            buyer_phone = st.text_input("聯絡電話", key=f"phone_{row['id']}")

                            submit_buy = st.form_submit_button("確認下單（自動獲得抽獎資格）")

                            if submit_buy:
                                # 防錯驗證：檢查欄位是否填寫
                                if not buyer_name.strip() or not buyer_phone.strip():
                                    st.error("❌ 請填寫完整的姓名與電話！")
                                else:
                                    # 寫入資料庫
                                    conn_buy = get_db_connection()
                                    cursor_buy = conn_buy.cursor()

                                    # 1. 更新商品狀態為已售出
                                    cursor_buy.execute("UPDATE products SET status = '已售出' WHERE id = ?",
                                                       (row['id'],))
                                    # 2. 隨機產生一個幸運抽獎號碼 (100-999)
                                    lucky_num = random.randint(100, 999)
                                    # 3. 建立訂單
                                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    cursor_buy.execute("""
                                        INSERT INTO orders (product_id, buyer, phone, lucky_number, order_time)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (row['id'], buyer_name, buyer_phone, lucky_num, now_str))

                                    conn_buy.commit()
                                    conn_buy.close()

                                    st.success(f"🎉 購買成功！您的抽獎號碼是：**【{lucky_num}】**，請妥善保存！")
                                    st.balloons()
                                    st.rerun()

# ---- 頁面 B：上架二手商品 ----
elif page == "📤 上架二手商品":
    st.title("📤 上架您的二手商品")
    st.caption("把用不到的東西，變成學弟妹的寶物吧！")

    with st.form("upload_form", clear_on_submit=True):
        title = st.text_input("商品名稱 *", placeholder="例：微積分(上)課本 9成新")
        price = st.number_input("預售價格 (TWD) *", min_value=0, step=10, value=100)
        category = st.selectbox("商品分類", ["教科書/書籍", "3C電子", "生活雜貨", "衣服配件", "體育用品", "其他"])
        seller = st.text_input("賣家名稱/學號 *", placeholder="例：資工二 張同學")
        description = st.text_area("商品詳細說明", placeholder="請描述新舊程度、面交地點等資訊...")

        submit_btn = st.form_submit_button("🚀 確認上架")

        if submit_btn:
            # 防錯驗證：必填欄位檢查
            if not title.strip() or not seller.strip():
                st.error("❌ 錯誤：『商品名稱』與『賣家名稱』為必填欄位！")
            elif price <= 0:
                st.warning("⚠️ 提示：價格為 0 元嗎？免費贈送也很棒！")
            else:
                # 寫入資料庫
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO products (title, price, category, description, seller, status, created_at)
                        VALUES (?, ?, ?, ?, ?, '上架中', ?)
                    """, (title, price, category, description, seller, now_str))
                    conn.commit()
                    conn.close()

                    st.success(f"✅ 【{title}】上架成功！已同步發佈至市集。")

# ---- 頁面 C：幸運抽獎活動 ----
elif page == "🎉 幸運抽獎活動":
    st.title("🎉 市集好康：買家幸運大抽獎")
    st.info("💡 **活動規則：** 凡是在市集成功購買任何商品的同學，都會獲得一組幸運抽獎號碼。")

    conn = get_db_connection()
    if conn:
        # 讀取所有訂單（有抽獎資格的人）
        df_orders = pd.read_sql_query("""
            SELECT orders.lucky_number, orders.buyer, products.title 
            FROM orders 
            JOIN products ON orders.product_id = products.id
        """, conn)
        conn.close()

        if df_orders.empty:
            st.warning("目前還沒有任何交易產生，抽獎箱裡面空空如也！")
        else:
            st.write(f"📊 目前共有 **{len(df_orders)}** 位同學參與抽獎。")

            # 展示所有具備抽獎資格的號碼
            with st.expander("👀 查看目前所有合格的抽獎號碼"):
                st.dataframe(df_orders, use_container_width=True)

            st.markdown("---")
            st.subheader("🔮 抽出幸運兒")

            if st.button("🔥 開始抽獎！", type="primary"):
                # 隨機抽取一筆
                winner = df_orders.sample(n=1).iloc[0]

                # 大螢幕與手機皆適用的大型得獎宣告
                st.balloons()
                st.markdown(f"""
                <div style="background-color: #fff3cd; border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2 style="color: #856404; margin: 0;">🎊 恭喜得獎者 🎊</h2>
                    <p style="font-size: 2rem; font-weight: bold; color: #ff4b4b; margin: 10px 0;">
                        抽獎號碼：{winner['lucky_number']}
                    </p>
                    <p style="font-size: 1.2rem; margin: 0;">
                        恭喜 <b>{winner['buyer']}</b> 同學！(購買商品：{winner['title']})
                    </p>
                </div>
                """, unsafe_allow_html=True)

# ---- 頁面 D：後台數據管理 ----
elif page == "⚙️ 後台數據管理":
    st.title("⚙️ 後台數據管理面板")
    st.caption("此處用於檢視系統內的所有原始資料，以便於維護與 Debug。")

    conn = get_db_connection()
    if conn:
        st.subheader("📦 所有商品原始數據 (含已售出)")
        df_all_p = pd.read_sql_query("SELECT * FROM products", conn)
        st.dataframe(df_all_p, use_container_width=True)

        st.subheader("🛒 所有訂單紀錄")
        df_all_o = pd.read_sql_query("SELECT * FROM orders", conn)
        st.dataframe(df_all_o, use_container_width=True)

        # 刪除重置功能 (防錯：提供危險按鈕警告)
        st.markdown("---")
        st.subheader("⚠️ 危險區域 (重置系統)")
        if st.checkbox("我確定要刪除所有測試資料並重置系統"):
            if st.button("❌ 點我清空資料庫"):
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS products")
                cursor.execute("DROP TABLE IF EXISTS orders")
                conn.commit()
                conn.close()
                st.success("資料庫已完全清空，請重新整理網頁！")
                st.rerun()
        conn.close()