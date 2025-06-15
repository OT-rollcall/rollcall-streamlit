import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Read the Excel file
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        # Clean column names: remove line breaks, normalize whitespace
        df.columns = df.columns.str.replace("\n", " ", regex=True).str.strip().str.replace(r"\s+", " ", regex=True)

        # Rename columns to simplified internal names
        col_map = {
            "OT's Name": "name",
            "Ward": "ward",
            "Present / Absent": "present",
            "Must See / P1 (Total)": "p1_total",
            "Must See / P1 (TA Assist)": "p1_ta",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "p2_total",
            "P2 (TA Assist)": "p2_ta",
            "P3 (Total)": "p3_total",
            "P3 (TA Assist)": "p3_ta",
            "TA-led cases (To indicate P level and TransD cases)": "ta_cases",
            "Can Help (indicate number of cases/timings under \"Others\")": "can_help",
            "Need Help (indicate number of cases under \"Others\")": "need_help",
            "TA Slot 1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)": "ta_slot",
            "Notes": "notes"
        }

        df.rename(columns=col_map, inplace=True)

        # Convert relevant fields to lowercase for matching
        df["present"] = df["present"].str.strip().str.lower()
        df["name"] = df["name"].str.strip()

        # Parse can_help and need_help columns as numbers (fill NAs as 0)
        df["can_help"] = pd.to_numeric(df["can_help"], errors="coerce").fillna(0).astype(int)
        df["need_help"] = pd.to_numeric(df["need_help"], errors="coerce").fillna(0).astype(int)

        # Convert case counts to numeric (if not already)
        df["p1_total"] = pd.to_numeric(df["p1_total"], errors="coerce").fillna(0).astype(int)

        # Identify absent therapists who need help
        absent_therapists = df[(df["present"] == "no") & (df["need_help"] > 0)]

        # Identify available helpers
        available_helpers = df[(df["present"] == "yes") & (df["can_help"] > 0)]

        st.success("✅ File uploaded and worksheet processed successfully.")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("📊 Redistribution Preview")

        if not absent_therapists.empty:
            st.write("Therapists who are absent and need help:")
            st.dataframe(absent_therapists[["name", "ward", "need_help", "p1_total"]])

            if not available_helpers.empty:
                st.write("Therapists available to help:")
                st.dataframe(available_helpers[["name", "ward", "can_help"]])

                # Very basic Must See redistribution logic
                total_ms_cases_to_assign = absent_therapists["p1_total"].sum()
                helpers = available_helpers.copy()
                helpers["assigned"] = 0

                i = 0
                while total_ms_cases_to_assign > 0 and not helpers.empty:
                    idx = i % len(helpers)
                    if helpers.iloc[idx]["assigned"] < 9:  # Fair distribution cap
                        helpers.at[helpers.index[idx], "assigned"] += 1
                        total_ms_cases_to_assign -= 1
                    i += 1

                st.markdown("### 🔁 Proposed MS Case Distribution (Prototype)")
                st.dataframe(helpers[["name", "ward", "can_help", "assigned"]])

            else:
                st.warning("No therapists are marked as 'Can Help'. Consider adjusting the roll call input.")
        else:
            st.info("✅ No redistribution needed today based on current 'Present / Absent' and 'Need Help' info.")

        st.markdown("---")
        st.subheader("🧠 Next Steps")
        st.markdown("""
        - Redistribute P2 and P3 fairly using logic for P2.1 and P2.2 scheduling
        - Prioritize keeping therapists in their assigned buildings
        - Adjust for outpatient clinics, home visits, and blockouts
        - Respect ‘Can Help = No’ unless caseload is very high
        - Auto-detect long absences from ‘Notes’ for weekly redistribution
        """)

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("📂 Please upload an Excel file to begin.")
