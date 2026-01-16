import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="EM Audit | Neon Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- NEON CSS ----------------
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
</style>
""", unsafe_allow_html=True)

st.title("⚡ EM Audit – Neon Analytics Dashboard")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()

# ---------------- STEP 3: EXECUTIVE KPI STRIP ----------------
total_visits = len(df)
pass_count = (df["Audit Status"] == "Pass").sum()
fail_count = (df["Audit Status"] == "Fail").sum()
exempted_count = (df["Audit Status"] == "Exempted").sum()
pass_pct = round(pass_count / total_visits * 100, 1) if total_visits else 0

st.markdown("## 🚀 Executive Overview")

c1, c2, c3, c4 = st.columns(4)

def neon_card(title, value, sub=""):
    st.markdown(f"""
    <div class="neon-card">
        <div class="neon-title">{title}</div>
        <div class="neon-value">{value}</div>
        <div class="neon-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

with c1:
    neon_card("Total Visits", total_visits)

with c2:
    neon_card("Pass", pass_count, f"{pass_pct}% Pass Rate")

with c3:
    neon_card("Fail", fail_count)

with c4:
    neon_card("Exempted", exempted_count)

# ---------------- STEP 4: NEON DONUT ----------------
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

# ---------------- STEP 5: REGION PERFORMANCE ----------------
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

# ---------------- STEP 6: FLM RISK RANKING ----------------
st.markdown("## 🚨 FLM Risk Ranking")

flm_summary = (
    df.groupby(["Region", "FLM Name"])
    .agg(
        Total_Visits=("SiteID", "count"),
        Fail_Count=("Audit Status", lambda x: (x == "Fail").sum()),
    )
    .reset_index()
)

flm_summary["Fail %"] = (
    flm_summary["Fail_Count"] / flm_summary["Total_Visits"] * 100
).round(1)

flm_summary = flm_summary[flm_summary["Total_Visits"] >= 3]
flm_summary = flm_summary.sort_values(
    ["Fail %", "Fail_Count"], ascending=False
)

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

# ---------------- STEP 7: DISTRICT PERFORMANCE (NEON CARDS) ----------------
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

        with cols[i % 4]:
            st.markdown(f"""
            <div class="neon-card">
                <div class="neon-title">{district}</div>
                <div class="neon-sub">Total Visits</div>
                <div class="neon-value">{total}</div>
                <div class="neon-sub">
                    Pass: {pass_cnt} &nbsp;&nbsp;
                    Fail: {fail_cnt} &nbsp;&nbsp;
                    Exempted: {exempt_cnt}
                </div>
            </div>
            """, unsafe_allow_html=True)
