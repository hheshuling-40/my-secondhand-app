import streamlit as st
import sqlite3
import random
import base64
import pandas as pd
from PIL import Image
import io
import time

# 設定網頁標題與網頁自動配置
st.set_page_config(page_title="Campus Market", page_icon="🛍️", layout="wide")

# ==========================================
# 🎨 UI 視覺與色彩極致精美化
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
        margin-bottom: 20px;
    }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }

    /* 📦 商品卡片精美化 */
    .product-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
        display: flex;
        flex-direction: row;
        gap: 20px;
        align-items: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.06);
    }
    .prod-info-container {
        flex: 3;
    }
    .prod-action-container {
        flex: 1.5;
        text-align: right;
        min-width: 150px;
    }

    /* 🌟 全站按鈕極致美化 (漸層 + 陰影 + 懸停動態) */
    .stButton>button {
        background: linear-gradient(135deg, #4da3ff 0%, #1a75ff 100%) !important;
        color: #ffffff !important;
        height: 48px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(26, 117, 255, 0.25) !important;
        transition: all 0.25s ease-in-out !important;
    }
    .stButton>button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(26, 117, 255, 0.4) !important;
        background: linear-gradient(135deg, #66b2ff 0%, #3385ff 100%) !important;
    }

    /* 🚪 登出按鈕特殊精美外觀 */
    div[data-testid="stSidebar"] .stButton>button {
        background: linear-gradient(135deg, #ff6b6b 0%, #fa5252 100%) !important;
        box-shadow: 0 4px 14px rgba(250, 82, 82, 0.25) !important;
    }
    div[data-testid="stSidebar"] .stButton>button:hover {
        background: linear-gradient(135deg, #ff8787 0%, #ff6b6b 100%) !important;
        box-shadow: 0 6px 20px rgba(250, 82, 82, 0.4) !important;
    }

    /* 🤍 智慧盲盒專區改成純白色高質感卡片 */
    .blindbox-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        color: #212529;
        margin-bottom: 20px;
        font-weight: bold;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .blindbox-subtitle {
        color: #6c757d;
        font-size: 13px;
        font-weight: 400;
        margin-top: 4px;
        display: block;
    }

    /* 💛 精美失物招領卡片 */
    .lost-card {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        padding: 18px;
        border-radius: 14px;
        border-left: 6px solid #f59e0b;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.06);
    }

    .price-tag {
        font-size: 26px;
        font-weight: 700;
        color: #212529;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. 地理大數據與基礎設定
# ==========================================
DB_NAME = 'streamlit_campus_market_v116_perfect_taiwan_fixed.db'

CAMPUS_TYPE_MAP = {
    "公立學校": [
        "國立臺灣大學", "國立政治大學", "國立臺灣師範大學", "國立清華大學", "國立陽明交通大學",
        "國立成功大學", "國立中興大學", "國立中央大學", "國立中山大學", "國立中正大學",
        "國立臺灣科技大學", "國立臺北科技大學", "國立雲林科技大學", "國立屏東科技大學", "國立虎尾科技大學"
    ],
    "私立學校": [
        "輔仁大學", "東吳大學", "淡江大學", "中原大學", "逢甲大學", "中國文化大學",
        "靜宜大學", "長庚大學", "元智大學", "中華大學", "大葉大學", "華梵大學"
    ]
}

CAMPUS_LABELS = list(CAMPUS_TYPE_MAP.keys())

EMAP_URLS = {
    "7-11": "https://emap.pcsc.com.tw/",
    "全家": "https://www.family.com.tw/Marketing/zh/Map",
    "萊爾富": "https://www.hilife.com.tw/storeInquiry_street.aspx",
    "OK": "https://www.okmart.com.tw/convenient_shopSearch"
}

PRODUCT_CATEGORIES = ["全部類型", "書籍", "3C配件", "生活雜物", "服飾配件"]


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
            university TEXT NOT NULL, department TEXT NOT NULL, description TEXT, shipping_method TEXT DEFAULT '