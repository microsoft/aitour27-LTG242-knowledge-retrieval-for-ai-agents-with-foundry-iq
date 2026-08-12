# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   }
# META }

# MARKDOWN ********************

# # Deploy Vendor Lakehouse & AI-Ready Semantic Model
# 
# This notebook is designed to run inside a **Microsoft Fabric** notebook (PySpark).
# 
# It will:
# 1. Deploy a new **Lakehouse** (name controlled by the parameter cell — default `EnterpriseLakehouse`).
# 2. Create the **`DimVendor`** dimension and a **dated** **`VendorPerformance`** fact table — one row per vendor **per day** over the last **2 years** — joinable on `VendorID` and `DateKey`.
# 3. Create supporting **dimension tables** for the vendor star schema (`DimDate`, `DimLocation`, `DimInspectionResult`, `DimAuditResult`, `DimFinancialRating`).
# 4. Build a **Direct Lake semantic model** over the lakehouse (with date intelligence and recent-trend measures).
# 5. **Prep the model for AI / Copilot** (relationships, measures, descriptions, and Q&A synonyms).
# 
# > Source data is sourced from the *Allerveo CMO Vendor Comparison* workbook
# > (`Vendor Overview`, `Quality & Regulatory`, and `Capacity & Commercial` tabs) and embedded below so the notebook is self-contained.
# > The daily performance history is **synthesized** from those headline metrics so we can analyse trends over time.
# 
# **Star schema**
# 
# ```
#         DimLocation        DimFinancialRating
#             |                     |
#             +------ DimVendor ----+
#                         |
#         DimDate ── VendorPerformance (fact, daily) ──┬── DimInspectionResult
#                                                      └── DimAuditResult
# ```


# MARKDOWN ********************

# ## 0. Install libraries
# 
# - `fabric-data-agent-sdk` — creates the Vendor Data Agent (step 11). Ships pre-release builds only, so `--pre` is required.
# - `semantic-link-labs` (`sempy_labs`) — generates the Direct Lake semantic model and preps it for AI.
# 
# > **Run this cell first, then re-run the whole notebook top-to-bottom** — `%pip install` restarts the
# > Python kernel and clears every variable, so it must run before any parameters are set.
# >
# > The Vendor Data Agent (step 11) requires a **paid Fabric F-SKU capacity**; it isn't supported on Trial capacities.


# CELL ********************

# fabric-data-agent-sdk only ships pre-release builds, so --pre is required.
%pip install -q --pre fabric-data-agent-sdk semantic-link-labs


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 1. Parameters
# 
# This cell is tagged **`parameters`** so the values can be overridden when the notebook is run from a pipeline or `notebookutils.run`.

# PARAMETERS CELL ********************

# --- Parameters (overridable) ---
lakehouse_name       = "EnterpriseLakehouse"    # Lakehouse to create / reuse
semantic_model_name  = "VendorSM"               # Direct Lake semantic model name
overwrite_tables     = True                     # Overwrite Delta tables if they already exist

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

print('Parameters set: ',lakehouse_name, semantic_model_name, overwrite_tables)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 3. Imports & workspace context

# CELL ********************

import notebookutils
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, DateType,
)

