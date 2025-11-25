import streamlit as st
import pandas as pd
import os
import glob
from datetime import date

# --- CONFIGURATION ---
DATA_FOLDER_NAME = "Data" 
ATTENDANCE_LOG_FILE = "attendance_log.csv"
ADMIN_PASSWORD = "admin"

st.set_page_config(page_title="School Attendance", layout="wide")

@st.cache_data
def load_data_strict():
    """Only loads CSVs from the specific Data folder."""
    # 1. Locate the Data folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(current_dir, DATA_FOLDER_NAME)
    
    # 2. Safety Check: Does folder exist?
    if not os.path.exists(target_path):
        st.error(f"❌ Error: I cannot find a folder named '{DATA_FOLDER_NAME}'.")
        return pd.DataFrame()
        
    # 3. Get all CSV files inside THAT folder only
    files = glob.glob(os.path.join(target_path, "*.csv"))
    
    if not files:
        st.error(f"❌ The '{DATA_FOLDER_NAME}' folder is empty or has no .csv files.")
        return pd.DataFrame()

    df_list = []
    for filepath in files:
        try:
            # Force everything to be Text (String) to avoid errors
            temp_df = pd.read_csv(filepath, dtype=str)
            # Clean extra spaces from column names
            temp_df.columns = [c.strip() for c in temp_df.columns]
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"Skipped {os.path.basename(filepath)}: {e}")

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

# --- MAIN APP ---
st.title("🏫 Attendance System")

df = load_data_strict()

if not df.empty:
    # Ensure Class column exists
    if 'Class' not in df.columns:
        st.error("❌ Data loaded, but 'Class' column is missing.")
    else:
        # --- SIDEBAR ---
        menu = st.sidebar.radio("Login As", ["Teacher", "Admin"])

        # --- TEACHER VIEW ---
        if menu == "Teacher":
            st.subheader("👩‍🏫 Teacher View")
            # Sort classes alphabetically
            classes = sorted(df['Class'].dropna().unique())
            selected = st.selectbox("Select Class", classes)
            
            if selected:
                st.info(f"Marking: {selected}")
                # Filter students for selected class
                students = df[df['Class'] == selected].sort_values('Student Name')
                
                with st.form("att_form"):
                    checks = {}
                    for idx, row in students.iterrows():
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"**{row['Student Name']}**")
                        # Unique key for every checkbox
                        checks[idx] = c2.checkbox("Absent", key=f"{row['Phone']}_{idx}")
                    
                    if st.form_submit_button("Submit"):
                        # Save Logic
                        today = str(date.today())
                        absent = [students.loc[i] for i, c in checkboxes.items() if c]
                        
                        new_data = []
                        if not absent:
                            new_data.append([today, selected, "ALL PRESENT", ""])
                        else:
                            for s in absent:
                                # Clean phone numbers (remove .0 or nan)
                                clean_ph = str(s['Phone']).replace('.0', '').replace('nan', '')
                                new_data.append([today, selected, s['Student Name'], clean_ph])
                        
                        # Create DataFrame and FORCE TEXT FORMAT
                        new_df = pd.DataFrame(new_data, columns=['Date', 'Class', 'Name', 'Phone'])
                        new_df = new_df.astype(str)
                        
                        # Append to CSV
                        if os.path.exists(ATTENDANCE_LOG_FILE):
                            old = pd.read_csv(ATTENDANCE_LOG_FILE, dtype=str)
                            # Overwrite previous entry for this class/today
                            old = old[~((old['Date'] == today) & (old['Class'] == selected))]
                            final = pd.concat([old, new_df], ignore_index=True)
                        else:
                            final = new_df
                        
                        final.to_csv(ATTENDANCE_LOG_FILE, index=False)
                        st.success("✅ Saved Successfully!")

        # --- ADMIN VIEW ---
        elif menu == "Admin":
            st.header("Admin")
            if st.sidebar.text_input("Password", type="password") == ADMIN_PASSWORD:
                if os.path.exists(ATTENDANCE_LOG_FILE):
                    log = pd.read_csv(ATTENDANCE_LOG_FILE, dtype=str)
                    today = str(date.today())
                    today_log = log[log['Date'] == today]
                    
                    st.write(f"### 📅 Report for {today}")
                    st.dataframe(today_log)
                    
                    # Download Button
                    absentees = today_log[today_log['Name'] != "ALL PRESENT"]
                    if not absentees.empty:
                        txt = "\n".join(absentees['Phone'].tolist())
                        st.download_button("Download Phone Numbers", txt, "absent.txt")
                else:
                    st.info("No attendance marked yet.")
