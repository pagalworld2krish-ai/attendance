import streamlit as st
import pandas as pd
import os
from datetime import date
import glob
import json

# ---------- MOBILE UI SETTINGS ----------
st.set_page_config(page_title="Attendance", layout="wide")

# Hide sidebar + mobile styling
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
.block-container {padding: 1rem;}
button {
    height: 55px;
    font-size: 18px !important;
    border-radius: 10px;
}
.stTextInput>div>div>input {
    height: 50px;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ---------- CONFIG ----------
DATA_FOLDER = "data"
ATTENDANCE_FILE = "attendance_log.csv"
PASSWORD_FILE = "teacher_passwords.json"
ADMIN_PASSWORD = "admin"

# ---------- TEACHERS ----------
TEACHERS = {
    "IX-A": "Ms.Ruchita Celeste",
    "IX-B": "Mr.Ramkrishna Shukla",
    "IX-C": "Mr.Ravindra K W Alexander",
    "IX-D": "Mr.Aditya Mishra",
    "X-A": "Ms.Swati Srivastava",
    "X-B": "Ms.Jyoti Mishra",
    "X-C": "Mr.Saurav Daurka",
    "X-D": "Ms.Shikha Chaudhary",
    "XII-A": "Mr.Anurag Mishra",
    "XII-B": "Mr.Nafees Ahmad",
    "XII-C": "Mr.Ajay Shukla"
}

# ---------- PASSWORD SYSTEM ----------
def load_passwords():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            return json.load(f)
    return {cls: "123" for cls in TEACHERS}

def save_passwords(p):
    with open(PASSWORD_FILE, "w") as f:
        json.dump(p, f)

passwords = load_passwords()

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    df_list = []

    for f in files:
        temp = pd.read_csv(f, dtype=str)
        temp.columns = [c.strip() for c in temp.columns]
        df_list.append(temp)

    if df_list:
        df = pd.concat(df_list, ignore_index=True)
        df = df.rename(columns={
            "Class & Section": "Class",
            "Mo.no": "Phone"
        })
        df["Class"] = df["Class"].str.strip().str.upper().str.replace(" ", "-")
        return df

    return pd.DataFrame()

# ---------- SAVE ATTENDANCE ----------
def save_attendance(class_name, absent):
    today = str(date.today())
    records = []

    if not absent:
        records.append([today, class_name, "ALL PRESENT", ""])
    else:
        for s in absent:
            records.append([today, class_name, s["Student Name"], s["Phone"]])

    new_df = pd.DataFrame(records, columns=["Date","Class","Name","Phone"])

    if os.path.exists(ATTENDANCE_FILE):
        old = pd.read_csv(ATTENDANCE_FILE)
        old = old[~((old["Date"] == today) & (old["Class"] == class_name))]
        final = pd.concat([old, new_df], ignore_index=True)
    else:
        final = new_df

    final.to_csv(ATTENDANCE_FILE, index=False)

# ---------- LOAD ----------
df = load_data()
if df.empty:
    st.error("No student data found")
    st.stop()

# ---------- HOME ----------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------- HOME SCREEN ----------
if st.session_state.page == "home":
    st.title("🏫 Attendance App")

    st.write("### Select Login Type")

    col1, col2 = st.columns(2)

    if col1.button("👩‍🏫 Teacher Login"):
        st.session_state.page = "teacher_login"

    if col2.button("👮 Admin Login"):
        st.session_state.page = "admin"

# ---------- TEACHER LOGIN ----------
elif st.session_state.page == "teacher_login":

    st.title("👩‍🏫 Teacher Login")

    class_selected = st.selectbox("Select Class", list(TEACHERS.keys()))
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if passwords[class_selected] == password_input:
            st.session_state.page = "teacher_panel"
            st.session_state.class_name = class_selected
        else:
            st.error("Wrong Password")

    if st.button("⬅ Back"):
        st.session_state.page = "home"

# ---------- TEACHER PANEL ----------
elif st.session_state.page == "teacher_panel":

    class_name = st.session_state.class_name
    teacher_name = TEACHERS[class_name]

    st.title(f"👩‍🏫 {teacher_name}")
    st.write(f"📘 Class: {class_name}")
    st.write(f"📅 {date.today()}")

    st.info("✔ Tick absent students. You can resubmit anytime.")

    class_data = df[df["Class"] == class_name].sort_values("Student Name")

    with st.form("attendance"):
        checks = {}

        for i, row in class_data.iterrows():
            col1, col2 = st.columns([3,1])
            col1.write(row["Student Name"])
            key = f"{row['Student Name']}_{row['Phone']}"
            checks[i] = col2.checkbox("Absent", key=key)

        if st.form_submit_button("✅ Submit Attendance"):
            absent = [class_data.loc[i] for i,v in checks.items() if v]
            save_attendance(class_name, absent)
            st.success("Attendance Saved")

    # Change password
    st.divider()
    st.subheader("🔑 Change Password")

    new_pass = st.text_input("New Password", type="password")

    if st.button("Update Password"):
        passwords[class_name] = new_pass
        save_passwords(passwords)
        st.success("Password Updated")

    if st.button("🚪 Logout"):
        st.session_state.page = "home"

# ---------- ADMIN ----------
elif st.session_state.page == "admin":

    st.title("👮 Admin Login")

    password = st.text_input("Password", type="password")

    if password == ADMIN_PASSWORD:

        st.success("Login Successful")

        if os.path.exists(ATTENDANCE_FILE):
            log = pd.read_csv(ATTENDANCE_FILE)

            st.subheader("📊 View Attendance")

            selected_date = st.date_input("Select Date", value=date.today())
            selected_class = st.selectbox("Select Class", sorted(df["Class"].unique()))

            filtered = log[
                (log["Date"] == str(selected_date)) &
                (log["Class"] == selected_class)
            ]

            if not filtered.empty:
                st.dataframe(filtered)
            else:
                st.warning("No data found")

            st.divider()

            st.subheader("📥 Download Absentees")

            absentees = filtered[filtered["Name"] != "ALL PRESENT"]

            if not absentees.empty:
                phones = absentees["Phone"].astype(str).str.replace(r'\.0$', '', regex=True)
                text = "\n".join(phones)

                st.download_button("Download Numbers", text)
            else:
                st.info("No absentees")

    elif password:
        st.error("Wrong Password")

    if st.button("⬅ Back"):
        st.session_state.page = "home"
