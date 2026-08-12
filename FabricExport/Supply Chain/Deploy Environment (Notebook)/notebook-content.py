# Fabric notebook source


# MARKDOWN ********************

# # Deploy Vendor Lakehouse & AI-Ready Semantic Model
# 
# This notebook is designed to run inside a **Microsoft Fabric** notebook (PySpark).
# 
# It will:
# 1. Deploy a new **Lakehouse** (name controlled by the parameter cell — default `EnterpriseLakehouse`).
# 2. Create the two requested tables — **Vendors** and **VendorPerformance** — joinable on `VendorID`.
# 3. Create supporting **dimension tables** for a vendor star schema (`DimLocation`, `DimInspectionResult`, `DimAuditResult`, `DimFinancialRating`).
# 4. Build a **Direct Lake semantic model** over the lakehouse.
# 5. **Prep the model for AI / Copilot** (relationships, measures, descriptions, and Q&A synonyms).
# 
# > Source data is sourced from the *Allerveo CMO Vendor Comparison* workbook
# > (`Vendor Overview`, `Quality & Regulatory`, and `Capacity & Commercial` tabs) and embedded below so the notebook is self-contained.
# 
# **Star schema**
# 
# ```
#         DimLocation
#             |
#         Vendors (vendor dimension)
#             |
#    VendorPerformance (fact)  ──┬── DimInspectionResult
#                                ├── DimAuditResult
#                                └── DimFinancialRating
# ```


# MARKDOWN ********************

# ## 1. Parameters
# 
# This cell is tagged **`parameters`** so the values can be overridden when the notebook is run from a pipeline or `notebookutils.run`.

# PARAMETERS CELL ********************

# --- Parameters (overridable) ---
lakehouse_name       = "EnterpriseLakehouse"   # Lakehouse to create / reuse
semantic_model_name  = "EnterpriseVendorModel" # Direct Lake semantic model name
overwrite_tables     = True                     # Overwrite Delta tables if they already exist

# MARKDOWN ********************

# ## 2. Install libraries
# 
# `semantic-link-labs` (`sempy_labs`) is used to generate the Direct Lake semantic model and prep it for AI.
# It is pre-installed on most Fabric runtimes; the install below guarantees a recent version.

# CELL ********************

%pip install -q semantic-link-labs

# MARKDOWN ********************

# ## 3. Imports & workspace context

# CELL ********************

import notebookutils
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
)

# Resolve the current workspace from the notebook runtime context
ctx = notebookutils.runtime.context
workspace_id = ctx.get("currentWorkspaceId") or ctx.get("workspaceId")
print(f"Workspace id : {workspace_id}")
print(f"Lakehouse    : {lakehouse_name}")
print(f"Model        : {semantic_model_name}")

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

# MARKDOWN ********************

# ## 5. Source data
# 
# The rows below are transcribed directly from the workbook tabs. A surrogate **`VendorID`** (`V001`..`V007`)
# is assigned consistently so every table joins cleanly.

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

# MARKDOWN ********************

# ## 6. Build the dimension & fact DataFrames
# 
# We derive a `LocationID` for the location dimension, then assemble each table with an explicit schema
# so the Delta / Direct Lake column types are correct.

# CELL ********************

# --- DimLocation -------------------------------------------------------------
# Parse "State/City, Country" into structured attributes.
def parse_location(loc):
    parts = [p.strip() for p in loc.split(",")]
    region = parts[0]
    country = parts[1] if len(parts) > 1 else parts[0]
    return region, country

distinct_locations = []
seen = {}
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

# --- Vendors (from "Vendor Overview") ----------------------------------------
vendors_rows = []
for (vendor, loc, cap, lead, otif, batch, insp, cost) in vendor_overview:
    vendors_rows.append((
        vendor_ids[vendor], vendor, seen[loc], loc, cap, lead, otif, batch, insp, cost,
    ))

