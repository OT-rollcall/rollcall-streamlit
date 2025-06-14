import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df.columns = df.columns.str.strip().str.replace("\n", " ").str.replace(r"\s+", " ", regex=True)

        # Optional: show raw column names for debug
        st.write("Detected columns:", list(df.columns))

        # Map long columns to short, usable names
        col_map = {
            "OT's Name": "Name",
            "Present / Absent": "Present",
            "Must See / P1 (Total)": "P1",
            "Must See / P1 (TA Assist)": "P1_TA",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "P2",
            "P2 (TA Assist)": "P2_TA",
            "P3 (Total)": "P3",
            "P3 (TA Assist)": "P3_TA",
            "TA-led cases (To indicate P level and TransD cases)": "TA_led",
            "Can Help (indicate number of cases/timings under \"Others\")": "Can_Help",
            "Need Help (indicate number of cases under \"Others\")": "Need_Help",
            "TA Slot - 1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)": "TA_Slot",
            "Ward": "Ward",
            "Notes": "Notes"
        }

        # Rename if columns match
        missing = [k for k in col_map if k not in df.columns]
        if missing:
            st.error(f"❌ Missing expected columns: {missing}")
        else:
            df = df.rename(columns=col_map)

            st.success("✅ File uploaded and worksheet loaded successfully.")
            st.dataframe(df)

            st.markdown("---")
            st.subheader("⚙️ Case Assignment Logic (Under Development)")

            st.markdown("""
            Next steps will include:
            - Detecting therapist availability
            - Matching 'can help' / 'need help'
            - Reducing movement between Main / Renci / NCID
            - Assigning by case priority (MS > P2.1 > P2.2 > P3)
            - Fair distribution with max 9 cases
            """)

            st.info("Assignment logic is under development. Data loaded successfully.")
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
