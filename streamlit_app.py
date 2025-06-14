import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("📤 Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        # Standardize column names
        required_columns = [
            "OT's Name", "Ward", "Present / Absent", "Must See / P1 (Total)", "Must See / P1 (TA Assist)",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)", "P2 (TA Assist)", "P3 (Total)", "P3 (TA Assist)",
            "TA-led cases (To indicate P level and TransD cases)",
            "Can Help (indicate number of cases/timings under \"Others\")",
            "Need Help (indicate number of cases under \"Others\")",
            "TA Slot - 1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)",
            "Notes"
        ]

        df = df[required_columns]
        df.columns = [col.strip() for col in df.columns]

        # Rename for easier access
        df = df.rename(columns={
            "OT's Name": "Name",
            "Present / Absent": "Present",
            "Can Help (indicate number of cases/timings under \"Others\")": "Can Help",
            "Need Help (indicate number of cases under \"Others\")": "Need Help",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "P2 Total",
            "Must See / P1 (Total)": "P1 Total",
            "P3 (Total)": "P3 Total",
        })

        # Clean and convert relevant columns
        for col in ["P1 Total", "P2 Total", "P3 Total", "Can Help", "Need Help"]:
            df[col] = df[col].fillna(0)
            df[col] = df[col].astype(str).str.extract(r'(\d+)').fillna(0).astype(int)

        # Total case count
        df["Total Cases"] = df["P1 Total"] + df["P2 Total"] + df["P3 Total"]

        # Separate helpers and those needing help
        helpers = df[(df["Present"].str.lower() == "yes") & (df["Can Help"] > 0)].copy()
        needs_help = df[(df["Need Help"] > 0) | (df["Present"].str.lower() == "no")].copy()

        st.success("✅ File loaded. Case redistribution will now be displayed.")
        st.dataframe(df)

        # Case assignment logic
        assignment_log = []

        # Calculate total cases needing reassignment
        total_cases_to_assign = needs_help["Total Cases"].sum()

        for _, helper in helpers.iterrows():
            max_assignable = min(helper["Can Help"], 9 - helper["Total Cases"])
            if max_assignable <= 0:
                continue

            assigned = 0

            for i, (idx, needy) in enumerate(needs_help.iterrows()):
                if needy["Total Cases"] <= 0:
                    continue

                assign_count = min(max_assignable - assigned, needy["Total Cases"])
                if assign_count <= 0:
                    break

                needs_help.at[idx, "Total Cases"] -= assign_count
                assigned += assign_count

                assignment_log.append(
                    f"🔄 {helper['Name']} helps {needy['Name']} with {assign_count} case(s)"
                )

            if assigned > 0:
                st.write(f"✅ {helper['Name']} assigned {assigned} case(s) to assist others.")

        unassigned = needs_help[needs_help["Total Cases"] > 0]
        if not assignment_log:
            st.info("No case redistribution was needed.")
        else:
            st.markdown("### 🔍 Case Redistribution Summary")
            for line in assignment_log:
                st.markdown(f"- {line}")

        if not unassigned.empty:
            st.warning("⚠️ Some cases could not be reassigned due to helper limits:")
            st.dataframe(unassigned[["Name", "Total Cases"]])
        else:
            st.success("🎉 All help requests and absentee caseloads have been assigned!")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("Please upload your Excel file to begin.")
