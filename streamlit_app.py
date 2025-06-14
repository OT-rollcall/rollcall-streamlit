import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call Assistant", layout="wide")
st.title("Roll Call Assistant (Prototype with Assignment Logic)")

uploaded_file = st.file_uploader("📁 Upload today's Excel file (worksheet = 'sorted')", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        st.success("✅ File uploaded successfully!")
        st.dataframe(df)

        # Extract relevant fields
        name_col = "OT's Name"
        present_col = "Present / Absent "
        ms_col = "Must See / P1 (Total)"
        can_help_col = "Can Help (indicate number of cases/timings under \"Others\")"
        need_help_col = "Need Help (indicate number of cases under \"Others\")"
        ward_col = "Ward"

        df = df[df[present_col].str.lower() == 'yes'].copy()
        df[name_col] = df[name_col].fillna("Unknown")

        # Clean and convert numbers
        df[ms_col] = pd.to_numeric(df[ms_col], errors='coerce').fillna(0).astype(int)
        df[can_help_col] = pd.to_numeric(df[can_help_col], errors='coerce').fillna(0).astype(int)
        df[need_help_col] = pd.to_numeric(df[need_help_col], errors='coerce').fillna(0).astype(int)

        # Calculate total initial caseload
        df['Total Load'] = df[ms_col]

        # --- Rule: Distribute help fairly (max 9 cases) ---
        assignments = []

        for idx, row in df.iterrows():
            therapist = row[name_col]
            can_give = row[need_help_col]
            can_take = row[can_help_col]
            total_load = row['Total Load']
            ward = row[ward_col]

            if can_give > 0:
                # Find helpers in same ward first
                helpers = df[
                    (df[name_col] != therapist) &
                    (df[can_help_col] > 0) &
                    (df['Total Load'] < 9)
                ].copy()

                # Sort helpers by same ward > lowest load
                helpers['same_ward'] = helpers[ward_col] == ward
                helpers = helpers.sort_values(by=['same_ward', 'Total Load'], ascending=[False, True])

                to_assign = can_give
                for _, helper_row in helpers.iterrows():
                    helper = helper_row[name_col]
                    helper_load = helper_row['Total Load']
                    helper_capacity = min(9 - helper_load, helper_row[can_help_col], to_assign)

                    if helper_capacity > 0:
                        assignments.append(f"➡️ **{helper}** helps **{therapist}** with **{helper_capacity} case(s)**")
                        df.loc[df[name_col] == helper, 'Total Load'] += helper_capacity
                        df.loc[df[name_col] == helper, can_help_col] -= helper_capacity
                        to_assign -= helper_capacity

                        if to_assign <= 0:
                            break

        st.markdown("---")
        st.subheader("📊 Summary: Help Distribution")
        if assignments:
            for line in assignments:
                st.markdown(line)
        else:
            st.info("No case redistribution needed today.")

        st.markdown("---")
        st.caption("Prototype last updated: June 2025")

    except Exception as e:
        st.error(f"❌ Error reading worksheet: {e}")
else:
    st.info("Upload the Excel file to get started.")
