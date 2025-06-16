import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call Assistant", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df.columns = df.columns.str.strip()

        required_columns = [
            "OT's Name", "Ward", "Present / Absent", "Must See / P1 (Total)",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)", "Can Help (indicate number of cases/timings under \"Others\")",
            "Need Help (indicate number of cases under \"Others\")", "Notes"
        ]

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        df = df.fillna(0)

        df.rename(columns={
            "OT's Name": "name",
            "Present / Absent": "present",
            "Must See / P1 (Total)": "ms",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "p2",
            "Can Help (indicate number of cases/timings under \"Others\")": "can_help",
            "Need Help (indicate number of cases under \"Others\")": "need_help",
            "Notes": "notes"
        }, inplace=True)

        df['present'] = df['present'].astype(str).str.lower().str.strip()
        df['absent'] = df['present'].isin(['no'])
        df['ms'] = pd.to_numeric(df['ms'], errors='coerce').fillna(0).astype(int)
        df['p2'] = pd.to_numeric(df['p2'].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0).astype(int)
        df['can_help'] = pd.to_numeric(df['can_help'], errors='coerce').fillna(0).astype(int)
        df['need_help'] = pd.to_numeric(df['need_help'], errors='coerce').fillna(0).astype(int)

        st.success("✅ File uploaded and parsed successfully.")
        st.dataframe(df)

        # Intelligent redistribution
        st.markdown("---")
        st.subheader("📊 Redistributed Must See / P1 Cases")

        redistributed = []
        helpers = df[(df['absent'] == False) & (df['can_help'] > 0)].copy()
        helpers["assigned"] = 0

        tight_caseload_pool = df[(df['absent'] == False) & (df['can_help'] == 0)].copy()
        tight_caseload_pool["assigned"] = 0

        needs_help = df[df['absent'] & (df['ms'] > 0)].copy()

        if needs_help.empty:
            st.info("✅ No redistribution needed. No absent staff with Must See cases.")
        else:
            total_to_redistribute = int(needs_help['ms'].sum())
            st.write(f"Total Must See cases to redistribute: {total_to_redistribute}")

            case_count = 0
            for _, row in needs_help.iterrows():
                cases = row['ms']
                source_name = row['name']
                notes = row['notes']
                strict = any(keyword in str(notes).lower() for keyword in ["mentoring", "student"])

                # First try assigning to helpers
                for i, h_row in helpers.iterrows():
                    if h_row['assigned'] < h_row['can_help']:
                        assign = min(h_row['can_help'] - h_row['assigned'], cases)
                        if assign > 0:
                            helpers.at[i, 'assigned'] += assign
                            redistributed.append({
                                "From": source_name,
                                "To": h_row['name'],
                                "Cases Assigned": assign
                            })
                            cases -= assign
                            case_count += assign
                        if cases <= 0:
                            break

                # If still cases left and not strict, try tight-caseload pool
                if cases > 0 and not strict:
                    for i, h_row in tight_caseload_pool.iterrows():
                        if h_row['assigned'] < 9:  # max 9 cases rule
                            assign = min(9 - h_row['assigned'], cases)
                            if assign > 0:
                                tight_caseload_pool.at[i, 'assigned'] += assign
                                redistributed.append({
                                    "From": source_name,
                                    "To": h_row['name'],
                                    "Cases Assigned": assign
                                })
                                cases -= assign
                                case_count += assign
                            if cases <= 0:
                                break

                if cases > 0:
                    redistributed.append({
                        "From": source_name,
                        "To": "Unassigned",
                        "Cases Assigned": cases
                    })

            if redistributed:
                st.dataframe(pd.DataFrame(redistributed))
            else:
                st.warning("⚠️ Redistribution attempted but no available capacity to assign cases.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
