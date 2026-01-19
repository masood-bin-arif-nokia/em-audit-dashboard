import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO
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
CURRENT_COL = "Current Status"

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()
df.columns = df.columns.str.strip().str.replace("\n", "", regex=False)

# 🔑 USE MIRROR CURRENT RECORDS ONLY
df_current = df[df[CURRENT_COL] == "YES"].copy()

# ================= FLM RISK =================
@st.cache_data
def load_flm_risk():
    return pd.read_excel("data/FLM_Risk_Summary.xlsx")

flm_exists = os.path.exists("data/FLM_Risk_Summary.xlsx")

# ================= HELPERS =================
def get_last_generated_time(path):
    if os.path.exists(path):
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d %b %Y, %H:%M")
    return "Not generated yet"

# ================= TITLE =================
st.title("⚡ EM Audit – Neon Analytics Dashboard")

# ================= DOWNLOAD =================
ppt_path = "data/Summary.pptx"
st.markdown("## 📥 Download Reports")
st.caption(f"🕒 Last Generated: **{get_last_generated_time(ppt_path)}**")

if os.path.exists(ppt_path):
    with open(ppt_path, "rb") as f:
        st.download_button(
            "⬇ Download Executive PPT",
            f,
            "EM_Audit_Executive_Summary.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

# ================= CSS =================
st.markdown("""
<style>
.neon-card {
    background: linear-gradient(145deg,#0f172a,#020617);
    border-radius:16px;
    padding:20px;
    box-shadow:0 0 15px rgba(0,245,255,.35);
    border:1px solid rgba(0,245,255,.25);
}
.neon-title{color:#00F5FF;font-weight:600}
.neon-value{font-size:34px;font-weight:800;color:#A7F3D0}
.neon-sub{color:#9CA3AF;font-size:13px}
.neon-green{box-shadow:0 0 18px rgba(34,197,94,.6)}
.neon-amber{box-shadow:0 0 18px rgba(245,158,11,.6)}
.neon-red{box-shadow:0 0 18px rgba(239,68,68,.6)}
</style>
""", unsafe_allow_html=True)

# ================= EXECUTIVE OVERVIEW (MIRROR ONLY) =================
st.markdown("## 🚀 Executive Overview (Latest Status Only)")

total = len(df_current)
pass_cnt = (df_current[STATUS_COL] == "Pass").sum()
fail_cnt = (df_current[STATUS_COL] == "Fail").sum()

c1, c2, c3 = st.columns(3)
c1.markdown(f"<div class='neon-card'><div class='neon-title'>Total</div><div class='neon-value'>{total}</div></div>", True)
c2.markdown(f"<div class='neon-card neon-green'><div class='neon-title'>Pass</div><div class='neon-value'>{pass_cnt}</div></div>", True)
c3.markdown(f"<div class='neon-card neon-red'><div class='neon-title'>Fail</div><div class='neon-value'>{fail_cnt}</div></div>", True)

# ================= DONUT =================
st.markdown("## 🎯 Audit Status Distribution")
fig = px.pie(
    df_current,
    names=STATUS_COL,
    hole=0.55,
    color_discrete_map={"Pass":"#22C55E","Fail":"#EF4444","Exempted":"#F59E0B"}
)
fig.update_layout(paper_bgcolor="#0B0F1A", font_color="#E5E7EB")
st.plotly_chart(fig, use_container_width=True)

# ================= REGION PERFORMANCE (MIRROR ONLY) =================
st.markdown("## 🌍 Region Performance (Latest Only)")
cols = st.columns(4)

for i, region in enumerate(df_current[REGION_COL].dropna().unique()):
    r = df_current[df_current[REGION_COL] == region]
    t = len(r)
    f = (r[STATUS_COL] == "Fail").sum()
    f_pct = round(f / t * 100, 1) if t else 0

    with cols[i % 4]:
        st.markdown(f"""
        <div class="neon-card">
            <div class="neon-title">{region}</div>
            <div class="neon-value">{t}</div>
            <div class="neon-sub">Fail: {f} ({f_pct}%)</div>
        </div>
        """, True)

# ================= DISTRICT PERFORMANCE (MIRROR ONLY) =================
st.markdown("## 🧭 District Performance (Latest Only)")

df_d = df_current.dropna(subset=[REGION_COL, DISTRICT_COL])

for region in df_d[REGION_COL].unique():
    st.markdown(f"### {region}")
    cols = st.columns(4)
    r_df = df_d[df_d[REGION_COL] == region]

    for i, dist in enumerate(r_df[DISTRICT_COL].unique()):
        d = r_df[r_df[DISTRICT_COL] == dist]
        t = len(d)
        f = (d[STATUS_COL] == "Fail").sum()
        f_pct = round(f / t * 100, 1) if t else 0

        glow = "neon-red" if f_pct >= 30 else "neon-amber" if f_pct >= 10 else "neon-green"

        with cols[i % 4]:
            st.markdown(f"""
            <div class="neon-card {glow}">
                <div class="neon-title">{dist}</div>
                <div class="neon-value">{t}</div>
                <div class="neon-sub">Fail: {f} ({f_pct}%)</div>
            </div>
            """, True)

# ================= FLM RISK =================
st.markdown("## 🚨 FLM Risk Summary")

if flm_exists:
    st.dataframe(load_flm_risk(), use_container_width=True, height=520)
else:
    st.error("FLM_Risk_Summary.xlsx not found in data/")

# ================= FAILED VISITS =================
st.markdown("## ❌ Failed Visits – Detailed Export")

failed = df[df[STATUS_COL] == "Fail"].copy()

excel_cols = [
    SITE_COL,
    "Date of visit",
    REGION_COL,
    DISTRICT_COL,
    FLM_COL,
    "Email1",
    "Audit remarks",
    "District_Region_Status",
    "Month"
]
excel_cols = [c for c in excel_cols if c in failed.columns]
failed_excel = failed[excel_cols]

ui_cols = [
    SITE_COL,
    "Date of visit",
    REGION_COL,
    DISTRICT_COL,
    FLM_COL,
    "Audit remarks",
    "Month"
]
ui_cols = [c for c in ui_cols if c in failed.columns]
failed_ui = failed[ui_cols]

st.success(f"Total Failed Visits: {len(failed_ui)}")
st.dataframe(failed_ui, use_container_width=True, height=520)

buf = BytesIO()
failed_excel.to_excel(buf, index=False)
buf.seek(0)

st.download_button(
    "⬇ Download Failed Visits (Excel)",
    buf,
    "Failed_Visits_Detailed.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
