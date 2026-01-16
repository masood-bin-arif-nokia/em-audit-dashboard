import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="EM Audit | Neon Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# NEON CSS
# =====================================================
st.markdown("""
<style>
.neon-card {
    background: linear-gradient(145deg, #0f172a, #020617);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 0 15px rgba(0, 245, 255, 0.35);
    border: 1px solid rgba(0, 245, 255, 0.25);
}
.neon-title {
    color: #00F5FF;
    font-size: 16px;
    font-weight: 600;
}
.neon-value {
    font-size: 34px;
    font-weight: 800;
    color: #A7F3D0;
}
.neon-sub {
    color: #9CA3AF;
    font-size: 13px;
}

/* Risk glows */
.neon-green {
    box-shadow: 0 0 18px rgba(34, 197, 94, 0.6);
    border: 1px solid rgba(34, 197, 94, 0.6);
}
.neon-amber {
    box-shadow: 0 0 18px rgba(245, 158, 11, 0.6);
    border: 1px solid rgba(245, 158, 11, 0.6);
}
.neon-red {
    box-shadow: 0 0 18px rgba(239, 68, 68, 0.6);
    border: 1px solid rgba(239, 68, 68, 0.6);
}

/* Badges */
.badge {
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
}
.badge-green { background: #22C55E; color: black; }
.badge-amber { background: #F59E0B; color: black; }
.badge-red { background: #EF4444; color: white; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# TITLE + DOWNLOAD
# =====================================================
st.title("⚡ EM Audit – Neon Analytics Dashboard")

st.markdown("## 📥 Download Reports")

ppt_path = Path("data/Summary.pptx")
if ppt_path.exists():
    with open(ppt_path, "rb") as f:
        st.download_button(
            label="Download Dashboard (PPT)",
            data=f,
            file_name="EM_Audit_Dashboard_Summary.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
else:
    st.info("Summary PPT will be available after the next automation run.")

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()

# =====================================================
# EXECUTIVE OVERVIEW
# =====================================================
total_visits = len(df)
pass_count = (df["Audit Status"] == "Pass").sum()
fail_count = (df["Audit Status"] == "Fail").sum()
exempted_count = (df["Audit Status"] == "Exempted").sum()
pass_pct = round(pass_count / total_visits * 100, 1) if total_visits else 0

st.markdown("## 🚀 Executive Overview")

def neon_card(title, value, sub=""):
    st.markdown(f"""
    <div class="neon-card">
        <div class="neon-title">{title}</div>
        <div class="neon-value">{value}</div>
        <div class="neon-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: neon_card("Total Visits", total_visits)
with c2: neon_card("Pass", pass_count, f"{pass_pct}% Pass Rate")
with c3: neon_card("Fail", fail_count)
with c4: neon_card("Exempted", exempted_count)

# =====================================================
# AUDIT STATUS DONUT
# =====================================================
st.markdown("## 🎯 Audit Status Distribution")

fig = px.pie(
    df,
    names="Audit Status",
    hole=0.55,
    color_discrete_map={
        "Pass": "#22C55E",
        "Fail": "#EF4444",
        "Exempted": "#F59E0B"
    }
)

fig.update_layout(
    paper_bgcolor="#0B0F1A",
    plot_bgcolor="#0B0F1A",
    font_color="#E5E7EB",
    height=420
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# REGION PERFORMANCE
# =====================================================
st.markdown("## 🌍 Region Performance")

regions = df["Region"].dropna().unique()
cols = st.columns(4)

for i, region in enumerate(regions):
    r = df[df["Region"] == region]
    with cols[i % 4]:
        st.markdown(f"""
        <div class="neon-card">
            <div class="neon-title">{region}</div>
            <div class="neon-sub">Total Visits</div>
            <div class="neon-value">{len(r)}</div>
            <div class="neon-sub">
                Pass: {(r["Audit Status"] == "Pass").sum()} &nbsp;&nbsp;
                Fail: {(r["Audit Status"] == "Fail").sum()} &nbsp;&nbsp;
                Exempted: {(r["Audit Status"] == "Exempted").sum()}
            </div>
        </div>
        """, unsafe_allow_html=True)

# =====================================================
# DISTRICT PERFORMANCE (NEON + RISK)
# =====================================================
st.markdown("## 🧭 District Performance (By Region)")

df_district = df.dropna(subset=["Region", "District(Updated)"])

for region in df_district["Region"].unique():
    st.markdown(f"### {region}")
    region_df = df_district[df_district["Region"] == region]
    districts = region_df["District(Updated)"].unique()
    cols = st.columns(4)

    for i, district in enumerate(districts):
        d = region_df[region_df["District(Updated)"] == district]

        total = len(d)
        pass_cnt = (d["Audit Status"] == "Pass").sum()
        fail_cnt = (d["Audit Status"] == "Fail").sum()
        exempt_cnt = (d["Audit Status"] == "Exempted").sum()
        fail_pct = round((fail_cnt / total) * 100, 1) if total else 0

        if fail_pct >= 30:
            glow, badge = "neon-red", "badge-red"
        elif fail_pct >= 10:
            glow, badge = "neon-amber", "badge-amber"
        else:
            glow, badge = "neon-green", "badge-green"

        with cols[i % 4]:
            st.markdown(f"""
            <div class="neon-card {glow}">
                <div class="neon-title">{district}</div>
                <div class="neon-sub">Total Visits</div>
                <div class="neon-value">{total}</div>
                <div class="neon-sub">
                    Pass: {pass_cnt} &nbsp;&nbsp;
                    Fail: {fail_cnt} &nbsp;&nbsp;
                    Exempted: {exempt_cnt}
                </div>
                <div style="margin-top:8px;">
                    <span class="badge {badge}">Fail %: {fail_pct}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =====================================================
# DISTRICT RISK RANKING TABLE
# =====================================================
st.markdown("## 🚨 District Risk Ranking")

district_risk = (
    df_district.groupby(["Region", "District(Updated)"])
    .agg(
        Total_Visits=("SiteID", "count"),
        Fail_Count=("Audit Status", lambda x: (x == "Fail").sum())
    )
    .reset_index()
)

district_risk["Fail %"] = (
    district_risk["Fail_Count"] / district_risk["Total_Visits"] * 100
).round(1)

district_risk = district_risk[district_risk["Total_Visits"] >= 3]
district_risk = district_risk.sort_values("Fail %", ascending=False)

st.dataframe(district_risk, use_container_width=True, height=350)

# =====================================================
# DISTRICT FILTER → FLM DRILLDOWN
# =====================================================
st.markdown("## 🎯 Drill-Down Controls")

selected_district = st.selectbox(
    "Select District",
    ["All"] + sorted(district_risk["District(Updated)"].unique().tolist())
)

flm_df = df.copy()
if selected_district != "All":
    flm_df = flm_df[flm_df["District(Updated)"] == selected_district]

# =====================================================
# FLM RISK RANKING
# =====================================================
st.markdown("## 🚨 FLM Risk Ranking")

flm_summary = (
    flm_df.groupby(["Region", "FLM Name"])
    .agg(
        Total_Visits=("SiteID", "count"),
        Fail_Count=("Audit Status", lambda x: (x == "Fail").sum())
    )
    .reset_index()
)

flm_summary["Fail %"] = (
    flm_summary["Fail_Count"] / flm_summary["Total_Visits"] * 100
).round(1)

flm_summary = flm_summary[flm_summary["Total_Visits"] >= 3]
flm_summary = flm_summary.sort_values(["Fail %", "Fail_Count"], ascending=False)

fig2 = px.imshow(
    flm_summary[["Fail %", "Fail_Count", "Total_Visits"]],
    color_continuous_scale=["#22C55E", "#F59E0B", "#EF4444"],
    aspect="auto"
)

fig2.update_layout(
    paper_bgcolor="#0B0F1A",
    plot_bgcolor="#0B0F1A",
    font_color="#E5E7EB",
    height=500
)

st.plotly_chart(fig2, use_container_width=True)
st.markdown("### 📋 FLM Risk Table")
st.dataframe(flm_summary, use_container_width=True, height=450)

