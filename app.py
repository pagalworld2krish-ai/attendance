import streamlit as st
import pandas as pd
import os
import glob

# --- CONFIGURATION ---
DATA_FOLDER_NAME = "Data" 

st.set_page_config(page_title="Attendance Debugger", layout="wide")
st.title("🕵️‍♂️ Data Detective Mode")

# 1. FIND FILES
current_dir = os.path.dirname(os.path.abspath(__file__))
# Look in Data folder
data_path = os.path.join(current_dir, DATA_FOLDER_NAME)
files = glob.glob(os.path.join(data_path, "*.csv"))

st.write(f"### 📂 1. Files Found in '{DATA_FOLDER_NAME}' folder:")
if not files:
    st.error("No files found!")
else:
    for f in files:
        st.write(f"- `{os.path.basename(f)}`")

st.divider()

# 2. INSPECT CONTENT
st.write("### 🔍 2. Inspecting File Contents:")

all_data = []

for filepath in files:
    filename = os.path.basename(filepath)
    try:
        # Read file
        df = pd.read_csv(filepath, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        
        # Find Class Column
        class_col = None
        if 'Class & Section' in df.columns:
            class_col = 'Class & Section'
        elif 'Class' in df.columns:
            class_col = 'Class'
            
        if class_col:
            # Check what classes are INSIDE this specific file
            unique_classes = df[class_col].unique()
            
            st.write(f"**File:** `{filename}`")
            st.info(f"👉 Contains Students for: **{unique_classes}**")
            
            # Warn if mixing happens
            if len(unique_classes) > 1:
                st.error(f"⚠️ WARNING: This file contains multiple classes! {unique_classes}")
            
            # Check if filename matches content
            if "VII B" in filename and "VII-C" in unique_classes:
                 st.error("🚨 MISMATCH: File is named 'VII B' but contains 'VII-C' data!")
                 
        else:
            st.warning(f"File `{filename}` has no Class column.")
            
    except Exception as e:
        st.error(f"Error reading {filename}: {e}")

st.divider()
st.success("Analysis Complete. If you see a 'mismatch' above, delete that file and re-upload the correct one.")
