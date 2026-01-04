import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import io
import time

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Nami POS System",
    page_icon="🍰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ข้อมูลเมนูสินค้าตั้งต้น (Master Data)
INITIAL_CSV = """Date,รายการ,ราคา,จำนวน/ชิ้น,รวม/บาท
2026-01-01,เค้กนมสด,50,0,0
2026-01-01,เค้กญี่ปุ่น,60,0,0
2026-01-01,เค้ก 60 บาท,90,0,0
2026-01-01,ชีสเค้ก,60,0,0
2026-01-01,คุกกี้ป๊อป,25,0,0
2026-01-01,เค้กป๊อป,75,0,0
2026-01-01,มาการองการ์ตูน,70,0,0
2026-01-01,คอนเฟลค,100,0,0
2026-01-01,ช็อคบอล 30,30,0,0
2026-01-01,ช็อคบอล 20,20,0,0
2026-01-01,ชาชงสด,40,0,0
2026-01-01,cold brew,65,0,0
2026-01-01,ลาบูบู้,159,0,0
2026-01-01,คุกกี้เนย,39,0,0
2026-01-01,เมอแรง,35,0,0
2026-01-01,กล่องเค้ก 4,35,0,0
2026-01-01,กล่องเค้ก 12ชี้น,65,0,0
2026-01-01,กล่องเค้ก 24,120,0,0
2026-01-01,กล่องเค้ก 36,100,0,0
2026-01-01,พริกทอด,110,0,0
2026-01-01,เจ้าหญิง/แคร์แบร์,79,0,0
2026-01-01,ถุงผ้า nami,40,0,0
2026-01-01,แก้วน้ำนามิ,0,0,0
2026-01-01,อื่นๆ,0,0,0
2026-01-01,cake pop,65,0,0
2026-01-01,กะบอกน๋า,0,0,0
2026-01-01,cake orange,45,0,0"""

# เชื่อมต่อ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. HELPER FUNCTIONS ---

def get_current_sheet_name():
    return datetime.now().strftime("%b_%Y")

def get_menu_dict():
    """แปลง CSV เป็น Dictionary {ชื่อสินค้า: ราคา}"""
    try:
        df = pd.read_csv(io.StringIO(INITIAL_CSV))
        menu = df[['รายการ', 'ราคา']].drop_duplicates(subset='รายการ')
        return dict(zip(menu['รายการ'], menu['ราคา']))
    except:
        return {}

def load_data():
    """โหลดข้อมูลจาก Cloud หรือสร้างใหม่ถ้าไม่มี"""
    try:
        df = conn.read(worksheet=get_current_sheet_name())
        if df.empty:
             # ใช้ Header จาก CSV แต่ไม่เอาข้อมูล
            df = pd.read_csv(io.StringIO(INITIAL_CSV)).head(0)
        
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except:
        # Fallback กรณีต่อเน็ตไม่ได้
        df = pd.read_csv(io.StringIO(INITIAL_CSV)).head(0)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df

def save_to_cloud(df):
    """บันทึกข้อมูลลง Cloud"""
    try:
        conn.update(worksheet=get_current_sheet_name(), data=df)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# --- 3. STATE MANAGEMENT ---
if 'df' not in st.session_state:
    st.session_state.df = load_data()

if 'menu_items' not in st.session_state:
    st.session_state.menu_items = get_menu_dict()

# ตัวแปรสำหรับ Reset Form
if 'reset_trigger' not in st.session_state:
    st.session_state.reset_trigger = False

# --- 4. UI LAYOUT ---

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🍰 Nami Shop POS")
    st.caption(f"ระบบบันทึกยอดขายประจำเดือน: **{get_current_sheet_name()}**")
with c2:
    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
        st.cache_data.clear()
        st.session_state.df = load_data()
        st.rerun()

st.divider()

# สร้าง Tab แยกหน้าทำงาน
tab_pos, tab_dashboard, tab_admin = st.tabs(["🛒 หน้าขาย (Cashier)", "📊 แดชบอร์ดสรุปยอด", "⚙️ จัดการข้อมูล (Admin)"])

