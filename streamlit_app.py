import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Roll Call Assistant", layout="wide")
st.title("Roll Call Assistant (Prototype)")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("📄 Upload today's roll call Excel file (.xlsx)", type=["xlsx"])

def clean_headers(df):
    cleaned_columns = {}
    for col in df.columns:
        clean_col = str(col).strip().replace('\n', ' ').replace('\r', '').replace('\u00a0', ' ')
        cleaned_columns[col] = clean_col
    df.rename(columns=cleaned_columns, inplace=True)
    return df

if uploaded_file:
    try:
        # Read and clean headers
        df_raw = pd.read_excel(uploaded_file, sheet_name="sorted", engine="openpyxl")
        df = clean_headers(df_raw)

        st.success("✅ File uploaded and headers cleaned successfully.")
        st.dataframe(df.head(20))

        # --- Normalize key columns ---
        df["Present"] = df["Present / Absent"].str.strip().str.lower() == "yes"
        df["Can Help"] = df["Can Help (indicate number of cases/timings under \"Others\")"].fillna("0").astype(str)
        df["Need Help"] = df["Need Help (indicate number of cases under \"Others\")"].fillna("0").astype(str)

        df["Can Help Num"] = df["Can Help"].str.extract("(\d+)").fillna(0).astype(int)
        df["Need Help Num"] = df["Need Help"].str.extract("(\d+)").fillna(0).astype(int)

        # --- Extract Must See / P1 ---
        df["P1 Count"] = df["Must See / P1 (Total)"].fillna(0).astype(int)

        # --- Intelligent Redistribution ---
        st.markdown("### 🧠 Intelligent Case Redistribution")

        absent = df[~df["Present"] & (df["P1 Count"] > 0)]
        present = df[df["Present"]]

        total_cases_to_redistribute = absent["P1 Count"].sum()
        st.info(f"📦 Total P1 cases needing redistribution: {total_cases_to_redistribute}")

        if total_cases_to_redistribute == 0:
            st.success("✅ No redistribution needed.")
        else:
            helpers = present[present["Can Help Num"] > 0].copy()
            helpers["Assigned Cases"] = 0
            available_helpers = helpers.index.tolist()

            assignments = []
            for _, row in absent.iterrows():
                p1_cases = row["P1 Count"]
                therapist = row["OT's Name"]
                notes = row.get("Notes", "")

                while p1_cases > 0 and available_helpers:
                    for idx in available_helpers:
                        helper = helpers.loc[idx]
                        name = helper["OT's Name"]

                        if helper["Assigned Cases"] < helper["Can Help Num"]:
                            helpers.at[idx, "Assigned Cases"] += 1
                            p1_cases -= 1
                            assignments.append({
                                "From": therapist,
                                "To": name,
                                "Case Type": "P1",
                                "Note": f"{therapist}'s redistributed P1"
                            })
                            if p1_cases == 0:
                                break

                if p1_cases > 0:
                    st.warning(f"⚠️ Not enough helpers to fully redistribute P1s from {therapist}. {p1_cases} cases unassigned.")

            result_df = pd.DataFrame(assignments)
            st.subheader("📋 Redistribution Result")
            if not result_df.empty:
                st.dataframe(result_df)
            else:
                st.info("No redistribution assignments were made.")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("Upload an Excel file to begin.")
