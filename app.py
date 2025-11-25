import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
ATTENDANCE_LOG_FILE = "attendance_log.csv"
ADMIN_PASSWORD = "admin"

st.set_page_config(page_title="School Attendance", layout="wide")

@st.cache_data
def load_data_universal():
    """Searches EVERY folder to find CSV files."""
    found_files = []
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Walk through every folder in the repository
    for current_root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".csv"):
                if file == ATTENDANCE_LOG_FILE:
                    continue
                full_path = os.path.join(current_root, file)
                found_files.append(full_path)

    if not found_files:
        st.error("❌ No Student CSV files found.")
        return pd.DataFrame()

    df_list = []
    for filepath in found_files:
        try:
            # FORCE ALL COLUMNS TO BE STRINGS (TEXT) TO AVOID ERRORS
            temp_df = pd.read_csv(filepath, dtype=str)
            temp_df.columns = [c.strip() for c in temp_df.columns]
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"Skipped file: {os.path.basename(filepath)}")

    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        final_df = final_df.rename(columns={
            'Class & Section': 'Class', 
            'Mo.no': 'Phone',
            'Mobile': 'Phone'
        })
        return final_df
    
    return pd.DataFrame()

# --- APP LOGIC ---
st.title("🏫 Attendance System")

df = load_data_universal()

if not df.empty:
    if 'Class' not in df.columns:
        st.error("❌ 'Class' column missing in CSV files.")
    else:
        menu = st.sidebar.radio("Login As", ["Teacher", "Admin"])

        if menu == "Teacher":
            st.subheader("👩‍🏫 Teacher View")
            class_list = sorted(df['Class'].dropna().unique())
            selected_class = st.selectbox("Select Class", class_list)

            if selected_class:
                st.write(f"Marking for: **{selected_class}**")
                students = df[df['Class'] == selected_class].sort_values('Student Name')
                
                with st.form("attendance_form"):
                    checkboxes = {}
                    for idx, row in students.iterrows():
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"**{row['Student Name']}**")
                        # Create unique key
                        checkboxes[idx] = c2.checkbox("Absent", key=f"{row['Phone']}_{idx}")
                    
                    if st.form_submit_button("Submit Attendance"):
                        today = str(pd.Timestamp.now().date())
                        
                        # Get absent students
                        absent_list = [students.loc[i] for i, c in checkboxes.items() if c]
                        
                        new_data = []
                        if not absent_list:
                            new_data.append([today, selected_class, "ALL PRESENT", ""])
                        else:
                            for s in absent_list:
                                # CLEAN PHONE NUMBER: Force to string, remove decimals
                                raw_phone = str(s['Phone'])
                                clean_phone = raw_phone.replace('.0', '').replace('nan', '')
                                new_data.append([today, selected_class, s['Student Name'], clean_phone])
                        
                        # Create dataframe and FORCE STRING TYPE
                        new_df = pd.DataFrame(new_data, columns=['Date', 'Class', 'Name', 'Phone'])
                        new_df = new_df.astype(str) # <--- THIS FIXES THE ERROR
                        
                        # Append to file
                        if os.path.exists(ATTENDANCE_LOG_FILE):
                            # Read old file as STRING to match new data
                            old_df = pd.read_csv(ATTENDANCE_LOG_FILE, dtype=str)
                            old_df = old_df[~((old_df['Date'] == today) & (old_df['Class'] == selected_class))]
                            final_log = pd.concat([old_df, new_df], ignore_index=True)
                        else:
                            final_log = new_df
                        
                        final_log.to_csv(ATTENDANCE_LOG_FILE, index=False)
                        st.success("✅ Saved Successfully!")

        elif menu == "Admin":
            st.header("Admin Dashboard")
            pwd = st.sidebar.text_input("Password", type="password")
            if pwd == ADMIN_PASSWORD:
                if os.path.exists(ATTENDANCE_LOG_FILE):
                    # Read as STRING to prevent errors
                    log = pd.read_csv(ATTENDANCE_LOG_FILE, dtype=str)
                    today = str(pd.Timestamp.now().date())
                    today_recs = log[log['Date'] == today]
                    
                    st.dataframe(today_recs)
                    
                    absentees = today_recs[today_recs['Name'] != "ALL PRESENT"]
                    if not absentees.empty:
                        txt = "\n".join(absentees['Phone'].tolist())
                        st.download_button("Download Absentees", txt, "absent.txt")
                else:
                    st.info("No records yet.")

# --- PASTE AT THE BOTTOM OF APP.PY ---
st.sidebar.divider()
st.sidebar.subheader("📊 Data Check")
if not df.empty:
    # Shows count of students per class
    st.sidebar.write(df['Class'].value_counts())
else:
    st.sidebar.warning("No data loaded")
