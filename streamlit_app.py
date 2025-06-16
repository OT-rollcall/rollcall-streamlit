import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        # Clean column names (remove line breaks, extra spaces)
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        # Rename the long TA Slot column for simplicity
        df = df.rename(columns={
            "TA Slot 1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)":
            "TA Slot"
        })

        # Confirm required columns are present
        required_cols = [
            "OT's Name", "Ward", "Present / Absent", "Must See / P1 (Total)",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)",
            "Can Help (indicate number of cases/timings under \"Others\")",
            "Need Help (indicate number of cases under \"Others\")", "Notes"
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        # Normalize data
        df["Present / Absent"] = df["Present / Absent"].str.strip().str.lower()
        df["Can Help"] = pd.to_numeric(df["Can Help (indicate number of cases/timings under \"Others\")"], errors='coerce').fillna(0)
        df["Need Help"] = pd.to_numeric(df["Need Help (indicate number of cases under \"Others\")"], errors='coerce').fillna(0)
        df["Must See"] = pd.to_numeric(df["Must See / P1 (Total)"], errors='coerce').fillna(0)

        # Parse P2 totals and P2.1 from custom text format
        p2_col = "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)"
        df["P2 Total"] = df[p2_col].astype(str).apply(lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
        df["P2.1"] = df[p2_col].astype(str).apply(lambda x: int(re.search(r'\((\d+)\s*P2/1\)', x).group(1)) if re.search(r'\((\d+)\s*P2/1\)', x) else 0)
        df["P2.2"] = df["P2 Total"] - df["P2.1"]

        # Who needs redistribution (absent or Need Help > 0)
        df["Needs Redistribution"] = (df["Present / Absent"] == "no") | (df["Need Help"] > 0)

        if df["Needs Redistribution"].any():
            st.success("✅ Redistribution is needed for some therapists.")
            st.write(df[df["Needs Redistribution"]][["OT's Name", "Must See", "P2 Total", "P2.1", "P2.2", "Need Help"]])
        else:
            st.info("✅ No redistribution required based on current data.")

        st.markdown("---")
        st.subheader("⚙️ Case Assignment Logic (Preview)")

        st.markdown("""
        This app now:
        - Parses P1, P2.1, P2.2 correctly
        - Detects absent staff and those who need help
        - Will assign in future version based on fair rules

        Next: Implement intelligent assignment considering:
        - 'Can Help' capacity
        - 9-case cap per therapist
        - Priority: MS > P2.1 > P2.2 > P3
        - Minimal movement between Main, Renci, NCID
        """)
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
