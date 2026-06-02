import streamlit as st
import random
import streamlit.components.v1 as components

# 1. 網頁基本設定 (維持你原本的設定)
st.set_page_config(page_title="My Secondhand App", page_icon="♻️", layout="centered")

# 2. 初始化 Session State (維持你原本儲存二手物與對話的狀態)
if "items" not in st.session_state:
    st.session_state.items = [
        {"name": "舊課本", "description": "微積分課本，九成新", "price": 100, "image": None},
        {"name": "二手吉他", "description": "入門級吉他，弦已換新", "price": 1500, "image": None}
    ]

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 側邊欄導覽選單 (幫你新增了最後一項：盲盒專區)
page = st.sidebar.selectbox(
    "選擇頁面",
    ["首頁", "二手專區", "上傳二手物", "聊天室", "盲盒專區 ($150 / 次)"]
)

# ==========================================
# 分頁 1：首頁 (文字與圖片一致)
# ==========================================
if page == "首頁":
    st.title("歡迎來到二手物交換平台 👋")
    st.write("在這裡，你可以自由分享、交換或販售你的二手物品，讓資源重獲新生！")

    st.subheader("平台特色")
    st.markdown("- **安全交易**：認證用戶，保障雙方權益")
    st.markdown("- **環保永續**：減少浪費，物盡其用")
    st.markdown("- **社群互動**：內建聊天室，溝通零距離")

# ==========================================
# 分頁 2：二手專區
# ==========================================
elif page == "二手專區":
    st.title("🛍️ 二手專區")
    st.write("看看大家都在賣什麼：")

    if not st.session_state.items:
        st.write("目前沒有物品上架。")
    else:
        for idx, item in enumerate(st.session_state.items):
            with st.container():
                st.markdown(f"### {item['name']}")
                st.write(f"**價格：** ${item['price']}")
                st.write(f"**描述：** {item['description']}")
                if item['image']:
                    st.image(item['image'], use_container_width=True)

                if st.button("聯絡賣家", key=f"contact_{idx}"):
                    st.success(f"已開啟與 {item['name']} 賣家的對話通道！")
                st.markdown("---")

# ==========================================
# 分頁 3：上傳二手物
# ==========================================
elif page == "上傳二手物":
    st.title("📤 上傳二手物")
    with st.form("upload_form", clear_on_submit=True):
        name = st.text_input("物品名稱")
        description = st.text_area("物品描述")
        price = st.number_input("期望價格", min_value=0, step=10)
        image = st.file_uploader("上傳照片", type=["jpg", "png", "jpeg"])

        submit = st.form_submit_button("確認上傳")
        if submit:
            if name and description:
                new_item = {
                    "name": name,
                    "description": description,
                    "price": price,
                    "image": image
                }
                st.session_state.items.append(new_item)
                st.success(f"成功上架：{name}")
            else:
                st.error("請填寫物品名稱與描述！")

# ==========================================
# 分頁 4：聊天室
# ==========================================
elif page == "聊天室":
    st.title("💬 內建聊天室")
    st.write("與買家/賣家即時溝通：")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("請輸入訊息..."):
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        reply = f"已收到您的訊息：『{user_input}』。賣家上線後會立即回覆您！"
        with st.chat_message("assistant"):
            st.write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ==========================================
