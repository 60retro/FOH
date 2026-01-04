import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import io

# --- 1. ตั้งค่าและข้อมูลเบื้องต้น ---

INITIAL_CSV = """Date,รายการ,ราคา,จำนวน/ชิ้น,รวม/บาท
2026-01-03,เค้กนมสด,50,47,2350
2026-01-03,เค้กญี่ปุ่น,60,12,720
2026-01-03,เค้ก 60 บาท,90,6,540
2026-01-02,ชีสเค้ก,60,0,0
2026-01-02,คุกกี้ป๊อป,25,0,0
2026-01-02,เค้กป๊อป,75,0,0
2026-01-02,มาการองการ์ตูน,70,5,350
2026-01-02,คอนเฟลค,100,0,0
2026-01-02,ช็อคบอล 30,30,10,300
2026-01-02,ช็อคบอล 20,20,0,0
2026-01-02,ชาชงสด,40,0,0
2026-01-02,cold brew,65,0,0
2026-01-02,ลาบูบู้,159,0,0
2026-01-02,คุกกี้เนย,39,0,0
2002-01-21,เมอแรง,35,0,0
2026-01-02,กล่องเค้ก 4,35,0,0
2026-01-02,กล่องเค้ก 12ชี้น,65,0,0
2026-01-02,กล่องเค้ก 24,120,0,0
2026-01-02,กล่องเค้ก 36,100,0,0
2026-01-02,พริกทอด,110,0,0
2026-01-02,เจ้าหญิง/แคร์แบร์,79,0,0
2026-01-02,ถุงผ้า nami,40,0,0
2026-01-02,แก้วน้ำนามิ,0,0,0
2026-01-02,อื่นๆ,0,0,0
2026-01-02,cake pop,65,0,0
2026-01-02,กะบอกน๋า,0,0,0
2026-01-02,cake orange,45,0,0"""

st.set_page_config(page_title="ระบบเบิกของ Nami Shop", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def get_current_sheet_name():
    return datetime.now().strftime("%b_%Y")

def get_menu_from_csv():
    try:
        df_init = pd.read_csv(io.StringIO(INITIAL_CSV))
        menu_df = df_init[['รายการ', 'ราคา']].drop_duplicates(subset='รายการ')
        return dict(zip(menu_df['รายการ'], menu_df['ราคา']))
    except Exception:
        return {"สินค้าทั่วไป": 0}

MENU_PRESETS = get_menu_from_csv()

def load_data():
    current_sheet = get_current_sheet_name()
    try:
        df = conn.read(worksheet=current_sheet)
        if df.empty: 
            df = pd.read_csv(io.StringIO(INITIAL_CSV))
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except Exception:
        df = pd.read_csv(io.StringIO(INITIAL_CSV))
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.fillna(0)
        return df

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- 2. ส่วนหน้าจอแสดงผล ---

st.title("🍰 ระบบเบิกของหน้าร้าน (Nami Shop)")
st.caption(f"Sheet ประจำเดือน: {get_current_sheet_name()}")

# ==========================================
# ส่วนที่ 1: ฟอร์มเพิ่มข้อมูลใหม่ (Add New)
# ==========================================
with st.container(border=True):
    st.subheader("➕ เพิ่มรายการขายใหม่")
    c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
    
    with c1:
        input_date = st.date_input("วันที่", value=datetime.now().date())
    with c2:
        options = ["-- เลือกสินค้า --"] + list(MENU_PRESETS.keys())
        selected_item = st.selectbox("รายการสินค้า", options, index=0)
        default_price = 0.0
        if selected_item != "-- เลือกสินค้า --":
            default_price = float(MENU_PRESETS.get(selected_item, 0.0))
    with c3:
        input_price = st.number_input("ราคาต่อชิ้น", value=default_price, step=1.0, format="%.2f")
    with c4:
        input_qty = st.number_input("จำนวน", min_value=1, step=1, value=1)

    if st.button("📥 บันทึกรายการนี้", type="primary", use_container_width=True):
        if selected_item == "-- เลือกสินค้า --":
            st.warning("กรุณาเลือกรายการสินค้า")
        else:
            total_val = input_price * input_qty
            new_row = pd.DataFrame([{
                'Date': input_date,
                'รายการ': selected_item,
                'ราคา': input_price,
                'จำนวน/ชิ้น': input_qty,
                'รวม/บาท': total_val
            }])
            st.session_state.df = pd.concat([new_row, st.session_state.df], ignore_index=True)
            try:
                conn.update(worksheet=get_current_sheet_name(), data=st.session_state.df)
                st.success(f"บันทึก '{selected_item}' เรียบร้อย!")
                st.rerun() 
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอัปโหลด: {e}")

st.divider()

# ==========================================
# ส่วนที่ 2: ตารางประวัติและแก้ไขข้อมูล (Editor)
# ==========================================
st.subheader("📝 ตารางรายการสินค้า (แก้ไขได้)")
st.info("💡 **วิธีใช้งาน:** เมื่อแก้ไข 'ราคา' หรือ 'จำนวน' ให้กด Enter ยอดรวมด้านล่างจะเปลี่ยนทันที แต่ในตารางจะเปลี่ยนเมื่อกดปุ่ม 'บันทึก' ครับ")

# แสดงตาราง Editor
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    column_config={
        "Date": st.column_config.DateColumn("วันที่", format="YYYY-MM-DD"),
        "รายการ": st.column_config.TextColumn("ชื่อสินค้า", required=True),
        "ราคา": st.column_config.NumberColumn("ราคาต่อชิ้น", format="%.2f"),
        "จำนวน/ชิ้น": st.column_config.NumberColumn("จำนวน"),
        "รวม/บาท": st.column_config.NumberColumn("รวมเงิน", disabled=True) 
    },
    use_container_width=True,
    key="history_editor"
)

