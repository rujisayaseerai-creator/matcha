import streamlit as st
from datetime import datetime
import pandas as pd
import os
import uuid
import requests  # ใช้สำหรับส่ง LINE Notify (ถ้าตั้ง token ไว้)

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Matcha Cafe Order",
    page_icon="🍵",
    layout="centered"
)

# พื้นหลังธีมมัจฉะเขียวอ่อน
page_bg = """
<style>
[data-testid="stAppViewContainer"]{
    background: #DFF5D2;
}
[data-testid="stSidebar"]{
    background: #CDE8B3;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

ORDERS_FILE = "orders.csv"
SLIPS_DIR = "slips"
os.makedirs(SLIPS_DIR, exist_ok=True)

# ค่าจัดส่งคงที่
DELIVERY_FEE = 5

# เมนูมัจฉะ + เครื่องดื่มอื่น ๆ (เย็นทั้งหมด)
MENU_ITEMS = {
    "matcha oat milk เย็น 60 บาท": 60,
    "matcha fresh milk เย็น 60 บาท": 60,
    "clear matcha เย็น 50 บาท": 50,
    "coconut matcha เย็น 60 บาท": 60,
    "ชาไทยเย็น 40 บาท": 40,
    "ชาเขียวเย็น 40 บาท": 40,
    "โกโก้เย็น 50 บาท": 50,
    "โอวัลตินเย็น 40 บาท": 40,
    "es-yen 50 บาท": 50,
}

SWEETNESS_LEVEL = ["หวานน้อย", "หวานปกติ", "หวานมาก"]

# LINE Notify token (ตั้งใน Streamlit secrets ถ้ามี)
LINE_NOTIFY_TOKEN = st.secrets.get("LINE_NOTIFY_TOKEN", "")


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
        st.warning("⚠️ ไม่พบไฟล์ QR Code (ต้องมี qr_matcha.jpeg/.jpg/.png อยู่โฟลเดอร์เดียวกับ app.py)")


def send_line_notify(message: str):
    """ส่งข้อความแจ้งเตือนไป LINE Notify (ถ้าเซ็ต token ไว้)"""
    if not LINE_NOTIFY_TOKEN:
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
    payload = {"message": message}
    try:
        requests.post(url, headers=headers, data=payload, timeout=5)
    except Exception as e:
        print("LINE notify error:", e)


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
    st.title("🍵 ระบบรับออเดอร์ (ปิดรับวันอาทิตย์ 6โมงเย็นนะคะ)")

    st.sidebar.header("ขั้นตอนการสั่งซื้อ")
    st.sidebar.markdown(
        f"""