vendors_schema = StructType([
    StructField("VendorID",                    StringType(),  False),
    StructField("VendorName",                  StringType(),  True),
    StructField("LocationID",                  StringType(),  True),
    StructField("Location",                    StringType(),  True),
    StructField("AvailableCapacityKPerMonth",  IntegerType(), True),
    StructField("LeadTimeToFirstProductionWks",IntegerType(), True),
    StructField("OTIF12moPct",                 DoubleType(),  True),
    StructField("BatchRejectionRatePct",       DoubleType(),  True),
    StructField("LastRegulatoryInspection",    StringType(),  True),
    StructField("CostIndex",                   IntegerType(), True),
])
vendors = spark.createDataFrame(vendors_rows, schema=vendors_schema)

# --- VendorPerformance (Quality & Regulatory + Capacity & Commercial) --------
cap_by_vendor = {row[0]: row for row in capacity_commercial}
perf_rows = []
for (vendor, otif, batch, rft, complaints, insp, open_act, insp_3yr, audit) in quality_regulatory:
    c = cap_by_vendor[vendor]
    perf_rows.append((
        vendor_ids[vendor],          # VendorID
        otif, batch, rft, complaints, insp, open_act, insp_3yr, audit,
        c[1],                        # OSDExperienceYrs
        c[2],                        # AvailableCapacityKPerMonth
        c[3],                        # CurrentUtilizationPct
        c[4],                        # LeadTimeToFirstProductionWks
        c[5],                        # CostIndex
        c[6],                        # MOQKUnits
        c[7],                        # TechTransferSuccessPct
        c[8],                        # FinancialStabilityRating
    ))

