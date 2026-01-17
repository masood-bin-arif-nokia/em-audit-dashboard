import os
import pandas as pd
from datetime import datetime
import traceback

# ======================================================
# PATH SETUP
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
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

log("========== EM AUDIT AUTOMATION STARTED ==========")

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
    # LOAD SOURCE DATA
    # --------------------------------------------------
    source_file = os.path.join(DATA_DIR, "Mirror_C1.xlsx")
    df = pd.read_excel(source_file)

    df.columns = df.columns.str.strip().str.replace("\n", "", regex=False)

    log(f"Loaded Mirror_C1.xlsx | Rows: {len(df)}")

    # --------------------------------------------------
    # SPLIT PASS / FAIL
    # --------------------------------------------------
    pass_df = df[df[STATUS_COL] == "Pass"]
    fail_df = df[df[STATUS_COL] == "Fail"]

    log(f"Pass records: {len(pass_df)} | Fail records: {len(fail_df)}")

    # --------------------------------------------------
    # FAILED VISITS – DETAILED EXPORT (201)
    # --------------------------------------------------
    failed_visits_file = os.path.join(OUTPUT_DIR, "Failed_Visits_Detailed.xlsx")

    fail_df.to_excel(failed_visits_file, index=False)

    log(f"Failed Visits exported | Count: {len(fail_df)}")

    # --------------------------------------------------
    # PASS TRUTH (unique sites per FLM)
    # --------------------------------------------------
    pass_truth = (
        pass_df
        .groupby([REGION_COL, DISTRICT_COL, FLM_COL])[SITE_COL]
        .nunique()
        .reset_index(name="Total Sites")
    )

    # --------------------------------------------------
    # FAIL COUNTS (unique failed sites per FLM)
    # --------------------------------------------------
    fail_summary = (
        fail_df
        .groupby([REGION_COL, DISTRICT_COL, FLM_COL])[SITE_COL]
        .nunique()
        .reset_index(name="Fail")
    )

    # --------------------------------------------------
    # MERGE PASS + FAIL
    # --------------------------------------------------
    flm_risk = pass_truth.merge(
        fail_summary,
        on=[REGION_COL, DISTRICT_COL, FLM_COL],
        how="left"
    )

    flm_risk["Fail"] = flm_risk["Fail"].fillna(0).astype(int)
    flm_risk["Pass"] = flm_risk["Total Sites"] - flm_risk["Fail"]
    flm_risk["Fail %"] = (
        flm_risk["Fail"] / flm_risk["Total Sites"] * 100
    ).round(1)

    # --------------------------------------------------
    # KEEP ONLY FLMs WITH FAILURES
    # --------------------------------------------------
    flm_risk = flm_risk[flm_risk["Fail"] > 0]

    # --------------------------------------------------
    # TOTAL ROW (MATCHES FAILED VISITS COUNT)
    # --------------------------------------------------
    total_sites = flm_risk["Total Sites"].sum()
    total_fail = flm_risk["Fail"].sum()
    total_pass = flm_risk["Pass"].sum()

    total_row = {
        REGION_COL: "TOTAL",
        DISTRICT_COL: "",
        FLM_COL: "",
        "Total Sites": total_sites,
        "Pass": total_pass,
        "Fail": total_fail,
        "Fail %": round((total_fail / total_sites) * 100, 1) if total_sites else 0
    }

    flm_risk = pd.concat(
        [flm_risk, pd.DataFrame([total_row])],
        ignore_index=True
    )

    # --------------------------------------------------
    # SORT (TOTAL ALWAYS LAST)
    # --------------------------------------------------
    body = flm_risk[flm_risk[REGION_COL] != "TOTAL"]
    total = flm_risk[flm_risk[REGION_COL] == "TOTAL"]

    flm_risk = pd.concat([
        body.sort_values(["Fail %", "Fail"], ascending=False),
        total
    ])

    # --------------------------------------------------
    # EXPORT FLM RISK SUMMARY
    # --------------------------------------------------
    flm_file = os.path.join(OUTPUT_DIR, "FLM_Risk_Summary.xlsx")
    flm_risk.to_excel(flm_file, index=False)

    log(f"FLM_Risk_Summary.xlsx generated | Total Fail Sites: {total_fail}")

    log("========== TASK COMPLETED SUCCESSFULLY ==========\n")

except Exception as e:
    log("========== TASK FAILED ==========")
    log(str(e))
    log(traceback.format_exc())
    raise
