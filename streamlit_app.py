import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call Assistant", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("📄 Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df_raw.columns = df_raw.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        # Show detected columns for debugging
        st.subheader("🔍 Detected Columns:")
        st.write(df_raw.columns.tolist())

        # Helper function: Find column by keyword
        def find_col(keyword):
            for col in df_raw.columns:
                if keyword.lower() in col.lower():
                    return col
            return None

        col_map = {
            "name": find_col("OT's Name"),
            "ward": find_col("ward"),
            "present": find_col("Present / Absent"),
            "p1": find_col("Must See / P1 (Total)"),
            "p1_ta": find_col("Must See / P1 (TA Assist)"),
            "p2_raw": find_col("P2 (Total)"),
            "p2_ta": find_col("P2 (TA Assist)"),
            "p3": find_col("P3 (Total)"),
            "p3_ta": find_col("P3 (TA Assist)"),
            "ta_led": find_col("TA-led"),
            "can_help": find_col("Can Help"),
            "need_help": find_col("Need Help"),
            "ta_slot": find_col("TA Slot"),
            "notes": find_col("Notes")
        }

        # Check if any essential column is missing
        missing = [k for k, v in col_map.items() if v is None]
        if missing:
            st.error(f"❌ Missing required columns: {missing}")
            st.stop()

        # Rename columns to internal keys
        df = df_raw.rename(columns={v: k for k, v in col_map.items()})

        # Normalize values
        df["present"] = df["present"].str.strip().str.lower()
        df["present"] = df["present"].map({"yes": True, "no": False})
        df["can_help"] = df["can_help"].fillna("").astype(str).str.strip()
        df["need_help"] = df["need_help"].fillna("").astype(str).str.strip()
        df["notes"] = df["notes"].fillna("").astype(str).str.lower()

        # Extract P2 numbers from raw
        def extract_p2(text):
            text = str(text)
            match = re.match(r"(\d+)\s*\((\d+)\s*P2/1\)", text)
            if match:
                return int(match.group(1)), int(match.group(2))
            nums = re.findall(r"\d+", text)
            return (int(nums[0]), 0) if nums else (0, 0)

        df[["p2_total", "p2_1"]] = df["p2_raw"].apply(lambda x: pd.Series(extract_p2(x)))

        st.success("✅ File loaded successfully")
        st.dataframe(df)

        # Check for P1 redistribution
        st.markdown("### 🔄 Redistribution Suggestions")
        redistribution_needed = False
        for _, row in df.iterrows():
            if row["present"] is False and row["p1"] > 0:
                st.markdown(f"- {row['name']} is absent and has **{row['p1']} Must See (P1)** case(s).")
                redistribution_needed = True

        if not redistribution_needed:
            st.success("✅ No P1 redistribution needed.")

        # Next steps placeholder
        st.markdown("---")
        st.subheader("🚧 Intelligent Assignment Preview Coming Up")
        st.markdown("Will include:")
        st.markdown("""
        - P1, P2.1 and P2.2 fair case distribution (≤9 total per therapist)
        - Honour 'Need Help' / 'Can Help'
        - Respect Present / Absent
        - Minimize building movement
        - Schedule-aware (AM/PM/HV/Clinic blocking)
        """)

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("📤 Please upload an Excel file to begin.")
