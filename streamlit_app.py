import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call Assistant", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df.columns = df.columns.str.strip()  # Remove leading/trailing whitespace

        st.success("✅ File uploaded and 'sorted' worksheet loaded successfully.")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("📋 Case Redistribution Summary")

        # Clean and process relevant columns
        df["Present / Absent"] = df["Present / Absent"].fillna("Yes").str.strip().str.lower()
        df["Can Help"] = df["Can Help"].fillna("No").astype(str).str.lower()
        df["Need Help"] = df["Need Help"].fillna("No").astype(str).str.lower()
        df["Notes"] = df["Notes"].fillna("").astype(str)

        # Extract Must See, P2, P3 totals
        df["Must See"] = df["Must See / P1 (Total)"].fillna(0)
        df["P2_raw"] = df["P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)"].fillna("").astype(str)
        df["P2_Total"] = df["P2_raw"].apply(lambda x: int(re.findall(r"\d+", x)[0]) if re.findall(r"\d+", x) else 0)

        # Identify absent staff who need help
        absent_df = df[df["Present / Absent"] == "no"]
        need_redistribution = absent_df[(absent_df["Need Help"] != "no") | (absent_df["Must See"] > 0) | (absent_df["P2_Total"] > 0)]

        if need_redistribution.empty:
            st.success("✅ No redistribution needed today.")
        else:
            st.warning(f"♻️ {len(need_redistribution)} therapist(s) are absent and have caseload to be reassigned.")

            total_cases_to_redistribute = need_redistribution["Must See"].sum() + need_redistribution["P2_Total"].sum()
            st.write(f"🔄 Total Must See (P1) + P2 to redistribute: **{int(total_cases_to_redistribute)}**")

            # Identify potential helpers
            present_helpers = df[df["Present / Absent"] == "yes"].copy()
            present_helpers["Current Load"] = present_helpers["Must See"] + present_helpers["P2_Total"]
            present_helpers["Helper Eligibility"] = present_helpers["Can Help"].apply(lambda x: x != "no")

            # Sort by current caseload (ascending)
            present_helpers = present_helpers.sort_values(by="Current Load")

            # Cap caseloads to 9 if possible
            available_capacity = (9 - present_helpers["Current Load"]).clip(lower=0)
            total_available = available_capacity.sum()

            st.write(f"🧑‍⚕️ Total capacity available across present therapists (max 9 rule): **{int(total_available)}**")

            # Redistribute cases (basic proportional logic)
            if total_available == 0:
                st.error("⚠️ No available therapist capacity to redistribute. Consider inter-team help.")
            else:
                redistribution_plan = []
                cases_left = int(total_cases_to_redistribute)

                for _, row in present_helpers.iterrows():
                    name = row["OT's Name"]
                    can_help = row["Helper Eligibility"]
                    capacity = 9 - row["Current Load"]
                    if capacity <= 0:
                        continue

                    # if they said "no" to can help, deprioritize them
                    if not can_help and total_available < total_cases_to_redistribute:
                        continue

                    assign = min(cases_left, capacity)
                    if assign > 0:
                        redistribution_plan.append((name, assign))
                        cases_left -= assign
                    if cases_left <= 0:
                        break

                if redistribution_plan:
                    st.success("✅ Redistribution Plan:")
                    for name, assigned in redistribution_plan:
                        st.write(f"- {name}: assigned **{assigned}** case(s)")

                    if cases_left > 0:
                        st.warning(f"⚠️ {cases_left} unassigned case(s) remain. You may need inter-team help or relax constraints.")
                else:
                    st.error("❌ Could not assign any cases. No eligible helpers or zero capacity.")

        st.markdown("---")
        st.subheader("🚧 Next Steps (In Progress)")
        st.markdown("""
        - Split P2 into P2.1 vs P2.2 based on case info
        - Prioritize minimal movement between Main / Renci / NCID
        - Consider clinic/HV commitments blocking AM/PM
        - Auto-distribute TA-led cases
        """)
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("⬆️ Please upload your Excel file to begin.")