# ==========================================
# TAB 1: หน้าขาย (CASHIER)
# ==========================================
with tab_pos:
    col_input, col_recent = st.columns([1.5, 2])

    with col_input:
        st.subheader("📝 บันทึกรายการ")
        
        with st.container(border=True):
            # Input Fields
            # วันที่
            pick_date = st.date_input("วันที่ทำรายการ", value=datetime.now().date())
            
            # เลือกสินค้า
            options = ["-- เลือกสินค้า --"] + list(st.session_state.menu_items.keys())
            item_selected = st.selectbox("เลือกสินค้า", options, index=0, key="pos_item")
            
            # ราคา (Auto Fill)
            price_default = 0.0
            if item_selected != "-- เลือกสินค้า --":
                price_default = float(st.session_state.menu_items.get(item_selected, 0))
            
            # แสดงราคาและจำนวน
            c_price, c_qty = st.columns(2)
            with c_price:
                price_val = st.number_input("ราคา", value=price_default, min_value=0.0, step=1.0, key="pos_price")
            with c_qty:
                qty_val = st.number_input("จำนวน", value=1, min_value=1, step=1, key="pos_qty")
            
            # คำนวณยอดรวม Realtime
            total_calc = price_val * qty_val
            st.markdown(f"#### 💰 รวม: `{total_calc:,.0f}` บาท")
            
            # ปุ่มบันทึก (ใหญ่ๆ)
            if st.button("บันทึกรายการ (Save)", type="primary", use_container_width=True):
                if item_selected == "-- เลือกสินค้า --":
                    st.error("กรุณาเลือกสินค้าก่อนครับ")
                else:
                    # Logic บันทึก
                    new_row = pd.DataFrame([{
                        'Date': pick_date,
                        'รายการ': item_selected,
                        'ราคา': price_val,
                        'จำนวน/ชิ้น': qty_val,
                        'รวม/บาท': total_calc
                    }])
                    
                    # 1. Update Session
                    st.session_state.df = pd.concat([new_row, st.session_state.df], ignore_index=True)
                    
                    # 2. Update Cloud
                    with st.spinner("กำลังส่งข้อมูลขึ้น Cloud..."):
                        if save_to_cloud(st.session_state.df):
                            st.toast(f"บันทึก {item_selected} เรียบร้อย!", icon="✅")
                            time.sleep(0.5) # หน่วงเวลานิดนึงให้เห็น Toast
                            st.rerun() # รีเซ็ตหน้าจอ

    with col_recent:
        st.subheader("🕒 รายการล่าสุด (วันนี้)")
        
        # Filter ดูเฉพาะวันนี้
        today = datetime.now().date()
        today_df = st.session_state.df[st.session_state.df['Date'] == today].copy()
        
        if not today_df.empty:
            # โชว์แค่ 10 รายการล่าสุด
            show_df = today_df.tail(10).iloc[::-1] # กลับด้านให้ล่าสุดอยู่บน
            
            # แต่งตารางให้สวย
            st.dataframe(
                show_df[['รายการ', 'ราคา', 'จำนวน/ชิ้น', 'รวม/บาท']], 
                hide_index=True, 
                use_container_width=True,
                height=400
            )
        else:
            st.info("ยังไม่มีรายการขายวันนี้")

# ==========================================
# TAB 2: แดชบอร์ด (DASHBOARD)
# ==========================================
with tab_dashboard:
    df = st.session_state.df
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        today = datetime.now().date()
        
        # คำนวณ
        daily_sales = df[df['Date'] == today]['รวม/บาท'].sum()
        daily_qty = df[df['Date'] == today]['จำนวน/ชิ้น'].sum()
        monthly_sales = df['รวม/บาท'].sum()
        monthly_qty = df['จำนวน/ชิ้น'].sum()

        # Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ยอดขายวันนี้", f"{daily_sales:,.0f} ฿", delta="รายวัน")
        m2.metric("จำนวนชิ้นวันนี้", f"{daily_qty:,.0f} ชิ้น")
        m3.metric("ยอดขายทั้งเดือน", f"{monthly_sales:,.0f} ฿", delta="สะสม")
        m4.metric("จำนวนชิ้นทั้งเดือน", f"{monthly_qty:,.0f} ชิ้น")
        
        st.divider()
        
        # กราฟ/ตารางสรุปรายวัน
        st.subheader("📅 สรุปยอดขายรายวัน")
        daily_summary = df.groupby('Date')[['รวม/บาท']].sum().sort_index(ascending=False)
        st.bar_chart(daily_summary)
        
    else:
        st.warning("ยังไม่มีข้อมูลในระบบ")

# ==========================================
# TAB 3: หลังบ้าน (ADMIN / EDIT)
# ==========================================
with tab_admin:
    st.markdown("### 🛠️ แก้ไขข้อมูลย้อนหลัง")
    st.info("หน้านี้สำหรับแก้ไขข้อมูลที่ผิดพลาด หรือลบรายการทิ้ง")
    
    # Editor Mode
    edited_df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.DateColumn("วันที่", format="YYYY-MM-DD"),
            "รวม/บาท": st.column_config.NumberColumn("รวมเงิน", disabled=True) # ล็อกช่องรวม
        },
        use_container_width=True,
        key="admin_editor"
    )
    
    col_save_edit, col_dummy = st.columns([1, 4])
    with col_save_edit:
        if st.button("💾 บันทึกการแก้ไขทั้งหมด", type="primary"):
            # Recalculate Total
            edited_df['รวม/บาท'] = edited_df['ราคา'] * edited_df['จำนวน/ชิ้น']
            
            # Save
            st.session_state.df = edited_df
            if save_to_cloud(edited_df):
                st.success("อัปเดตข้อมูลบน Cloud เรียบร้อย!")
                time.sleep(1)
                st.rerun()
