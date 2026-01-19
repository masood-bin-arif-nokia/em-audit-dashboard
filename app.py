import streamlit as st
import pandas as pd
import plotly.express as px
import os, zipfile
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

# Normalize column names
df.columns = df.columns.str.strip().str.replace("\n", "", regex=False)

# ================= FLM RISK LOADER =================
@st.cache_data
def load_flm_risk():
    return pd.read_excel("data/FLM_Risk_Summary.xlsx")

# ================= HELPERS =================
def get_last_generated_time(file_path):
    if os.path.exists(file_path):
        return datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).strftime("%d %b %Y, %H:%M")
    return "Not generated yet"

def generate_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = 800

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "EM Audit Dashboard Summary")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Generated on: {datetime.now():%d %b %Y %H:%M}")
    y -= 30

    total = len(df)
    passed = (df[STATUS_COL] == "Pass").sum()
    failed = (df[STATUS_COL] == "Fail").sum()

    c.drawString(40, y, f"Total Sites: {total}")
    y -= 15
    c.drawString(40, y, f"Pass: {passed}")
    y -= 15
    c.drawString(40, y, f"Fail: {failed}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ================= TITLE =================
st.title("⚡ EM Audit – Neon Analytics Dashboard")

# ================= DOWNLOAD SECTION =================
ppt_path = "data/Summary.pptx"
last_generated = get_last_generated_time(ppt_path)

st.markdown("## 📥 Download Reports")
st.caption(f"🕒 Last Generated: **{last_generated}**")

if os.path.exists(ppt_path):
    pdf = generate_pdf(df)

    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("EM_Audit_Summary.pdf", pdf.getvalue())
        z.write(ppt_path, "EM_Audit_Summary.pptx")
    zip_buf.seek(0)

    st.download_button(
        "📦 Download Dashboard (PDF + PPT)",
        zip_buf,
        "EM_Audit_Dashboard.zip",
        "application/zip"
    )
else:
    st.warning("⚠ Summary.pptx not found in data/ folder")

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

# ================= EXECUTIVE OVERVIEW =================
st.markdown("## 🚀 Executive Overview")

total = len(df)
pass_cnt = (df[STATUS_COL] == "Pass").sum()
fail_cnt = (df[STATUS_COL] == "Fail").sum()

pass_pct = round(pass_cnt / total * 100, 1)
fail_pct = round(fail_cnt / total * 100, 1)

c1, c2, c3 = st.columns(3)
c1.markdown(f"<div class='neon-card'><div class='neon-title'>Total</div><div class='neon-value'>{total}</div></div>", True)
c2.markdown(f"<div class='neon-card'><div class='neon-title'>Pass</div><div class='neon-value'>{pass_cnt}</div><div class='neon-sub'>{pass_pct}%</div></div>", True)
c3.markdown(f"<div class='neon-card'><div class='neon-title'>Fail</div><div class='neon-value'>{fail_cnt}</div><div class='neon-sub'>{fail_pct}%</div></div>", True)

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
fig.update_layout(paper_bgcolor="#0B0F1A", font_color="#E5E7EB")
st.plotly_chart(fig, use_container_width=True)

# ================= REGION PERFORMANCE =================
st.markdown("## 🌍 Region Performance")
cols = st.columns(4)

for i, region in enumerate(df[REGION_COL].dropna().unique()):
    r = df[df[REGION_COL] == region]
    t = len(r)
    p = (r[STATUS_COL] == "Pass").sum()
    f = (r[STATUS_COL] == "Fail").sum()
    p_pct = round(p/t*100, 1) if t else 0
    f_pct = round(f/t*100, 1) if t else 0

    with cols[i % 4]:
        st.markdown(f"""
        <div class="neon-card">
            <div class="neon-title">{region}</div>
            <div class="neon-value">{t}</div>
            <div class="neon-sub">Pass: {p} ({p_pct}%) | Fail: {f} ({f_pct}%)</div>
        </div>
        """, True)

# ================= FAILED VISITS EXPORT =================
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