# Resolve the current workspace from the notebook runtime context
ctx = notebookutils.runtime.context
workspace_id = ctx.get("currentWorkspaceId") or ctx.get("workspaceId")
print(f"Workspace id : {workspace_id}")
print(f"Lakehouse    : {lakehouse_name}")
print(f"Model        : {semantic_model_name}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 4. Deploy (or reuse) the Lakehouse
# 
# We look for an existing lakehouse with the requested name and create it if missing, then build the
# OneLake `abfss` path used to write managed Delta tables — this lets us target the new lakehouse even
# though it is not the notebook's attached default.

# CELL ********************

# Find existing lakehouse by name, otherwise create it
existing = [lh for lh in notebookutils.lakehouse.list() if lh["displayName"] == lakehouse_name]
if existing:
    lakehouse = existing[0]
    print(f"Reusing existing lakehouse '{lakehouse_name}'.")
else:
    lakehouse = notebookutils.lakehouse.create(lakehouse_name)
    print(f"Created lakehouse '{lakehouse_name}'.")

lakehouse_id = lakehouse["id"]
tables_base = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables"
print(f"Lakehouse id : {lakehouse_id}")
print(f"Tables path  : {tables_base}")

def write_delta(df, table_name):
    """Writes a Spark DataFrame as a managed Delta table in the target lakehouse."""
    path = f"{tables_base}/{table_name}"
    mode = "overwrite" if overwrite_tables else "errorifexists"
    (df.write.mode(mode).format("delta").option("overwriteSchema", "true").save(path))
    print(f"  wrote {table_name:<22} ({df.count()} rows)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 5. Source data
# 
# The rows below are transcribed directly from the workbook tabs. A surrogate **`VendorID`** (`V001`..`V007`)
# is assigned consistently so every table joins cleanly. These headline figures are used as the **current
# baseline** from which the daily 2-year performance history is synthesized in the next step.


# CELL ********************

# VendorID assigned in a fixed order so all tables align
vendor_ids = {
    "Annterra Pharma":       "V001",
    "Kristos Pharma":        "V002",
    "Sabyn Formulations":    "V003",
    "Vexara Manufacturing":  "V004",
    "Telsin Group":          "V005",
    "Orova Pharmatech":      "V006",
    "Meridax Life Sciences": "V007",
}

# --- "Vendor Overview" tab ---------------------------------------------------
# vendor, location, avail_capacity_k, lead_time_wks, otif_12mo, batch_rej_rate, last_insp, cost_index
vendor_overview = [
    ("Annterra Pharma",       "New Jersey, USA",            850, 14, 0.972, 0.008, "NAI", 118),
    ("Kristos Pharma",        "North Carolina, USA",        520, 16, 0.958, 0.011, "VAI",  82),
    ("Sabyn Formulations",    "Massachusetts, USA",         380, 10, 0.965, 0.014, "NAI", 101),
    ("Vexara Manufacturing",  "Pennsylvania, USA",          120, 32, 0.981, 0.005, "NAI", 122),
    ("Telsin Group",          "Texas, USA",                 400, 18, 0.883, 0.038, "OAI",  74),
    ("Orova Pharmatech",      "Ohio, USA",                  100, 20, 0.941, 0.018, "VAI",  95),
    ("Meridax Life Sciences", "Dublin, Ireland / Singapore", 650, 24, 0.912, 0.021, "VAI",  88),
]

# --- "Quality & Regulatory" tab ----------------------------------------------
# vendor, otif_12mo, batch_rej_rate, right_first_time, complaints_per_1k,
# last_insp, open_actions, inspections_3yr, last_audit_result
quality_regulatory = [
    ("Annterra Pharma",       0.972, 0.008, 0.981, 0.9, "NAI", 0, 3, "Satisfactory"),
    ("Kristos Pharma",        0.958, 0.011, 0.974, 1.2, "VAI", 0, 2, "Satisfactory"),
    ("Sabyn Formulations",    0.965, 0.014, 0.962, 1.5, "NAI", 0, 2, "Satisfactory"),
    ("Vexara Manufacturing",  0.981, 0.005, 0.988, 0.6, "NAI", 0, 3, "Outstanding"),
    ("Telsin Group",          0.883, 0.038, 0.891, 4.2, "OAI", 2, 2, "Requires Improvement"),
    ("Orova Pharmatech",      0.941, 0.018, 0.955, 1.9, "VAI", 0, 2, "Satisfactory"),
    ("Meridax Life Sciences", 0.912, 0.021, 0.948, 2.3, "VAI", 0, 1, "Satisfactory"),
]

# --- "Capacity & Commercial" tab ---------------------------------------------
# vendor, osd_experience_yrs, avail_capacity_k, utilization, lead_time_wks,
# cost_index, moq_k, tech_transfer_success, financial_stability_rating
capacity_commercial = [
    ("Annterra Pharma",       22, 850, 0.68, 14, 118, 250, 1.00, "A+"),
    ("Kristos Pharma",        15, 520, 0.78, 16,  82, 125, 0.94, "A"),
    ("Sabyn Formulations",    11, 380, 0.71, 10, 101,  63, 0.92, "B+"),
    ("Vexara Manufacturing",  28, 120, 0.96, 32, 122, 500, 0.97, "A+"),
    ("Telsin Group",           7, 400, 0.58, 18,  74, 125, 0.78, "B-"),
    ("Orova Pharmatech",      18, 100, 0.88, 20,  95, 188, 0.89, "B+"),
    ("Meridax Life Sciences", 14, 650, 0.73, 24,  88, 625, 0.86, "A-"),
]

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 6. Build the dimension & fact DataFrames
# 
# We build:
# 
# - **`DimDate`** — a daily date dimension covering the last **2 years** (calendar attributes for time intelligence).
# - **`DimVendor`** — the vendor dimension (renamed from `Vendors` for naming consistency with the other `Dim*` tables). Holds the *static* vendor attributes (location, experience, capacity, MOQ, financial rating).
# - **`VendorPerformance`** — the fact table, now at **daily grain**: one row per vendor per **weekly snapshot day** across the 2-year window. Each row carries a `DateKey` that links to `DimDate` and a `VendorID` that links to `DimVendor`. The time-varying KPIs (OTIF, batch rejection, right-first-time, complaints, utilization, lead time, cost index, tech-transfer) are **synthesized** so they trend realistically toward each vendor's baseline.
# - The reference dimensions (`DimLocation`, `DimInspectionResult`, `DimAuditResult`, `DimFinancialRating`).


# CELL ********************

import random
from datetime import date, timedelta

# ----------------------------------------------------------------------------
# Reference window: weekly snapshots across the last 2 years (~105 weeks).
# Each snapshot lands on a Monday and links to a real day in DimDate, so the
# fact is "tied to a day" while staying a manageable size for a demo.
# ----------------------------------------------------------------------------
random.seed(42)

today        = date.today()
last_monday  = today - timedelta(days=today.weekday())   # most recent Monday
num_weeks    = 105                                        # ~2 years of weekly snapshots
snapshot_dates = sorted(last_monday - timedelta(weeks=w) for w in range(num_weeks))
history_start, history_end = snapshot_dates[0], snapshot_dates[-1]

shift_weeks     = 5                                       # the "recent change" window
shift_start_idx = num_weeks - shift_weeks                 # index where the recent shift begins
step_idx        = shift_start_idx + shift_weeks // 2      # where categorical values flip

print(f"History window        : {history_start} -> {history_end} ({num_weeks} weekly snapshots)")
print(f"Recent-change window  : starts {snapshot_dates[shift_start_idx]}")

# --- DimDate (daily grain over the full 2-year window) -----------------------
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
DAYS   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

date_rows = []
d = history_start
while d <= history_end:
    iso = d.isocalendar()
    q = (d.month - 1) // 3 + 1
    date_rows.append((
        int(d.strftime("%Y%m%d")),                # DateKey
        d,                                        # Date
        d.year,                                   # Year
        q,                                        # Quarter
        f"Q{q} {d.year}",                         # QuarterName
        d.month,                                  # MonthNumber
        MONTHS[d.month - 1],                      # MonthName
        f"{MONTHS[d.month - 1][:3]} {d.year}",    # MonthYear
        d.year * 100 + d.month,                   # MonthKey (sort)
        iso[1],                                   # WeekOfYear
        d.weekday() + 1,                          # DayOfWeekNumber (1 = Monday)
        DAYS[d.weekday()],                        # DayName
        "Yes" if d.weekday() >= 5 else "No",      # IsWeekend
    ))
    d += timedelta(days=1)

dim_date_schema = StructType([
    StructField("DateKey",         IntegerType(), False),
    StructField("Date",            DateType(),    True),
    StructField("Year",            IntegerType(), True),
    StructField("Quarter",         IntegerType(), True),
    StructField("QuarterName",     StringType(),  True),
    StructField("MonthNumber",     IntegerType(), True),
    StructField("MonthName",       StringType(),  True),
    StructField("MonthYear",       StringType(),  True),
    StructField("MonthKey",        IntegerType(), True),
    StructField("WeekOfYear",      IntegerType(), True),
    StructField("DayOfWeekNumber", IntegerType(), True),
    StructField("DayName",         StringType(),  True),
    StructField("IsWeekend",       StringType(),  True),
])
dim_date = spark.createDataFrame(date_rows, schema=dim_date_schema)

# --- DimLocation -------------------------------------------------------------
def parse_location(loc):
    parts = [p.strip() for p in loc.split(",")]
    region = parts[0]
    country = parts[1] if len(parts) > 1 else parts[0]
    return region, country

distinct_locations, seen = [], {}
for v in vendor_overview:
    loc = v[1]
    if loc not in seen:
        region, country = parse_location(loc)
        loc_id = f"L{len(distinct_locations) + 1:03d}"
        seen[loc] = loc_id
        distinct_locations.append((loc_id, loc, region, country))

dim_location_schema = StructType([
    StructField("LocationID",     StringType(), False),
    StructField("Location",       StringType(), True),
    StructField("StateOrRegion",  StringType(), True),
    StructField("Country",        StringType(), True),
])
dim_location = spark.createDataFrame(distinct_locations, schema=dim_location_schema)

# --- DimVendor (renamed from "Vendors"): STATIC vendor attributes only --------
cap_by_vendor  = {row[0]: row for row in capacity_commercial}
qual_by_vendor = {row[0]: row for row in quality_regulatory}

vendor_rows = []
for (vendor, loc, cap, lead, otif, batch, insp, cost) in vendor_overview:
    c = cap_by_vendor[vendor]    # capacity_commercial
    q = qual_by_vendor[vendor]   # quality_regulatory
    vendor_rows.append((
        vendor_ids[vendor], vendor, seen[loc], loc,
        c[1],   # OSDExperienceYrs
        c[2],   # AvailableCapacityKPerMonth
        c[6],   # MOQKUnits
        q[7],   # RegulatoryInspections3yr
        c[8],   # FinancialStabilityRating
    ))

dim_vendor_schema = StructType([
    StructField("VendorID",                   StringType(),  False),
    StructField("VendorName",                 StringType(),  True),
    StructField("LocationID",                 StringType(),  True),
    StructField("Location",                   StringType(),  True),
    StructField("OSDExperienceYrs",           IntegerType(), True),
    StructField("AvailableCapacityKPerMonth", IntegerType(), True),
    StructField("MOQKUnits",                  IntegerType(), True),
    StructField("RegulatoryInspections3yr",   IntegerType(), True),
    StructField("FinancialStabilityRating",   StringType(),  True),
])
dim_vendor = spark.createDataFrame(vendor_rows, schema=dim_vendor_schema)

# --- VendorPerformance (DATED fact) ------------------------------------------
# Each vendor's KPIs are synthesized so they drift toward today's baseline over
# two years, then a deliberate "recent change" is applied in the final weeks so
# the demo shows some vendors improving and others declining (see next section).

# story direction per vendor
story = {
    "V001": "stable", "V002": "stable", "V003": "declining", "V004": "stable",
    "V005": "improving", "V006": "improving", "V007": "declining",
}

# explicit CURRENT (end-of-window) values that create the recent-change story
end_overrides = {
    "V005": {"OTIF": 0.931, "Batch": 0.019, "RFT": 0.946, "Complaints": 2.1, "Util": 0.69,
             "Tech": 0.86, "OpenActions": 0, "Inspection": "VAI", "Audit": "Satisfactory"},
    "V006": {"OTIF": 0.963, "Batch": 0.011, "RFT": 0.969, "Complaints": 1.2, "Util": 0.90, "Tech": 0.92},
    "V007": {"OTIF": 0.874, "Batch": 0.035, "RFT": 0.921, "Complaints": 3.7, "Util": 0.91, "Tech": 0.83},
    "V003": {"OTIF": 0.947, "Batch": 0.024, "RFT": 0.945, "Complaints": 2.4, "Util": 0.79},
}

# numeric metric tuning: (noise std, lower bound, upper bound, is_integer, decimals)
metric_specs = {
    "OTIF":       (0.004,  0.80,  0.999, False, 4),
    "Batch":      (0.0015, 0.002, 0.060, False, 4),
    "RFT":        (0.004,  0.80,  0.999, False, 4),
    "Complaints": (0.15,   0.20,  6.00,  False, 2),
    "Util":       (0.010,  0.40,  0.99,  False, 4),
    "Lead":       (0.4,    6,     40,    True,  0),
    "Cost":       (1.0,    60,    140,   True,  0),
    "Tech":       (0.006,  0.70,  1.00,  False, 4),
}

# how much WORSE each metric was ~2 years ago (gentle long-run drift to baseline)
start_delta = {
    "OTIF": -0.010, "Batch": +0.004, "RFT": -0.012, "Complaints": +0.4,
    "Util": -0.03,  "Lead": +1,      "Cost": +3,    "Tech": -0.03,
}


def lerp(a, b, t):
    return a + (b - a) * t


def gen_series(start_v, mid_v, end_v, std, lo, hi, integer, decimals):
    """Drift start -> mid over the history, then mid -> end over the recent window."""
    out = []
    for i in range(num_weeks):
        if i <= shift_start_idx:
            t = i / shift_start_idx if shift_start_idx else 1.0
            base, noise = lerp(start_v, mid_v, t), random.gauss(0, std)
        else:
            denom = (num_weeks - 1 - shift_start_idx)
            t = (i - shift_start_idx) / denom if denom else 1.0
            base, noise = lerp(mid_v, end_v, t), random.gauss(0, std * 0.5)
        v = min(hi, max(lo, base + noise))
        out.append(int(round(v)) if integer else round(v, decimals))
    return out


perf_rows = []
for (vendor, loc, cap, lead, otif, batch, insp, cost) in vendor_overview:
    vid = vendor_ids[vendor]
    c, q = cap_by_vendor[vendor], qual_by_vendor[vendor]
    mid = {"OTIF": q[1], "Batch": q[2], "RFT": q[3], "Complaints": q[4],
           "Util": c[3], "Lead": c[4], "Cost": c[5], "Tech": c[7]}
    ov  = end_overrides.get(vid, {})
    end = {k: ov.get(k, mid[k]) for k in metric_specs}

    series = {}
    for k, (std, lo, hi, integer, dec) in metric_specs.items():
        start_v = min(hi, max(lo, mid[k] + start_delta[k]))
        series[k] = gen_series(start_v, mid[k], end[k], std, lo, hi, integer, dec)

    insp_mid,  insp_end  = q[5], ov.get("Inspection", q[5])
    audit_mid, audit_end = q[8], ov.get("Audit", q[8])
    oa_mid,    oa_end    = q[6], ov.get("OpenActions", q[6])

    for i, snap in enumerate(snapshot_dates):
        use_end = i >= step_idx
        perf_rows.append((
            vid,
            int(snap.strftime("%Y%m%d")),                 # DateKey -> DimDate
            series["OTIF"][i], series["Batch"][i], series["RFT"][i], series["Complaints"][i],
            insp_end if use_end else insp_mid,            # LastRegulatoryInspection
            oa_end if use_end else oa_mid,                # OpenRegulatoryActions
            audit_end if use_end else audit_mid,          # LastInternalAuditResult
            series["Util"][i], series["Lead"][i], series["Cost"][i], series["Tech"][i],
        ))

perf_schema = StructType([
    StructField("VendorID",                     StringType(),  False),
    StructField("DateKey",                      IntegerType(), False),
    StructField("OTIF12moPct",                  DoubleType(),  True),
    StructField("BatchRejectionRatePct",        DoubleType(),  True),
    StructField("RightFirstTimePct",            DoubleType(),  True),
    StructField("CustomerComplaintsPer1k",      DoubleType(),  True),
    StructField("LastRegulatoryInspection",     StringType(),  True),
    StructField("OpenRegulatoryActions",        IntegerType(), True),
    StructField("LastInternalAuditResult",      StringType(),  True),
    StructField("CurrentUtilizationPct",        DoubleType(),  True),
    StructField("LeadTimeToFirstProductionWks", IntegerType(), True),
    StructField("CostIndex",                    IntegerType(), True),
    StructField("TechTransferSuccessPct",       DoubleType(),  True),
])
vendor_performance = spark.createDataFrame(perf_rows, schema=perf_schema)

# --- DimInspectionResult (FDA-style classification) --------------------------
inspection_rows = [
    ("NAI", "No Action Indicated",        "No objectionable conditions or practices were found during the inspection.", 1, False),
    ("VAI", "Voluntary Action Indicated", "Objectionable conditions were found; voluntary correction is expected but no regulatory action is planned.", 2, False),
    ("OAI", "Official Action Indicated",  "Regulatory and/or administrative action will be recommended. A knockout for sourcing decisions.", 3, True),
]
inspection_schema = StructType([
    StructField("ResultCode",     StringType(),  False),
    StructField("ResultName",     StringType(),  True),
    StructField("Description",    StringType(),  True),
    StructField("SeverityRank",   IntegerType(), True),
    StructField("IsDisqualifying",StringType(),  True),
])
dim_inspection = spark.createDataFrame(
    [(c, n, d, r, "Yes" if f else "No") for (c, n, d, r, f) in inspection_rows],
    schema=inspection_schema,
)

# --- DimAuditResult ----------------------------------------------------------
audit_rows = [
    ("Outstanding",          1, "Yes"),
    ("Satisfactory",         2, "Yes"),
    ("Requires Improvement", 3, "No"),
]
audit_schema = StructType([
    StructField("AuditResult", StringType(),  False),
    StructField("ResultRank",  IntegerType(), True),
    StructField("IsPassing",   StringType(),  True),
])
dim_audit = spark.createDataFrame(audit_rows, schema=audit_schema)

# --- DimFinancialRating ------------------------------------------------------
rating_rows = [
    ("A+", 1, "Yes"), ("A", 2, "Yes"), ("A-", 3, "Yes"),
    ("B+", 4, "Yes"), ("B", 5, "No"),  ("B-", 6, "No"),
]
rating_schema = StructType([
    StructField("Rating",          StringType(),  False),
    StructField("RatingRank",      IntegerType(), True),
    StructField("InvestmentGrade", StringType(),  True),
])
dim_financial = spark.createDataFrame(rating_rows, schema=rating_schema)

print(f"\nVendorPerformance rows: {vendor_performance.count()} "
      f"({len(vendor_overview)} vendors x {num_weeks} weekly snapshots)")
display(dim_vendor)
display(vendor_performance.orderBy("VendorID", "DateKey"))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### 📈 The "recent change" demo story
# 
# The daily history is generated so that **most vendors are steady**, but in the **last ~5 weeks** a few
# vendors move sharply — giving us something interesting to analyse in the demo. Watch these in the trend
# charts and the *recent change* scorecard:
# 
# | Vendor | Direction | What changed in the last month |
# | --- | --- | --- |
# | **Telsin Group** (V005) | ⬆️ **Improving (turnaround)** | OTIF climbs ~0.88 → **0.93**, batch rejection falls ~3.8% → **1.9%**, complaints drop, and the regulatory inspection result recovers **OAI → VAI** with the internal audit moving *Requires Improvement → Satisfactory*. A clear recovery story. |
# | **Orova Pharmatech** (V006) | ⬆️ **Improving** | Steady gains — OTIF ~0.94 → **0.96**, batch rejection ~1.8% → **1.1%**. |
# | **Meridax Life Sciences** (V007) | ⬇️ **Declining** | OTIF slips ~0.91 → **0.87**, batch rejection rises ~2.1% → **3.5%**, complaints climb, and utilization spikes to **~91%** (capacity stress). |
# | **Sabyn Formulations** (V003) | ⬇️ **Declining** | Mild erosion — OTIF ~0.965 → **0.95**, batch rejection ~1.4% → **2.4%**. |
# | Annterra, Kristos, Vexara | ➡️ **Stable** | Normal week-to-week noise only. |
# 
# > Because the data is **date-aware**, the semantic model's *Latest* and *Δ vs 4 weeks* measures
# > surface exactly **who is trending up and who is trending down** — perfect for a "what changed and
# > why does it matter for sourcing?" conversation with Copilot.


# MARKDOWN ********************

# ## 7. Write the Delta tables to the lakehouse

# CELL ********************

tables = {
    "DimDate":             dim_date,
    "DimVendor":           dim_vendor,
    "VendorPerformance":   vendor_performance,
    "DimLocation":         dim_location,
    "DimInspectionResult": dim_inspection,
    "DimAuditResult":      dim_audit,
    "DimFinancialRating":  dim_financial,
}

print("Writing tables to lakehouse...")
for name, df in tables.items():
    write_delta(df, name)
print("Done.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 8. Generate the Direct Lake semantic model
# 
# `generate_direct_lake_semantic_model` creates a Direct Lake model over the lakehouse Delta tables.
# 
# > Its signature differs across `semantic-link-labs` versions — older builds use `lakehouse_tables` /
# > `lakehouse`, newer builds use `tables` / `source` / `source_type`. The cell inspects the installed
# > function and passes the matching arguments, so it works regardless of which version Fabric resolves.
# 
# > The model is created with `refresh=False`, then refreshed in a **retry loop with backoff**. A brand-new
# > lakehouse needs a short while for its just-written Delta tables to become discoverable to Direct Lake, so
# > retrying the refresh avoids the timing error *"source tables either do not exist or access was denied"*.


# CELL ********************

import time
import inspect
import sempy_labs as labs
from sempy_labs.directlake import generate_direct_lake_semantic_model

model_tables = [
    "DimDate",
    "DimVendor",
    "VendorPerformance",
    "DimLocation",
    "DimInspectionResult",
    "DimAuditResult",
    "DimFinancialRating",
]

# Remove any existing model with the same name so re-runs are clean.
# (this build of sempy-labs has no `overwrite` kwarg, so we delete first.)
try:
    _existing = labs.list_semantic_models(workspace=workspace_id)
    if semantic_model_name in set(_existing["Dataset Name"]):
        labs.delete_semantic_model(dataset=semantic_model_name, workspace=workspace_id)
        print(f"Removed existing semantic model '{semantic_model_name}'.")
except Exception as e:
    print(f"  (could not check/delete existing model: {e})")

# The generate_direct_lake_semantic_model signature changed across sempy-labs
# versions. fabric-data-agent-sdk pins an older sempy-labs (~0.14.x) that uses
# `lakehouse_tables` + `lakehouse` + `lakehouse_workspace`; newer builds use
# `tables` + `source` + `source_type` + `source_workspace`. Build kwargs to
# match whichever version is installed.
_params = set(inspect.signature(generate_direct_lake_semantic_model).parameters)
gen_kwargs = {"dataset": semantic_model_name, "refresh": False, "workspace": workspace_id}

if "lakehouse_tables" in _params:                 # older lakehouse-only API
    gen_kwargs["lakehouse_tables"] = model_tables
    gen_kwargs["lakehouse"] = lakehouse_name
    if "lakehouse_workspace" in _params:
        gen_kwargs["lakehouse_workspace"] = workspace_id
else:                                             # newer source-based API
    gen_kwargs["tables"] = model_tables
    gen_kwargs["source"] = lakehouse_name
    gen_kwargs["source_type"] = "Lakehouse"
    if "source_workspace" in _params:
        gen_kwargs["source_workspace"] = workspace_id
    if "use_sql_endpoint" in _params:
        # Direct Lake over OneLake avoids waiting on SQL endpoint sync.
        gen_kwargs["use_sql_endpoint"] = False

# Create the model WITHOUT refreshing. A brand-new lakehouse needs a moment for
# its Delta tables to become discoverable to Direct Lake, so we refresh in a
# separate retry loop below to avoid the timing error:
#   "source tables either do not exist or access was denied".
generate_direct_lake_semantic_model(**gen_kwargs)
print(f"Semantic model '{semantic_model_name}' created. Waiting for tables to become available...")

# Refresh (Direct Lake framing) with exponential-ish backoff so newly written
# tables have time to propagate before the first successful refresh.
max_attempts = 6
for attempt in range(1, max_attempts + 1):
    try:
        labs.refresh_semantic_model(dataset=semantic_model_name, workspace=workspace_id)
        print(f"Refreshed semantic model '{semantic_model_name}' on attempt {attempt}.")
        break
    except Exception as e:
        print(f"  refresh attempt {attempt}/{max_attempts} failed: {e}")
        if attempt == max_attempts:
            raise
        wait = 20 * attempt
        print(f"  waiting {wait}s for source tables to become available...")
        time.sleep(wait)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 9. Relationships, measures & AI readiness
# 
# This is the **prep-for-AI** step. Using the TOM wrapper we:
# - wire the **star-schema relationships** (including `VendorPerformance` → `DimDate` and the renamed `DimVendor`),
# - add business **measures** (headline KPIs plus **`Latest …`** and **`… Δ 4 Weeks`** trend measures that drive the recent-change story),
# - set **table / column / measure descriptions** so Copilot understands the model,
# - add **Q&A synonyms** (e.g. *suppliers*, *CMOs*) so natural-language questions resolve,
# - **mark `DimDate` as the date table** for time intelligence, and
# - tidy the model (hide key columns, set summarization, sort dimensions by rank).


# CELL ********************

from sempy_labs.tom import connect_semantic_model

# Descriptions used to ground Copilot / Data Agents
model_description = (
    "Contract manufacturer (CMO) vendor analytics for Allerveo. VendorPerformance is the fact table "
    "at daily grain (one row per vendor per weekly snapshot day over the last two years) describing "
    "quality, regulatory, capacity and commercial KPIs; DimVendor is the vendor dimension and DimDate "
    "is the calendar. Use these to compare, rank and shortlist contract manufacturers and to analyse "
    "how each vendor's performance is trending over time."
)

table_desc = {
    "DimDate":             "Date dimension at daily grain covering the last two years. Use for trends, time intelligence and recent-change analysis.",
    "DimVendor":           "Vendor dimension: one row per contract manufacturer with location, experience, capacity, MOQ and financial rating.",
    "VendorPerformance":   "Fact table at daily grain: one row per vendor per weekly snapshot day with quality, regulatory, capacity and commercial KPIs. Joins to DimVendor on VendorID and to DimDate on DateKey.",
    "DimLocation":         "Location dimension: state/region and country for each vendor site.",
    "DimInspectionResult": "Regulatory inspection outcome reference (NAI/VAI/OAI) with severity ranking; OAI is disqualifying.",
    "DimAuditResult":      "Internal audit outcome reference (Outstanding / Satisfactory / Requires Improvement).",
    "DimFinancialRating":  "Financial stability rating reference (A+ down to B-) with rank and investment-grade flag.",
}

col_desc = {
    ("DimDate", "Date"):                              "Calendar date of the record.",
    ("DimDate", "MonthYear"):                         "Month and year label (e.g. 'Jan 2025') for trend axes.",
    ("DimVendor", "VendorID"):                        "Surrogate vendor key. Joins to VendorPerformance.",
    ("DimVendor", "VendorName"):                      "Contract manufacturer (CMO) name.",
    ("DimVendor", "Location"):                        "Vendor site location as reported.",
    ("DimVendor", "OSDExperienceYrs"):                "Years of oral solid dose (OSD) manufacturing experience.",
    ("DimVendor", "AvailableCapacityKPerMonth"):      "Available manufacturing capacity in thousands of units per month.",
    ("DimVendor", "MOQKUnits"):                       "Minimum order quantity in thousands of units.",
    ("DimVendor", "RegulatoryInspections3yr"):        "Number of regulatory inspections in the last 3 years.",
    ("DimVendor", "FinancialStabilityRating"):        "Financial stability rating (A+ to B-).",
    ("VendorPerformance", "VendorID"):                "Vendor key. Joins to the DimVendor dimension.",
    ("VendorPerformance", "DateKey"):                 "Date key (yyyymmdd). Joins to the DimDate dimension.",
    ("VendorPerformance", "OTIF12moPct"):             "On-time-in-full delivery rate, trailing 12 months.",
    ("VendorPerformance", "BatchRejectionRatePct"):   "Share of batches rejected for quality reasons.",
    ("VendorPerformance", "RightFirstTimePct"):       "Share of batches produced right the first time.",
    ("VendorPerformance", "CustomerComplaintsPer1k"): "Customer complaints per 1,000 batches.",
    ("VendorPerformance", "OpenRegulatoryActions"):   "Count of open regulatory actions; 0 is required to qualify.",
    ("VendorPerformance", "CurrentUtilizationPct"):   "Current plant utilization; high utilization limits new capacity.",
    ("VendorPerformance", "LeadTimeToFirstProductionWks"): "Lead time to first production, in weeks.",
    ("VendorPerformance", "CostIndex"):               "Cost index where the market average = 100; lower is cheaper.",
    ("VendorPerformance", "TechTransferSuccessPct"):  "Historical technology-transfer success rate.",
}

# Measures: (table, name, DAX, format, description, display_folder)
measures = [
    # --- Headline KPIs -------------------------------------------------------
    ("DimVendor",         "Vendor Count",                    "DISTINCTCOUNT(DimVendor[VendorID])", "#,0", "Number of vendors.", "KPIs"),
    ("DimVendor",         "Total Available Capacity (K/mo)", "SUM(DimVendor[AvailableCapacityKPerMonth])", "#,0", "Total available capacity (thousand units/month).", "KPIs"),
    ("VendorPerformance", "Avg OTIF %",                      "AVERAGE(VendorPerformance[OTIF12moPct])", "0.0%", "Average on-time-in-full delivery rate over the period.", "KPIs"),
    ("VendorPerformance", "Avg Batch Rejection %",           "AVERAGE(VendorPerformance[BatchRejectionRatePct])", "0.0%", "Average batch rejection rate over the period.", "KPIs"),
    ("VendorPerformance", "Avg Right First Time %",          "AVERAGE(VendorPerformance[RightFirstTimePct])", "0.0%", "Average right-first-time rate over the period.", "KPIs"),
    ("VendorPerformance", "Avg Complaints /1k",              "AVERAGE(VendorPerformance[CustomerComplaintsPer1k])", "0.0", "Average customer complaints per 1,000 batches.", "KPIs"),
    ("VendorPerformance", "Avg Utilization %",               "AVERAGE(VendorPerformance[CurrentUtilizationPct])", "0.0%", "Average current plant utilization over the period.", "KPIs"),
    ("VendorPerformance", "Avg Lead Time (wks)",             "AVERAGE(VendorPerformance[LeadTimeToFirstProductionWks])", "0.0", "Average lead time to first production (weeks).", "KPIs"),
    ("VendorPerformance", "Avg Cost Index",                  "AVERAGE(VendorPerformance[CostIndex])", "0.0", "Average cost index (market = 100).", "KPIs"),
    ("VendorPerformance", "Avg Tech Transfer %",             "AVERAGE(VendorPerformance[TechTransferSuccessPct])", "0.0%", "Average technology-transfer success rate.", "KPIs"),
    ("VendorPerformance", "Total Open Reg Actions",          "SUM(VendorPerformance[OpenRegulatoryActions])", "#,0", "Total open regulatory actions in context.", "KPIs"),

    # --- Latest value (at the most recent date in context) -------------------
    ("VendorPerformance", "Latest OTIF %",             "LASTNONBLANKVALUE(DimDate[Date], AVERAGE(VendorPerformance[OTIF12moPct]))", "0.0%", "On-time-in-full at the most recent date in context.", "Trend"),
    ("VendorPerformance", "Latest Batch Rejection %",  "LASTNONBLANKVALUE(DimDate[Date], AVERAGE(VendorPerformance[BatchRejectionRatePct]))", "0.0%", "Batch rejection rate at the most recent date in context.", "Trend"),
    ("VendorPerformance", "Latest Right First Time %", "LASTNONBLANKVALUE(DimDate[Date], AVERAGE(VendorPerformance[RightFirstTimePct]))", "0.0%", "Right-first-time at the most recent date in context.", "Trend"),
    ("VendorPerformance", "Latest Utilization %",      "LASTNONBLANKVALUE(DimDate[Date], AVERAGE(VendorPerformance[CurrentUtilizationPct]))", "0.0%", "Plant utilization at the most recent date in context.", "Trend"),
    ("VendorPerformance", "Latest Complaints /1k",     "LASTNONBLANKVALUE(DimDate[Date], AVERAGE(VendorPerformance[CustomerComplaintsPer1k]))", "0.0", "Complaints per 1,000 batches at the most recent date in context.", "Trend"),

    # --- Change vs 4 weeks ago (the recent-change story) ---------------------
    ("VendorPerformance", "OTIF % \u0394 4 Weeks",
        "VAR lastDt = MAXX(VendorPerformance, RELATED(DimDate[Date])) "
        "VAR prevDt = lastDt - 28 "
        "VAR cur = CALCULATE(AVERAGE(VendorPerformance[OTIF12moPct]), FILTER(ALL(DimDate), DimDate[Date] = lastDt)) "
        "VAR prev = CALCULATE(AVERAGE(VendorPerformance[OTIF12moPct]), FILTER(ALL(DimDate), DimDate[Date] = prevDt)) "
        "RETURN cur - prev",
        "+0.0%;-0.0%;0.0%", "Change in OTIF % versus 4 weeks (28 days) earlier. Positive = improving.", "Trend"),
    ("VendorPerformance", "Batch Rejection % \u0394 4 Weeks",
        "VAR lastDt = MAXX(VendorPerformance, RELATED(DimDate[Date])) "
        "VAR prevDt = lastDt - 28 "
        "VAR cur = CALCULATE(AVERAGE(VendorPerformance[BatchRejectionRatePct]), FILTER(ALL(DimDate), DimDate[Date] = lastDt)) "
        "VAR prev = CALCULATE(AVERAGE(VendorPerformance[BatchRejectionRatePct]), FILTER(ALL(DimDate), DimDate[Date] = prevDt)) "
        "RETURN cur - prev",
        "+0.0%;-0.0%;0.0%", "Change in batch rejection % versus 4 weeks (28 days) earlier. Negative = improving.", "Trend"),
]

# Q&A synonyms: object -> [synonyms]
synonyms = {
    ("table", "DimVendor", None):                ["suppliers", "manufacturers", "CMOs", "contract manufacturers", "vendors"],
    ("table", "VendorPerformance", None):        ["performance", "scorecard", "metrics", "KPIs"],
    ("table", "DimDate", None):                  ["calendar", "dates", "time"],
    ("measure", None, "Avg OTIF %"):             ["on time in full", "delivery reliability"],
    ("measure", None, "Avg Batch Rejection %"):  ["reject rate", "quality failures"],
    ("measure", None, "OTIF % \u0394 4 Weeks"):  ["otif trend", "otif change", "delivery improvement"],
    ("measure", None, "Total Available Capacity (K/mo)"): ["spare capacity", "available capacity"],
}

with connect_semantic_model(dataset=semantic_model_name, readonly=False, workspace=workspace_id) as tom:

    # 1) Star-schema relationships ------------------------------------------------
    rels = [
        ("VendorPerformance", "VendorID",                "DimVendor",           "VendorID"),
        ("VendorPerformance", "DateKey",                 "DimDate",             "DateKey"),
        ("DimVendor",         "LocationID",              "DimLocation",         "LocationID"),
        ("DimVendor",         "FinancialStabilityRating","DimFinancialRating",  "Rating"),
        ("VendorPerformance", "LastRegulatoryInspection","DimInspectionResult", "ResultCode"),
        ("VendorPerformance", "LastInternalAuditResult", "DimAuditResult",      "AuditResult"),
    ]
    for ft, fc, tt, tc in rels:
        try:
            tom.add_relationship(
                from_table=ft, from_column=fc, to_table=tt, to_column=tc,
                from_cardinality="Many", to_cardinality="One",
                cross_filtering_behavior="OneDirection",
            )
            print(f"relationship: {ft}[{fc}] -> {tt}[{tc}]")
        except Exception as e:
            print(f"  skip relationship {ft}[{fc}] -> {tt}[{tc}]: {e}")

    # 2) Measures -----------------------------------------------------------------
    for t, name, dax, fmt, desc, folder in measures:
        try:
            tom.add_measure(table_name=t, measure_name=name, expression=dax,
                            format_string=fmt, description=desc, display_folder=folder)
            print(f"measure: {name}")
        except Exception as e:
            print(f"  skip measure {name}: {e}")

    # 3) Model + table + column descriptions (AI grounding) -----------------------
    tom.model.Description = model_description
    for t, d in table_desc.items():
        try:
            tom.model.Tables[t].Description = d
        except Exception as e:
            print(f"  skip table desc {t}: {e}")
    for (t, c), d in col_desc.items():
        try:
            tom.update_column(table_name=t, column_name=c, description=d)
        except Exception as e:
            print(f"  skip col desc {t}.{c}: {e}")

    # 4) Q&A synonyms -------------------------------------------------------------
    for (kind, tname, oname), words in synonyms.items():
        try:
            if kind == "table":
                obj = tom.model.Tables[tname]
            else:
                obj = [m for m in tom.all_measures() if m.Name == oname][0]
            for w in words:
                tom.set_synonym(culture="en-US", object=obj, synonym_name=w)
            print(f"synonyms: {tname or oname} -> {words}")
        except Exception as e:
            print(f"  skip synonyms for {tname or oname}: {e}")

    # 5) Date table + sort-by + summarization + hide keys -------------------------
    try:
        tom.set_sort_by_column("DimDate", "MonthName", "MonthNumber")
        tom.set_sort_by_column("DimDate", "MonthYear", "MonthKey")
        tom.set_sort_by_column("DimDate", "DayName", "DayOfWeekNumber")
        tom.set_sort_by_column("DimInspectionResult", "ResultName", "SeverityRank")
        tom.set_sort_by_column("DimAuditResult", "AuditResult", "ResultRank")
        tom.set_sort_by_column("DimFinancialRating", "Rating", "RatingRank")
    except Exception as e:
        print(f"  skip sort-by: {e}")

    # Keys / numeric date attributes should not be summed
    no_sum = [
        ("DimVendor", "VendorID"), ("DimVendor", "LocationID"),
        ("DimLocation", "LocationID"), ("VendorPerformance", "VendorID"),
        ("VendorPerformance", "DateKey"), ("DimDate", "DateKey"),
        ("DimDate", "Year"), ("DimDate", "Quarter"), ("DimDate", "MonthNumber"),
        ("DimDate", "MonthKey"), ("DimDate", "WeekOfYear"), ("DimDate", "DayOfWeekNumber"),
    ]
    for t, c in no_sum:
        try:
            tom.set_summarize_by(table_name=t, column_name=c, value="None")
        except Exception as e:
            print(f"  skip summarize_by {t}.{c}: {e}")

    # Hide surrogate key clutter from the field list
    for t, c in [("VendorPerformance", "VendorID"), ("VendorPerformance", "DateKey"),
                 ("DimVendor", "LocationID"), ("DimDate", "DateKey"), ("DimDate", "MonthKey")]:
        try:
            tom.update_column(table_name=t, column_name=c, hidden=True)
        except Exception as e:
            print(f"  skip hide {t}.{c}: {e}")

    # Mark primary keys FIRST (this flags relationship "one"-side columns, incl.
    # DimDate[DateKey]), then mark the date table. A table may have only ONE key
    # column, so we clear IsKey on every DimDate column except the date column.
    try:
        tom.mark_primary_keys()
    except Exception as e:
        print(f"  skip mark_primary_keys: {e}")

    try:
        tom.mark_as_date_table(table_name="DimDate", column_name="Date")
        print("marked DimDate as the date table")
    except Exception as e:
        print(f"  skip mark_as_date_table: {e}")

    # Ensure DimDate has a single key column (the date column 'Date').
    # Skip the auto-generated RowNumber system column, which cannot be modified.
    try:
        for col in tom.model.Tables["DimDate"].Columns:
            if str(col.Type) == "RowNumber" or col.Name.startswith("RowNumber"):
                continue
            if col.Name != "Date" and col.IsKey:
                col.IsKey = False
                print(f"  cleared duplicate key DimDate[{col.Name}]")
    except Exception as e:
        print(f"  skip DimDate key cleanup: {e}")

print("Semantic model prepped for AI.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 10. Validate
# 
# A quick check that the model is in Direct Lake mode and that relationships and measures landed.

# CELL ********************

import sempy.fabric as fabric

print("Relationships:")
display(fabric.list_relationships(dataset=semantic_model_name, workspace=workspace_id))

print("Measures:")
display(fabric.list_measures(dataset=semantic_model_name, workspace=workspace_id))

print("\nDone. Open the semantic model in Fabric and start asking Copilot questions, e.g.:")
print("  - 'Which vendors improved OTIF % the most in the last month?'")
print("  - 'Show the OTIF % trend by vendor over the last 2 years.'")
print("  - 'Which vendors are declining on batch rejection rate recently?'")
print("  - 'Rank CMOs by latest OTIF %, excluding any with open regulatory actions.'")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 11. Create a Vendor Data Agent
# 
# Create a **Fabric Data Agent** connected to the `EnterpriseVendorModel` semantic model so
# business users can ask natural-language questions (NL2DAX) about the vendors. The agent
# inherits the **Prep for AI** grounding (descriptions, synonyms, measures) configured above.  Note: Data Agents require Fabric capacity to be running (not trial capacity)

# CELL ********************

from fabric.dataagent.client import create_data_agent, delete_data_agent

data_agent_name = "VendorDataAgent"

# Agent-level AI instructions to steer routing, qualification logic and tone
agent_instructions = (
    "You are a sourcing and supply-chain analyst assistant for contract manufacturer (CMO) "
    "selection. Answer questions about vendors using the semantic model. VendorPerformance is the "
    "fact table at daily grain (one row per vendor per weekly snapshot day over the last two years) "
    "with quality, regulatory, capacity and commercial KPIs; DimVendor is the vendor dimension and "
    "DimDate is the calendar. Use the 'Latest ...' measures for current values and the '... Delta 4 "
    "Weeks' measures to describe recent trends (who is improving or declining). When ranking or "
    "shortlisting vendors, exclude any vendor with open regulatory actions or a disqualifying (OAI) "
    "inspection result. Prefer lower CostIndex, higher OTIF %, higher RightFirstTime %, and lower "
    "BatchRejection %. Always state the vendor name and the metrics behind your recommendation."
)

# Re-create cleanly so this cell is idempotent on re-runs
try:
    delete_data_agent(data_agent_name)
    print(f"Removed existing data agent '{data_agent_name}'.")
except Exception as e:
    print(f"  (no existing data agent to remove: {e})")

# Create the agent and wire it to the semantic model
data_agent = create_data_agent(data_agent_name)
data_agent.update_configuration(instructions=agent_instructions)

# Datasource type for a Power BI semantic model is 'semanticmodel'
data_agent.add_datasource(semantic_model_name, type="semanticmodel")

# Publish so the agent is available to consumers (Copilot, Foundry, REST)
data_agent.publish()

print(f"Data agent '{data_agent_name}' created, connected to '{semantic_model_name}', and published.")
print("Datasources:", data_agent.get_datasources())
print("\nTry asking the agent:")
print("  - 'Which vendors improved the most in the last month and why?'")
print("  - 'Rank CMOs by latest OTIF %, excluding any with open regulatory actions.'")
print("  - 'Which vendors are trending down on quality recently?'")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 12. Create the Power BI report
# 
# Finish the deployment by publishing the **Vendor Performance** report directly on the `VendorSM`
# semantic model deployed in step 9. The full report definition (the page, every visual, the layout,
# filtering, and the Copilot theme) is **embedded in this notebook** and rebound to `VendorSM` at run
# time, so the notebook **stands on its own** — it needs no other workspace or pre-existing report.
# 
# The report opens on a **Vendor Performance Comparison** page with:
# 
# - **Slicers** — filter by vendor and by year.
# - **KPI cards** — latest OTIF % and latest batch rejection %.
# - **Trend lines** — OTIF % and batch-rejection rate by vendor over the last 2 years.
# - **Comparison bars** — each vendor's **OTIF % Δ vs 4 weeks ago**, average lead time, and right-first-time.
# 
# The step is idempotent — re-running updates the existing report in place instead of duplicating it.


# CELL ********************

# ---------------------------------------------------------------------------
# Deploy the "Vendor Performance" report — an EXACT reproduction of the
# original report — entirely from inside this notebook.
#
# The complete Power BI report definition (the page, all 12 visuals, layout,
# filtering, and the Copilot theme) is embedded below as a gzip + base64
# string. It is decoded in memory only — no external storage, OneLake, or any
# other connection is required.
# At run time we decode it, rebind it to the VendorSM semantic model deployed
# in step 9, and publish it with the Fabric REST API. Nothing outside this
# notebook is required, so the deployment "stands on its own".
#
# Re-running is idempotent: an existing "Vendor Performance" report is updated
# in place instead of being duplicated.
# ---------------------------------------------------------------------------
import base64, gzip, json, time
from urllib.parse import urlparse

import sempy.fabric as fabric

report_name = "Vendor Performance"

# --- Embedded original PBIR definition (parts keyed by item-relative path) ----
_REPORT_DEFINITION_B64 = "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"

pbir_parts = json.loads(gzip.decompress(base64.b64decode(_REPORT_DEFINITION_B64)).decode("utf-8"))

# --- Rebind the report to THIS workspace's VendorSM semantic model -------------
workspace_name = fabric.resolve_workspace_name(workspace_id)
dataset_id = fabric.resolve_item_id(
    item_name=semantic_model_name, type="SemanticModel", workspace=workspace_id
)

connection_string = (
    f'Data Source="powerbi://api.powerbi.com/v1.0/myorg/{workspace_name}";'
    f"initial catalog={semantic_model_name};integrated security=ClaimsToken;"
    f"semanticmodelid={dataset_id}"
)
pbir_parts["definition.pbir"] = json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0",
    "datasetReference": {"byConnection": {"connectionString": connection_string}},
}, indent=2)

# --- Assemble the Fabric item definition (InlineBase64 parts) ------------------
definition = {"parts": [
    {
        "path": path,
        "payload": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "payloadType": "InlineBase64",
    }
    for path, text in pbir_parts.items()
]}

client = fabric.FabricRestClient()

def _wait(resp):
    """Block until a Fabric long-running operation finishes."""
    if resp.status_code in (200, 201):
        return resp
    if resp.status_code != 202:
        raise RuntimeError(f"{resp.status_code}: {resp.text}")
    loc = resp.headers.get("Location")
    retry = int(resp.headers.get("Retry-After", "2") or "2")
    while loc:
        time.sleep(retry)
        u = urlparse(loc)
        path = (u.path + ("?" + u.query if u.query else "")) if u.scheme else loc
        s = client.get(path)
        if s.status_code not in (200, 201):
            raise RuntimeError(f"polling {s.status_code}: {s.text}")
        state = ""
        try:
            state = (s.json() or {}).get("status", "")
        except Exception:
            pass
        if state.lower() in ("succeeded", "completed", ""):
            return s
        if state.lower() == "failed":
            raise RuntimeError(f"operation failed: {s.text}")
        retry = int(s.headers.get("Retry-After", str(retry)) or retry)
    return resp

# --- Create or update the report (idempotent) ----------------------------------
_reports = fabric.list_reports(workspace=workspace_id)
_exists = (not _reports.empty) and (_reports["Name"] == report_name).any()
report_id = (
    fabric.resolve_item_id(item_name=report_name, type="Report", workspace=workspace_id)
    if _exists else None
)

if report_id:
    print(f"Updating existing report '{report_name}' ...")
    _wait(client.post(
        f"/v1/workspaces/{workspace_id}/reports/{report_id}/updateDefinition?updateMetadata=True",
        json={"definition": definition},
    ))
    print(f"Report '{report_name}' updated in place.")
else:
    print(f"Creating report '{report_name}' ...")
    _wait(client.post(
        f"/v1/workspaces/{workspace_id}/reports",
        json={"displayName": report_name, "definition": definition},
    ))
    print(f"Report '{report_name}' created on '{semantic_model_name}'.")

print(f"\nOpen '{report_name}' in workspace '{workspace_name}' to explore the vendor performance comparison.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
