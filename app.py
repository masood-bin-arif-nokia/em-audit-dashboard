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

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()
df.columns = df.columns.str.strip().str.replace("\n", "", regex=False)

@st.cache_data
def load_flm_risk():
    return pd.read_excel("data/FLM_Risk_Summary.xlsx")

flm_risk_file_exists = os.path.exists("data/FLM_Risk_Summary.xlsx")

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
    st.warning("⚠ Summary.pptx not found in data/ folder")

# ================= EXECUTIVE OVERVIEW =================
st.markdown("## 🚀 Executive Overview")

total = len(df)
pass_cnt = (df[STATUS_COL] == "Pass").sum()
fail_cnt = (df[STATUS_COL] == "Fail").sum()
exempt_cnt = (df[STATUS_COL] == "Exempted").sum()

pass_pct = round(pass_cnt / total * 100, 1) if total else 0
fail_pct = round(fail_cnt / total * 100, 1) if total else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Audits", total)
c2.metric("Pass", f"{pass_cnt} ({pass_pct}%)")
c3.metric("Fail", f"{fail_cnt} ({fail_pct}%)")
c4.metric("Exempted", exempt_cnt)

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

# ================= REGION PERFORMANCE =================
st.markdown("## 🌍 Region Performance")
cols = st.columns(4)

for i, region in enumerate(sorted(df[REGION_COL].dropna().unique())):
    r = df[df[REGION_COL] == region]
    t = len(r)
    p = (r[STATUS_COL] == "Pass").sum()
    f = (r[STATUS_COL] == "Fail").sum()
    p_pct = round(p / t * 100, 1) if t else 0
    f_pct = round(f / t * 100, 1) if t else 0

    with cols[i % 4]:
        st.metric(
            label=region,
            value=t,
            delta=f"Fail: {f} ({f_pct}%)"
        )

# ================= DISTRICT PERFORMANCE =================
st.markdown("## 🧭 District Performance (By Region)")
df_d = df.dropna(subset=[REGION_COL, DISTRICT_COL])

for region in sorted(df_d[REGION_COL].unique()):
    st.markdown(f"### {region}")
    cols = st.columns(4)
    r_df = df_d[df_d[REGION_COL] == region]

    for i, dist in enumerate(sorted(r_df[DISTRICT_COL].unique())):
        d = r_df[r_df[DISTRICT_COL] == dist]
        t = len(d)
        f = (d[STATUS_COL] == "Fail").sum()
        f_pct = round(f / t * 100, 1) if t else 0

        with cols[i % 4]:
            st.metric(
                label=dist,
                value=t,
                delta=f"Fail {f_pct}%"
            )

# ================= FLM RISK SUMMARY =================
st.markdown("## 🚨 FLM Risk Summary")

if flm_risk_file_exists:
    flm_risk = load_flm_risk()
    st.dataframe(flm_risk, use_container_width=True, height=520)
else:
    st.warning("FLM_Risk_Summary.xlsx not found")

# ================= FAILED VISITS – DETAILED EXPORT =================
st.markdown("## ❌ Failed Visits – Detailed Export")

failed_visits = df[df[STATUS_COL] == "Fail"].copy()

export_cols = [
    SITE_COL,
    "Date of visit",
    REGION_COL,
    DISTRICT_COL,
    FLM_COL,
    "Email1",
    "Audit remarks",
    "District_Region_Status",
    "Month",
]

export_cols = [c for c in export_cols if c in failed_visits.columns]
failed_export = failed_visits[export_cols]

st.success(f"Total Failed Visits: {len(failed_export)}")
st.dataframe(failed_export, use_container_width=True, height=520)

excel_buffer = BytesIO()
failed_export.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)

st.download_button(
    "⬇ Download Failed Visits (Excel)",
    excel_buffer,
    "Failed_Visits_Detailed.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
