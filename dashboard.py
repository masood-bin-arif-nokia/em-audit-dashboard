import streamlit as st
import pandas as pd
import plotly.express as px
import os
import zipfile

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="EM Audit | Neon Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================== HELPERS ==================
def get_last_generated_time(file_path):
    if os.path.exists(file_path):
        ts = os.path.getmtime(file_path)
        return datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")
    return "Not generated yet"

# ================== PDF GENERATOR ==================
def generate_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "EM Audit Dashboard Summary")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Generated on: {datetime.now().strftime('%d %b %Y %H:%M')}")
    y -= 40

    total = len(df)
    passed = (df["Audit Status"] == "Pass").sum()
    failed = (df["Audit Status"] == "Fail").sum()

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Executive Overview")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Total Visits: {total}")
    y -= 15
    c.drawString(40, y, f"Pass: {passed}")
    y -= 15
    c.drawString(40, y, f"Fail: {failed}")
    y -= 30

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()

# ================= PATHS =================
ppt_path = "output/Summary.pptx"
last_generated = get_last_generated_time(ppt_path)

# ================= TITLE =================
st.title("⚡ EM Audit – Neon Analytics Dashboard")

# ================= DOWNLOAD SECTION =================
st.markdown("## 📥 Download Reports")
st.caption(f"🕒 Last Generated: **{last_generated}**")

if os.path.exists(ppt_path):
    if st.button("📦 Download Dashboard (PDF + PPT)"):
        with st.spinner("Preparing dashboard package..."):
            pdf_buffer = generate_pdf(df)

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("EM_Audit_Summary.pdf", pdf_buffer.getvalue())
                z.write(ppt_path, arcname="EM_Audit_Summary.pptx")

            zip_buffer.seek(0)

        st.download_button(
            label="⬇ Download ZIP",
            data=zip_buffer,
            file_name="EM_Audit_Dashboard.zip",
            mime="application/zip"
        )
else:
    st.info("Summary PPT will appear after the next automation run.")

# ================= NEON CSS =================
st.markdown("""
<style>
.neon-card {
    background: linear-gradient(145deg, #0f172a, #020617);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 0 15px rgba(0,245,255,.35);
    border: 1px solid rgba(0,245,255,.25);
}
.neon-title { color:#00F5FF; font-size:16px; font-weight:600; }
.neon-value { font-size:34px; font-weight:800; color:#A7F3D0; }
.neon-sub { color:#9CA3AF; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ================= EXECUTIVE OVERVIEW =================
st.markdown("## 🚀 Executive Overview")

total = len(df)
passed = (df["Audit Status"] == "Pass").sum()
failed = (df["Audit Status"] == "Fail").sum()
pass_pct = round(passed / total * 100, 1)

c1, c2, c3 = st.columns(3)
c1.markdown(f"<div class='neon-card'><div class='neon-title'>Total Visits</div><div class='neon-value'>{total}</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='neon-card'><div class='neon-title'>Pass</div><div class='neon-value'>{passed}</div><div class='neon-sub'>{pass_pct}% Pass Rate</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='neon-card'><div class='neon-title'>Fail</div><div class='neon-value'>{failed}</div></div>", unsafe_allow_html=True)

# ================= DONUT =================
st.markdown("## 🎯 Audit Status Distribution")

fig = px.pie(
    df,
    names="Audit Status",
    hole=0.55,
    color_discrete_map={"Pass":"#22C55E","Fail":"#EF4444","Exempted":"#F59E0B"}
)
fig.update_layout(paper_bgcolor="#0B0F1A", font_color="#E5E7EB")
st.plotly_chart(fig, use_container_width=True)

# ================= REGION PERFORMANCE =================
st.markdown("## 🌍 Region Performance")
cols = st.columns(4)

for i, region in enumerate(df["Region"].dropna().unique()):
    r = df[df["Region"] == region]
    with cols[i % 4]:
        st.markdown(f"""
        <div class="neon-card">
            <div class="neon-title">{region}</div>
            <div class="neon-value">{len(r)}</div>
            <div class="neon-sub">
                Pass: {(r["Audit Status"]=="Pass").sum()} |
                Fail: {(r["Audit Status"]=="Fail").sum()}
            </div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("## 🧭 District Performance (By Region)")

DISTRICT_COL = "District(Updated)"

df_d = df.dropna(subset=["Region", DISTRICT_COL])

for region in df_d["Region"].unique():
    st.markdown(f"### {region}")

    region_df = df_d[df_d["Region"] == region]
    cols = st.columns(4)

    for i, district in enumerate(region_df[DISTRICT_COL].unique()):
        d = region_df[region_df[DISTRICT_COL] == district]

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



# ---------------- FLM RISK ----------------
st.markdown("## 🚨 FLM Risk Ranking")

flm = (
    df.groupby(["Region", "FLM Name"])
    .agg(
        Total=("SiteID", "count"),
        Fail=("Audit Status", lambda x: (x == "Fail").sum()),
        Sites=("SiteID", lambda x: ", ".join(sorted(x.astype(str).unique())))
    )
    .reset_index()
)

flm["Fail %"] = (flm["Fail"] / flm["Total"] * 100).round(1)

# Filter low-volume noise
flm = flm[flm["Total"] >= 3]

# Sort by highest risk
flm = flm.sort_values("Fail %", ascending=False)

# --------- HEATMAP ---------
fig2 = px.imshow(
    flm[["Fail %", "Fail", "Total"]],
    color_continuous_scale=["#22C55E", "#F59E0B", "#EF4444"],
    aspect="auto"
)
)

fig2.update_layout(
    paper_bgcolor="#0B0F1A",
    plot_bgcolor="#0B0F1A",
    font_color="#E5E7EB",
    height=500
)

st.plotly_chart(fig2, use_container_width=True)


)
# ---------------- FLM RISK (WITH SITE IDS) ----------------
st.markdown("## 🚨 FLM Risk Table (with SiteIDs)")

flm = (
    df.groupby(["Region", "FLM Name"])
    .agg(
        Total=("SiteID", "count"),
        Fail=("Audit Status", lambda x: (x == "Fail").sum()),
        Sites=("SiteID", lambda x: ", ".join(sorted(set(x.astype(str)))))
    )
    .reset_index()
)

flm["Fail %"] = (flm["Fail"] / flm["Total"] * 100).round(1)
flm = flm[flm["Total"] >= 3].sort_values("Fail %", ascending=False)

st.dataframe(
    flm,
    use_container_width=True,
    height=450
)
