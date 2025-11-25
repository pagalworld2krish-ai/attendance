import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime, date

# --- CONFIGURATION ---
ATTENDANCE_FILE = "attendance_log.csv" 
ADMIN_PASSWORD = "admin" 

st.set_page_config(page_title="School Attendance", layout="wide")

# --- SMART DATA LOADER ---
@st.cache_data
def load_data():
    """Smartly finds CSV files no matter where they are uploaded"""
    
    # 1. Get the folder where this app.py file is running
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Search for CSV files in common places
    # Option A: Are they right here? (Root)
    files = glob.glob(os.path.join(current_dir, "*.csv"))
    
    # Option B: Are they in a 'data' folder?
    if not files:
        files = glob.glob(os.path.join(current_dir, "data", "*.csv"))
        
    # Option C: Are they in a 'student_data' folder?
    if not files:
        files = glob.glob(os.path.join(current_dir, "student_data", "*.csv"))

    # --- DEBUGGING ASSISTANT ---
    # If we STILL find nothing, show the user exactly what is wrong
    if not files:
        st.error("⚠️ I cannot find your student CSV files.")
        st.write("I looked in this folder:", current_dir)
        st.write("I found these files instead:", os.listdir(current_dir))
        st.info("👉 Please ensure your student files end with .csv (not .xlsx) and are uploaded to GitHub.")
        return pd.DataFrame()

    # 3. Load the files we found
    df_list = []
    for filename in files:
        # Skip the attendance log file itself so we don't read it as a class
        if "attendance_log.csv" in filename:
            continue
            
        try:
            # Load CSV
            temp_df = pd.read_csv(filename, dtype=str)
            # Clean column names
            temp_df.columns = [c.strip() for c in temp_df.columns]
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"Skipped {os.path.basename(filename)}: {e}")
            
    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        # Fix column names to match your specific Excel format
        # Trying multiple common variations just in case
        final_df = final_df.rename(columns={
            'Class & Section': 'Class', 
            'Class': 'Class',
            'Mo.no': 'Phone',
            'Mobile': 'Phone'
        })
        return final_df
    
    return pd.DataFrame()

def save_absentees(class_name, absent_list):
    today = str(date.today())
    records = []
    if not absent_list:
        records.append([today, class_name, "ALL PRESENT", ""])
    else:
        for student in absent_list:
            records.append([today, class_name, student['Student Name'], student['Phone']])
            
    new_df = pd.DataFrame(records, columns=['Date', 'Class', 'Name', 'Phone'])
    
    if os.path.exists(ATTENDANCE_FILE):
        old_df = pd.read_csv(ATTENDANCE_FILE)
        old_df = old_df[~((old_df['Date'] == today) & (old_df['Class'] == class_name))]
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df
    final_df.to_csv(ATTENDANCE_FILE, index=False)

# --- APP LAYOUT ---
st.title("🏫 Attendance System")

df = load_data()

# Only show the app if data is loaded
if not df.empty:
    # Ensure Class column exists
    if 'Class' not in df.columns:
        st.error("❌ I found the CSV files, but I couldn't find a column named 'Class & Section'. Check your CSV headers.")
        st.write("Columns found:", df.columns.tolist())
        st.stop()

    class_list = sorted(df['Class'].dropna().unique())

    menu = st.sidebar.radio("Login As", ["Teacher", "Admin"])

    if menu == "Teacher":
        st.subheader("👩‍🏫 Mark Attendance")
        selected_class = st.selectbox("Select your Class", class_list)
        
        if selected_class:
            st.write(f"Date: **{date.today().strftime('%d-%m-%Y')}**")
            st.warning("Check the box ONLY if the student is **ABSENT**.")
            
            class_data = df[df['Class'] == selected_class].sort_values('Student Name')
            
            with st.form("attendance_form"):
                checkboxes = {}
                for index, row in class_data.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{row['Student Name']}**")
                    unique_key = f"{row['Student Name']}_{row['Phone']}"
                    checkboxes[index] = c2.checkbox("Absent", key=unique_key)
                
                if st.form_submit_button("Submit Attendance"):
                    absent_students = [class_data.loc[idx] for idx, checked in checkboxes.items() if checked]
                    save_absentees(selected_class, absent_students)
                    st.success("✅ Attendance Submitted Successfully!")

    elif menu == "Admin":
        st.subheader("👮‍♂️ Admin Dashboard")
        if st.sidebar.text_input("Password", type="password") == ADMIN_PASSWORD:
            if os.path.exists(ATTENDANCE_FILE):
                log = pd.read_csv(ATTENDANCE_FILE)
                today_log = log[log['Date'] == str(date.today())]
                
                st.metric("Classes Submitted", len(today_log['Class'].unique()))
                
                absentees = today_log[today_log['Name'] != "ALL PRESENT"]
                if not absentees.empty:
                    st.write("### 🔴 Today's Absentees")
                    st.dataframe(absentees)
                    
                    phone_text = "\n".join(absentees['Phone'].astype(str).str.replace(r'\.0$', '', regex=True))
                    st.download_button("Download Phone Numbers (.txt)", phone_text, "absentees.txt")
                else:
                    st.info("No absentees marked today yet.")
            else:
                st.info("No records found.")
