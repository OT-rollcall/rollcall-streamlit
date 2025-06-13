import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        st.success("✅ File uploaded and 'sorted' worksheet loaded successfully.")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("⚙️ Case Assignment Logic (Preview)")

        st.markdown("""
        Next steps will include:
        - Detecting therapist availability
        - Matching 'can help' / 'need help'
        - Reducing movement between Main / Renci / NCID
        - Assigning by case priority (MS > P2.1 > P2.2 > P3)
        """)

        st.info("This section is under development. Let me know when you'd like to test the logic with your data.")
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