- {'✅' if st.session_state.step > 1 else '👉'} **Step 1:** ลงทะเบียน  
- {'✅' if st.session_state.step > 2 else '👉'} **Step 2:** เลือกเมนู + ความหวาน + โน้ต  
- {'👉'} **Step 3:** ชำระเงิน
"""
    )

    # STEP 1 – ลงทะเบียนลูกค้า
    if st.session_state.step == 1:
        st.subheader("Step 1: ลงทะเบียนลูกค้า")

        name = st.text_input("ชื่อลูกค้า", placeholder="เช่น น้องกิ๊ฟ เชอรี่ น้องไวน์ มีตั้งมากมายไม่ยอมเรียกกัน")
        phone = st.text_input("เบอร์โทรศัพท์", placeholder=" ใส่เบอร์มือถือ หรือ เบอร์โต๊ะก็ได้ค่ะ")
        st.caption("**หมายเหตุ:** หากข้อมูลไม่สามารถระบุตัวตนได้ ขออนุญาตไม่รับออเดอร์นะคะ")

        if st.button("ไป Step 2 ➡️"):
            if not name.strip() or not phone.strip():
                st.error("กรุณากรอกข้อมูลให้ครบด้วยค่ะ")
            else:
                st.session_state.customer = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                go_to_step(2)

    # STEP 2 – เลือกเมนู + ความหวาน + โน้ต + สรุป
    elif st.session_state.step == 2:
        st.subheader("Step 2: เลือกเมนู และระบุความหวาน")

        # เลือกเมนู
        st.markdown("### 🥤 เลือกเมนูเครื่องดื่ม")
        menu_choice = st.radio(
            "",
            options=list(MENU_ITEMS.keys()),
            index=0
        )
        drink_price = MENU_ITEMS[menu_choice]

        # เลือกความหวาน
        st.markdown("### 🍬 เลือกระดับความหวาน")
        sweetness = st.radio(
            "",
            options=SWEETNESS_LEVEL,
            horizontal=True
        )

        # ช่องโน้ตเพิ่มเติม
        st.markdown("### 📝 โน้ตเพิ่มเติม (ถ้ามี)")
        note = st.text_area(
            "",
            placeholder="เช่น แม่ค้าน่ารักม๊ากกก อิอิ ",
            height=80
        )

        # คำนวณราคา
        total_price = drink_price

        # สรุป
        st.markdown("---")
        st.markdown("### 📋 สรุปรายการที่เลือก")

        st.write(f"**เมนู:** {menu_choice}")
        st.write(f"**ความหวาน:** {sweetness}")
        if note.strip():
            st.write(f"**โน้ตเพิ่มเติม:** {note.strip()}")
        else:
            st.write("**โน้ตเพิ่มเติม:** -")
        st.write(f"**ยอดรวมทั้งหมด:** 💸 {total_price} บาท")

        # เก็บค่าลง session
        st.session_state.order = {
            "menu": menu_choice,
            "sweetness": sweetness,
            "note": note.strip(),
            "price": drink_price,
            "delivery_fee": DELIVERY_FEE,
            "total_price": total_price,
        }

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ ย้อนกลับไปแก้ข้อมูลลูกค้า"):
                go_to_step(1)
        with col2:
            if st.button("ไป Step 3 – ชำระเงิน ➡️"):
                go_to_step(3)

    # STEP 3 – ชำระเงิน + แนบสลิป
    elif st.session_state.step == 3:
        st.subheader("Step 3: ชำระเงิน & แนบสลิป")

        customer = st.session_state.customer
        order = st.session_state.order

        st.markdown("### 👤 ข้อมูลลูกค้า")
        st.write(f"**ชื่อ:** {customer.get('name', '-')}")
        st.write(f"**เบอร์โทรศัพท์:** {customer.get('phone', '-')}")

        st.markdown("### 🥤 รายการที่สั่ง")

        drink_price = order.get("price", 0)
        delivery_fee = order.get("delivery_fee", 0)
        total_price = order.get("total_price", drink_price + delivery_fee)

        st.write(f"**เมนู:** {order.get('menu', '-')}")
        st.write(f"**ความหวาน:** {order.get('sweetness', '-')}")
        if order.get("note", ""):
            st.write(f"**โน้ตเพิ่มเติม:** {order.get('note')}")
        else:
            st.write("**โน้ตเพิ่มเติม:** -")

        st.write(f"**ราคาเครื่องดื่ม:** {drink_price} บาท")
        st.write(f"**ค่าจัดส่ง:** {delivery_fee} บาท")
        st.write(f"**ยอดรวมทั้งหมด:** 💸 {total_price} บาท")

        st.markdown("---")
        st.markdown("### 📲 สแกน QR เพื่อชำระเงิน")
        show_qr_image()

        st.markdown("### 🧾 แนบสลิปโอนเงิน")
        slip_file = st.file_uploader(
            "อัปโหลดสลิปโอนเงิน (ไฟล์รูป)",
            type=["png", "jpg", "jpeg"]
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ ย้อนกลับไปแก้เมนู / ความหวาน / โน้ต"):
                go_to_step(2)

        with col2:
            confirm_btn = st.button("✅ ยืนยันออเดอร์")

        if confirm_btn:
            if slip_file is None:
                st.error("กรุณาอัปโหลดสลิปโอนเงินก่อนกดยืนยันออเดอร์นะคะ")
            else:
                # เซฟไฟล์สลิป
                ext = os.path.splitext(slip_file.name)[1].lower()
                if ext == "":
                    ext = ".jpg"
                slip_name = f"slip_{uuid.uuid4().hex}{ext}"
                slip_path = os.path.join(SLIPS_DIR, slip_name)
                with open(slip_path, "wb") as f:
                    f.write(slip_file.getbuffer())

                # สร้าง order_id รวมชื่อ + เบอร์ + เวลา
                now = datetime.now()
                clean_name = customer.get("name", "").strip().replace(" ", "").lower()
                clean_phone = customer.get("phone", "").strip()
                timestamp = now.strftime("%Y%m%d%H%M%S")
                order_id = f"{clean_name}-{clean_phone}-{timestamp}"

                # บันทึกข้อมูลออเดอร์
                order_data = {
                    "order_id": order_id,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "name": customer.get("name", ""),
                    "phone": customer.get("phone", ""),
                    "menu": order.get("menu", ""),
                    "sweetness": order.get("sweetness", ""),
                    "note": order.get("note", ""),
                    "price": drink_price,
                    "delivery_fee": delivery_fee,
                    "total_price": total_price,
                    "slip_file": slip_name,
                }
                save_order(order_data)

                # แจ้งเตือน LINE (ถ้าตั้ง token ไว้)
                try:
                    msg = (
                        "📦 มีออเดอร์มัจฉะใหม่!\n"
                        f"ID: {order_id}\n"
                        f"ลูกค้า: {customer.get('name', '')}\n"
                        f"เบอร์: {customer.get('phone', '')}\n"
                        f"เมนู: {order.get('menu', '')}\n"
                        f"ความหวาน: {order.get('sweetness', '')}\n"
                        f"โน้ต: {order.get('note', '-')}\n"
                        f"ราคาเครื่องดื่ม: {drink_price} บาท\n"
                        f"ค่าจัดส่ง: {delivery_fee} บาท\n"
                        f"ยอดรวมทั้งหมด: {total_price} บาท"
                    )
                    send_line_notify(msg)
                except Exception:
                    pass

                st.success(f"🎉 รับออเดอร์เรียบร้อยแล้ว! (Order ID: {order_id})")
                st.info("กรุณารอเรียกชื่อเมื่อเครื่องดื่มของคุณพร้อมเสิร์ฟนะคะ 🍵")

                if st.button("เริ่มออเดอร์ใหม่ 🆕"):
                    st.session_state.step = 1
                    st.session_state.customer = {}
                    st.session_state.order = {}

# -------------------------------------------------
#                 ADMIN MODE
# -------------------------------------------------
else:
    st.title("🛠 Admin Login")

    password = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าหน้า Admin", type="password")

    if password != "goggag1112":
        st.warning("รหัสผ่านไม่ถูกต้องหรือยังไม่ได้กรอก")
        st.stop()
    else:
        st.success("เข้าสู่ระบบสำเร็จ ✔️")
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
- โน้ตเพิ่มเติม: {row.get('note', '')}
- ราคาเครื่องดื่ม: {row.get('price', 0)} บาท
- ค่าจัดส่ง: {row.get('delivery_fee', 0)} บาท
- ยอดรวมทั้งหมด: {row.get('total_price', 0)} บาท
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

                # สร้าง HTML สำหรับดาวน์โหลดไปปริ้น
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
       โน้ตเพิ่มเติม: {row.get('note', '')}<br/>
       ราคาเครื่องดื่ม: {row.get('price', 0)} บาท<br/>
       ค่าจัดส่ง: {row.get('delivery_fee', 0)} บาท<br/>
       ยอดรวมทั้งหมด: {row.get('total_price', 0)} บาท
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
