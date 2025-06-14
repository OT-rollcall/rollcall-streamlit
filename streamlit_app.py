import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("🏥 Roll Call Assistant (Prototype)")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("📤 Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        st.success("✅ File uploaded and 'sorted' worksheet loaded successfully.")
        st.dataframe(df)

        # --- Extract relevant data ---
        therapist_avail = {}
        give_help = {}
        receive_help = {}

        # Extract columns dynamically
        name_col = "OT's Name"
        help_col = "Can help"
        need_col = "Need help"
        total_col = "Total cases"
        ms_col = "MS"
        p21_col = "P2.1"
        p22_col = "P2.2"
        p3_col = "P3"

        for _, row in df.iterrows():
            name = row[name_col]
            therapist_avail[name] = {
                "max_cases": 9,
                "assigned": 0,
                "details": {
                    "MS": 0,
                    "P2.1": 0,
                    "P2.2": 0,
                    "P3": 0,
                },
                "ward_locs": [],
                "committed": False
            }

            if pd.notna(row[help_col]):
                try:
                    give_help[name] = int(row[help_col])
                except:
                    pass

            if pd.notna(row[need_col]):
                try:
                    receive_help[name] = int(row[need_col])
                except:
                    pass

        # --- Assign cases by priority ---
        cases = []

        for _, row in df.iterrows():
            name = row[name_col]
            for case_type in ["MS", "P2.1", "P2.2", "P3"]:
                try:
                    count = int(row[case_type])
                    for _ in range(count):
                        cases.append({"therapist": name, "type": case_type})
                except:
                    continue

        # Sort by priority
        priority_order = {"MS": 1, "P2.1": 2, "P2.2": 3, "P3": 4}
        cases.sort(key=lambda x: priority_order[x["type"]])

        # Distribute cases
        assignment_log = []

        for case in cases:
            giver = case["therapist"]
            ctype = case["type"]

            # Try to reassign if giver is overloaded or requested help
            assigned = False

            if receive_help.get(giver, 0) > 0:
                for receiver, can_take in give_help.items():
                    if therapist_avail[receiver]["assigned"] < therapist_avail[receiver]["max_cases"] and can_take > 0:
                        therapist_avail[receiver]["assigned"] += 1
                        therapist_avail[receiver]["details"][ctype] += 1
                        give_help[receiver] -= 1
                        receive_help[giver] -= 1
                        assignment_log.append(f"🟢 {receiver} helps {giver} with 1 {ctype}")
                        assigned = True
                        break

            if not assigned:
                therapist_avail[giver]["assigned"] += 1
                therapist_avail[giver]["details"][ctype] += 1

        # --- Display result summary ---
        st.markdown("---")
        st.subheader("📋 Assignment Summary")

        if assignment_log:
            for line in assignment_log:
                st.markdown(f"- {line}")
        else:
            st.info("No cross-therapist help needed today.")

        # Optional: display caseloads
        with st.expander("📊 View individual caseloads"):
            for name, info in therapist_avail.items():
                st.markdown(f"**{name}** – Total: {info['assigned']} cases")
                st.write(info["details"])

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("⬆️ Please upload an Excel file to begin.")
