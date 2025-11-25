import streamlit as st
import pandas as pd
import os
import glob
from datetime import date

# --- CONFIGURATION ---
# We use "Data" with a capital D because that is your folder name
DATA_FOLDER = "Data"
ATTENDANCE_FILE = "attendance_log.csv" 
ADMIN_PASSWORD = "admin"

st.set_page_config(page_title="School Attendance", layout="wide")

@st.cache_data
def load_data():
    # 1. Get the current directory where app.py is
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Build the path to the "Data" folder
    target_folder = os.path.join(current_dir, DATA_FOLDER)
    
    # 3. Find all CSV files inside "Data"
    files = glob.glob(os.path.join(target_folder, "*.csv"))
    
    # --- DEBUG HELP ---
    if not files:
        st.error(f"❌ No CSV files found in '{DATA_FOLDER}' folder.")
        st.write(f"I am looking at this path: {target_folder}")
        
        if os.path.exists(target_folder):
             st.write(f"The folder '{DATA_FOLDER}' exists, but it contains:", os.listdir(target_folder))
        else:
             st.write(f"⚠️ I cannot even find the folder '{DATA_FOLDER}'.")
             st.write("Folders I DO see here:", os.listdir(current_dir))
        return pd.DataFrame()
    # ------------------

    df_list = []
    for filename in files:
        try:
            # Read CSV
            temp_df = pd.read_csv(filename, dtype=str)
            # Clean header names
            temp_df.columns = [c.strip() for c in temp_df.columns]
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"⚠️ Could not read {os.path.basename(filename)}: {e}")

    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        # Rename columns to match your Excel format
        final_df = final_df.rename(columns={
            'Class & Section': 'Class', 
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
            records.append([today, class_name, student['Name'], student['Phone']])
            
    new_df = pd.DataFrame(records, columns=['Date', 'Class', 'Name', 'Phone'])
    
    if os.path.exists(ATTENDANCE_FILE):
        old_df = pd.read_csv(ATTENDANCE_FILE)
        old_df = old_df[~((old_df['Date'] == today) & (old_df['Class'] == class_name))]
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df
    final_df.to_csv(ATTENDANCE_FILE, index=False)

# --- MAIN APP ---
st.title("🏫 Attendance System")
df = load_data()

if not df.empty:
    if 'Class' not in df.columns:
        st.error("❌ Files loaded, but column 'Class & Section' is missing.")
        st.write("Columns found:", df.columns.tolist())
    else:
        menu = st.sidebar.radio("Menu", ["Teacher", "Admin"])
        
        if menu == "Teacher":
            st.header("👩‍🏫 Teacher View")
            classes = sorted(df['Class'].dropna().unique())
            selected = st.selectbox("Select Class", classes)
            
            if selected:
                st.write(f"Marking for: **{selected}**")
                students = df[df['Class'] == selected].sort_values('Student Name')
                
                with st.form("att"):
                    checks = {}
                    for idx, row in students.iterrows():
                        c1, c2 = st.columns([3,1])
                        c1.write(row['Student Name'])
                        checks[idx] = c2.checkbox("Absent", key=row['Phone'])
                    
                    if st.form_submit_button("Submit"):
                        absent = [students.loc[i] for i, c in checks.items() if c]
                        save_absentees(selected, absent)
                        st.success("Done!")

        elif menu == "Admin":
            st.header("Admin")
            if st.sidebar.text_input("Password", type="password") == ADMIN_PASSWORD:
                if os.path.exists(ATTENDANCE_FILE):
                    log = pd.read_csv(ATTENDANCE_FILE)
                    today_recs = log[log['Date'] == str(date.today())]
                    st.dataframe(today_recs)
                    
                    absent_only = today_recs[today_recs['Name'] != "ALL PRESENT"]
                    if not absent_only.empty:
                        nums = "\n".join(absent_only['Phone'].astype(str).tolist())
                        st.download_button("Download Numbers", nums, "absentees.txt")