perf_schema = StructType([
    StructField("VendorID",                     StringType(),  False),
    StructField("OTIF12moPct",                  DoubleType(),  True),
    StructField("BatchRejectionRatePct",        DoubleType(),  True),
    StructField("RightFirstTimePct",            DoubleType(),  True),
    StructField("CustomerComplaintsPer1k",      DoubleType(),  True),
    StructField("LastRegulatoryInspection",     StringType(),  True),
    StructField("OpenRegulatoryActions",        IntegerType(), True),
    StructField("RegulatoryInspections3yr",     IntegerType(), True),
    StructField("LastInternalAuditResult",      StringType(),  True),
    StructField("OSDExperienceYrs",             IntegerType(), True),
    StructField("AvailableCapacityKPerMonth",   IntegerType(), True),
    StructField("CurrentUtilizationPct",        DoubleType(),  True),
    StructField("LeadTimeToFirstProductionWks", IntegerType(), True),
    StructField("CostIndex",                    IntegerType(), True),
    StructField("MOQKUnits",                    IntegerType(), True),
    StructField("TechTransferSuccessPct",       DoubleType(),  True),
    StructField("FinancialStabilityRating",     StringType(),  True),
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
# store boolean as string-friendly flag for clean modeling
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
    ("A+", 1, "Yes"),
    ("A",  2, "Yes"),
    ("A-", 3, "Yes"),
    ("B+", 4, "Yes"),
    ("B",  5, "No"),
    ("B-", 6, "No"),
]
rating_schema = StructType([
    StructField("Rating",          StringType(),  False),
    StructField("RatingRank",      IntegerType(), True),
    StructField("InvestmentGrade", StringType(),  True),
])
dim_financial = spark.createDataFrame(rating_rows, schema=rating_schema)

display(vendors)
display(vendor_performance)

# MARKDOWN ********************

# ## 7. Write the Delta tables to the lakehouse

# CELL ********************

tables = {
    "Vendors":             vendors,
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

# MARKDOWN ********************

# ## 8. Generate the Direct Lake semantic model
# 
# `generate_direct_lake_semantic_model` creates a Direct Lake model that reads the lakehouse Delta tables
# directly from OneLake (`use_sql_endpoint=False` avoids waiting on SQL endpoint sync for a brand-new lakehouse).

# CELL ********************

import sempy_labs as labs
from sempy_labs.directlake import generate_direct_lake_semantic_model

model_tables = [
    "Vendors",
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

generate_direct_lake_semantic_model(
    dataset=semantic_model_name,
    tables=model_tables,
    source=lakehouse_name,
    source_type="Lakehouse",
    source_workspace=workspace_id,
    workspace=workspace_id,
    use_sql_endpoint=False,
    refresh=True,
)
print(f"Semantic model '{semantic_model_name}' created.")

# MARKDOWN ********************

# ## 9. Relationships, measures & AI readiness
# 
# This is the **prep-for-AI** step. Using the TOM wrapper we:
# - wire the **star-schema relationships**,
# - add business **measures** (with format strings + descriptions),
# - set **table / column / measure descriptions** so Copilot understands the model,
# - add **Q&A synonyms** (e.g. *suppliers*, *CMOs*) so natural-language questions resolve, and
# - tidy the model (hide key columns, set summarization, sort dimensions by rank).

# CELL ********************

from sempy_labs.tom import connect_semantic_model

# Descriptions used to ground Copilot / Data Agents
model_description = (
    "Contract manufacturer (CMO) vendor analytics for Allerveo. VendorPerformance is the fact table "
    "(one row per vendor) describing quality, regulatory, capacity and commercial metrics; Vendors is the "
    "vendor dimension. Use these to compare, rank and shortlist contract manufacturers."
)

table_desc = {
    "Vendors":             "Vendor dimension: one row per contract manufacturer with location and headline overview metrics.",
    "VendorPerformance":   "Fact table: one row per vendor with quality, regulatory, capacity and commercial KPIs. Joins to Vendors on VendorID.",
    "DimLocation":         "Location dimension: state/region and country for each vendor site.",
    "DimInspectionResult": "Regulatory inspection outcome reference (NAI/VAI/OAI) with severity ranking; OAI is disqualifying.",
    "DimAuditResult":      "Internal audit outcome reference (Outstanding / Satisfactory / Requires Improvement).",
    "DimFinancialRating":  "Financial stability rating reference (A+ down to B-) with rank and investment-grade flag.",
}

col_desc = {
    ("Vendors", "VendorID"):                          "Surrogate vendor key. Joins to VendorPerformance.",
    ("Vendors", "VendorName"):                        "Contract manufacturer (CMO) name.",
    ("Vendors", "Location"):                          "Vendor site location as reported.",
    ("Vendors", "AvailableCapacityKPerMonth"):        "Available manufacturing capacity in thousands of units per month.",
    ("Vendors", "LeadTimeToFirstProductionWks"):      "Lead time to first production, in weeks.",
    ("Vendors", "OTIF12moPct"):                       "On-time-in-full delivery rate, trailing 12 months.",
    ("Vendors", "BatchRejectionRatePct"):             "Share of batches rejected for quality reasons.",
    ("Vendors", "CostIndex"):                         "Cost index where the market average = 100; lower is cheaper.",
    ("VendorPerformance", "VendorID"):                "Vendor key. Joins to the Vendors dimension.",
    ("VendorPerformance", "OTIF12moPct"):             "On-time-in-full delivery rate, trailing 12 months.",
    ("VendorPerformance", "BatchRejectionRatePct"):   "Share of batches rejected for quality reasons.",
    ("VendorPerformance", "RightFirstTimePct"):       "Share of batches produced right the first time.",
    ("VendorPerformance", "CustomerComplaintsPer1k"): "Customer complaints per 1,000 batches.",
    ("VendorPerformance", "OpenRegulatoryActions"):   "Count of open regulatory actions; 0 is required to qualify.",
    ("VendorPerformance", "RegulatoryInspections3yr"):"Number of regulatory inspections in the last 3 years.",
    ("VendorPerformance", "OSDExperienceYrs"):        "Years of oral solid dose (OSD) manufacturing experience.",
    ("VendorPerformance", "AvailableCapacityKPerMonth"):"Available capacity in thousands of units per month.",
    ("VendorPerformance", "CurrentUtilizationPct"):   "Current plant utilization; high utilization limits new capacity.",
    ("VendorPerformance", "LeadTimeToFirstProductionWks"):"Lead time to first production, in weeks.",
    ("VendorPerformance", "CostIndex"):               "Cost index where the market average = 100; lower is cheaper.",
    ("VendorPerformance", "MOQKUnits"):               "Minimum order quantity in thousands of units.",
    ("VendorPerformance", "TechTransferSuccessPct"):  "Historical technology-transfer success rate.",
}

# Measures: (table, name, DAX, format, description)
measures = [
    ("VendorPerformance", "Vendor Count",              "DISTINCTCOUNT(VendorPerformance[VendorID])", "#,0",   "Number of vendors."),
    ("VendorPerformance", "Avg OTIF %",                "AVERAGE(VendorPerformance[OTIF12moPct])", "0.0%",      "Average on-time-in-full delivery rate."),
    ("VendorPerformance", "Avg Batch Rejection %",     "AVERAGE(VendorPerformance[BatchRejectionRatePct])", "0.0%", "Average batch rejection rate."),
    ("VendorPerformance", "Avg Right First Time %",    "AVERAGE(VendorPerformance[RightFirstTimePct])", "0.0%",  "Average right-first-time rate."),
    ("VendorPerformance", "Avg Utilization %",         "AVERAGE(VendorPerformance[CurrentUtilizationPct])", "0.0%", "Average current plant utilization."),
    ("VendorPerformance", "Avg Lead Time (wks)",       "AVERAGE(VendorPerformance[LeadTimeToFirstProductionWks])", "0.0", "Average lead time to first production (weeks)."),
    ("VendorPerformance", "Avg Cost Index",            "AVERAGE(VendorPerformance[CostIndex])", "0.0",          "Average cost index (market = 100)."),
    ("VendorPerformance", "Avg Tech Transfer %",       "AVERAGE(VendorPerformance[TechTransferSuccessPct])", "0.0%", "Average technology-transfer success rate."),
    ("VendorPerformance", "Total Available Capacity (K/mo)", "SUM(VendorPerformance[AvailableCapacityKPerMonth])", "#,0", "Total available capacity (thousand units/month)."),
    ("VendorPerformance", "Total Open Reg Actions",    "SUM(VendorPerformance[OpenRegulatoryActions])", "#,0",   "Total open regulatory actions across vendors."),
]

# Q&A synonyms: object -> [synonyms]
synonyms = {
    ("table", "Vendors", None):                 ["suppliers", "manufacturers", "CMOs", "contract manufacturers"],
    ("table", "VendorPerformance", None):        ["performance", "scorecard", "metrics", "KPIs"],
    ("measure", None, "Avg OTIF %"):             ["on time in full", "delivery reliability"],
    ("measure", None, "Avg Batch Rejection %"):  ["reject rate", "quality failures"],
    ("measure", None, "Total Available Capacity (K/mo)"): ["spare capacity", "available capacity"],
}

with connect_semantic_model(dataset=semantic_model_name, readonly=False, workspace=workspace_id) as tom:

    # 1) Star-schema relationships ------------------------------------------------
    rels = [
        ("VendorPerformance", "VendorID",                "Vendors",             "VendorID"),
        ("Vendors",           "LocationID",              "DimLocation",         "LocationID"),
        ("VendorPerformance", "LastRegulatoryInspection","DimInspectionResult", "ResultCode"),
        ("VendorPerformance", "LastInternalAuditResult", "DimAuditResult",      "AuditResult"),
        ("VendorPerformance", "FinancialStabilityRating","DimFinancialRating",  "Rating"),
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
    for t, name, dax, fmt, desc in measures:
        try:
            tom.add_measure(table_name=t, measure_name=name, expression=dax,
                            format_string=fmt, description=desc, display_folder="KPIs")
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

    # 5) Tidy up: sort dimensions by rank, summarization, hide keys ---------------
    try:
        tom.set_sort_by_column("DimInspectionResult", "ResultName", "SeverityRank")
        tom.set_sort_by_column("DimAuditResult", "AuditResult", "ResultRank")
        tom.set_sort_by_column("DimFinancialRating", "Rating", "RatingRank")
    except Exception as e:
        print(f"  skip sort-by: {e}")

    # IDs should not be summed
    for t, c in [("Vendors", "VendorID"), ("Vendors", "LocationID"),
                 ("DimLocation", "LocationID"), ("VendorPerformance", "VendorID")]:
        try:
            tom.set_summarize_by(table_name=t, column_name=c, value="None")
        except Exception as e:
            print(f"  skip summarize_by {t}.{c}: {e}")

    # Hide surrogate key clutter from the field list
    for t, c in [("VendorPerformance", "VendorID"), ("Vendors", "LocationID")]:
        try:
            tom.update_column(table_name=t, column_name=c, hidden=True)
        except Exception as e:
            print(f"  skip hide {t}.{c}: {e}")

    try:
        tom.mark_primary_keys()
    except Exception as e:
        print(f"  skip mark_primary_keys: {e}")

print("Semantic model prepped for AI.")

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
print("  - 'Which vendors have the lowest cost index and no open regulatory actions?'")
print("  - 'Show average OTIF % by country.'")
print("  - 'Rank CMOs by available capacity.'")

# MARKDOWN ********************

# ## 11. Create a Vendor Data Agent
# 
# Create a **Fabric Data Agent** connected to the `EnterpriseVendorModel` semantic model so
# business users can ask natural-language questions (NL2DAX) about the vendors. The agent
# inherits the **Prep for AI** grounding (descriptions, synonyms, measures) configured above.

# CELL ********************

%pip install -q fabric-data-agent-sdk

# CELL ********************

from fabric.dataagent.client import create_data_agent, delete_data_agent

data_agent_name = "VendorDataAgent"

# Agent-level AI instructions to steer routing, qualification logic and tone
agent_instructions = (
    "You are a sourcing and supply-chain analyst assistant for contract manufacturer (CMO) "
    "selection. Answer questions about vendors using the semantic model. VendorPerformance is "
    "the fact table (one row per vendor) with quality, regulatory, capacity and commercial KPIs; "
    "Vendors is the vendor dimension. When ranking or shortlisting vendors, exclude any vendor "
    "with open regulatory actions or a disqualifying (OAI) inspection result. Prefer lower "
    "CostIndex, higher OTIF %, higher RightFirstTime %, and lower BatchRejection %. Always state "
    "the vendor name and the metrics behind your recommendation."
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
print("  - 'Which vendors qualify and have the lowest cost index?'")
print("  - 'Rank CMOs by available capacity, excluding any with open regulatory actions.'")
print("  - 'Compare OTIF % and batch rejection % for vendors in the USA.'")

# MARKDOWN ********************

# ## 12. Create a Power BI report
# 
# Finish the deployment by building a starter **Power BI report** directly on the
# `EnterpriseVendorModel` semantic model: KPI cards, an on-time-in-full ranking, and a vendor
# scorecard table. The report is generated from a `report.json` layout via `semantic-link-labs`
# and is idempotent — re-running updates the existing report instead of duplicating it.

# CELL ********************

import json
import uuid
import sempy.fabric as fabric
import sempy_labs.report as rep

report_name = "Vendor Sourcing Overview"


# --- helpers to build a legacy report.json layout ---------------------------
def _col(alias, entity, prop):
    return {
        "Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
        "Name": f"{entity}.{prop}",
    }


def _measure(alias, prop):
    return {
        "Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
        "Name": f"VendorPerformance.{prop}",
    }


def _visual(vtype, x, y, w, h, frm, selects, projections, title=None):
    single = {
        "visualType": vtype,
        "projections": projections,
        "prototypeQuery": {"Version": 2, "From": frm, "Select": selects},
        "drillFilterOtherVisuals": True,
        "objects": {},
        "vcObjects": {},
    }
    if title:
        single["vcObjects"] = {
            "title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": "'" + title + "'"}}},
            }}]
        }
    cfg = {
        "name": uuid.uuid4().hex,
        "layouts": [{"id": 0, "position": {
            "x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": 0}}],
        "singleVisual": single,
    }
    return {"x": x, "y": y, "z": 0, "width": w, "height": h, "config": json.dumps(cfg)}


