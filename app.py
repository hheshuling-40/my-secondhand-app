import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與網頁自動配置
st.set_page_config(page_title="Campus Market | 全國大學生智慧市集", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 RWD 響應式視覺優化 UI
# ==========================================
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-title {
        font-size: clamp(22px, 4vw, 30px);
        font-weight: 800;
        color: #212529;
        margin-bottom: 5px;
    }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    .product-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
        display: flex;
        flex-direction: row;
        gap: 20px;
        align-items: center;
        cursor: pointer;
    }
    .prod-img-container {
        flex: 1.2;
        min-width: 120px;
        max-width: 200px;
    }
    .prod-info-container {
        flex: 3;
    }
    .prod-action-container {
        flex: 1.5;
        text-align: right;
        min-width: 150px;
    }
    .line-btn {
        background: linear-gradient(135deg, #06C755 0%, #05b34c 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        text-align: center;
        padding: 10px;
        display: block;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(6, 199, 85, 0.15);
        transition: all 0.2s ease;
        font-size: 14px;
        margin-top: 5px;
    }
    .stButton>button {
        height: 60px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        border: none !important;
        background-color: #ffffff !important;
        color: #495057 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    .stButton>button:hover {
        background-color: #f1f3f5 !important;
        color: #06C755 !important;
    }
    .lost-card {
        background-color: #fff9db;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #fcc419;
        margin-bottom: 15px;
    }
    .price-tag {
        font-size: 26px;
        font-weight: 700;
        color: #212529;
        margin-bottom: 5px;
    }
    .record-box {
        background: #f1f3f5;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 13px;
    }

    @media (max-width: 768px) {
        .product-card {
            flex-direction: column !important;
            align-items: flex-start !important;
            padding: 15px;
        }
        .prod-img-container {
            max-width: 100% !important;
            width: 100% !important;
            text-align: center;
        }
        .prod-img-container img {
            max-height: 180px;
            object-fit: contain;
        }
        .prod-info-container {
            width: 100%;
        }
        .prod-action-container {
            width: 100%;
            text-align: left !important;
            border-top: 1px dashed #e9ecef;
            padding-top: 10px;
            margin-top: 5px;
        }
        .stButton>button {
            width: 100% !important;
            height: 55px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 萬全地理大數據：完整台灣 368 個鄉鎮市區
# ==========================================
DB_NAME = 'streamlit_campus_market_v116_perfect_taiwan_fixed.db'

CAMPUS_TYPE_MAP = {
    "公立學校": [
        "國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學",
        "國立成功大學", "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學",
        "國立臺灣科技大學", "國立臺北科技大學", "國立雲林科技大學", "國立屏東科技大學", "國立虎尾科技大學",
        "國立高雄科技大學", "國立臺北大學", "國立臺灣海洋大學", "國立彰化師範大學", "國立高雄師範大學",
        "國立東華大學", "國立暨南國際大學", "國立臺東大學", "國立宜蘭大學", "國立聯合大學",
        "國立臺南大學", "國立臺北教育大學", "國立臺中教育大學", "國立臺灣藝術大學", "國立臺北藝術大學",
        "國立臺灣體育運動大學", "國立體育大學", "國立金門大學", "國立澎湖科技大學", "國立勤益科技大學",
        "國立臺北商業大學", "國立臺中科技大學", "國立臺北護理健康大學", "國立高雄餐旅大學", "國立臺灣戲曲學院",
        "臺北市立大學", "國立防衛大學", "國立空中大學", "高雄市立空中大學", "國立臺東專科學校",
        "國立警察大學", "中央警察大學"
    ],
    "私立學校": [
        "輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學",
        "靜宜大學", "長庚大學", "元智大學", "中華大學", "大葉大學", "華梵大學",
        "義守大學", "銘傳大學", "實踐大學", "世新大學", "真理大學", "東海大學",
        "高雄醫學大學", "中國醫藥大學", "中山醫學大學", "台北醫學大學", "長榮大學",
        "南華大學", "玄奘大學", "佛光大學", "明道大學", "亞洲大學", "開南大學",
        "台灣首府大學", "康寧大學", "大同大學", "南台科技大學", "崑山科技大學",
        "嘉南藥理大學", "樹德科技大學", "龍華科技大學", "輔英科技大學", "明志科技大學",
        "聖約翰科技大學", "嶺東科技大學", "中國科技大學", "中台科技大學", "台南應用科技大學",
        "遠東科技大學", "元培醫事科技大學", "景文科技大學", "中華醫事科技大學", "萬能科技大學",
        "建國科技大學", "高苑科技大學", "大仁科技大學", "文藻外語大學", "正修科技大學",
        "朝陽科技大學", "弘光科技大學", "健行科技大學", "僑光科技大學", "明新科技大學",
        "東南科技大學", "德明財經科技大學", "致理科技大學", "醒吾科技大學", "亞東科技大學",
        "台北城市科技大學", "環球科技大學", "修平科技大學", "中華科技大學", "育達科技大學",
        "美和科技大學", "吳鳳科技大學", "臺灣神學研究學院", "法鼓文理學院", "中信金融管理學院",
        "馬偕醫學院", "基督書院", "台北海洋科技大學", "宏國德霖科技大學", "長庚科技大學",
        "黎明技術學院", "東方設計大學", "南榮科技大學", "崇右影藝科技大學", "和春技術學院",
        "大漢技術學院", "慈濟科技大學", "慈濟大學"
    ]
}

# 動態生成含數量的體系選單標籤對照表 (例如 "公立學校" -> "公立學校 (共47所)")
CAMPUS_LABEL_TO_KEY = {f"{k} (共{len(v)}所)": k for k, v in CAMPUS_TYPE_MAP.items()}
CAMPUS_LABELS = list(CAMPUS_LABEL_TO_KEY.keys())

TW_368_DISTRICTS = {
    "臺北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區",
               "南港區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區",
               "汐止區", "瑞芳區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區",
               "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區",
               "新屋區", "觀音區", "復興區"],
    "臺中市": ["中區", "東區", "南區", "西區", "北區", "北屯區", "西屯區", "南屯區", "太平區", "大里區", "霧峰區",
               "烏日區", "豐原區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "潭子區", "大雅區", "神岡區",
               "大肚區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區"],
    "臺南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區",
               "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區",
               "將軍區", "學甲區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區",
               "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "旗津區", "前鎮區", "三民區", "楠梓區", "小港區",
               "左營區", "仁武區", "大社區", "岡山區", "路竹區", "阿蓮區", "田寮區", "燕巢區", "橋頭區", "梓官區",
               "彌陀區", "永安區", "湖內區", "鳳山區", "大寮區", "林園區", "鳥松區", "大樹區", "旗山區", "美濃區",
               "六龜區", "內門區", "杉林區", "甲仙區", "桃源區", "那瑪夏區", "茂林區", "茄萣區"],
    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],
    "新竹市": ["東區", "北區", "香山區"],
    "嘉義市": ["東區", "西區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉",
               "峨眉鄉", "尖石鄉", "五峰鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "竹南鎮", "後龍鎮", "通霄鎮", "苑裡鎮", "卓蘭鎮", "造橋鄉", "西湖鄉", "頭屋鄉",
               "公館鄉", "銅鑼鄉", "三義鄉", "大湖鄉", "獅潭鄉", "三灣鄉", "南庄鄉", "泰安鄉"],
    "彰化縣": ["彰化市", "員林市", "鹿港鎮", "和美鎮", "北斗鎮", "溪湖鎮", "田中鎮", "二林鎮", "線西鄉", "伸港鄉",
               "福興鄉", "秀水鄉", "花壇鄉", "芬園鄉", "大村鄉", "埔鹽鄉", "埔心鄉", "永靖鄉", "社頭鄉", "二水鄉",
               "田尾鄉", "埤頭鄉", "芳苑鄉", "大城鄉", "竹塘鄉", "溪州鄉"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉",
               "水里鄉", "信義鄉", "仁愛鄉"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉",
               "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "臺西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉",
               "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "鹽埔鄉",
               "高樹鄉", "萬巒鄉", "內埔鄉", "竹田鄉", "新埤鄉", "枋寮鄉", "新園鄉", "崁頂鄉", "林邊鄉", "南州鄉",
               "佳冬鄉", "琉球鄉", "車城鄉", "滿州鄉", "枋山鄉", "三地門鄉", "霧臺鄉", "瑪家鄉", "泰武鄉", "來義鄉",
               "春日鄉", "獅子鄉", "牡丹鄉"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉",
               "大同鄉", "南澳鄉"],
    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉",
               "秀林鄉", "萬榮鄉", "卓溪鄉"],
    "臺東縣": ["臺東市", "成功鎮", "關山鎮", "卑南鄉", "鹿野鄉", "池上鄉", "東河鄉", "長濱鄉", "太麻里鄉", "大武鄉",
               "綠島鄉", "海端鄉", "延平鄉", "金峰鄉", "達仁鄉", "蘭嶼鄉"],
    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],
    "金門縣": ["金城鎮", "金湖鎮", "金沙鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
}

