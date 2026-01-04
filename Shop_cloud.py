import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. การตั้งค่าและการเชื่อมต่อ ---
st.set_page_config(page_title="ระบบบันทึกการเบิกของ", layout="wide")

def get_current_sheet_name():
    return datetime.now().strftime("%b_%Y")

conn = st.connection("gsheets", type=GSheetsConnection)

# ฟังก์ชันโหลดข้อมูลจาก Cloud
def load_data():
    current_sheet = get_current_sheet_name()
    try:
        df = conn.read(worksheet=current_sheet)
        if df.empty: return pd.DataFrame(columns=['Date', 'รายการ', 'ราคา', 'จำนวน/ชิ้น', 'รวม/บาท'])
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except Exception:
        return pd.DataFrame(columns=['Date', 'รายการ', 'ราคา', 'จำนวน/ชิ้น', 'รวม/บาท'])

# โหลดข้อมูลเริ่มต้น
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- 2. ส่วนของแบบฟอร์มบันทึกข้อมูล (Input Form) ---
st.title("🍰 แบบฟอร์มบันทึกการเบิกของหน้าร้าน")
st.subheader(f"📅 ประจำเดือน: {get_current_sheet_name()}")

# สร้าง Form สำหรับบันทึก
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
    
    with col1:
        input_date = st.date_input("วันที่", value=datetime.now().date())
    with col2:
        input_item = st.text_input("รายการสินค้า")
    with col3:
        input_price = st.number_input("ราคาต่อชิ้น", min_value=0.0, step=1.0)
    with col4:
        input_qty = st.number_input("จำนวน", min_value=0, step=1)
    
    submit_button = st.form_submit_button("💾 บันทึกข้อมูลและอัปโหลด")

# เมื่อกดปุ่มบันทึก
if submit_button:
    if input_item == "":
        st.warning("กรุณากรอกชื่อรายการสินค้า")
    else:
        # 1. คำนวณยอดรวมอัตโนมัติ
        total_price = input_price * input_qty
        
        # 2. สร้างข้อมูลแถวใหม่
        new_data = pd.DataFrame([{
            'Date': input_date,
            'รายการ': input_item,
            'ราคา': input_price,
            'จำนวน/ชิ้น': input_qty,
            'รวม/บาท': total_price
        }])
        
        # 3. รวมข้อมูลใหม่เข้ากับข้อมูลเดิมที่มีอยู่
        st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
        
        # 4. อัปโหลดขึ้น Google Sheets (ถ้ายังไม่มี Sheet ให้สร้างใหม่)
        current_sheet = get_current_sheet_name()
        try:
            conn.update(worksheet=current_sheet, data=st.session_state.df)
        except Exception:
            conn.create(worksheet=current_sheet, data=st.session_state.df)
            
        st.success(f"บันทึก '{input_item}' เรียบร้อยแล้ว และอัปโหลดขึ้น Cloud แล้ว!")
        st.rerun()

st.divider()

# --- 3. ส่วนสรุปยอดขาย (Dashboard) ---
current_df = st.session_state.df

if not current_df.empty:
    st.subheader("📊 สรุปยอดขายปัจจุบัน")
    c1, c2, c3 = st.columns(3)
    
    today = datetime.now().date()
    daily_total = current_df[current_df['Date'] == today]['รวม/บาท'].sum()
    monthly_total = current_df['รวม/บาท'].sum()
    total_qty = current_df[current_df['Date'] == today]['จำนวน/ชิ้น'].sum()
    
    c1.metric("ยอดรวมวันนี้", f"{daily_total:,.2f} บาท")
    c2.metric("ยอดรวมเดือนนี้", f"{monthly_total:,.2f} บาท")
    c3.metric("จำนวนชิ้นวันนี้", f"{total_qty:,.0f} ชิ้น")

    st.divider()

    # --- 4. ส่วนตารางสรุปรายวัน และ การแก้ไขข้อมูล ---
    tab1, tab2 = st.tabs(["📅 สรุปยอดแยกตามวัน", "📝 รายการทั้งหมด (ดู/แก้ไข/ลบ)"])
    
    with tab1:
        summary_by_date = current_df.groupby('Date')[['จำนวน/ชิ้น', 'รวม/บาท']].sum().sort_index(ascending=False)
        st.table(summary_by_date)
        
    with tab2:
        st.write("คุณสามารถแก้ไขข้อมูลในตารางนี้ได้ และกดปุ่มอัปเดตด้านล่างหากมีการแก้ไข")
        edited_all_df = st.data_editor(current_df, num_rows="dynamic", use_container_width=True, key="main_editor")
        
        if st.button("🔄 อัปเดตการแก้ไขทั้งหมดขึ้น Cloud"):
            edited_all_df['รวม/บาท'] = edited_all_df['ราคา'] * edited_df['จำนวน/ชิ้น'] # Re-calc ก่อนเซฟ
            st.session_state.df = edited_all_df
            conn.update(worksheet=get_current_sheet_name(), data=edited_all_df)
            st.success("อัปเดตข้อมูลบน Cloud เรียบร้อย!")
            st.rerun()
else:
    st.info("ยังไม่มีข้อมูลบันทึกในเดือนนี้")
