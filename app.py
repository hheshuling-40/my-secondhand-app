import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time
import re

# ==========================================
# 1. 網頁配置與 RWD 視覺優化 (CSS)
# ==========================================
st.set_page_config(page_title="Campus Market", page_icon="🛍️", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #f8f9fa; }
    .main-title { font-size: clamp(22px, 4vw, 30px); font-weight: 800; color: #212529; margin-bottom: 20px; }
    .product-card {
        background-color: #ffffff; padding: 20px; border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02); margin-bottom: 20px;
        border: 1px solid #e9ecef; display: flex; flex-direction: row; gap: 20px; align-items: center;
    }
    .line-btn {
        background: linear-gradient(135deg, #06C755 0%, #05b34c 100%) !important;
        color: white !important; font-weight: 600 !important; border-radius: 12px !important;
        text-align: center; padding: 10px; display: block; text-decoration: none; margin-top: 5px;
    }
    .emap-btn {
        background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%) !important;
        color: white !important; font-weight: 700 !important; border-radius: 10px !important;
        text-align: center; padding: 12px 0; display: block; text-decoration: none; margin-bottom: 15px;
    }
    .checkout-box { background-color: #f1f3f5; padding: 15px; border-radius: 12px; border: 1px solid #dee2e6; margin: 15px 0; }
    .checkout-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 14px; }
    .checkout-total { display: flex; justify-content: space-between; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #ced4da; font-size: 18px; font-weight: bold; }
    .lost-card { background-color: #fafffa; padding: 15px; border-radius: 12px; border-left: 5px solid #2ecc71; margin-bottom: 15px; }
    .gift-grid-card { background: white; border-radius: 16px; border: 1px solid #eef2f5; margin-bottom: 15px; text-align: center; padding: 15px; }
    @media (max-width: 768px) { .product-card { flex-direction: column !important; align-items: flex-start !important; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 地理大數據與基礎設定
# ==========================================
DB_NAME = 'campus_market_v2.db'
CAMPUS_MAP = {
    "公立學校": ["國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學", "國立成功大學",
                 "國立雲林科技大學"],
    "私立學校": ["輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學", "銘傳大學"]
}
EMAP_URLS = {
    "7-11 統一超商": "https://emap.pcsc.com.tw/",
    "全家便利商店": "https://www.family.com.tw/Marketing/zh/Map"
}
PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件"]


# ==========================================
# 3. 資料庫初始化與核心函數
# ==========================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            student_id TEXT, name TEXT, password TEXT, university TEXT, line_id TEXT DEFAULT '未填寫', 
            green_coins INTEGER DEFAULT 100, buy_count INTEGER DEFAULT 0, report_count INTEGER DEFAULT 0, PRIMARY KEY (student_id, university))''')
        conn.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, category TEXT, university TEXT, 
            description TEXT, shipping_method TEXT, shipping_link TEXT, status TEXT DEFAULT '上架中', 
            is_blindbox INTEGER DEFAULT 0, image_base64 TEXT, seller_id TEXT, buyer_id TEXT, final_trade_info TEXT DEFAULT '')''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, gift_name TEXT, code TEXT, status TEXT DEFAULT '未使用', timestamp TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS lost_found (
            id INTEGER PRIMARY KEY AUTOINCREMENT, university TEXT, item_name TEXT, place TEXT, contact_location TEXT, finder_id TEXT, status TEXT DEFAULT '招領中')''')
        conn.execute(
            "INSERT OR IGNORE INTO users VALUES ('A112', '王小明', '1234', '國立雲林科技大學', 'line_cool', 500, 3, 1)")


init_db()


def get_db_data(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)


def execute_db(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(query, params)
        conn.commit()


# ==========================================
# 4. 登入 / 註冊區 (含找回密碼)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 Campus Market 全國大學生智慧市集</div>', unsafe_allow_html=True)
    mode = st.radio("請選擇操作項目：", ["🔑 同學登入", "📝 新同學註冊帳號", "🔍 忘記密碼"], horizontal=True)

    log_type = st.selectbox("請選擇體系類型", list(CAMPUS_MAP.keys()))
    log_uni = st.selectbox("請選取您的就讀學校", CAMPUS_MAP[log_type])

    if mode == "🔑 同學登入":
        with st.form("login_form"):
            sid = st.text_input("學號")
            pas = st.text_input("密碼", type="password")
            if st.form_submit_button("登入市集"):
                res = get_db_data("SELECT name FROM users WHERE student_id=? AND password=? AND university=?",
                                  (sid, pas, log_uni))
                if not res.empty:
                    st.session_state.update(
                        {"logged_in": True, "student_id": sid, "user_uni": log_uni, "user_name": res['name'][0],
                         "current_menu": "探索二手市集"})
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼輸入錯誤！")

    elif mode == "📝 新同學註冊帳號":
        with st.form("reg_form"):
            reg_name = st.text_input("您的稱呼 *")
            reg_sid = st.text_input("學號 *")
            reg_line = st.text_input("LINE ID *")
            reg_pass = st.text_input("設定密碼 *", type="password")
            if st.form_submit_button("提交註冊"):
                try:
                    execute_db(
                        "INSERT INTO users (student_id, name, password, university, line_id) VALUES (?, ?, ?, ?, ?)",
                        (reg_sid, reg_name, reg_pass, log_uni, reg_line))
                    st.success("🎉 註冊成功！請切換到登入頁面。")
                except:
                    st.error("該學校此學號已被註冊！")

    elif mode == "🔍 忘記密碼":
        st.caption("🔒 安全驗證：請輸入正確的註冊學號與持有的 LINE ID 以核對資料庫。")
        with st.form("forgot_form"):
            f_sid = st.text_input("請輸入學號")
            f_line = st.text_input("請輸入註冊時綁定的 LINE ID")
            if st.form_submit_button("驗證身分並找回密碼"):
                res = get_db_data("SELECT password, name FROM users WHERE student_id=? AND line_id=? AND university=?",
                                  (f_sid, f_line, log_uni))
                if not res.empty:
                    st.success(f"🔑 驗證成功！{res['name'][0]} 同學，您的密碼為：【 {res['password'][0]} 】")
                else:
                    st.error("❌ 驗證失敗：學號、LINE ID 或學校資訊不吻合！")

# ==========================================
# 5. 主系統主控台 (登入後)
# ==========================================
else:
    cur_sid, cur_uni, cur_name = st.session_state.student_id, st.session_state.user_uni, st.session_state.user_name

    # 讀取用戶當前狀態
    u_data = get_db_data("SELECT green_coins, buy_count, report_count FROM users WHERE student_id=? AND university=?",
                         (cur_sid, cur_uni)).iloc[0]
    user_coins, buy_cnt, report_cnt = int(u_data['green_coins']), int(u_data['buy_count']), int(u_data['report_count'])
    total_actions = buy_cnt + report_cnt

    # 側邊欄：個人資訊與進度
    with st.sidebar:
        st.markdown(f"### 🧑‍🎓 攤主：{cur_name} 同學\n學校｜**{cur_uni}**")
        st.metric(label="我的環保集點幣", value=f"{user_coins} 🪙")

        st.markdown(f"""<div style='background: #fff4e6; border:1px solid #ffd43b; padding:12px; border-radius:12px;'>
            <span style='color:#d9480f; font-weight:bold;'>🎁 活躍滿額抽獎進度</span><br>
            <small>二手交易 + 失物通報累計：<b>{total_actions} / 5 次</b></small>
        </div>""", unsafe_allow_html=True)


        # 幸運大抽獎對話框
        @st.dialog("🎁 校園幸運大抽獎")
        def lucky_draw_dialog():
            st.write("系統檢測到您的校園貢獻已達標！")
            if st.button("🎰 開始抽獎", use_container_width=True, type="primary"):
                prize = random.choice(["50 點綠幣 🪙", "全家 35元點心折價券 🍰", "免運通關券 🚚"])
                st.balloons()
                st.success(f"🎊 恭喜抽中：【{prize}】！")
                if "綠幣" in prize:
                    execute_db("UPDATE users SET green_coins = green_coins + 50 WHERE student_id=? AND university=?",
                               (cur_sid, cur_uni))
                else:
                    execute_db("INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                               (cur_sid, f"【抽獎】{prize}", f"DRAW-{random.randint(100000, 999999)}", "2026-06-02"))
                execute_db("UPDATE users SET buy_count=0, report_count=0 WHERE student_id=? AND university=?",
                           (cur_sid, cur_uni))
                time.sleep(2.0)
                st.rerun()


        if total_actions >= 5 and st.button("🔥 滿足條件！點我抽獎", type="primary", use_container_width=True):
            lucky_draw_dialog()

        st.markdown("---")
        # 側邊欄我的資產清單
        with st.expander("📦 我買進與兌換的福利"):
            my_buys = get_db_data("SELECT name, final_trade_info FROM products WHERE buyer_id = ?", (cur_sid,))
            my_vouchers = get_db_data("SELECT gift_name, code FROM vouchers WHERE student_id = ?", (cur_sid,))
            for _, r in my_buys.iterrows(): st.caption(f"🛍️ {r['name']}\n{r['final_trade_info']}")
            for _, r in my_vouchers.iterrows(): st.caption(f"🎫 {r['gift_name']}\n序號: {r['code']}")

        if st.button("🚪 登出市集", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 中央主選單導覽
    st.markdown('<div class="main-title">🛍 全國大學生智慧市集</div>', unsafe_allow_html=True)
    cols_menu = st.columns(5)
    menus = ["探索二手市集", "智慧物資上架", "綠幣集點福利", "失物招領中心", "盲盒專區"]
    for i, m in enumerate(menus):
        if cols_menu[i].button(m, use_container_width=True): st.session_state.current_menu = m
    st.write("---")

    # ------------------------------------------
    # 功能 1: 探索二手市集
    # ------------------------------------------
    if st.session_state.current_menu == "探索二手市集":
        st.subheader("🪐 全國二手物資流通池")
        search_cat = st.selectbox("📦 物品分類篩選", PRODUCT_CATEGORIES)

        query = "SELECT * FROM products WHERE status = '上架中'"
        params = []
        if search_cat != "全部類型":
            query += " AND category = ?";
            params.append(search_cat)

        df_prod = get_db_data(query, params)


        @st.dialog("🔍 商品詳情與標準下單")
        def show_product_dialog(prod):
            st.write(f"### {prod['name']} (${prod['price']:.0f} 元)")
            st.caption(f"學校: {prod['university']} | 賣家學號: {prod['seller_id']}")

            buyer_ship_choice = st.selectbox("請選擇配送管道", ["四大超商取貨", "預約校園面交"])
            final_memo, form_valid = "", False

            if buyer_ship_choice == "四大超商取貨":
                chain = st.selectbox("選擇超商", list(EMAP_URLS.keys()))
                st.markdown(
                    f'<a href="{EMAP_URLS[chain]}" target="_blank" class="emap-btn">🌐 開氣【{chain}】真實地圖查店號</a>',
                    unsafe_allow_html=True)
                raw_store = st.text_input("貼上門市名稱與店號", placeholder="例如：台大門市 115234")

                # 🚀 亮點：Regex 智能防錯過濾器
                if raw_store.strip():
                    code_match = re.search(r'\d{5,6}', raw_store)
                    name_match = re.sub(r'\d+', '', raw_store).replace("門市", "").strip()
                    if code_match and len(name_match) >= 2:
                        final_memo = f"[{chain}] {name_match}門市 (店號:{code_match.group()})"
                        st.success(f"⚡ AI 物流格式校正成功：`{final_memo}`")
                        form_valid = True
                    else:
                        st.error("❌ 請確保輸入包含門市名稱與 5-6 位數字店號！")
            else:
                meet = st.text_input("輸入面交時間地點", placeholder="星期三中午校門口")
                if meet: final_memo = f"[面交] {meet}"; form_valid = True

            if form_valid and st.button("🚀 確定送出訂單", use_container_width=True, type="primary"):
                if prod['seller_id'] == cur_sid:
                    st.error("不能購買自己上架的商品！")
                else:
                    execute_db("UPDATE products SET status='已售出', buyer_id=?, final_trade_info=? WHERE id=?",
                               (cur_sid, final_memo, prod['id']))
                    execute_db("UPDATE users SET buy_count = buy_count + 1 WHERE student_id=? AND university=?",
                               (cur_sid, cur_uni))
                    st.success("🎉 下單成功！交易已計入活躍進度。")
                    time.sleep(1.5);
                    st.rerun()


        for _, row in df_prod.iterrows():
            st.markdown(
                f'<div class="product-card"><div><h4>{row["name"]}</h4><p>學校：{row["university"]} | 售價：${row["price"]:.0f}</p></div></div>',
                unsafe_allow_html=True)
            if st.button("🔍 查看詳情 / 購買", key=f"p_{row['id']}", use_container_width=True): show_product_dialog(row)

    # ------------------------------------------
    # 功能 2: 智慧物資上架
    # ------------------------------------------
    elif st.session_state.current_menu == "智慧物資上架":
        st.subheader("🏪 二手物資快速上架")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱")
            p_price = st.number_input("欲售金額", min_value=0, value=100)
            p_cat = st.selectbox("分類項目", PRODUCT_CATEGORIES[1:])
            p_desc = st.text_area("商品狀況描述")
            if st.form_submit_button("🚀 發布至校園市集"):
                if p_name and p_desc:
                    execute_db(
                        "INSERT INTO products (name, price, category, university, description, seller_id) VALUES (?,?,?,?,?,?)",
                        (p_name, p_price, p_cat, cur_uni, p_desc, cur_sid))
                    execute_db("UPDATE users SET green_coins = green_coins + 10 WHERE student_id=? AND university=?",
                               (cur_sid, cur_uni))
                    st.success("🎉 上架成功！獲得 10 點低碳綠幣。")
                    time.sleep(1.2);
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利
    # ------------------------------------------
    elif st.session_state.current_menu == "綠幣集點福利":
        st.subheader("🪙 綠幣集點福利社")
        gifts = [{"name": "全家 77乳加巧克力 🍫", "cost": 30}, {"name": "麥當勞 蛋捲冰淇淋 🍦", "cost": 40}]

        for idx, g in enumerate(gifts):
            st.markdown(
                f'<div class="gift-grid-card"><h5>{g["name"]}</h5><p style="color:#06C755;">🪙 {g["cost"]} 綠幣</p></div>',
                unsafe_allow_html=True)
            if st.button("馬上兌換", key=f"g_{idx}", use_container_width=True):
                if user_coins >= g['cost']:
                    execute_db("UPDATE users SET green_coins = green_coins - ? WHERE student_id=? AND university=?",
                               (g['cost'], cur_sid, cur_uni))
                    execute_db("INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                               (cur_sid, g['name'], f"CM-{random.randint(100000, 999999)}", "2026-06-02"))
                    st.balloons();
                    st.success("🎉 兌換成功！序號已存入您的福利清單。")
                    time.sleep(1.2);
                    st.rerun()
                else:
                    st.error("❌ 綠幣餘額不足！")

    # ------------------------------------------
    # 功能 4: 失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "失物招領中心":
        st.subheader("📍 校園失物招領聯防")
        t1, t2 = st.tabs(["🔍 招領佈告欄", "➕ 發布失物通報"])

        with t1:
            df_lost = get_db_data("SELECT * FROM lost_found WHERE status='招領中' AND university=?", (cur_uni,))
            for _, r in df_lost.iterrows():
                st.markdown(
                    f'<div class="lost-card"><h5>🔍 {r["item_name"]}</h5><p>地點：{r["place"]} | 暫存：{r["contact_location"]}</p></div>',
                    unsafe_allow_html=True)
                if st.button("✨ 確認領回（撤除公告）", key=f"l_{r['id']}", use_container_width=True):
                    execute_db("UPDATE lost_found SET status='已認領' WHERE id=?", (r['id'],))
                    st.success("🎉 公告已撤除。");
                    time.sleep(0.5);
                    r.rerun()
        with t2:
            with st.form("lost_form", clear_on_submit=True):
                l_name = st.text_input("物品名稱")
                l_place = st.text_input("拾獲地點")
                l_loc = st.text_input("目前暫存位置 (如:生輔組)")
                if st.form_submit_button("📢 廣播發布招領資訊"):
                    if l_name and l_place:
                        execute_db(
                            "INSERT INTO lost_found (university, item_name, place, contact_location, finder_id) VALUES (?,?,?,?,?)",
                            (cur_uni, l_name, l_place, l_loc, cur_sid))
                        execute_db(
                            "UPDATE users SET report_count = report_count + 1 WHERE student_id=? AND university=?",
                            (cur_sid, cur_uni))
                        st.success("🎉 通報成功！已計入活躍抽獎進度。")
                        time.sleep(0.5);
                        st.rerun()

    # ------------------------------------------
    # 功能 5: 盲盒專區 ($150 / 次 - 信用卡支付正式版)
    # ------------------------------------------
    elif st.session_state.current_menu == "盲盒專區":
        st.subheader("🎁 驚喜校園盲盒專區")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e1e2f 0%, #111119 100%); padding: 30px; border-radius: 20px; text-align: center; color: white;">
            <h2 style="color: #ffcc00; font-weight: 800;">CAMPUS BLIND BOX</h2>
            <div style="font-size: 60px; margin: 15px 0;">❓</div>
            <div style="font-size: 22px; font-weight: bold; color: #06C755;">單次驚喜價：$150 TWD</div>
        </div>
        """, unsafe_allow_html=True)

        prizes_pool = ["🎁 神秘高級大專生實體福袋", "☕ 星巴克 150元電子即享券", "🚚 超商免運年費通行證",
                       "💾 1TB 高速行動硬碟"]


        @st.dialog("💳 安全金流：信用卡線上結帳")
        def credit_card_payment_dialog():
            st.write("### 🔒 填寫付款信用卡資訊")
            cc_num = st.text_input("💳 信用卡卡號 (16位數)", placeholder="XXXX XXXX XXXX XXXX", max_chars=19)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                cc_exp = st.text_input("📅 有效到期日", placeholder="MM/YY", max_chars=5)
            with col_c2:
                cc_cvc = st.text_input("🔒 安全碼", type="password", placeholder="***", max_chars=3)
            cc_holder = st.text_input("👤 持卡人姓名")

            st.write("---")
            st.markdown(
                '<div class="checkout-box"><div class="checkout-row"><span>消費項目</span><span>校園驚喜盲盒 x 1</span></div><div class="checkout-row"><span>支付總額</span><span style="color:#d9480f; font-weight:bold;">$150 TWD</span></div></div>',
                unsafe_allow_html=True)

            # 金流防錯熔斷器：檢查字串長度與格式
            clean_cc = cc_num.replace(" ", "")
            pay_ready = len(clean_cc) == 16 and clean_cc.isdigit() and len(cc_exp) == 5 and len(cc_cvc) == 3 and len(
                cc_holder.strip()) >= 2

            if pay_ready:
                if st.button("🚀 確認授權付款 $150", use_container_width=True, type="primary"):
                    with st.spinner("💳 金流安全驗證中..."): time.sleep(2.0)

                    final_prize = random.choice(prizes_pool)
                    v_code = f"BBOX-{random.randint(100000, 999999)}"

                    # 實體寫入資料庫，達成完整閉環
                    execute_db("INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                               (cur_sid, f"【盲盒】{final_prize}", v_code, "2026-06-02"))
                    execute_db("UPDATE users SET buy_count = buy_count + 1 WHERE student_id=? AND university=?",
                               (cur_sid, cur_uni))

                    st.balloons()
                    st.success(f"🎉 成功抽中：【{final_prize}】！")
                    st.info(f"💡 憑證序號 `{v_code}` 已存入側邊欄「我買進與兌換的福利」中。")
                    time.sleep(3.0);
                    st.rerun()
            else:
                st.button("🔒 請完整填寫正確的信用卡資訊以解鎖付款", use_container_width=True, disabled=True)


        if st.button("🔥 線上支付解鎖盲盒 ($150)", use_container_width=True, type="primary"):
            credit_card_payment_dialog()