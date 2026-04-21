import streamlit as st
import pandas as pd
import os
from datetime import date
import glob
import json

# ---------- UI ----------
st.set_page_config(page_title="Attendance", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {display:none;}
.block-container {padding: 1rem 1rem 3rem 1rem;}

button {
    height: 60px !important;
    font-size: 18px !important;
    border-radius: 12px !important;
    width: 100% !important;
}

/* Mobile tap fix */
button, .stButton>button {
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
}
button:focus {
    outline: none !important;
    box-shadow: none !important;
}

.stTextInput input {
    height: 55px !important;
    font-size: 18px !important;
}

.stCheckbox {
    transform: scale(1.3);
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

# ---------- SAVE ----------
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
    st.error("No data")
    st.stop()

if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------- HOME ----------
if st.session_state.page == "home":
    st.title("🏫 Attendance App")

    with st.form("home_form"):
        col1, col2 = st.columns(2)
        teacher_btn = col1.form_submit_button("👩‍🏫 Teacher")
        admin_btn = col2.form_submit_button("👮 Admin")

        if teacher_btn:
            st.session_state.page = "teacher_login"

        if admin_btn:
            st.session_state.page = "admin_login"

# ---------- TEACHER LOGIN ----------
elif st.session_state.page == "teacher_login":

    st.title("👩‍🏫 Teacher Login")

    with st.form("teacher_login_form"):
        cls = st.selectbox("Class", list(TEACHERS.keys()))
        pwd = st.text_input("Password", type="password")

        login = st.form_submit_button("Login")
        back = st.form_submit_button("Back")

        if login:
            if passwords[cls] == pwd:
                st.session_state.page = "teacher"
                st.session_state.cls = cls
            else:
                st.error("Wrong Password")

        if back:
            st.session_state.page = "home"

# ---------- TEACHER PANEL ----------
elif st.session_state.page == "teacher":

    cls = st.session_state.cls
    st.title(f"{TEACHERS[cls]}")
    st.write(f"📘 {cls}")
    st.write(f"📅 {date.today().strftime('%d/%m/%Y')}")

    data = df[df["Class"] == cls].sort_values("Student Name")

    # Attendance Form
    with st.form("attendance_form"):
        checks = {}

        for i, row in data.iterrows():
            c1, c2 = st.columns([3,1])
            c1.markdown(f"**{row['Student Name']}**")
            key = f"{row['Student Name']}_{row['Phone']}"
            checks[i] = c2.checkbox("", key=key)
            st.markdown("---")

        submit = st.form_submit_button("Submit Attendance")

        if submit:
            absent = [data.loc[i] for i,v in checks.items() if v]
            save_attendance(cls, absent)
            st.session_state.submitted = True
            st.success("Attendance Saved")

    # Update Attendance
    if st.session_state.get("submitted"):
        with st.form("update_form"):
            update = st.form_submit_button("🔄 Update Attendance")
            if update:
                st.session_state.submitted = False
                st.rerun()

    # Password
    st.divider()

    with st.form("password_toggle"):
        show = st.form_submit_button("🔑 Update Password")
        if show:
            st.session_state.show_pass = True

    if st.session_state.get("show_pass"):
        with st.form("password_form"):
            new = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            save = st.form_submit_button("Save Password")

            if save:
                if new != confirm:
                    st.error("Passwords do not match")
                elif new == "":
                    st.warning("Empty password not allowed")
                else:
                    passwords[cls] = new
                    save_passwords(passwords)
                    st.success("Password Updated")
                    st.session_state.show_pass = False

    # Logout
    with st.form("logout_form"):
        logout = st.form_submit_button("Logout")
        if logout:
            st.session_state.clear()
            st.session_state.page = "home"

# ---------- ADMIN LOGIN ----------
elif st.session_state.page == "admin_login":

    st.title("👮 Admin Login")

    with st.form("admin_login_form"):
        pwd = st.text_input("Password", type="password")

        login = st.form_submit_button("Login")
        back = st.form_submit_button("Back")

        if login:
            if pwd == ADMIN_PASSWORD:
                st.session_state.page = "admin"
            else:
                st.error("Wrong Password")

        if back:
            st.session_state.page = "home"

# ---------- ADMIN PANEL ----------
elif st.session_state.page == "admin":

    st.title("👮 Admin Dashboard")

    if os.path.exists(ATTENDANCE_FILE):
        log = pd.read_csv(ATTENDANCE_FILE)

        selected_date = st.date_input("Select Date", value=date.today())
        selected_class = st.selectbox("Class", sorted(df["Class"].unique()))

        st.write(f"📅 {selected_date.strftime('%d/%m/%Y')}")

        filtered = log[
            (log["Date"] == str(selected_date)) &
            (log["Class"] == selected_class)
        ]

        if not filtered.empty:
            st.dataframe(filtered)
        else:
            st.warning("No data")

        st.divider()

        today_all = log[log["Date"] == str(selected_date)]
        abs_all = today_all[today_all["Name"] != "ALL PRESENT"]

        if not abs_all.empty:
            phones = abs_all["Phone"].astype(str).str.replace(r'\.0$', '', regex=True)
            text = "\n".join(phones)

            st.download_button("Download All Numbers", text)

    with st.form("admin_logout"):
        logout = st.form_submit_button("Logout")
        if logout:
            st.session_state.clear()
            st.session_state.page = "home"
