import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="EM Audit Dashboard", layout="wide")
st.title("📊 EM Audit Dashboard")

@st.cache_data
def load_data():
    return pd.read_excel("data/Mirror_C1.xlsx")

df = load_data()

# ---------------- SUMMARY TABLE ----------------
summary = df.groupby("Region").agg(
    Unique_Sites=("SiteID", "nunique"),
    Total_Visits=("SiteID", "count"),
    Pass_Count=("Audit Status", lambda x: (x == "Pass").sum()),
    Fail_Count=("Audit Status", lambda x: (x == "Fail").sum()),
    Exempted_Count=("Audit Status", lambda x: (x == "Exempted").sum())
).reset_index()

for col in ["Pass", "Fail", "Exempted"]:
    summary[f"{col} %"] = (
        summary[f"{col}_Count"] / summary["Total_Visits"] * 100
    ).round(1)

st.subheader("Overall Summary")
st.dataframe(summary, use_container_width=True)

st.plotly_chart(
    px.pie(df, names="Audit Status", hole=0.4),
    use_container_width=True
)

# ---------------- REGION PERFORMANCE ----------------
st.subheader("Region Performance")

cols = st.columns(4)
for i, region in enumerate(df["Region"].dropna().unique()):
    r = df[df["Region"] == region]
    with cols[i % 4]:
        st.metric("Region", region)
        st.metric("Total Visits", len(r))
        st.metric("Pass", (r["Audit Status"] == "Pass").sum())
        st.metric("Fail", (r["Audit Status"] == "Fail").sum())
        st.metric("Exempted", (r["Audit Status"] == "Exempted").sum())
