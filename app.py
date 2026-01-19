import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="EM Audit | Neon Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= COLUMN CONSTANTS =================
REGION_COL = "Region"
DISTRICT_COL = "District(Updated)"
FLM_COL = "FLM Name"
SITE_COL = "SiteID"
STATUS_COL = "Audit Status"

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()
df.columns = df.columns.str.strip().str.replace("\n", "", regex=False)

# ================= HELPERS =================
def get_last_generated_time(file_path):
    if os.path.exists(file_path):
        return datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).strftime("%d %b %Y, %H:%M")
    return "Not generated yet"

# ================= TITLE =================
st.title("⚡ EM Audit – Neon Analytics Dashboard")

# ================= DOWNLOAD (PPT ONLY) =================
ppt_path = "data/Summary.pptx"
last_generated = get_last_generated_time(ppt_path)

st.markdown("## 📥 Download Reports")
st.caption(f"🕒 Last Generated: **{last_generated}**")

if os.path.exists(ppt_path):
    with open(ppt_path, "rb") as f:
        st.download_button(
            "⬇ Download Executive PPT",
            f,
            file_name="EM_Audit_Executive_Summary.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
else:
    st.warning("PPT not found. Please run the pipeline.")

# ================= EXECUTIVE OVERVIEW =================
st.markdown("## 🚀 Executive Overview")

total = len(df)
pass_cnt = (df[STATUS_COL] == "Pass").sum()
fail_cnt = (df[STATUS_COL] == "Fail").sum()

pass_pct = round(pass_cnt / total * 100, 1)
fail_pct = round(fail_cnt / total * 100, 1)

c1, c2, c3 = st.columns(3)
c1.metric("Total Audits", total)
c2.metric("Pass", f"{pass_cnt} ({pass_pct}%)")
c3.metric("Fail", f"{fail_cnt} ({fail_pct}%)")

# ================= DONUT =================
st.markdown("## 🎯 Audit Status Distribution")
fig = px.pie(
    df,
    names=STATUS_COL,
    hole=0.55,
    color_discrete_map={
        "Pass": "#22C55E",
        "Fail": "#EF4444",
        "Exempted": "#F59E0B"
    }
)
st.plotly_chart(fig, use_container_width=True)

# ================= FAILED VISITS =================
st.markdown("## ❌ Failed Visits – Detailed Export")

failed = df[df[STATUS_COL] == "Fail"]
st.success(f"Total Failed Visits: {len(failed)}")
st.dataframe(failed, use_container_width=True)
