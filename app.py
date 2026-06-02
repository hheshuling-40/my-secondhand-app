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
DB_NAME = 'streamlit_campus_market_v115_perfect_taiwan_368.db'

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

# 🛠️ 100% 完整收錄台灣 368 鄉鎮市區結構表
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
    "高雄市": ["興達港區", "新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "旗津區", "前鎮區", "三民區", "楠梓區",
               "小港區", "左營區", "仁武區", "大社區", "岡山區", "路竹區", "阿蓮區", "田寮區", "燕巢區", "橋頭區",
               "梓官區", "彌陀區", "永安區", "湖內區", "鳳山區", "大寮區", "林園區", "鳥松區", "大樹區", "旗山區",
               "美濃區", "六龜區", "內門區", "杉林區", "甲仙區", "桃源區", "那瑪夏區", "茂林區", "茄萣區"],
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
    conn = sqlite3.connect(DB_NAME