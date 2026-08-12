# Data

This folder contains fictional data used by the session demos.

## Supplier invoices

Invoice facts come from the Waypoint corpus pinned at commit
`045637b6eea72550ce3aad61bfac851356ca824a`. The generator caches its canonical
`supplier-invoices.json` in `invoices/source/`, renders each record through
the matching supplier template in `invoices/templates/`, and writes a browser
preview and searchable PDF to `invoices/html/` and `invoices/pdf/`. The 15
supplier templates use different document structures and domain-specific table
labels while sharing print, formatting, and accessibility primitives.

Generate all 15 supplier invoices from the repository root:

```bash
uv run python scripts/generate_invoice.py --all
```

Generate one invoice by ID:

```bash
uv run python scripts/generate_invoice.py INV-SUP-002-2026-10
```

Refresh the cached source from the pinned commit while generating:

```bash
uv run python scripts/generate_invoice.py --all --refresh-source
```

The generator verifies that line amounts sum to the declared invoice total and
that every canonical line ID belongs to its invoice before creating either output.
Reconciliation outcomes remain in the source data and are not rendered into the
supplier-facing documents.

### Generated invoice PDFs

Each PDF below is a direct visual rendering of the named invoice record in the
cached [pinned Waypoint supplier-invoice file](invoices/source/waypoint-supplier-invoices.json).
The PDF preserves Waypoint's supplier, invoice, purchase-order, line-item,
reference, quantity, rate, and total facts while omitting expected audit outcomes.

