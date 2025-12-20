import streamlit as st
from datetime import datetime
import pandas as pd
import os
import uuid
import base64

def get_img_as_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_bg = get_img_as_base64("bg_matcha.jpeg")

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpeg;base64,{img_bg}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

[data-testid="stSidebar"] {{
    background-color: rgba(255, 255, 255, 0.8);
}}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)

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
# -------------------------------------------------
if mode == "ลูกค้าสั่งเครื่องดื่ม":
    st.title("🍵 ระบบรับออเดอร์ (ปิดรับออเดอร์วันอาทิตย์ 6โมงเย็นจ้า)")

    st.sidebar.header("ขั้นตอนการสั่งซื้อ")
    st.sidebar.markdown(
        f"""
- {'✅' if st.session_state.step > 1 else '👉'} **Step 1:** ลงทะเบียน  
- {'✅' if st.session_state.step > 2 else '👉'} **Step 2:** เลือกเมนู  
- {'👉'} **Step 3:** ชำระเงิน
"""
    )

    # STEP 1
    if st.session_state.step == 1:
        st.subheader("Step 1: ลงทะเบียนลูกค้า")

        name = st.text_input("ชื่อลูกค้า", placeholder="เช่น น้องกิ๊ฟ เชอรี่ น้องวาย มีตั้งมากมายไม่ยอมเรียกกัน")
        phone = st.text_input("เบอร์โทรศัพท์", placeholder="เบอร์มือถือ หรือ โต๊ะก็ได้จ้า")
        st.caption("ใส่ชื่อ+แผนกไว้นะคะ พี่ปุ๋ยจะติดต่อไปเพื่อนัดรับของค่ะ หากข้อมูลไม่สมบูรณ์ระบุตัวตนไม่ได้จะไม่รับออเดอร์นะคะ")

        if st.button("ไป Step 2 ➡️"):
            if not name.strip() or not phone.strip():
                st.error("กรุณากรอกชื่อและเบอร์โทรศัพท์ให้ครบก่อนนะคะ")
            else:
                st.session_state.customer = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                go_to_step(2)

    # STEP 2
    elif st.session_state.step == 2:
        st.subheader("Step 2: เลือกเมนูมัจฉะ")

        st.markdown("### 🥤 Option 1: เลือกเมนู")
        menu_choice = st.selectbox(
            "เลือกเมนูมัจฉะ",
            options=list(MENU_ITEMS.keys())
        )
        price = MENU_ITEMS[menu_choice]

        st.markdown("### 🍬 Option 2: เลือกระดับความหวาน")
        sweetness = st.radio(
            "เลือกระดับความหวาน",
            options=SWEETNESS_LEVEL,
            horizontal=True
        )

        st.markdown("### 🔥 Option 3: เลือกร้อน / เย็น")
        temp_choice = st.radio(
            "เลือกรูปแบบเครื่องดื่ม",
            options=TEMP_OPTIONS,
            horizontal=True
        )

        st.markdown("---")
        st.markdown("### สรุปรายการที่เลือก")
        st.write(f"**เมนู:** {menu_choice}")
        st.write(f"**ความหวาน:** {sweetness}")
        st.write(f"**อุณหภูมิ:** {temp_choice}")
        st.write(f"**ราคารวม:** 💸 {price} บาท")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ ย้อนกลับไปแก้ข้อมูลลูกค้า"):
                go_to_step(1)
        with col2:
            if st.button("ไป Step 3 – ชำระเงิน ➡️"):
                st.session_state.order = {
                    "menu": menu_choice,
                    "sweetness": sweetness,
                    "temperature": temp_choice,
                    "price": price,
                }
                go_to_step(3)

    # STEP 3
    elif st.session_state.step == 3:
        st.subheader("Step 3: ชำระเงิน & แนบสลิป")

        customer = st.session_state.customer
        order = st.session_state.order

        st.markdown("### 👤 ข้อมูลลูกค้า")
        st.write(f"**ชื่อ:** {customer.get('name', '-')}")
        st.write(f"**เบอร์โทรศัพท์:** {customer.get('phone', '-')}")

        st.markdown("### 🥤 รายการที่สั่ง")
        st.write(f"**เมนู:** {order.get('menu', '-')}")
        st.write(f"**ความหวาน:** {order.get('sweetness', '-')}")
        st.write(f"**อุณหภูมิ:** {order.get('temperature', '-')}")
        st.write(f"**ราคารวม:** 💸 {order.get('price', 0)} บาท")

        st.markdown("---")
        st.markdown("### 📲 สแกน QR เพื่อชำระเงิน , ถ้าไม่สะดวกจ่ายก่อนสามาถอัพรูปอะไรก็ได้เพื่อให้ระบบรับออเดอร์ค่ะ ตอนรับของค่อยจ่ายที่พี่ปุ๋ยได้ค่ะ")
        show_qr_image()

        st.markdown("### 🧾 แนบสลิปโอนเงิน")
        slip_file = st.file_uploader(
            "อัปโหลดสลิปโอนเงิน (ไฟล์รูป)",
            type=["png", "jpg", "jpeg"]
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ ย้อนกลับไปแก้เมนู"):
                go_to_step(2)

        with col2:
            confirm_btn = st.button("✅ ยืนยันออเดอร์")

        if confirm_btn:
            if slip_file is None:
                st.error("กรุณาอัปโหลดสลิปโอนเงินก่อนกดยืนยันออเดอร์นะคะ")
            else:
                # เซฟไฟล์สลิปลงโฟลเดอร์ slips/
                ext = os.path.splitext(slip_file.name)[1].lower()
                if ext == "":
                    ext = ".jpg"
                slip_name = f"slip_{uuid.uuid4().hex}{ext}"
                slip_path = os.path.join(SLIPS_DIR, slip_name)
                with open(slip_path, "wb") as f:
                    f.write(slip_file.getbuffer())

                # เตรียมข้อมูลออเดอร์สำหรับบันทึก
                now = datetime.now()
                order_id = now.strftime("%Y%m%d%H%M%S")

                order_data = {
                    "order_id": order_id,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "name": customer.get("name", ""),
                    "phone": customer.get("phone", ""),
                    "menu": order.get("menu", ""),
                    "sweetness": order.get("sweetness", ""),
                    "temperature": order.get("temperature", ""),
                    "price": order.get("price", 0),
                    "slip_file": slip_name,
                }

                save_order(order_data)

                st.success(f"🎉 รับออเดอร์เรียบร้อยแล้ว! (Order ID: {order_id})")
                st.info("กรุณารอเรียกชื่อเมื่อเครื่องดื่มของคุณพร้อมเสิร์ฟนะคะ 💚🍵")

                if st.button("เริ่มออเดอร์ใหม่ 🆕"):
                    st.session_state.step = 1
                    st.session_state.customer = {}
                    st.session_state.order = {}

# -------------------------------------------------
#                 ADMIN MODE
# -------------------------------------------------
else:
    st.title("🛠 Admin Login")

    # ระบบใส่รหัสผ่านก่อนเข้า Admin UI
    password = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าหน้า Admin", type="password")

    if password != "goggag1112":
        st.warning("รหัสผ่านไม่ถูกต้องหรือยังไม่ได้กรอก")
        st.stop()   # ❌ หยุดไม่ให้ไปต่อ
    else:
        st.success("เข้าสู่ระบบสำเร็จ! ✔️")
        st.title("📦 Admin – จัดการออเดอร์")

        df = load_orders()

        if df.empty:
            st.info("ยังไม่มีออเดอร์เข้ามาในระบบ")
        else:
            st.subheader("ลิสต์ออเดอร์ทั้งหมด")
            st.dataframe(df)

            st.markdown("---")
            st.subheader("🧾 ดู / พิมพ์ Slip")

            order_ids = df["order_id"].astype(str).tolist()
            selected_id = st.selectbox("เลือก Order ID", order_ids)

            if selected_id:
                row = df[df["order_id"].astype(str) == selected_id].iloc[0]

                st.markdown("### ตัวอย่าง Slip สำหรับปริ้น")
                st.markdown(
                    f"""
**Matcha Cafe – ใบรับออเดอร์**

- Order ID: `{row['order_id']}`
- วันที่: {row['created_at']}
- ชื่อลูกค้า: {row['name']}
- เบอร์โทร: {row['phone']}

**รายการเครื่องดื่ม**

- เมนู: {row['menu']}
- ความหวาน: {row['sweetness']}
- ร้อน/เย็น: {row['temperature']}
- ราคารวม: 💸 {row['price']} บาท
"""
                )

                slip_file = row.get("slip_file", None)
                if isinstance(slip_file, str):
                    slip_path = os.path.join(SLIPS_DIR, slip_file)
                    if os.path.exists(slip_path):
                        st.markdown("**สลิปโอนเงิน (จากลูกค้า):**")
                        st.image(slip_path, use_column_width=True)
                    else:
                        st.warning("ไม่พบไฟล์สลิปที่บันทึกไว้")

                slip_html = f"""
<html>
  <head>
    <meta charset="utf-8" />
    <title>Order {row['order_id']}</title>
  </head>
  <body style="font-family: sans-serif; max-width: 400px; margin: 0 auto;">
    <h2>Matcha Cafe – ใบรับออเดอร์</h2>
    <p><strong>Order ID:</strong> {row['order_id']}<br/>
       <strong>วันที่:</strong> {row['created_at']}<br/>
       <strong>ชื่อลูกค้า:</strong> {row['name']}<br/>
       <strong>เบอร์โทร:</strong> {row['phone']}</p>
    <hr/>
    <h3>รายการเครื่องดื่ม</h3>
    <p>
       เมนู: {row['menu']}<br/>
       ความหวาน: {row['sweetness']}<br/>
       ร้อน/เย็น: {row['temperature']}<br/>
       ราคารวม: {row['price']} บาท
    </p>
    <hr/>
    <p style="text-align:center;">ขอบคุณที่อุดหนุนค่ะ 🍵</p>
  </body>
</html>
"""
                slip_bytes = slip_html.encode("utf-8")

                st.download_button(
                    "⬇️ ดาวน์โหลด Slip (HTML สำหรับ Print)",
                    data=slip_bytes,
                    file_name=f"order_{row['order_id']}.html",
                    mime="text/html"
                )
