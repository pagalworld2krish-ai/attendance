import streamlit as st
import pandas as pd
import os
from datetime import date
import glob
import json

# ---------- CONFIG ----------
DATA_FOLDER = "data"
ATTENDANCE_FILE = "attendance_log.csv"
PASSWORD_FILE = "teacher_passwords.json"
ADMIN_PASSWORD = "admin"

st.set_page_config(page_title="Attendance", layout="wide")

# ---------- MOBILE UI ----------
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
button {height:55px; font-size:18px;}
</style>
""", unsafe_allow_html=True)

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

# ---------- PASSWORD ----------
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

# ---------- INIT ----------
df = load_data()
if df.empty:
    st.error("No data found")
    st.stop()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------- HOME ----------
if not st.session_state.logged_in:
    st.title("🏫 Attendance App")

    role = st.radio("Select Role", ["Teacher", "Admin"])

    if role == "Teacher":
        cls = st.selectbox("Select Class", list(TEACHERS.keys()))
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            if passwords[cls] == pwd:
                st.session_state.logged_in = True
                st.session_state.class_name = cls
                st.rerun()
            else:
                st.error("Wrong Password")

    else:
        pwd = st.text_input("Admin Password", type="password")

        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Wrong Password")

# ---------- TEACHER ----------
elif "class_name" in st.session_state:

    cls = st.session_state.class_name
    teacher = TEACHERS[cls]

    st.title(f"👩‍🏫 {teacher}")
    st.write(f"📘 {cls}")
    st.write(f"📅 {date.today().strftime('%d/%m/%Y')}")

    class_data = df[df["Class"] == cls].sort_values("Student Name")

    st.subheader("Mark Attendance")

    checks = {}
    for i, row in class_data.iterrows():
        col1, col2 = st.columns([3,1])
        col1.write(row["Student Name"])
        key = f"{row['Student Name']}_{row['Phone']}"
        checks[i] = col2.checkbox("Absent", key=key)

    if st.button("✅ Update Attendance"):
        absent = [class_data.loc[i] for i,v in checks.items() if v]
        save_attendance(cls, absent)
        st.success("Attendance Updated")

    # ---------- PASSWORD ----------
    st.divider()
    st.subheader("🔑 Change Password")

    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm Password", type="password")

    if st.button("Update Password"):
        if new_pass != confirm_pass:
            st.error("Passwords do not match")
        elif new_pass == "":
            st.warning("Password cannot be empty")
        else:
            passwords[cls] = new_pass
            save_passwords(passwords)
            st.success("Password Updated")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ---------- ADMIN ----------
elif "admin" in st.session_state:

    st.title("👮 Admin Dashboard")

    if os.path.exists(ATTENDANCE_FILE):
        log = pd.read_csv(ATTENDANCE_FILE)

        selected_date = st.date_input("Select Date", value=date.today())
        selected_class = st.selectbox("Select Class", sorted(df["Class"].unique()))

        filtered = log[
            (log["Date"] == str(selected_date)) &
            (log["Class"] == selected_class)
        ]

        if not filtered.empty:
            st.dataframe(filtered)
        else:
            st.warning("No data")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
