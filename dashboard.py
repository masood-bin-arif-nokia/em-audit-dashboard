import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---------- PDF IMPORTS (MISSING BEFORE) ----------
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- PDF GENERATOR ----------------
def generate_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "EM Audit Dashboard Summary")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 40

    # Executive KPIs
    total = len(df)
    passed = (df["Audit Status"] == "Pass").sum()
    failed = (df["Audit Status"] == "Fail").sum()
    exempted = (df["Audit Status"] == "Exempted").sum()

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Executive Overview")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Total Visits: {total}")
    y -= 15
    c.drawString(40, y, f"Pass: {passed}")
    y -= 15
    c.drawString(40, y, f"Fail: {failed}")
    y -= 15
    c.drawString(40, y, f"Exempted: {exempted}")
    y -= 30

    # Region Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Region Summary")
    y -= 20

    region_summary = df.groupby("Region").agg(
        Total=("SiteID", "count"),
        Fail=("Audit Status", lambda x: (x == "Fail").sum())
    ).reset_index()

    c.setFont("Helvetica", 10)
    for _, row in region_summary.iterrows():
        c.drawString(40, y, f"{row['Region']} - Total: {row['Total']} | Fail: {row['Fail']}")
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    # FLM Risk (Top 10)
    c.showPage()
    y = height - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Top FLM Risk (Fail %)")
    y -= 20

    flm = (
        df.groupby("FLM Name")
        .agg(
            Total=("SiteID", "count"),
            Fail=("Audit Status", lambda x: (x == "Fail").sum())
        )
        .reset_index()
    )
    flm["Fail %"] = (flm["Fail"] / flm["Total"] * 100).round(1)
    flm = flm.sort_values("Fail %", ascending=False).head(10)

    c.setFont("Helvetica", 10)
    for _, row in flm.iterrows():
        c.drawString(
            40, y,
            f"{row['FLM Name']} | Visits: {row['Total']} | Fail %: {row['Fail %']}"
        )
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="EM Audit | Neon Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- TITLE ----------------
st.title("EM Audit – Neon Analytics Dashboard")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()

# ---------------- DOWNLOAD SECTION ----------------
st.markdown("## Download Reports")

# PPT
ppt_path = "data/Summary.pptx"
if os.path.exists(ppt_path):
    with open(ppt_path, "rb") as f:
        st.download_button(
            label="Download Dashboard (PPT)",
            data=f,
            file_name="EM_Audit_Dashboard_Summary.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
else:
    st.info("Summary PPT will appear after the next automation run.")

# PDF (NEW)
pdf_buffer = generate_pdf(df)
st.download_button(
    label="Download Dashboard (PDF)",
    data=pdf_buffer,
    file_name="EM_Audit_Dashboard_Summary.pdf",
    mime="application/pdf"
)

# ---------------- REST OF YOUR DASHBOARD ----------------
# (Executive KPIs, donut, trends, region, district, FLM risk)
# 🔹 NO CHANGE REQUIRED BELOW THIS POINT
