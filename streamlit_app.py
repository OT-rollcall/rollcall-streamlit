import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call Assistant", layout="wide")
st.title("Roll Call Assistant (Prototype)")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("📄 Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Load Excel sheet
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        # Clean column names
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()
        st.write("📌 Column names detected in uploaded file:")
        st.write(df.columns.tolist())  # DEBUG output

        # Rename key columns to shorter internal names
        df = df.rename(columns={
            "OT's Name": "name",
            "Ward": "ward",
            "Present / Absent": "present",
            "Must See / P1 (Total)": "p1",
            "Must See / P1 (TA Assist)": "p1_ta",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "p2_raw",
            "P2 (TA Assist)": "p2_ta",
            "P3 (Total)": "p3",
            "P3 (TA Assist)": "p3_ta",
            "TA-led cases (To indicate P level and TransD cases)": "ta_led",
            "Can Help (indicate number of cases/timings under \"Others\")": "can_help",
            "Need Help (indicate number of cases under \"Others\")": "need_help",
            "TA Slot - 1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)": "ta_slot",
            "Notes": "notes"
        })

        # Normalize values
        df["present"] = df["present"].str.strip().str.lower()
        df["present"] = df["present"].map({"yes": True, "no": False})

        df["can_help"] = df["can_help"].fillna("").astype(str).str.strip()
        df["need_help"] = df["need_help"].fillna("").astype(str).str.strip()
        df["notes"] = df["notes"].fillna("").astype(str).str.lower()

        # Extract P2 total and P2/1 values from "p2_raw"
        def extract_p2_values(text):
            text = str(text)
            match = re.match(r"(\d+)\s*\((\d+)\s*P2/1\)", text)
            if match:
                return int(match.group(1)), int(match.group(2))
            else:
                # Try to extract just a total if no bracketed P2/1
                num = re.findall(r"\d+", text)
                return (int(num[0]), 0) if num else (0, 0)

        df[["p2_total", "p2_1"]] = df["p2_raw"].apply(lambda x: pd.Series(extract_p2_values(x)))

        st.success("✅ File processed successfully.")
        st.dataframe(df)

        # --- Redistribute P1 cases if person is absent and has P1s ---
        st.markdown("### 🔄 Redistribution Suggestions")

        redistribution_needed = False
        p1_redistribute = []
        for _, row in df.iterrows():
            if row["present"] is False and row["p1"] > 0:
                redistribution_needed = True
                p1_redistribute.append((row["name"], row["p1"]))

        if p1_redistribute:
            st.write("📌 Must See (P1) cases need redistribution from absent therapists:")
            for name, count in p1_redistribute:
                st.markdown(f"- {name}: {count} P1 case(s)")
        else:
            st.success("✅ No redistribution needed for Must See (P1) cases.")

        # --- Preview: Future logic ---
        st.markdown("---")
        st.subheader("⚙️ Next: Intelligent Case Assignment Preview")
        st.markdown("""
        Coming up:
        - Assign Must See (P1) from absent staff
        - Fairly distribute P2.1 and P2.2, up to 9 total per person
        - Honour 'Need Help' and 'Can Help' fields
        - Minimise therapist movement between Main / Renci / NCID
        - Account for notes like 'away rest of week'
        - Block sessions for clinics, HVs, etc.
        """)

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("📤 Please upload an Excel file to begin.")
