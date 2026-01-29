import os
import pandas as pd
from datetime import datetime
import traceback

# ======================================================
# PATH SETUP
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")   # dashboard reads from data/
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "automation.log")

# ======================================================
# LOGGING
# ======================================================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {msg}\n")

log("========== FLM RISK AUTOMATION STARTED ==========")

# ======================================================
# COLUMN CONSTANTS (DO NOT CHANGE)
# ======================================================
REGION_COL = "Region"
DISTRICT_COL = "District(Updated)"
FLM_COL = "FLM Name"
SITE_COL = "SiteID"
STATUS_COL = "Audit Status"

# ======================================================
# MAIN LOGIC
# ======================================================
try:
    # --------------------------------------------------
    # LOAD MIRROR (CANONICAL TRUTH)
    # --------------------------------------------------
    source_file = os.path.join(DATA_DIR, "Mirror_C1.xlsx")

    if not os.path.exists(source_file):
        raise FileNotFoundError(f"Mirror file not found: {source_file}")

    df = pd.read_excel(source_file)
    df.columns = df.columns.str.strip().str.replace("\n", "", regex=False)

    log(f"Loaded Mirror_C1.xlsx | Rows: {len(df)}")

    required_cols = [
        REGION_COL,
        DISTRICT_COL,
        FLM_COL,
        SITE_COL,
        STATUS_COL
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in mirror: {missing}")

    # --------------------------------------------------
    # FAILED VISITS – DETAILED EXPORT (DASHBOARD DOWNLOAD)
    # --------------------------------------------------
    fail_df = df[df[STATUS_COL] == "Fail"].copy()

    failed_visits_file = os.path.join(OUTPUT_DIR, "Failed_Visits_Detailed.xlsx")
    fail_df.to_excel(failed_visits_file, index=False)

    log(f"Failed Visits exported | Count: {len(fail_df)}")

    # --------------------------------------------------
    # FLM RISK AGGREGATION (PURE AGGREGATION)
    # --------------------------------------------------
    flm_risk = (
        df
        .groupby([FLM_COL, REGION_COL, DISTRICT_COL], dropna=False)
        .agg(
            Total_Sites=(SITE_COL, "nunique"),
            Fail=(STATUS_COL, lambda x: (x == "Fail").sum())
        )
        .reset_index()
    )

    flm_risk["Pass"] = flm_risk["Total_Sites"] - flm_risk["Fail"]
    flm_risk["Fail %"] = (
        flm_risk["Fail"] / flm_risk["Total_Sites"] * 100
    ).round(1)

    # --------------------------------------------------
    # TOTAL ROW (EXECUTIVE CHECK)
    # --------------------------------------------------
    total_sites = flm_risk["Total_Sites"].sum()
    total_fail = flm_risk["Fail"].sum()
    total_pass = flm_risk["Pass"].sum()

    total_row = {
        FLM_COL: "TOTAL",
        REGION_COL: "",
        DISTRICT_COL: "",
        "Total_Sites": total_sites,
        "Pass": total_pass,
        "Fail": total_fail,
        "Fail %": round((total_fail / total_sites) * 100, 1)
        if total_sites else 0
    }

    flm_risk = pd.concat(
        [flm_risk, pd.DataFrame([total_row])],
        ignore_index=True
    )

    # --------------------------------------------------
    # SORT (HIGHEST RISK FIRST, TOTAL LAST)
    # --------------------------------------------------
    body = flm_risk[flm_risk[FLM_COL] != "TOTAL"]
    total = flm_risk[flm_risk[FLM_COL] == "TOTAL"]

    flm_risk = pd.concat([
        body.sort_values(["Fail %", "Fail"], ascending=False),
        total
    ])

    # --------------------------------------------------
    # EXPORT FOR DASHBOARD
    # --------------------------------------------------
    flm_file = os.path.join(OUTPUT_DIR, "FLM_Risk_Summary.xlsx")
    flm_risk.to_excel(flm_file, index=False)

    log(f"FLM_Risk_Summary.xlsx generated | Rows: {len(flm_risk)}")
    log("========== FLM RISK AUTOMATION COMPLETED SUCCESSFULLY ==========\n")

except Exception as e:
    log("========== FLM RISK AUTOMATION FAILED ==========")
    log(str(e))
    log(traceback.format_exc())
    raise
