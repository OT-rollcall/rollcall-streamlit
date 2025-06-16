import streamlit as st
import pandas as pd
import datetime
import re

st.set_page_config(page_title="Roll Call App", layout="wide")
st.title("Roll Call Assistant (Prototype)")

uploaded_file = st.file_uploader("Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df = df_raw.copy()

        # Standardize column names
        df.columns = df.columns.str.strip()
        colmap = {col: col.lower().replace("\n", " ").strip() for col in df.columns}
        df.rename(columns=colmap, inplace=True)

        # Extract needed columns with matching
        def find_col(keywords):
            for col in df.columns:
                if all(k.lower() in col for k in keywords):
                    return col
            return None

        name_col = find_col(["ot", "name"])
        ward_col = find_col(["ward"])
        present_col = find_col(["present", "absent"])
        p1_col = find_col(["must", "see"])
        p2_raw_col = find_col(["p2", "total"])
        p3_col = find_col(["p3", "total"])
        need_help_col = find_col(["need", "help"])
        can_help_col = find_col(["can", "help"])
        notes_col = find_col(["notes"])

        required_cols = [name_col, ward_col, present_col, p1_col, p2_raw_col, p3_col, need_help_col, can_help_col, notes_col]
        if not all(required_cols):
            st.error("❌ Could not find all required columns in the uploaded file.")
            st.stop()

        df["present"] = df[present_col].str.strip().str.lower() == "yes"
        df["p1"] = pd.to_numeric(df[p1_col], errors="coerce").fillna(0).astype(int)

        # Parse P2/1 from "P2 (Total)" e.g. "10 (3 P2/1)"
        def extract_p2_counts(val):
            if pd.isna(val):
                return (0, 0)
            if isinstance(val, str):
                match = re.search(r"(\d+)\s*\(\s*(\d+)\s*P2/1", val)
                if match:
                    return (int(match.group(1)), int(match.group(2)))
                digits = re.findall(r"\d+", val)
                return (int(digits[0]), 0) if digits else (0, 0)
            return (int(val), 0)

        df[["p2_total", "p2_1"]] = df[p2_raw_col].apply(extract_p2_counts).apply(pd.Series)
        df["p2_2"] = df["p2_total"] - df["p2_1"]

        df["p3"] = pd.to_numeric(df[p3_col], errors="coerce").fillna(0).astype(int)

        df["can_help"] = pd.to_numeric(df[can_help_col], errors="coerce").fillna(0).astype(int)
        df["need_help"] = pd.to_numeric(df[need_help_col], errors="coerce").fillna(0).astype(int)
        df["notes"] = df[notes_col].fillna("").astype(str)

        today = datetime.datetime.today()
        weekday = today.strftime("%A")

        def get_p2_schedule(row):
            if "away" in row["notes"].lower() and "rest of week" in row["notes"].lower():
                return "distribute"
            return "keep"

        df["p2_plan"] = df.apply(get_p2_schedule, axis=1)

        st.success("✅ File loaded and parsed correctly.")

        # --- Redistribution Logic ---
        st.subheader("📊 Intelligent Case Assignment")

        absent = df[~df["present"]].copy()
        present = df[df["present"]].copy()

        redistributed_cases = []

        # Prioritize helpers
        helpers = present[present["can_help"] > 0].copy()
        nonhelpers = present[present["can_help"] == 0].copy()
        helpers["assigned"] = 0
        nonhelpers["assigned"] = 0

        def assign_cases(num_cases, source_name, priority_label):
            nonlocal helpers, nonhelpers, redistributed_cases
            remaining = num_cases

            for _, row in helpers.iterrows():
                available = 9 - (row["p1"] + row["p2_1"] + row["p2_2"] + row["p3"] + row["assigned"])
                to_assign = min(available, remaining)
                if to_assign > 0:
                    helpers.loc[helpers[name_col] == row[name_col], "assigned"] += to_assign
                    redistributed_cases.append({
                        "to": row[name_col],
                        "from": source_name,
                        "cases": to_assign,
                        "type": priority_label
                    })
                    remaining -= to_assign
                if remaining <= 0:
                    break

            # If still remaining, go to non-helpers
            if remaining > 0:
                for _, row in nonhelpers.iterrows():
                    available = 9 - (row["p1"] + row["p2_1"] + row["p2_2"] + row["p3"] + row["assigned"])
                    to_assign = min(available, remaining)
                    if to_assign > 0:
                        nonhelpers.loc[nonhelpers[name_col] == row[name_col], "assigned"] += to_assign
                        redistributed_cases.append({
                            "to": row[name_col],
                            "from": source_name,
                            "cases": to_assign,
                            "type": priority_label + " (non-helper)"
                        })
                        remaining -= to_assign
                    if remaining <= 0:
                        break

        for _, row in absent.iterrows():
            if row["p1"] > 0:
                assign_cases(row["p1"], row[name_col], "P1 (Must See)")
            if row["p2_plan"] == "distribute" and row["p2_1"] > 0:
                assign_cases(row["p2_1"], row[name_col], "P2.1")
            if row["p2_plan"] == "distribute" and row["p2_2"] > 0:
                assign_cases(row["p2_2"], row[name_col], "P2.2")

        if redistributed_cases:
            df_out = pd.DataFrame(redistributed_cases)
            st.dataframe(df_out)
        else:
            st.success("✅ No redistribution needed today.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
