import streamlit as st
from datetime import datetime
import pandas as pd
import os
import uuid

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Matcha Order",
    page_icon="🍵",
    layout="centered"
)

ORDERS_FILE = "orders.csv"
SLIPS_DIR = "slips"

os.makedirs(SLIPS_DIR, exist_ok=True)

MENU_ITEMS = {
    "matcha oat milk (60 บาท)": 60,
    "matcha fresh milk (60 บาท)": 60,
    "clear matcha (50 บาท)": 50,
    "coconut matcha (60 บาท)": 60,
}
SWEETNESS_LEVEL = ["หวานน้อย", "หวานปกติ", "หวานมาก"]
TEMP_OPTIONS = ["ร้อน", "เย็น"]


# ---------------- HELPERS ----------------
def go_to_step(step_number: int):
    st.session_state.step = step_number


def load_orders():
    if os.path.exists(ORDERS_FILE):
        return pd.read_csv(ORDERS_FILE)
    return pd.DataFrame()


def save_order(order_data: dict):
    df_new = pd.DataFrame([order_data])
    if os.path.exists(ORDERS_FILE):
        df_old = pd.read_csv(ORDERS_FILE)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(ORDERS_FILE, index=False)


def show_qr_image():
    qr_files = ["qr_matcha.jpeg", "qr_matcha.jpg", "qr_matcha.png"]
    found = False
    for f in qr_files:
        if os.path.exists(f):
            st.image(f, caption="สแกนเพื่อชำระเงิน", use_column_width=True)
            found = True
            break
    if not found:
        st.warning("⚠️ ไม่พบไฟล์ QR Code (รองรับ qr_matcha.jpeg/.jpg/.png)")


# ---------------- STATE INIT ----------------
if "step" not in st.session_state:
    st.session_state.step = 1
if "customer" not in st.session_state:
    st.session_state.customer = {}
if "order" not in st.session_state:
    st.session_state.order = {}

# ---------------- SIDEBAR ----------------
st.sidebar.title("🍵 Matcha Cafe")

mode = st.sidebar.radio(
    "เลือกโหมด",
    ["ลูกค้าสั่งเครื่องดื่ม", "Admin ดูออเดอร์"]
)

# -------------------------------------------------
#                 CUSTOMER MODE
# ---------------------------------