# 分頁 5：盲盒專區 ($150 / 次) —— 💡 這是新增的黑白灰極簡專區
# ==========================================
elif page == "盲盒專區 ($150 / 次)":
    st.title("BLIND BOX")

    # 抽獎的獎項庫 (可自行修改項目)
    prizes = ["神祕二手全新品", "星巴克電子咖啡券", "平台免運券", "精美文具福袋", "復古底片相機"]

    # 利用三引號 """ 將網頁前端程式碼完全轉為字串，徹底解決 Python 認錯 CSS 的 SyntaxError 報錯
    blind_box_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            body {{
                background-color: #0E0E0E;
                color: #FFFFFF;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 10px;
            }}
            .container {{
                width: 100%;
                max-width: 380px;
                background: #151515;
                border: 1px solid #222222;
                padding: 40px 20px;
                text-align: center;
            }}
            h2 {{
                font-size: 1.3rem;
                font-weight: 300;
                letter-spacing: 5px;
                margin-bottom: 6px;
                color: #E0E0E0;
            }}
            .subtitle {{
                font-size: 0.8rem;
                color: #666666;
                letter-spacing: 2px;
                margin-bottom: 35px;
            }}
            .box-display {{
                width: 130px;
                height: 130px;
                background: #1C1C1C;
                border: 1px solid #2C2C2C;
                margin: 0 auto 35px auto;
                display: flex;
                justify-content: center;
                align-items: center;
                transition: transform 0.5s;
            }}
            .box-display.shake {{
                animation: shake 0.6s ease-in-out;
            }}
            .box-icon {{
                font-size: 2rem;
                color: #444444;
                font-weight: 300;
            }}
            .price-tag {{
                font-size: 1.1rem;
                font-weight: 400;
                color: #999999;
                margin-bottom: 25px;
                letter-spacing: 1px;
            }}
            .btn {{
                width: 100%;
                padding: 14px;
                background: #FFFFFF;
                color: #000000;
                border: none;
                font-size: 0.85rem;
                font-weight: 600;
                letter-spacing: 3px;
                cursor: pointer;
                transition: background 0.2s;
            }}
            .btn:hover {{
                background: #CCCCCC;
            }}
            /* 信用卡彈窗 */
            .modal-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.3s;
                z-index: 100;
            }}
            .modal-overlay.active {{
                opacity: 1;
                pointer-events: auto;
            }}
            .modal {{
                background: #121212;
                border: 1px solid #2A2A2A;
                width: 85%;
                max-width: 320px;
                padding: 30px 20px;
            }}
            .modal-title {{
                font-size: 0.9rem;
                font-weight: 400;
                letter-spacing: 2px;
                margin-bottom: 25px;
                color: #CCCCCC;
                text-align: center;
            }}
            .form-group {{
                margin-bottom: 16px;
                text-align: left;
            }}
            .form-group label {{
                display: block;
                font-size: 0.7rem;
                color: #666666;
                margin-bottom: 6px;
                letter-spacing: 1px;
            }}
            .form-control {{
                width: 100%;
                padding: 10px;
                background: #1A1A1A;
                border: 1px solid #2A2A2A;
                color: #FFFFFF;
                font-size: 0.85rem;
                outline: none;
            }}
            .form-control:focus {{
                border-color: #555555;
            }}
            .form-row {{
                display: flex;
                gap: 10px;
            }}
            .modal-actions {{
                margin-top: 25px;
                display: flex;
                gap: 10px;
            }}
            .btn-secondary {{
                background: transparent;
                color: #666666;
                border: 1px solid #2A2A2A;
            }}
            .btn-secondary:hover {{
                color: #FFFFFF;
                border-color: #555555;
            }}
            @keyframes shake {{
                0% {{ transform: translate(1px, 1px) rotate(0deg); }}
                15% {{ transform: translate(-3px, -1px) rotate(-1deg); }}
                30% {{ transform: translate(2px, 2px) rotate(1deg); }}
                45% {{ transform: translate(-1px, -2px) rotate(-1deg); }}
                60% {{ transform: translate(3px, 1px) rotate(0deg); }}
                80% {{ transform: translate(-2px, 2px) rotate(1deg); }}
                100% {{ transform: translate(1px, -1px) rotate(0deg); }}
            }}
        </style>
    </head>
    <body>

        <div class="container">
            <h2>BLIND BOX</h2>
            <div class="subtitle">限量盲盒活動</div>
            <div class="box-display" id="blindBox">
                <div class="box-icon">?</div>
            </div>
            <div class="price-tag">$150 / 次</div>
            <button class="btn" id="openPayBtn">購買</button>
        </div>

        <div class="modal-overlay" id="payModal">
            <div class="modal">
                <div class="modal-title">CREDIT CARD</div>
                <form id="paymentForm" onsubmit="handlePayment(event)">
                    <div class="form-group">
                        <label>卡號</label>
                        <input type="text" class="form-control" placeholder="•••• •••• •••• ••••" maxlength="19" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group" style="flex: 1;">
                            <label>到期日</label>
                            <input type="text" class="form-control" placeholder="MM/YY" maxlength="5" required>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label>安全碼</label>
                            <input type="text" class="form-control" placeholder="CVC" maxlength="3" required>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" id="closePayBtn">取消</button>
                        <button type="submit" class="btn">支付 $150</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            const openPayBtn = document.getElementById('openPayBtn');
            const closePayBtn = document.getElementById('closePayBtn');
            const payModal = document.getElementById('payModal');
            const blindBox = document.getElementById('blindBox');

            // 帶入 Python 定義的獎品陣列
            const prizePool = {prizes};

            openPayBtn.addEventListener('click', () => payModal.classList.add('active'));
            closePayBtn.addEventListener('click', () => payModal.classList.remove('active'));

            function handlePayment(event) {{
                event.preventDefault();
                payModal.classList.remove('active');
                blindBox.classList.add('shake');

                setTimeout(() => {{
                    blindBox.classList.remove('shake');
                    // 隨機抽選獎項
                    const randomPrize = prizePool[Math.floor(Math.random() * prizePool.length)];
                    alert('✨ 支付成功！\\n\\n恭喜您抽中：【' + randomPrize + '】\\n工作人員將會與您聯繫發貨事宜。');
                }}, 1200);
            }}
        </script>
    </body>
    </html>
    """

    # 渲染至網頁中
    components.html(blind_box_html, height=500, scrolling=False)