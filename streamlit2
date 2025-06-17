import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call Assistant", layout="wide")

st.title("Roll Call Assistant (Prototype)")
st.write("Upload your Excel sheet and begin roll call logic here.")

uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted")

        # Clean column names
        df.columns = [str(col).replace("\n", " ").strip() for col in df.columns]

        # Rename long or multiline columns for consistency
        df = df.rename(columns={
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "P2_total_raw",
            "Must See / P1 (Total)": "P1",
            "Present / Absent": "Present",
            "Can Help (indicate number of cases/timings under \"Others\")": "Can Help",
            "Need Help (indicate number of cases under \"Others\")": "Need Help",
            "TA Slot 1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)": "TA Slot"
        })

        # Check all required columns exist
        required = ['OT\'s Name', 'P1', 'Present', 'Can Help', 'Need Help', 'Notes']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        df['P1'] = pd.to_numeric(df['P1'], errors='coerce').fillna(0).astype(int)
        df['Present'] = df['Present'].astype(str).str.strip().str.lower()
        df['Can Help Num'] = pd.to_numeric(df['Can Help'], errors='coerce').fillna(0).astype(int)
        df['Need Help Num'] = pd.to_numeric(df['Need Help'], errors='coerce').fillna(0).astype(int)
        df['Notes'] = df['Notes'].astype(str).fillna("")

        # Identify who is absent
        absent = df[df['Present'] == 'no']
        present = df[df['Present'] == 'yes']

        total_p1_to_redistribute = absent['P1'].sum()
        st.subheader(f"Total P1 cases needing redistribution: {total_p1_to_redistribute}")

        if total_p1_to_redistribute == 0:
            st.success("✅ No P1 cases need redistribution today.")
        else:
            # Filter helpers who can help AND are present
            helpers = present.copy()
            helpers['Assigned Cases'] = 0

            # Respect "Can Help = 0", override only if necessary
            helpers['Is Mentor'] = helpers['Notes'].str.contains("mentor", case=False, na=False)
            helpers['Strict Limit'] = helpers['Is Mentor'] | (helpers['Can Help Num'] == 0)

            assignments = []

            for _, row in absent.iterrows():
                therapist = row["OT's Name"]
                p1_cases = int(row["P1"])
                st.write(f"Redistributing {p1_cases} P1 case(s) from {therapist}...")

                # Eligible helpers: those who are not at their max
                eligible = helpers[helpers['Assigned Cases'] < helpers['Can Help Num']]

                assigned = 0
                for idx, helper in eligible.iterrows():
                    if p1_cases == 0:
                        break

                    if helper['Strict Limit'] and helper['Assigned Cases'] >= helper['Can Help Num']:
                        continue

                    helpers.at[idx, 'Assigned Cases'] += 1
                    p1_cases -= 1
                    assigned += 1
                    assignments.append({
                        "From": therapist,
                        "To": helper["OT's Name"],
                        "Case Type": "P1",
                        "Note": f"{therapist}'s redistributed P1"
                    })

                if p1_cases > 0:
                    st.warning(f"⚠️ Not enough helpers to fully redistribute {therapist}'s P1s. {p1_cases} case(s) unassigned.")

            if assignments:
                st.success("✅ Redistribution complete.")
                assignments_df = pd.DataFrame(assignments)
                st.dataframe(assignments_df)
            else:
                st.info("ℹ️ No eligible helpers found for redistribution.")

    except Exception as e:
        st.error(f"Error reading file: {e}")