vp = [{"Name": "p", "Entity": "VendorPerformance", "Type": 0}]
vp_vendors = [
    {"Name": "v", "Entity": "Vendors", "Type": 0},
    {"Name": "p", "Entity": "VendorPerformance", "Type": 0},
]

containers = []

# KPI cards across the top
cards = [
    ("Vendor Count", "Vendors"),
    ("Avg OTIF %", "Avg OTIF %"),
    ("Avg Cost Index", "Avg Cost Index"),
    ("Total Available Capacity (K/mo)", "Capacity (K/mo)"),
]
for i, (measure, title) in enumerate(cards):
    containers.append(_visual(
        "card", 20 + i * 312, 20, 296, 120, vp,
        [_measure("p", measure)],
        {"Values": [{"queryRef": f"VendorPerformance.{measure}"}]},
        title,
    ))

# Bar chart: vendors ranked by on-time-in-full
containers.append(_visual(
    "clusteredBarChart", 20, 160, 610, 520, vp_vendors,
    [_col("v", "Vendors", "VendorName"), _measure("p", "Avg OTIF %")],
    {
        "Category": [{"queryRef": "Vendors.VendorName"}],
        "Y": [{"queryRef": "VendorPerformance.Avg OTIF %"}],
    },
    "On-time-in-full by vendor",
))

