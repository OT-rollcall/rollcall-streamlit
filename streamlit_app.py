import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        # Standardize column names
        df.columns = df.columns.str.strip()

        df = df.rename(columns={
            "OT's Name": "name",
            "Ward": "ward",
            "Present / Absent": "present",
            "Must See / P1 (Total)": "p1_total",
            "Must See / P1 (TA Assist)": "p1_ta",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "p2_total",
            "P2 (TA Assist)": "p2_ta",
            "P3 (Total)": "p3_total",
            "P3 (TA Assist)": "p3_ta",
            "TA-led cases (To indicate P level and TransD cases)": "ta_led",
            "Can Help (indicate number of cases/timings under \"Others\")": "can_help",
            "Need Help (indicate number of cases under \"Others\")": "need_help",
            "Notes": "notes"
        })

        # Handle special TA Slot column with line breaks
        for col in df.columns:
            if col.strip().startswith("TA Slot"):
                df = df.rename(columns={col: "ta_slot"})
                break

        # Clean data
        df["present"] = df["present"].str.strip().str.lower()
        df["can_help"] = pd.to_numeric(df["can_help"], errors='coerce').fillna(0)
        df["need_help"] = pd.to_numeric(df["need_help"], errors='coerce').fillna(0)
        df["p1_total"] = pd.to_numeric(df["p1_total"], errors='coerce').fillna(0)

        # Parse P2/1 count from raw P2 column
        def extract_p2_1(val):
            if pd.isna(val): return 0
            match = re.search(r'\((\d+) P2/1\)', str(val))
            return int(match.group(1)) if match else 0

        def extract_p2_total(val):
            if pd.isna(val): return 0
            match = re.match(r'(\d+)', str(val))
            return int(match.group(1)) if match else 0

        df["p2_1"] = df["p2_total"].apply(extract_p2_1)
        df["p2_total"] = df["p2_total"].apply(extract_p2_total)
        df["p2_2"] = df["p2_total"] - df["p2_1"]

        st.success("✅ File uploaded and 'Sorted' worksheet loaded successfully.")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("⚙️ Intelligent Case Redistribution")

        # Identify therapists needing redistribution of MS (P1)
        absent_with_ms = df[(df["present"] == "no") & (df["p1_total"] > 0)]
        present_need_help = df[(df["present"] == "yes") & (df["need_help"] > 0)]

        if not absent_with_ms.empty or not present_need_help.empty:
            st.subheader("📌 Absent Therapists with Must See Cases")
            st.dataframe(absent_with_ms[["name", "ward", "p1_total"]])

            st.subheader("📌 Present Therapists Requesting Help")
            st.dataframe(present_need_help[["name", "ward", "need_help"]])

            st.info("This is a preview of who needs redistribution. Assignment logic will run in the next version.")
        else:
            st.success("✅ No case redistribution needed today based on current inputs.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