| PDF | Waypoint correspondence |
| --- | --- |
| [INV-SUP-001-2026-10.pdf](invoices/pdf/INV-SUP-001-2026-10.pdf) | Direct rendering of the [Aster Ridge Biomanufacturing invoice](invoices/source/waypoint-supplier-invoices.json#L209). |
| [INV-SUP-002-2026-10.pdf](invoices/pdf/INV-SUP-002-2026-10.pdf) | Direct rendering of the [Northstar Fill Finish invoice](invoices/source/waypoint-supplier-invoices.json#L268). |
| [INV-SUP-003-2026-10.pdf](invoices/pdf/INV-SUP-003-2026-10.pdf) | Direct rendering of the [HelioPack Pharma Services invoice](invoices/source/waypoint-supplier-invoices.json#L327). |
| [INV-SUP-004-2026-10.pdf](invoices/pdf/INV-SUP-004-2026-10.pdf) | Direct rendering of the [Meridian API Works invoice](invoices/source/waypoint-supplier-invoices.json#L386). |
| [INV-SUP-005-2026-10.pdf](invoices/pdf/INV-SUP-005-2026-10.pdf) | Direct rendering of the [Crescent GMP Labs invoice](invoices/source/waypoint-supplier-invoices.json#L445). |
| [INV-SUP-006-2026-10.pdf](invoices/pdf/INV-SUP-006-2026-10.pdf) | Direct rendering of the [Summit Dose Manufacturing invoice](invoices/source/waypoint-supplier-invoices.json#L504). |
| [INV-SUP-007-2026-10.pdf](invoices/pdf/INV-SUP-007-2026-10.pdf) | Direct rendering of the [Orchid Clinical Supply invoice](invoices/source/waypoint-supplier-invoices.json#L563). |
| [INV-SUP-008-2026-10.pdf](invoices/pdf/INV-SUP-008-2026-10.pdf) | Direct rendering of the [Valence Cold Chain Logistics invoice](invoices/source/waypoint-supplier-invoices.json#L628). |
| [INV-SUP-009-2026-Q4.pdf](invoices/pdf/INV-SUP-009-2026-Q4.pdf) | Direct rendering of the [BluePeak Biologics invoice](invoices/source/waypoint-supplier-invoices.json#L687). |
| [INV-SUP-010-2026-10.pdf](invoices/pdf/INV-SUP-010-2026-10.pdf) | Direct rendering of the [Keystone Device Assembly invoice](invoices/source/waypoint-supplier-invoices.json#L752). |
| [INV-SUP-011-2026-10.pdf](invoices/pdf/INV-SUP-011-2026-10.pdf) | Direct rendering of the [LumaSterile Services invoice](invoices/source/waypoint-supplier-invoices.json#L811). |
| [INV-SUP-012-2026-10.pdf](invoices/pdf/INV-SUP-012-2026-10.pdf) | Direct rendering of the [Pioneer Process Development invoice](invoices/source/waypoint-supplier-invoices.json#L870). |
| [INV-SUP-013-2026-10.pdf](invoices/pdf/INV-SUP-013-2026-10.pdf) | Direct rendering of the [Evergreen Excipients invoice](invoices/source/waypoint-supplier-invoices.json#L929). |
| [INV-SUP-014-2026-10.pdf](invoices/pdf/INV-SUP-014-2026-10.pdf) | Direct rendering of the [Atlas Regional Manufacturing invoice](invoices/source/waypoint-supplier-invoices.json#L988). |
| [INV-SUP-015-2026-10.pdf](invoices/pdf/INV-SUP-015-2026-10.pdf) | Direct rendering of the [Signal Ridge Regulatory Services invoice](invoices/source/waypoint-supplier-invoices.json#L1047). |

## Temperature excursion reports

The Valence report pair extends the pinned Waypoint records for shipment
`SHIP-VC-1026-BOS-FRA`. Waypoint supplies the invoice, shipment, proof of
delivery, lane authorization, temperature-log, and investigation identifiers.
The measurements, affected inventory, investigation narrative, and disposition
in `temperature-reports/source/valence-excursion.json` are fictional but shared
by both generated documents so their facts remain consistent.

The report structure is informed by public examples:

- [University of Iowa investigational product temperature monitoring procedure](https://www.healthcare.uiowa.edu/marcom/uihc/pharmacy/RES-NP002_INVESTIGATIONAL_PRODUCT_TEMPERATURE_MONITORING_ACTIONS.pdf)
- [New York State COVID-19 temperature excursion report](https://www.mssny.org/wp-content/uploads/2022/08/COVID19-Temperature-Excursion-Report_5-26-21.pdf)
- [EIMPRIS temperature excursion report](https://www.medimergent.com/wp-content/uploads/2022/08/EIMPRIS-Temperature-Excursion-Report-11Aug2022.pdf)
- [Sensitech TempTale 4 USB logger report](https://www.bepack.hu/static/media/dry.55b9103650e2f6a30b13.pdf)

Generate the searchable logger and investigation PDFs from the repository root:

```bash
uv run python scripts/generate_temperature_reports.py
```

The generator validates shared measurements and confirms that every Waypoint
identifier used by the reports exists in the pinned Valence invoice. It writes
HTML previews to `temperature-reports/html/` and PDFs to
`temperature-reports/pdf/`.

### Generated temperature PDFs

Both documents correspond to the [Waypoint Valence invoice](invoices/source/waypoint-supplier-invoices.json#L628),
which names shipment `SHIP-VC-1026-BOS-FRA`, temperature log `TL-VCL-1026`,
investigation `EXC-VC-1026-04`, proof of delivery `VCL-1026-8841`, and lane
authorization `LA-VCL-1026`. Their measurements and conclusions are synthetic
extensions defined in [valence-excursion.json](temperature-reports/source/valence-excursion.json).

| PDF | Waypoint correspondence |
| --- | --- |
| [TL-VCL-1026.pdf](temperature-reports/pdf/TL-VCL-1026.pdf) | Realizes Waypoint's named temperature-log evidence as a fictional machine-generated logger report for the same shipment. |
| [EXC-VC-1026-04.pdf](temperature-reports/pdf/EXC-VC-1026-04.pdf) | Realizes Waypoint's investigation reference as a fictional retrospective assessment linked to the same log, shipment, and invoice. |

## Operational evidence and assessments

The operational report corpus adds three evidence-and-assessment pairs to the
pinned Waypoint supplier records. Waypoint supplies the supplier, invoice, line,
lot, build, run, and supporting-document identifiers. All quantities beyond the
invoice facts, process measurements, defect findings, investigation narratives,
people, actions, and dispositions in
`operational-reports/source/supplier-evidence.json` are fictional. A single
structured source feeds both documents in each pair so figures, tables, and
conclusions remain consistent.

The public documents below informed field selection and information hierarchy;
the generated reports do not reproduce their branding, wording, or case data:

- [FDA Guidance for Industry #234: Question-Based Review for the Chemistry,
  Manufacturing, and Controls Technical Section of Animal Drug Applications](https://www.fda.gov/media/96718/download)
  informed the Meridian comparison of actual and theoretical yield and material
  reconciliation.
- [21 CFR 211.188: Batch production and control records](https://www.govinfo.gov/content/pkg/CFR-2013-title21-vol4/pdf/CFR-2013-title21-vol4-sec211-188.pdf)
  informed the controlled-record identity, batch quantities, yield checks, and
  review traceability in the Meridian worksheet.
- [FDA Nonconformity Grading System for Regulatory Purposes](https://www.fda.gov/media/152034/download)
  and [APHL Model Practices for Nonconforming Events](https://aphl.org/docs/default-source/technical/QSA-2021-PHL-Model-Practices-QMS11-A.pdf)
  informed Keystone's defect classification, impact, cause, disposition, action,
  approval, and closure sequence.
- [Strategic Biopharmaceutical Production Planning for Batch and Continuous
  Manufacturing](https://discovery.ucl.ac.uk/1505719/1/main.pdf) and
  [Reducing the Costs of Biopharmaceutical Separations and Purification](https://www.mmhimages.com/production/BP_Purolite_eBook_2021.pdf)
  informed BluePeak's run-level capacity table and included, excess, and unused
  capacity figure.
- [Deviation Handling and Quality Risk Management](https://dcvmn.org/wp-content/uploads/2016/03/who_guidance_deviation_and_risk_mgt_2013.pdf)
  and [FDA Investigating Out-of-Specification Test Results for Pharmaceutical
  Production](https://www.fda.gov/media/158416/download) informed the BluePeak
  event, containment, evidence, root-cause, impact, CAPA, and final-disposition
  flow.

Generate all six searchable PDFs from the repository root:

```bash
uv run python scripts/generate_operational_reports.py
```

The generator validates the arithmetic within each packet, confirms every
canonical identifier against the pinned invoice corpus, and checks the linked
invoice-line amount. It writes HTML previews to `operational-reports/html/` and
PDFs to `operational-reports/pdf/`. All measurements, findings, and dispositions
beyond the linked Waypoint facts come from
[supplier-evidence.json](operational-reports/source/supplier-evidence.json).

### Generated operational PDFs

| PDF | Waypoint correspondence |
| --- | --- |
| [YLD-MAW-1026.pdf](operational-reports/pdf/YLD-MAW-1026.pdf) | Realizes the yield worksheet named by the [Waypoint Meridian invoice](invoices/source/waypoint-supplier-invoices.json#L386), using its `LOT-MD-1026-A`, `MAW-API-1026`, and related references with synthetic process measurements. |
| [YTA-MAW-1026-04.pdf](operational-reports/pdf/YTA-MAW-1026-04.pdf) | Fictional assessment of Waypoint line `INV-SUP-004-2026-10-L004`; it explains why the canonical `$125,600` forecast-based yield adjustment is rejected. |
| [FIR-KDA-1026.pdf](operational-reports/pdf/FIR-KDA-1026.pdf) | Realizes the final inspection report named by the [Waypoint Keystone invoice](invoices/source/waypoint-supplier-invoices.json#L752), preserving its build, inspection, lot, and ECO references with synthetic defect data. |
| [NCR-KDA-1026-07.pdf](operational-reports/pdf/NCR-KDA-1026-07.pdf) | Fictional nonconformance assessment of Waypoint line `INV-SUP-010-2026-10-L004`; it connects the canonical `$86,450` excess-scrap charge to the generated inspection evidence. |
| [UTL-BPB-1026.pdf](operational-reports/pdf/UTL-BPB-1026.pdf) | Realizes the utilization log named by the [Waypoint BluePeak invoice](invoices/source/waypoint-supplier-invoices.json#L687), preserving the canonical 12,000 included hours, 4,800 excess hours, three runs, and related IDs. |
| [DEV-BPB-1026.pdf](operational-reports/pdf/DEV-BPB-1026.pdf) | Realizes Waypoint's deviation cost packet and supplier-caused contamination reference for line `INV-SUP-009-2026-Q4-L004`, with a fictional investigation supporting rejection of the canonical `$111,000` fee. |
