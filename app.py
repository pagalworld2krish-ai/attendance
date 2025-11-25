import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import glob
import os
# --- DEBUGGING CODE (Add this temporarily) ---
st.write("📂 Current Folder:", os.getcwd())
st.write("📄 Files found here:", os.listdir("."))
# ---------------------------------------------
# --- CONFIGURATION ---
DATA_FOLDER = "."  # Folder where your CSV files are
ATTENDANCE_FILE = "attendance_log.csv" 
ADMIN_PASSWORD = "admin" # You can change this password

st.set_page_config(page_title="School Attendance", layout="wide")

# --- FUNCTIONS ---
@st.cache_data
def load_data():
    """Loads all Class CSVs from the data folder"""
    all_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    df_list = []
    
    for filename in all_files:
        try:
            # Load CSV and force columns to be strings to prevent phone number errors
            temp_df = pd.read_csv(filename, dtype=str)
            # Clean column names (remove extra spaces)
            temp_df.columns = [c.strip() for c in temp_df.columns]
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {filename}: {e}")
            
    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        # Standardize column names based on your file
        final_df = final_df.rename(columns={
            'Class & Section': 'Class', 
            'Mo.no': 'Phone'
        })
        return final_df
    return pd.DataFrame()

def save_absentees(class_name, absent_list):
    """Saves data to a log file"""
    today = str(date.today())
    records = []
    
    # If nobody is absent, we still log that the teacher checked
    if not absent_list:
        records.append([today, class_name, "ALL PRESENT", ""])
    else:
        for student in absent_list:
            records.append([today, class_name, student['Student Name'], student['Phone']])
            
    new_df = pd.DataFrame(records, columns=['Date', 'Class', 'Name', 'Phone'])
    
    if os.path.exists(ATTENDANCE_FILE):
        old_df = pd.read_csv(ATTENDANCE_FILE)
        # Remove old entries for this class on this date (so teachers can update)
        old_df = old_df[~((old_df['Date'] == today) & (old_df['Class'] == class_name))]
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df
        
    final_df.to_csv(ATTENDANCE_FILE, index=False)

# --- APP LAYOUT ---
st.title("🏫 Attendance System")

# 1. Load Data
if not os.path.exists(DATA_FOLDER):
    st.error("Data folder not found. Please create a folder named 'data' and put your CSV files there.")
    st.stop()

df = load_data()
if df.empty:
    st.error("No student data found in CSV files.")
    st.stop()

# Get unique classes
class_list = sorted(df['Class'].dropna().unique())

# Sidebar Menu
menu = st.sidebar.radio("Login As", ["Teacher", "Admin"])

# --- TEACHER PAGE ---
if menu == "Teacher":
    st.subheader("👩‍🏫 Mark Attendance")
    selected_class = st.selectbox("Select your Class", class_list)
    
    if selected_class:
        st.write(f"Date: **{date.today().strftime('%d-%m-%Y')}**")
        st.warning("Check the box ONLY if the student is **ABSENT**.")
        
        # Filter students for this class
        class_data = df[df['Class'] == selected_class].sort_values('Student Name')
        
        with st.form("attendance_form"):
            col1, col2 = st.columns([3, 1])
            col1.write("**Student Name**")
            col2.write("**Mark Absent**")
            
            # Dictionary to store checkbox states
            checkboxes = {}
            
            for index, row in class_data.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(row['Student Name'])
                # Use Student Name + Phone as a unique key
                unique_key = f"{row['Student Name']}_{row['Phone']}"
                checkboxes[index] = c2.checkbox("Absent", key=unique_key)
            
            submit = st.form_submit_button("Submit Attendance")
            
            if submit:
                absent_students = []
                for idx, is_checked in checkboxes.items():
                    if is_checked:
                        absent_students.append(class_data.loc[idx])
                
                save_absentees(selected_class, absent_students)
                st.success("✅ Attendance Submitted Successfully!")

# --- ADMIN PAGE ---
elif menu == "Admin":
    st.subheader("👮‍♂️ Admin Dashboard")
    password = st.sidebar.text_input("Password", type="password")
    
    if password == ADMIN_PASSWORD:
        if not os.path.exists(ATTENDANCE_FILE):
            st.info("No attendance marked today yet.")
        else:
            log = pd.read_csv(ATTENDANCE_FILE)
            today = str(date.today())
            today_log = log[log['Date'] == today]
            
            # 1. Show Status
            classes_done = today_log['Class'].unique()
            classes_pending = set(class_list) - set(classes_done)
            
            c1, c2 = st.columns(2)
            c1.success(f"Classes Completed: {len(classes_done)}")
            c1.write(classes_done)
            c2.error(f"Classes Pending: {len(classes_pending)}")
            c2.write(list(classes_pending))
            
            st.divider()
            
            # 2. Download Phone Numbers
            st.write("### 📥 Download Absentee Phone Numbers")
            st.write("This file contains phone numbers of all students marked absent today.")
            
            # Filter actual absentees (exclude the "ALL PRESENT" markers)
            absentees_only = today_log[today_log['Name'] != "ALL PRESENT"]
            
            if not absentees_only.empty:
                st.dataframe(absentees_only)
                
                # Create text string of phone numbers
                # Clean phone numbers (remove decimals or spaces)
                phone_list = absentees_only['Phone'].astype(str).str.replace(r'\.0$', '', regex=True)
                text_data = "\n".join(phone_list)
                
                st.download_button(
                    label="Download Phone Numbers (.txt)",
                    data=text_data,
                    file_name=f"absent_numbers_{today}.txt",
                    mime="text/plain"
                )
            else:
                st.info("Attendance marked, but zero students are absent today.")
    elif password:
        st.error("Wrong Password")


