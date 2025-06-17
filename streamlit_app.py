import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

st.title("OT Roll Call – Ortho_SubGeri Team")
st.write("Upload the Excel file and automatically redistribute Must See (P1) cases from absent therapists to available helpers.")

uploaded_file = st.file_uploader("Upload Roll Call Excel File", type=["xlsx"])

# Helper: normalize column names
def normalize_column(col):
    return re.sub(r'\s+', ' ', col.strip().replace('\n', ' '))

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name="sorted")
        df_raw.columns = [normalize_column(col) for col in df_raw.columns]

        # Map to standard column keys
        colmap = {
            'name': "OT's Name",
            'present': "Present / Absent",
            'must_see': "Must See / P1 (Total)",
            'can_help': "Can Help (indicate number of cases/timings under \"Others\")",
            'need_help': "Need Help (indicate number of cases under \"Others\")",
            'notes': "Notes"
        }

        for key, col in colmap.items():
            if col not in df_raw.columns:
                raise ValueError(f"Missing required column: {col}")

        # Clean and extract data
        df = df_raw[[colmap['name'], colmap['present'], colmap['must_see'], colmap['can_help'], colmap['need_help'], colmap['notes']]].copy()
        df.columns = ['Name', 'Present', 'P1', 'Can Help', 'Need Help', 'Notes']
        df['P1'] = pd.to_numeric(df['P1'], errors='coerce').fillna(0).astype(int)
        df['Present'] = df['Present'].str.lower().str.strip()
        df['Can Help'] = df['Can Help'].fillna("").astype(str).str.lower()
        df['Need Help'] = df['Need Help'].fillna("").astype(str).str.lower()
        df['Notes'] = df['Notes'].fillna("").astype(str).str.lower()

        # Identify helpers and absentees
        absentees = df[df['Present'] == 'no']
        total_p1_to_redistribute = absentees['P1'].sum()

        st.subheader("📋 Summary")
        st.write(f"Total P1 cases needing redistribution: **{total_p1_to_redistribute}**")

        if total_p1_to_redistribute == 0:
            st.success("✅ No P1 redistribution needed today.")
        else:
            helpers_df = df[
                (df['Present'] == 'yes') &
                (df['Can Help'].str.contains('yes|ok|able|can|sure|3ms|2', na=False)) &
                (~(
                    (df['Notes'].str.contains('mentoring')) &
                    (~df['Can Help'].str.contains('yes|2|3|ok|can'))
                ))
            ].copy()

            # Estimate capacity
            def extract_capacity(text):
                match = re.search(r'\b(\d+)\b', text)
                return int(match.group(1)) if match else 1

            helpers_df['Help Capacity'] = helpers_df['Can Help'].apply(extract_capacity)
            helpers_df['Assigned'] = 0

            if helpers_df.empty:
                st.error("🚫 No suitable helpers available based on 'Can Help' and 'Notes'.")
            else:
                p1_remaining = total_p1_to_redistribute
                distribution = []

                for i in helpers_df.index:
                    if p1_remaining <= 0:
                        break
                    capacity = helpers_df.at[i, 'Help Capacity']
                    assign = min(capacity, p1_remaining)
                    helpers_df.at[i, 'Assigned'] = assign
                    p1_remaining -= assign
                    distribution.append((helpers_df.at[i, 'Name'], assign))

                st.subheader("📦 Redistribution Plan")
                if not distribution:
                    st.warning("⚠️ Not enough helper capacity to take over any P1 cases.")
                else:
                    dist_df = pd.DataFrame(distribution, columns=["Helper", "P1 Cases Assigned"])
                    st.dataframe(dist_df)

                    if p1_remaining > 0:
                        st.warning(f"⚠️ {p1_remaining} P1 cases still unassigned due to limited helper capacity.")
                    else:
                        st.success("✅ All P1 cases successfully redistributed.")

    except Exception as e:
        st.error(f"Error reading file: {e}")
