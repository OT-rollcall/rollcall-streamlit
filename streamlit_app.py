import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Read Excel sheet
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df.columns = df.columns.str.strip()  # Strip spaces
        st.success("✅ File uploaded and 'sorted' worksheet loaded successfully.")
        st.dataframe(df)

        # Normalize column names
        df.rename(columns={
            "OT's Name": "Name",
            "Present / Absent": "Present",
            "Must See / P1 (Total)": "P1",
            "Must See / P1 (TA Assist)": "P1_TA",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "P2_raw",
            "P2 (TA Assist)": "P2_TA",
            "P3 (Total)": "P3",
            "P3 (TA Assist)": "P3_TA",
            "TA-led cases (To indicate P level and TransD cases)": "TA_led",
            "Can Help (indicate number of cases/timings under \"Others\")": "Can_Help",
            "Need Help (indicate number of cases under \"Others\")": "Need_Help",
            "TA Slot\n1st slot (8.45 - 10am) | 2nd slot (10.15 - 11.30am) | 3rd slot (11.45 - 1pm) | 4th slot (2 - 3.15pm) | 5th slot (3.30 - 5pm)": "TA_Slot",
            "Notes": "Notes",
            "Ward": "Ward"
        }, inplace=True)

        # Convert relevant columns to usable types
        for col in ["P1", "P2_raw", "P3", "Can_Help", "Need_Help"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df["Present"] = df["Present"].str.strip().str.lower()
        df["Available"] = df["Present"] == "yes"

        # Extract P2.1 and P2.2 counts from raw string
        def parse_p2(p2_str):
            match = re.search(r"\((\d+)\s*P2/1", str(p2_str))
            p2_1 = int(match.group(1)) if match else 0
            total = int(str(p2_str).split()[0]) if str(p2_str).split()[0].isdigit() else 0
            p2_2 = max(0, total - p2_1)
            return pd.Series([total, p2_1, p2_2])

        df[["P2_Total", "P2_1", "P2_2"]] = df["P2_raw"].apply(parse_p2)

        # Compute total assigned caseload
        df["Assigned"] = df["P1"] + df["P2_Total"] + df["P3"] + df["TA_led"]
        df["Max_Cap"] = 9

        # Identify helpers
        helpers = df[(df["Available"]) & (df["Can_Help"] > 0)].copy()
        helpers["Remaining_Cap"] = df["Max_Cap"] - df["Assigned"]

        # Step 1: Redistribute Must See (P1) of absent therapists
        redistribution = []

        for _, row in df[df["Present"] == "no"].iterrows():
            if row["P1"] > 0:
                num_cases = row["P1"]
                help_needed = int(row["Need_Help"]) if row["Need_Help"] > 0 else num_cases

                assigned = 0
                for i, (_, helper) in enumerate(helpers.iterrows()):
                    if assigned >= help_needed:
                        break
                    if helpers.at[helper.name, "Remaining_Cap"] > 0:
                        helpers.at[helper.name, "Remaining_Cap"] -= 1
                        assigned += 1
                        redistribution.append({
                            "From": row["Name"],
                            "To": helper["Name"],
                            "Case": "P1 (Must See)"
                        })

        # Step 2: Distribute remaining P2.1 if therapist marked "away rest of week"
        for _, row in df[df["Notes"].str.contains("away", case=False, na=False)].iterrows():
            if row["P2_1"] > 0:
                help_needed = row["P2_1"]
                assigned = 0
                for _, helper in helpers.iterrows():
                    if assigned >= help_needed:
                        break
                    if helpers.at[helper.name, "Remaining_Cap"] > 0:
                        helpers.at[helper.name, "Remaining_Cap"] -= 1
                        assigned += 1
                        redistribution.append({
                            "From": row["Name"],
                            "To": helper["Name"],
                            "Case": "P2.1 (Away Rest of Week)"
                        })

        st.markdown("---")
        st.subheader("📋 Redistribution Plan")

        if redistribution:
            redist_df = pd.DataFrame(redistribution)
            st.dataframe(redist_df)
        else:
            st.success("✅ No redistribution needed based on current inputs.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