# 🔥 [จุดสำคัญ] คำนวณยอดใหม่ทันทีที่มีการเปลี่ยนแปลงใน edited_df 🔥
# การคำนวณตรงนี้จะทำให้ตัวแปร edited_df มีค่าที่ถูกต้องเสมอ แม้ในตารางจะยังไม่โชว์
edited_df['รวม/บาท'] = edited_df['ราคา'] * edited_df['จำนวน/ชิ้น']

# ปุ่มบันทึกการแก้ไข
if st.button("💾 บันทึกการแก้ไขทั้งหมดขึ้น Cloud", type="secondary", use_container_width=True):
    # อัปเดตข้อมูลจริงเข้า Session
    st.session_state.df = edited_df
    # ส่งขึ้น Cloud
    conn.update(worksheet=get_current_sheet_name(), data=edited_df)
    st.toast("✅ บันทึกข้อมูลและคำนวณยอดเรียบร้อยแล้ว!", icon="💾")
    # รีเฟรชหน้าจอเพื่อให้ตารางแสดงเลขใหม่
    st.rerun()

st.divider()

# ==========================================
# ส่วนที่ 3: Dashboard สรุปยอด (Real-time)
# ==========================================
# ใช้ข้อมูลจาก edited_df (ที่เพิ่งคำนวณใหม่สดๆ) มาแสดงผล
# ทำให้เวลากดแก้ไขจำนวนปุ๊บ ตัวเลขสรุปตรงนี้จะเปลี่ยนทันที
today = datetime.now().date()
current_view_df = edited_df.copy() # ใช้ตัวแปรที่ผ่านการคูณแล้ว

if not current_view_df.empty:
    current_view_df['Date'] = pd.to_datetime(current_view_df['Date']).dt.date
    
    daily_sales = current_view_df[current_view_df['Date'] == today]['รวม/บาท'].sum()
    monthly_sales = current_view_df['รวม/บาท'].sum()
    items_today = current_view_df[current_view_df['Date'] == today]['จำนวน/ชิ้น'].sum()
else:
    daily_sales, monthly_sales, items_today = 0, 0, 0

st.subheader("📊 สรุปยอดขาย (Real-time)")
col1, col2, col3 = st.columns(3)
col1.metric("💰 ยอดรวมวันนี้", f"{daily_sales:,.2f} บาท")
col2.metric("📅 ยอดรวมเดือนนี้", f"{monthly_sales:,.2f} บาท")
col3.metric("📦 จำนวนชิ้นวันนี้", f"{items_today:,.0f} ชิ้น")

with st.expander("ดูสรุปยอดแยกตามวัน"):
    if not current_view_df.empty:
        summary_by_date = current_view_df.groupby('Date')[['จำนวน/ชิ้น', 'รวม/บาท']].sum().sort_index(ascending=False)
        st.dataframe(summary_by_date, use_container_width=True)
