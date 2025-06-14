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

        # Separate hel
