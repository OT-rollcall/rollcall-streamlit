import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")

        # --- Normalize column names ---
        df_raw.columns = [col.strip().split("\n")[0] for col in df_raw.columns]

        # Rename key columns for ease
        df = df_raw.rename(columns={
            "OT's Name": "Name",
            "Present / Absent": "Present",
            "Must See / P1 (Total)": "P1",
            "Need Help (indicate number of cases under \"Others\")": "Need Help",
            "Can Help (indicate number of cases/timings under \"Others\")": "Can Help",
            "P2 (Total) - to indicate number of P2/1 e.g. 10 (3 P2/1)": "P2",
            "Notes": "Notes"
        })

        # Ensure missing cols are filled
        for col in ["P1", "Need Help", "Can Help", "P2", "Notes"]:
            if col not in df.columns:
                df[col] = 0

        # Clean data
        df["P1"] = pd.to_numeric(df["P1"], errors="coerce").fillna(0).astype(int)
        df["Need Help"] = pd.to_numeric(df["Need Help"], errors="coerce").fillna(0).astype(int)
        df["Can Help"] = pd.to_numeric(df["Can Help"], errors="coerce").fillna(0).astype(int)
        df["Present"] = df["Present"].astype(str).str.strip().str.lower()
        df["Notes"] = df["Notes"].astype(str).fillna("")

        st.success("✅ File uploaded and worksheet parsed successfully.")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("📊 Must See (P1) Case Redistribution")

        # Identify absent staff with P1s
        absent = df[df["Present"] == "no"]
        absent_with_p1 = absent[absent["P1"] > 0]

        if absent_with_p1.empty:
            st.info("✅ No Must See (P1) cases need redistribution today.")
        else:
            st.warning("⚠️ Redistributing Must See (P1) cases from absent staff...")

            total_to_redistribute = absent_with_p1["P1"].sum()

            # Identify potential helpers
            present = df[df["Present"] == "yes"].copy()
            helpers = present[present["Can Help"] > 0].copy()
            nonhelpers = present[present["Can Help"] == 0].copy()

            # Start with helpers, assign fairly up to max 9 total cases
            assignment = {name: 0 for name in present["Name"]}
            unassigned = total_to_redistribute

            def assign_cases(group, unassigned):
                for _, row in group.iterrows():
                    name = row["Name"]
                    current_load = df.loc[df["Name"] == name, "P1"].values[0] + assignment[name]
                    available_slots = max(0, 9 - current_load)
                    give = min(available_slots, unassigned)
                    assignment[name] += give
                    unassigned -= give
                    if unassigned <= 0:
                        break
                return unassigned

            unassigned = assign_cases(helpers, unassigned)
            if unassigned > 0:
                unassigned = assign_cases(nonhelpers, unassigned)

            st.markdown(f"🔁 Total Must See (P1) cases needing redistribution: **{total_to_redistribute}**")
            st.markdown(f"🧠 Cases distributed across available staff with max 9-case load limit:")

            assigned_df = pd.DataFrame([
                {"Name": name, "Assigned P1s": count}
                for name, count in assignment.items() if count > 0
            ])
            st.dataframe(assigned_df)

            if unassigned > 0:
                st.error(f"❗ {unassigned} cases could not be redistributed due to all staff at capacity.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")

else:
    st.info("Please upload an Excel file to begin.")