# Vendor scorecard table
table_measures = [
    "Avg OTIF %",
    "Avg Batch Rejection %",
    "Avg Cost Index",
    "Total Available Capacity (K/mo)",
    "Total Open Reg Actions",
]
table_selects = [_col("v", "Vendors", "VendorName")] + [_measure("p", m) for m in table_measures]
table_proj = {
    "Values": [{"queryRef": "Vendors.VendorName"}]
    + [{"queryRef": f"VendorPerformance.{m}"} for m in table_measures]
}
containers.append(_visual(
    "tableEx", 650, 160, 610, 520, vp_vendors,
    table_selects, table_proj, "Vendor scorecard",
))

report_json = {
    "version": "5.43",
    "sections": [{
        "name": "VendorOverview",
        "displayName": "Vendor Sourcing Overview",
        "filters": "[]",
        "width": 1280,
        "height": 720,
        "displayOption": 1,
        "visualContainers": containers,
    }],
    "config": json.dumps({"version": "5.43", "activeSectionIndex": 0}),
    "layoutOptimization": 0,
}

# Idempotent: update the report if it already exists, otherwise create it
_reports = fabric.list_reports(workspace=workspace_id)
_exists = (not _reports.empty) and (_reports["Name"] == report_name).any()

if _exists:
    rep.update_report_from_reportjson(
        report=report_name, report_json=report_json, workspace=workspace_id,
    )
    print(f"Report '{report_name}' updated in the workspace.")
else:
    rep.create_report_from_reportjson(
        report=report_name,
        dataset=semantic_model_name,
        report_json=report_json,
        workspace=workspace_id,
    )
    print(f"Report '{report_name}' created on '{semantic_model_name}'.")

print("Open the report in the Fabric workspace to explore the vendor KPIs.")