YUNTECH_ALL_DEPTS = ["不限科系/共同通識核心", "機械工程系", "電機工程系", "電子工程系", "資訊工程系", "營建工程系",
                     "工業設計系", "視覺傳達設計系", "數位媒體設計系", "企業管理系", "資訊管理系", "應用外語系"]
PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件", "體育用品", "學術講義"]


# ==========================================
# 1. 資料庫基礎建設
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT NOT NULL, name TEXT DEFAULT '同學', password TEXT NOT NULL, university TEXT NOT NULL, 
            line_id TEXT DEFAULT '未填寫', green_coins INTEGER DEFAULT 100, email TEXT DEFAULT '',
            PRIMARY KEY (student_id, university)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, category TEXT NOT NULL,
            university TEXT NOT NULL, department TEXT NOT NULL, description TEXT, shipping_method TEXT DEFAULT '校園面交',
            shipping_link TEXT DEFAULT '', status TEXT DEFAULT '上架中', is_blindbox INTEGER DEFAULT 0,
            carbon_saving REAL DEFAULT 0, image_base64 TEXT, seller_id TEXT NOT NULL, buyer_id TEXT,
            final_trade_info TEXT DEFAULT ''
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL, gift_name TEXT NOT NULL, 
            code TEXT NOT NULL, status TEXT DEFAULT '未使用', timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lost_found (
            id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT NOT NULL, university TEXT NOT NULL,
            item_name TEXT NOT NULL, place TEXT NOT NULL, contact_location TEXT NOT NULL, 
            description TEXT, finder_id TEXT NOT NULL, image_base64 TEXT, status TEXT DEFAULT '招領中'
        )
    ''')

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO users (student_id, name, password, university, line_id, green_coins, email) 
            VALUES ('A66666666', '王小明', '1234', '國立雲林科技大學', 'yuntech_cool', 150, 'a66666666@yuntech.edu.tw')
        """)
    except Exception as e:
        pass

    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 狀態管理與安全核心
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'student_id' not in st.session_state: st.session_state.student_id = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_uni' not in st.session_state: st.session_state.user_uni = ""
if 'current_menu' not in st.session_state: st.session_state.current_menu = "探索二手市集"


def mask_user_name(name_str):
    if not name_str or name_str == '同學': return "同學"
    length = len(name_str)
    if length == 2:
        return name_str[0] + "O"
    elif length == 3:
        return name_str[0] + "O" + name_str[2]
    elif length >= 4:
        return name_str[0] + "O" + name_str[-1]
    return name_str


def get_seller_masked_name(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT name FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return mask_user_name(res[0] if res else "同學")


def get_user_line(student_id):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT line_id FROM users WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return res[0] if res else "未填寫"


def get_coins(student_id, university):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT green_coins FROM users WHERE student_id = ? AND university = ?",
                       (student_id, university)).fetchone()
    conn.close()
    return res[0] if res else 0


def modify_coins(student_id, university, amount):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET green_coins = green_coins + ? WHERE student_id = ? AND university = ?",
                 (amount, student_id, university))
    conn.commit()
    conn.close()


# ==========================================
# 3. 登入 / 註冊區
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 Campus Market 全国大學生智慧市集</div>', unsafe_allow_html=True)
    st.write("已整合全台 368 完整鄉鎮市區大數據與 139 所大專院校系統。")

    mode = st.radio("請選擇操作項目：", ["🔑 同學登入", "📝 新同學註冊帳號", "❓ 忘記密碼"], horizontal=True)

    if mode == "🔑 同學登入":
        with st.form("login_form"):
            log_type_label = st.selectbox("請選擇體系類型", CAMPUS_LABELS)
            log_uni = st.selectbox("請選取您的就讀學校", CAMPUS_TYPE_MAP[CAMPUS_LABEL_TO_KEY[log_type_label]])
            sid = st.text_input("學號", placeholder="請輸入學號")
            pas = st.text_input("密碼", type="password", placeholder="請輸入密碼")
            if st.form_submit_button("登入市集"):
                conn = sqlite3.connect(DB_NAME)
                res = conn.execute(
                    "SELECT university, name FROM users WHERE student_id = ? AND password = ? AND university = ?",
                    (sid, pas, log_uni)).fetchone()
                conn.close()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.student_id = sid
                    st.session_state.user_uni = res[0]
                    st.session_state.user_name = res[1]
                    st.rerun()
                else:
                    st.error("❌ 學校、學號或密碼輸入錯誤，請重新確認！")

    elif mode == "📝 新同學註冊帳號":
        st.subheader("填寫校園註冊資料")
        reg_name = st.text_input("您的真實姓名/稱呼 *")
        reg_sid = st.text_input("註冊學號 *")
        reg_email = st.text_input("學校聯絡電子郵件 *")
        reg_type_label = st.selectbox("學校體系類型 *", CAMPUS_LABELS)
        reg_uni = st.selectbox("所屬大學 *", CAMPUS_TYPE_MAP[CAMPUS_LABEL_TO_KEY[reg_type_label]])
        reg_line = st.text_input("LINE ID *")
        reg_pass = st.text_input("設定系統密碼 *", type="password")

        if st.button("提交註冊並領取 100 幣 🪙"):
            if not reg_name or not reg_sid or not reg_email or not reg_pass:
                st.error("請完整填寫所有必填欄位！")
            else:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "INSERT INTO users (student_id, name, password, university, line_id, green_coins, email) VALUES (?, ?, ?, ?, ?, 100, ?)",
                        (reg_sid, reg_name, reg_pass, reg_uni, reg_line, reg_email))
                    conn.commit()
                    conn.close()
                    st.success("🎉 註冊成功！快切換到「同學登入」吧！")
                except:
                    st.error("在該校中此學號已被註冊過。")

    elif mode == "❓ 忘記密碼":
        st.info("忘記密碼功能請洽各校系統管理員。")

# ==========================================
# 4. 主功能區
# ==========================================
else:
    current_student = st.session_state.student_id
    current_uni = st.session_state.user_uni
    current_name = st.session_state.user_name

    with st.sidebar:
        st.markdown("### 🧑‍🎓 攤主名片")
        st.markdown(f"歡迎回來，**{current_name}** 同學！👋")
        st.write(f"學校｜**{current_uni}**")
        st.write(f"學號｜**{current_student}**")
        st.metric(label="我的環保集點幣", value=f"{get_coins(current_student, current_uni)} 🪙")

        st.markdown("---")
        st.markdown("### 📊 我的交易與物資清單")

        conn = sqlite3.connect(DB_NAME)
        my_selling = pd.read_sql_query("SELECT id, name, price FROM products WHERE seller_id = ? AND status = '上架中'",
                                       conn, params=(current_student,))
        my_sales = pd.read_sql_query(
            "SELECT name, price, status, final_trade_info FROM products WHERE seller_id = ? AND status = 'Ref售出' OR (seller_id = ? AND status = '已售出')",
            conn, params=(current_student, current_student))
        my_buys = pd.read_sql_query("SELECT name, price, university, final_trade_info FROM products WHERE buyer_id = ?",
                                    conn, params=(current_student,))
        my_vouchers = pd.read_sql_query("SELECT gift_name, code, timestamp, status FROM vouchers WHERE student_id = ?",
                                        conn, params=(current_student,))
        conn.close()

        with st.expander(f"🏪 我正在賣的商品 ({len(my_selling)})"):
            if my_selling.empty:
                st.caption("目前沒有在售物品。")
            else:
                for _, r in my_selling.iterrows():
                    col_pname, col_pbtn = st.columns([2, 1])
                    with col_pname:
                        st.markdown(f"**{r['name']}**<br><small style='color:green;'>售價: ${r['price']:.0f}</small>",
                                    unsafe_allow_html=True)
                    with col_pbtn:
                        if st.button("🛑 下架", key=f"del_{r['id']}", use_container_width=True, type="secondary"):
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("UPDATE products SET status = '已下架' WHERE id = ?", (r['id'],))
                            conn.commit()
                            conn.close()
                            st.toast(f"✅ 「{r['name']}」已成功移除！")
                            time.sleep(0.5)
                            st.rerun()

        with st.expander(f"🤝 我已售出的商品 ({len(my_sales)})"):
            if my_sales.empty:
                st.caption("目前尚無售出物資紀錄。")
            else:
                for _, r in my_sales.iterrows():
                    st.markdown(f"""
                    <div class="record-box">
                        <b>{r['name']}</b> <span style="color:green;">[已售出]</span><br>
                        金額：${r['price']:.0f}<br>
                        🤝 交易與寄送資料：{r['final_trade_info']}
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander(f"📦 我買進的商品 ({len(my_buys)})"):
            if my_buys.empty:
                st.caption("目前尚無購買物資紀錄。")
            else:
                for _, r in my_buys.iterrows():
                    st.markdown(f"""
                    <div class="record-box" style="background-color:#eef9ff;">
                        <b>{r['name']}</b><br>
                        金額：${r['price']:.0f} | 來源：{r['university']}<br>
                        🤝 配送方式：{r['final_trade_info']}
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander(f"🎁 我兌換的福利商品 ({len(my_vouchers)})"):
            if my_vouchers.empty:
                st.caption("目前尚無點心兌換紀錄。")
            else:
                for _, r in my_vouchers.iterrows():
                    st.markdown(f"""
                    <div class="record-box" style="background-color:#fff5f5; border-left: 3px solid #ff6b6b;">
                        <b>{r['gift_name']}</b><br>
                        <span style="color:#e64980; font-family:monospace; font-weight:bold; font-size:14px;">序號：{r['code']}</span><br>
                        <small style="color:#868e96;">兌換時間：{r['timestamp']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 登出市集", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="main-title">🛍 Honor 全國智慧服務選單</div>', unsafe_allow_html=True)
    st.write("---")

    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns([1, 1, 1, 1])
    with row1_c1:
        if st.button("探索二手市集", use_container_width=True): st.session_state.current_menu = "探索二手市集"
    with row1_c2:
        if st.button("智慧物資上架", use_container_width=True): st.session_state.current_menu = "智慧物資上架"
    with row1_c3:
        if st.button("綠幣集點福利", use_container_width=True): st.session_state.current_menu = "綠幣集點福利"
    with row1_c4:
        if st.button("失物招領中心", use_container_width=True): st.session_state.current_menu = "失物招領中心"

    st.write("---")

    # ------------------------------------------
    # 功能 1: 探索二手市集 (對應 368 鄉鎮市區與動態超商代碼)
    # ------------------------------------------
    if st.session_state.current_menu == "探索二手市集":
        st.subheader("🪐 全國二手物資流通池")
        f1, f2 = st.columns(2)
        with f1:
            search_cat = st.selectbox("📦 物品分類項目", PRODUCT_CATEGORIES)
        with f2:
            search_dept = st.selectbox("🎓 適用科系篩選", ["全部科系"] + YUNTECH_ALL_DEPTS)

        conn = sqlite3.connect(DB_NAME)
        query = "SELECT id, image_base64, name, price, category, university, department, description, shipping_method, shipping_link, seller_id FROM products WHERE is_blindbox = 0 AND status = '上架中'"
        df = pd.read_sql_query(query, conn)
        conn.close()


        @st.dialog("🔍 商品完整詳情與敲定交易方式")
        def show_product_details_dialog(prod_data):
            st.write(f"### {prod_data['name']}")
            if prod_data['image_base64']:
                st.image(prod_data['image_base64'], use_container_width=True)

            c_a, c_b = st.columns(2)
            with c_a:
                st.write(f"🏫 **出校園：** {prod_data['university']}")
                st.write(f"💰 **物資售價：** ${prod_data['price']:.0f} 元")
            with c_b:
                st.write(f"🚚 **原定寄送：** {prod_data['shipping_method']}")
                st.write(f"👤 **認證賣家：** {get_seller_masked_name(prod_data['seller_id'])} 同學")

            st.info(f"💡 **商品完整描述：**\n{prod_data['description']}")

            st.markdown("---")
            st.markdown("#### 🤝 請買家自行選擇需要的配送方式")

            buyer_ship_choice = st.selectbox("請選擇您想要的配送管道",
                                             ["四大超商取貨（7-11、全家、萊爾富、OK）", "使用賣家提供的 賣貨便 / 好賣+ 網址",
                                              "預約校園面交"])

            final_memo_output = ""

            if buyer_ship_choice == "使用賣家提供的 賣貨便 / 好賣+ 網址":
                st.markdown("##### 🔗 賣家預設的專屬第三方賣場連結：")
                if prod_data['shipping_link'] and prod_data['shipping_link'].strip() != "":
                    st.markdown(f"""
                    <div style="background:#eef9ff; padding:12px; border-radius:8px; border-left:4px solid #007bff; margin-bottom:10px;">
                        🎈 賣家已建立外連賣場：<br>
                        <a href="{prod_data['shipping_link']}" target="_blank" style="font-weight:bold; color:#007bff; text-decoration:underline;">👉 點我打開賣家專屬賣貨便賣場下單</a>
                    </div>
                    """, unsafe_allow_html=True)
                    final_memo_output = f"[賣貨便/好賣+] 買家已點擊前往外部連結：{prod_data['shipping_link']}"
                else:
                    st.warning("⚠️ 賣家上架時未附帶賣貨便超連結。請透過下方 LINE 聯繫賣家開單。")
                    final_memo_output = "[賣貨便/好賣+] 待賣家提供網址"

            elif buyer_ship_choice == "四大超商取貨（7-11、全家、萊爾富、OK）":
                st.markdown("##### 📍 全台電子地圖選店機制")
                chain_choice = st.radio("選擇目標超商系統", ["7-11", "全家", "萊爾富", "OK"], horizontal=True)

                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_city = st.selectbox("選擇縣市", sorted(list(TW_368_DISTRICTS.keys())))
                with c2:
                    sel_dist = st.selectbox("選擇地區", TW_368_DISTRICTS[sel_city])

                dynamic_stores = [
                    f"{sel_dist}站前店 ({100000 + hash(sel_dist) % 89999})",
                    f"{sel_dist}大學店 ({120000 + hash(sel_dist) % 79999})",
                    f"{sel_dist}新公園店 ({150000 + hash(sel_dist) % 69999})"
                ]
                with c3:
                    sel_store = st.selectbox("點選超商門市", dynamic_stores)

                formatted_store_info = f"[{chain_choice}] {sel_city}{sel_dist} - {sel_store}"
                st.success(f"🎯 已鎖定配送門市格式：`{formatted_store_info}`")

                b_name = st.text_input("收件人真實姓名", placeholder="請填寫證件相符姓名")
                b_phone = st.text_input("收件人手機號碼", placeholder="例如：0912345678")
                if b_name and b_phone:
                    final_memo_output = f"{formatted_store_info} (收件人:{b_name}, 電話:{b_phone})"

            else:
                meet_memo = st.text_input("填寫面交時間與地點", placeholder="例如：週三中午在校園正門口...")
                if meet_memo:
                    final_memo_output = f"[校園面交] 約定地點：{meet_memo}"

            s_line = get_user_line(prod_data['seller_id'])
            st.markdown(
                f'<a href="https://line.me/ti/p/~{s_line}" target="_blank" class="line-btn">💬 亦可私訊賣家 LINE 溝通</a>',
                unsafe_allow_html=True)

            if st.button("🚀 確定送出訂單（不扣幣，移入雙方清單）", use_container_width=True, type="primary"):
                if prod_data['seller_id'] == current_student:
                    st.error("不能購買自己上架的商品！")
                elif final_memo_output == "":
                    st.error("請確實填妥收件門市或面交細節資訊再送出！")
                else:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        "UPDATE products SET status = '已售出', buyer_id = ?, final_trade_info = ? WHERE id = ?",
                        (current_student, final_memo_output, prod_data['id']))
                    conn.commit()
                    conn.close()
                    st.success("🎉 訂單發送成功！格式已由系統統一標準化，快到左側「我的交易清單」查閱！")
                    time.sleep(1.5)
                    st.rerun()


        if df.empty:
            st.info("💡 目前市集商場尚無寶物在售。")
        else:
            for index, row in df.iterrows():
                img_html = f"<img src='{row['image_base64']}' style='width:100%; border-radius:12px; object-fit:cover;' />" if \
                row[
                    'image_base64'] else "<div style='background-color:#f1f3f5;height:120px;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#adb5bd;font-size:13px;'>📦 暫無商品照</div>"
                masked_seller_name = get_seller_masked_name(row['seller_id'])

                st.markdown(f"""
                <div class="product-card">
                    <div class="prod-img-container">{img_html}</div>
                    <div class="prod-info-container">
                        <h4 style="margin:0 0 8px 0; color:#212529;">{row['name']}</h4>
                        <p style="margin:2px 0; font-size:13px; color:#6c757d;">🏫 學校：{row['university']}</p>
                        <p style="margin:2px 0; font-size:13px; color:#6c757d;">🚚 賣家預設：{row['shipping_method']}</p>
                        <p style="margin:8px 0 0 0; font-size:13px; color:#06C755;">👤 <b>賣家：</b>{masked_seller_name} 同學</p>
                    </div>
                    <div class="prod-action-container">
                        <div class="price-tag">${row['price']:.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🔍 點此看詳細規格或下單流程（品名：{row['name']}）", key=f"view_{row['id']}",
                             use_container_width=True):
                    show_product_details_dialog(row)

    # ------------------------------------------
    # 功能 2: 智慧物資上架
    # ------------------------------------------
    elif st.session_state.current_menu == "智慧物資上架":
        st.subheader("🏪 多元物資快速上架櫃檯")
        with st.form("upload_form", clear_on_submit=True):
            p_name = st.text_input("物品名稱", placeholder="例如：微積分課本")
            p_price = st.number_input("欲售金額 (TWD)", min_value=0, value=100)
            p_shipping = st.selectbox("🚚 建議運送形式", ["校園面交", "7-11 賣貨便", "全家好賣+"])
            p_link = st.text_input("🔗 第三方賣場連結（若有，買家下單時會直接彈出網址）",
                                   placeholder="https://myship.7-11.com.tw/...")
            p_desc = st.text_area("物況詳細說明")
            p_file = st.file_uploader("📸 上傳商品實體照", type=['png', 'jpg', 'jpeg'])

            if st.form_submit_button("🚀 發布至校園市集"):
                if p_name and p_desc:
                    b64_str = ""
                    if p_file is not None:
                        img = Image.open(p_file).convert("RGB")
                        img.thumbnail((300, 300))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                    conn = sqlite3.connect(DB_NAME)
                    conn.execute(
                        'INSERT INTO products (name, price, category, university, department, description, shipping_method, shipping_link, seller_id, image_base64) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (p_name, p_price, "生活雜物", current_uni, "不限科系/共同通識核心", p_desc, p_shipping, p_link,
                         current_student, b64_str))
                    conn.commit()
                    conn.close()
                    modify_coins(current_student, current_uni, 10)
                    st.success("🎉 上架成功！")
                    st.rerun()

    # ------------------------------------------
    # 功能 3: 綠幣集點福利
    # ------------------------------------------
    elif st.session_state.current_menu == "綠幣集點福利":
        st.subheader("🪙 環保低碳集點福利社")
        user_coins = get_coins(current_student, current_uni)
        st.info(f"當前可用積點： {user_coins} 🪙")

        gifts = [
            {"name": "全家 77乳加巧克力 🍫", "cost": 30},
            {"name": "校園影印店 50元抵用券 📑", "cost": 60}
        ]

        for idx, g in enumerate(gifts):
            st.markdown(f"""
            <div style="background:#ffffff; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.02); margin-bottom:12px;">
                <h5 style="margin:0 0 5px 0;">{g['name']}</h5>
                <p style="margin:0; color:#06C755; font-weight:bold;">所需點數：{g['cost']} 點</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("確認兌換", key=f"g_{idx}", use_container_width=True):
                if user_coins >= g['cost']:
                    modify_coins(current_student, current_uni, -g['cost'])
                    v_code = f"CM-{random.randint(100000, 999999)}"
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO vouchers (student_id, gift_name, code, timestamp) VALUES (?, ?, ?, ?)",
                                 (current_student, g['name'], v_code, "2026-06-02"))
                    conn.commit()
                    conn.close()
                    st.balloons()
                    st.success(f"🎉 兌換成功！序號 {v_code} 已同步存入左側「我兌換的福利商品」清單中。")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("點數不足")

    # ------------------------------------------
    # 功能 4: 失物招領中心
    # ------------------------------------------
    elif st.session_state.current_menu == "失物招招領中心":
        st.subheader("📍 全國大學生聯防失物招領中心")
        m_tab1, m_tab2 = st.tabs(["🔍 招領佈告欄", "➕ 發布失物通報"])

        with m_tab1:
            sub_tab_local, sub_tab_national = st.tabs([f"🏫 本校公告 ({current_uni})", "🌐 全台跨校聯防"])

            with sub_tab_local:
                conn = sqlite3.connect(DB_NAME)
                query_local = "SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND university=?"
                df_local = pd.read_sql_query(query_local, conn, params=(current_uni,))
                conn.close()

                if df_local.empty:
                    st.info(f"💡 目前 {current_uni} 暫無校內失物招領公告。")
                else:
                    for idx, row in df_local.iterrows():
                        masked_finder_name = get_seller_masked_name(row['finder_id'])
                        st.markdown(f"""
                        <div class="lost-card" style="border-left: 5px solid #2ecc71; background-color: #fafffa;">
                            <h5>🔍 【本校專區】{row['item_name']}</h5>
                            <p style='margin:2px 0; font-size:13px;'>📍 <b>拾獲地點：</b>{row['place']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#e67e22;'>🏢 <b>認領位置：</b>{row['contact_location']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#7f8c8d;'>👤 <b>善心拾獲人：</b>{masked_finder_name} 同學</p>
                            <small>備註：{row['description']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        if row['image_base64']: st.image(row['image_base64'], width=220)
                        if st.button("✨ 本校物歸原主（撤除公告）", key=f"res_local_{row['id']}",
                                     use_container_width=True):
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("UPDATE lost_found SET status='已認領' WHERE id=?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.success("🎉 順利撤除校內公告。")
                            time.sleep(0.5)
                            st.rerun()

            with sub_tab_national:
                st.write("🌐 篩選其他學校的失物看板：")
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    nat_type_label = st.selectbox("學校體系篩選", CAMPUS_LABELS)
                nat_type = CAMPUS_LABEL_TO_KEY[nat_type_label]
                with c_t2:
                    search_nat_uni = st.selectbox("特定學校篩選",
                                                  ["全部學校"] + [u for u in CAMPUS_TYPE_MAP[nat_type] if
                                                                  u != current_uni])

                conn = sqlite3.connect(DB_NAME)
                if search_nat_uni == "全部學校":
                    placeholders = ','.join(['?'] * len(CAMPUS_TYPE_MAP[nat_type]))
                    query_nat = f"SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND university != ? AND university IN ({placeholders})"
                    params = [current_uni] + CAMPUS_TYPE_MAP[nat_type]
                    df_nat = pd.read_sql_query(query_nat, conn, params=params)
                else:
                    query_nat = "SELECT id, region, university, item_name, place, contact_location, description, image_base64, finder_id FROM lost_found WHERE status='招領中' AND university = ?"
                    df_nat = pd.read_sql_query(query_nat, conn, params=(search_nat_uni,))
                conn.close()

                if df_nat.empty:
                    st.info("💡 目前所選之其他大學暫無失物招領公告。")
                else:
                    for idx, row in df_nat.iterrows():
                        masked_finder_name = get_seller_masked_name(row['finder_id'])
                        st.markdown(f"""
                        <div class="lost-card">
                            <h5>🔍 【{row['university']}】{row['item_name']}</h5>
                            <p style='margin:2px 0; font-size:13px;'>📍 <b>拾獲地點：</b>{row['place']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#e67e22;'>🏢 <b>認領位置：</b>{row['contact_location']}</p>
                            <p style='margin:2px 0; font-size:13px; color:#7f8c8d;'>👤 <b>善心拾獲人：</b>{masked_finder_name} 同學</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if row['image_base64']: st.image(row['image_base64'], width=220)
                        if st.button("✨ 跨校物歸原主（撤除公告）", key=f"res_nat_{row['id']}", use_container_width=True):
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("UPDATE lost_found SET status='已認領' WHERE id=?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.success("🎉 已順利撤除公告。")
                            time.sleep(0.5)
                            st.rerun()

        with m_tab2:
            st.write("#### ➕ 填寫失物通報單")
            with st.form("lost_form", clear_on_submit=True):
                l_type_label = st.selectbox("拾獲物品學校體系 *", CAMPUS_LABELS)
                l_uni = st.selectbox("拾獲物品所屬學校 *", CAMPUS_TYPE_MAP[CAMPUS_LABEL_TO_KEY[l_type_label]])
                l_name = st.text_input("失物名稱 *", placeholder="例如：AirPods 左耳")
                l_place = st.text_input("詳細拾獲位置 *", placeholder="例如：綜大 1 樓飲水機旁")
                l_contact = st.text_input("目前暫存領取地點 *", placeholder="例如：生輔組櫃檯")
                l_desc = st.text_area("外觀、顏色等特徵備註")
                l_file = st.file_uploader("📸 上傳失物實體照（選填）", type=['png', 'jpg', 'jpeg'])

                if st.form_submit_button("📢 發布全台聯防公告"):
                    if l_name and l_place and l_contact:
                        lost_b64 = ""
                        if l_file is not None:
                            img = Image.open(l_file).convert("RGB")
                            img.thumbnail((300, 300))
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG")
                            lost_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "INSERT INTO lost_found (region, university, item_name, place, contact_location, description, finder_id, image_base64) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (CAMPUS_LABEL_TO_KEY[l_type_label], l_uni, l_name, l_place, l_contact, l_desc,
                             current_student, lost_b64))
                        conn.commit()
                        conn.close()
                        modify_coins(current_student, current_uni, 15)
                        st.balloons()
                        st.success("🎉 聯防公告發布成功！")
                        time.sleep(1)
                        st.rerun()