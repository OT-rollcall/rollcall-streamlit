import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

# Upload Excel
uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df.columns = df.columns.str.strip()

        st.success("✅ File uploaded and 'sorted' worksheet loaded.")
        st.dataframe(df)

        # Parse availability and help status
        df['Name'] = df['Name'].str.strip()
        present_status = df['Present / Absent'].str.strip().str.lower()
        can_help = df['Can Help'].fillna(0)
        need_help = df['Need Help'].fillna(0)

        # Step 1: Identify all people who need help
        need_help_therapists = df[df['Need Help'] > 0]

        # Step 2: Identify all helpers (can help > 0 and either present, or absent but 'caseload tight')
        helper_pool = df[
            (can_help > 0) & (present_status == 'yes')
        ].copy()

        # Step 3: Redistribute from those who are absent OR who explicitly marked need help
        redistribute_from = df[
            (present_status == 'no') | (df['Need Help'] > 0)
        ].copy()

        # Step 4: Handle special case: notes say "away the rest of the week"
        redistribute_from['Force_P2'] = redistribute_from['Notes'].fillna('').str.contains("away the rest of the week", case=False)

        # Summary: track who is helping whom
        assignments = []

        for idx, row in redistribute_from.iterrows():
            giver = row['Name']
            cases_to_give = int(row['Need Help']) if row['Need Help'] > 0 else 3  # default 3 for absent
            if row['Force_P2']:
                cases_to_give = max(cases_to_give, 2)  # Push at least 2 cases if away whole week

            while cases_to_give > 0 and not helper_pool.empty:
                # Pick helper with fewest already assigned
                helper_pool = helper_pool.sort_values(by='Can Help', ascending=False)
                for h_idx, h_row in helper_pool.iterrows():
                    helper = h_row['Name']
                    help_capacity = int(h_row['Can Help'])

                    if help_capacity <= 0:
                        continue

                    assigned_now = min(help_capacity, cases_to_give)
                    cases_to_give -= assigned_now

                    # Update Can Help pool
                    helper_pool.at[h_idx, 'Can Help'] -= assigned_now

                    assignments.append(f"🟢 {helper} helps {giver} with {assigned_now} case(s)")

                    if cases_to_give <= 0:
                        break

        st.markdown("### 📋 Assignment Summary")
        if assignments:
            for a in assignments:
                st.write(a)
        else:
            st.success("✅ No redistribution needed based on current inputs.")

        st.markdown("---")
        st.info("Let me know if you'd like this summary to be downloadable as Excel or shown by ward/session.")

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload a file to begin.")
