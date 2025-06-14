import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("📤 Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Load raw data
        df_raw = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        st.success("✅ File uploaded and 'sorted' worksheet loaded successfully.")
        st.subheader("📄 Raw column headers detected:")
        st.write(list(df_raw.columns))
        
        # Match required columns using flexible keywords
        col_map = {}
        for col in df_raw.columns:
            name = col.strip().lower()
            if "ot" in name and "name" in name:
                col_map["Name"] = col
            elif "present" in name and "absent" in name:
                col_map["Present"] = col
            elif "p1" in name and "total" in name:
                col_map["P1 Total"] = col
            elif "p2" in name and "total" in name:
                col_map["P2 Total"] = col
            elif "p3" in name and "total" in name:
                col_map["P3 Total"] = col
            elif "can help" in name:
                col_map["Can Help"] = col
            elif "need help" in name:
                col_map["Need Help"] = col
            elif "notes" in name:
                col_map["Notes"] = col
        
        # Ensure all required columns are present
        required = ["Name", "Present", "P1 Total", "P2 Total", "P3 Total", "Can Help", "Need Help"]
        missing = [r for r in required if r not in col_map]
        if missing:
            st.error(f"❌ Missing required columns: {missing}")
            st.stop()
        
        # Subset and rename
        df = df_raw[[col_map[c] for c in required]].rename(columns={v: k for k, v in col_map.items()})
        st.dataframe(df)

        # Case assignment logic
        assignment_log = []

        # Calculate total cases needing reassignment
        total_cases_to_assign = need_help["Total Cases"].sum()

        for _, helper in helpers.iterrows():
            max_assignable = min(helper["Can Help"], 9 - helper["Total Cases"])
            if max_assignable <= 0:
                continue

            assigned = 0

            for i, (idx, needy) in enumerate(need_help.iterrows()):
                if needy["Total Cases"] <= 0:
                    continue

                assign_count = min(max_assignable - assigned, needy["Total Cases"])
                if assign_count <= 0:
                    break

                need_help.at[idx, "Total Cases"] -= assign_count
                assigned += assign_count

                assignment_log.append(
                    f"🔄 {helper['Name']} helps {needy['Name']} with {assign_count} case(s)"
                )

            if assigned > 0:
                st.write(f"✅ {helper['Name']} assigned {assigned} case(s) to assist others.")

        unassigned = need_help[need_help["Total Cases"] > 0]
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
