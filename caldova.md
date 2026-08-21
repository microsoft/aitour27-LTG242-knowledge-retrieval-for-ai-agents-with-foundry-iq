# Caldova narrative and data reference

> **Internal planning reference:** The source document is marked Microsoft Confidential and was prepared for FY27 planning. Do not publish its content, fictional persona images, internal proof points, or source links without confirming that they are approved for public use.

## Source and purpose

This reference summarizes the canonical **FY27 Caldova Pharmaceuticals Company Overview & Demo Storyline** for planning LTG242, *Knowledge retrieval for AI agents with Foundry IQ*.

Caldova is Microsoft's fictional global pharmaceutical company. It succeeds the FY26 Zava retail and smart-fiber storyline. Do not mix the two narratives, even though some older assets may label the tenant `Caldova (Zava-Public)`.

The canonical Caldova story is one continuous business thread rather than a set of disconnected product demos. It moves from a demand signal to a governed and secured agent fleet. Microsoft IQ is the shared intelligence backbone, and the central message is that intelligence compounds within Caldova rather than within any one model.

## Company narrative

Caldova is a global pharmaceutical company in the middle of an AI-driven transformation. New clinical evidence causes durable prescription growth for a flagship medicine. The resulting demand exceeds Caldova's manufacturing capacity and forces the company to quickly add contract manufacturers.

The business arc has six stages:

1. **Demand signal:** New clinical evidence produces lasting prescription growth for a flagship medicine rather than a seasonal spike.
2. **Capacity limit:** Caldova's manufacturing network is already at maximum capacity and cannot absorb the increase.
3. **Sourcing sprint:** The Chief Supply Chain Officer starts an RFP to onboard contract manufacturers.
4. **Cost exposure:** The new manufacturers satisfy demand, but invoice accuracy declines and Caldova may be overpaying by hundreds of thousands of dollars.
5. **Agentic response:** Teams build, observe, and tune agents that audit invoices against contract terms.
6. **Trust at scale:** Caldova operates a governed, secured, and observable agent fleet across Agent 365, Microsoft Foundry, and Defender.

The narrative should be told in that order. Open with the medicine and capacity problem, not the technology. Each scenario should cause the next one.

## Narrative principles

- One company and one continuous thread.
- Lead with business outcomes, then explain the products.
- Keep Microsoft IQ visible as the connective tissue.
- Treat governance, access control, observability, and security as inherent to the architecture rather than additions at the end.
- Preserve the established sequence and handoffs.
- Do not conflate Caldova with Zava.
- Do not change approved persona names or images without approval.

## Organizations and personas

### Supply chain and operations

- **Chief Supply Chain Officer: Mona Kane**
  - Detects or receives the demand signal.
  - Starts the sourcing process and hands the RFP to procurement.
- **Sourcing Manager: Wonda Howard**
  - Analyzes supplier signals.
  - Shortlists suppliers, drafts the RFP, scores responses, and tracks vendor communications.
- **Regional Sales Manager: David Power**

### Engineering and development

- **Chief Technical Officer: Carlos Slattery**
- **AI Engineer: Elvia Atkins**
  - Builds, scales, and observes the invoice-audit agent.
- **AI Dev Lead: Serena Davis**
  - Tunes the agent and fine-tunes the model.
- **AI Compliance Analyst / IT Admin: Lydia Bauer**
  - Reviews permissions, allocates credits, and governs agent cost and policy.
- **App Dev Manager: Kian Lambert**

### Finance and procurement

- **Chief Finance Officer: Andre Lawson**
- **VP of Procurement: Charlotte Waltson**
- **AP Specialist: Kenvin Sturis**
- **Financial Reconciliation Lead: Babak Shammas**
- **Financial Reconciliation: Katri Ahokas**

### Security

- **Chief Information Security Officer: Kadji Bell**
- **Frontier Security Engineer: Isaac Fielder**
- **Data Security Architect: Aadi Kapoor**
- **Security Administrator: Cassandra Dunn**

### Other named organizations

- Product development
- Marketing
- Contact center and sales enablement
- Factory operations and field service

For the broader AI Tour storyline, stage roles consolidate to four demo personas: Sourcing Manager, AI Compliance Analyst, Developer / AI Engineer, and Security Lead. LTG242 does not need to reproduce that four-person stage structure, but its scenarios should remain consistent with their responsibilities.

## Canonical three-chapter story

### Chapter 1: Copilot, the sourcing sprint

A durable demand spike exceeds Caldova's capacity. The sourcing team runs an RFP to add contract-manufacturing capacity.

The canonical flow includes:

- A Teams handoff from the Supply Chain Leader to sourcing.
- Copilot pulling live supplier data through Fabric IQ into Excel.
- A Work IQ-grounded skill producing a supplier shortlist.
- The RFP being completed in Word.
- Purview applying labels to the Excel and Word files.
- Cowork scoring responses across Microsoft 365, Fabric, and Dynamics 365.
- An AI Compliance Analyst reviewing and allocating Copilot credits.
- Scout tracking vendor communications and preparing actions for human review.

The chapter's signature proof is approximately 2,600 credits, or $26, to score the RFP, compared with work Caldova previously outsourced for hundreds of thousands of dollars.

### Chapter 2: Build, observe, and tune the invoice-audit agent

Adding manufacturers solves the capacity problem but creates invoice-accuracy problems. Caldova builds an agent that audits invoices against contract terms.

The canonical flow includes:

- Prototyping an invoice-audit agent in GitHub Copilot.
- Detecting a $5.7K overstatement on an Aster Ridge invoice in the planning storyline; this is separate from Waypoint's verified $99,880 disputed packaging surcharge.
- Rehosting the agent in Microsoft Foundry.
- Grounding it with contracts in Foundry IQ.
- Detecting an approximately $100K unauthorized charge.
- Making the result auditable in the trace view.
- Governing the agent and its permissions through the Agent 365 registry.
- Identifying a GPT-5.5 cost-cap issue and considering a lower-cost model.
- Improving agent quality from 67% to 85% in one optimization pass.
- Fine-tuning a smaller model on Caldova contracts to retain approximately 82% quality at approximately 70% lower cost.

The narrative point is model diversity without lock-in: reusable knowledge, evaluation assets, and improvements accrue to Caldova.

### Chapter 3: Secure the agent fleet

Caldova's agent population grows across managed and unmanaged sources. Security teams use the same Agent 365 registry in Defender to inventory and protect the fleet.

The canonical flow includes:

- Finding a high-risk shadow agent.
- Mapping it to within two hops of the internal payment system.
- Blocking unsigned applications until the device is managed.
- Using MDASH to find, validate, and prioritize source-code vulnerabilities.
- Using Project Perception to investigate threat intelligence and develop detections and remediation.

LTG242 focuses on knowledge retrieval rather than fleet security. This chapter is useful mainly as context for access controls, governance, network isolation, and production architecture.

## Microsoft IQ backbone

| Layer | Caldova role | Canonical chapter |
| --- | --- | --- |
| Fabric IQ | Supplies live supplier data for analysis and shortlisting | Chapter 1 |
| Work IQ | Grounds the shortlist skill in Caldova's working context | Chapter 1 |
| Foundry IQ | Turns contracts into reusable knowledge for the invoice-audit agent | Chapter 2 |
| Agent 365 | Provides one registry for governance, cost management, and security visibility | Chapters 2 and 3 |

The core retrieval message for LTG242 can build on this distinction: operational data, working context, reusable indexed knowledge, and agent governance are complementary layers rather than interchangeable products.

## Business data needed by the narrative

The Caldova storyline and the available sample datasets are not yet confirmed as a single canonical package. The lists below describe the business data the narrative needs; the Fabric and Waypoint sections document two candidate sources that cover different parts of that need.

### Demand and capacity data

- Clinical evidence indicating increased demand for the flagship medicine.
- Prescription or demand forecasts showing durable growth.
- Manufacturing capacity by plant, line, or region.
- Capacity-gap analysis showing why internal production cannot absorb demand.
- Supply plans and execution plans.

The source mentions a separate 7% manufacturing-capacity-gap scenario as an adjacent narrative trigger, not an on-stage canonical demo. Use a specific 7% figure only if that adjacent asset is approved for this session.

### Supplier and sourcing data

- Supplier master records.
- Live supplier performance and capacity data.
- Contract manufacturer profiles.
- RFP template and completed RFP.
- Supplier responses and supporting attachments.
- Evaluation criteria and weighted scorecards.
- Vendor communications.
- Supplier onboarding and technology-transfer packages.
- Updated execution plans and stakeholder meetings.

### Contract and invoice data

- Contract manufacturer agreements.
- Contract clauses and commercial terms.
- Invoices from contract manufacturers.
- Invoice line items, totals, and supporting records.
- Purchase orders and payment records.
- Audit findings and evidence linking invoice discrepancies to contract terms.
- Aster Ridge invoice and related contract as a strong candidate example.

### Governance and security data

- User, group, and document permissions.
- SharePoint access control lists.
- Purview sensitivity labels.
- Agent identities, owners, permissions, and registry records.
- Usage, credit, and model-cost records.
- Agent traces, evaluation results, and audit logs.
- Tenant and network-boundary configuration.
- Security findings and remediation records.

### Working-context data

- Teams chats and handoffs.
- Outlook email and calendar context.
- Word RFP documents.
- Excel supplier analysis and scorecards.
- SharePoint sites and document libraries.
- Dynamics 365 supplier or business records.

## Historical source: Fabric vendor analytics sample

The original session draft used a seven-vendor Fabric export. That export has
been superseded by the canonical supplier assets in
[`pamelafox/aitour27-caldova-data`](https://github.com/pamelafox/aitour27-caldova-data).
The historical details below explain earlier planning decisions but are not the
current session data contract. Current implementations should use `SupplierSM`,
`SupplierDataAgent`, and the shared `sup-001` through `sup-018` registry.

The export contains two generations of the sample:

- **`Supply Chain/`** is the earlier static version. It has one current row per vendor, a simpler semantic model, a deployment notebook, and a vendor report.
- **`Supply Chain Operations/`** is the current v3.0 version. It separates vendor attributes from dated performance, adds approximately two years of trends, prepares the semantic model for AI, creates a Fabric Data Agent, and includes two comparison reports.

If this source is selected, use the `Supply Chain Operations/` model as the primary reference. The legacy model remains useful for understanding the original workbook-shaped data but should not be treated as a separate business dataset.

### Source and naming caveat

The notebook says the baseline rows were transcribed from the **Allerveo CMO Vendor Comparison** workbook, specifically its `Vendor Overview`, `Quality & Regulatory`, and `Capacity & Commercial` tabs. Some semantic-model descriptions also say "for Allerveo," although this export is supplied as official Caldova scenario data.

Before displaying the model or Data Agent in an LTG242 demo, confirm whether those residual Allerveo references should be changed to Caldova. Do not present Allerveo and Caldova as two companies in the storyline.

### Contract manufacturers

The sample defines seven fictional contract manufacturers with stable IDs from `V001` through `V007`.

#### Capacity and commercial baseline

| ID | Vendor | Location | OSD experience | Capacity K/month | Utilization | Lead time | Cost index | MOQ K units | Tech transfer | Financial rating |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V001 | Annterra Pharma | New Jersey, USA | 22 years | 850 | 68% | 14 weeks | 118 | 250 | 100% | A+ |
| V002 | Kristos Pharma | North Carolina, USA | 15 years | 520 | 78% | 16 weeks | 82 | 125 | 94% | A |
| V003 | Sabyn Formulations | Massachusetts, USA | 11 years | 380 | 71% | 10 weeks | 101 | 63 | 92% | B+ |
| V004 | Vexara Manufacturing | Pennsylvania, USA | 28 years | 120 | 96% | 32 weeks | 122 | 500 | 97% | A+ |
| V005 | Telsin Group | Texas, USA | 7 years | 400 | 58% | 18 weeks | 74 | 125 | 78% | B- |
| V006 | Orova Pharmatech | Ohio, USA | 18 years | 100 | 88% | 20 weeks | 95 | 188 | 89% | B+ |
| V007 | Meridax Life Sciences | Dublin, Ireland / Singapore | 14 years | 650 | 73% | 24 weeks | 88 | 625 | 86% | A- |

`CostIndex` uses a market average of 100, so a lower value is cheaper. Capacity is expressed in thousands of units per month, and MOQ is expressed in thousands of units. OSD means oral solid dose manufacturing.

#### Quality and regulatory baseline

| ID | Vendor | OTIF | Batch rejection | Right first time | Complaints/1K | Inspection | Open actions | Inspections/3yr | Internal audit |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| V001 | Annterra Pharma | 97.2% | 0.8% | 98.1% | 0.9 | NAI | 0 | 3 | Satisfactory |
| V002 | Kristos Pharma | 95.8% | 1.1% | 97.4% | 1.2 | VAI | 0 | 2 | Satisfactory |
| V003 | Sabyn Formulations | 96.5% | 1.4% | 96.2% | 1.5 | NAI | 0 | 2 | Satisfactory |
| V004 | Vexara Manufacturing | 98.1% | 0.5% | 98.8% | 0.6 | NAI | 0 | 3 | Outstanding |
| V005 | Telsin Group | 88.3% | 3.8% | 89.1% | 4.2 | OAI | 2 | 2 | Requires Improvement |
| V006 | Orova Pharmatech | 94.1% | 1.8% | 95.5% | 1.9 | VAI | 0 | 2 | Satisfactory |
| V007 | Meridax Life Sciences | 91.2% | 2.1% | 94.8% | 2.3 | VAI | 0 | 1 | Satisfactory |

OTIF means on-time-in-full delivery over the trailing 12 months. The inspection classifications are:

- **NAI, No Action Indicated:** No objectionable conditions or practices were found.
- **VAI, Voluntary Action Indicated:** Objectionable conditions were found and voluntary correction is expected, but regulatory action is not planned.
- **OAI, Official Action Indicated:** Regulatory or administrative action is recommended. The model treats OAI as disqualifying for sourcing.

Internal audits are ranked `Outstanding`, `Satisfactory`, and `Requires Improvement`; the first two pass and the last does not. Financial ratings run from A+ through B-, with a separate investment-grade indicator in the semantic model.

### Baseline versus synthesized history

The vendor values above are the source baseline transcribed from the workbook. The v3.0 notebook then synthesizes time-series history for demonstration:

- A daily date dimension covers the last two years.
- Performance uses 105 Monday snapshots per vendor, producing 735 fact rows.
- Each metric drifts toward the source baseline with bounded Gaussian noise.
- A deliberate five-week recent-change window makes selected vendors improve or decline.
- The random seed is fixed at `42`, making generation repeatable for a given run date.

The generated history is not an independent source of official business facts. It is synthetic trend data designed to support time-series visuals, Copilot questions, and Data Agent recommendations.

#### Synthetic recent-change stories

- **Telsin Group improves:** Its generated latest state reaches 93.1% OTIF, 1.9% batch rejection, 94.6% right-first-time, 2.1 complaints per 1,000, 69% utilization, and 86% technology-transfer success. Its inspection changes from OAI to VAI, open actions fall from two to zero, and its audit becomes Satisfactory.
- **Orova Pharmatech improves:** Its generated latest state reaches 96.3% OTIF, 1.1% batch rejection, 96.9% right-first-time, 1.2 complaints per 1,000, 90% utilization, and 92% technology-transfer success.
- **Sabyn Formulations declines:** Its generated latest state reaches 94.7% OTIF, 2.4% batch rejection, 94.5% right-first-time, 2.4 complaints per 1,000, and 79% utilization.
- **Meridax Life Sciences declines:** Its generated latest state reaches 87.4% OTIF, 3.5% batch rejection, 92.1% right-first-time, 3.7 complaints per 1,000, 91% utilization, and 83% technology-transfer success.
- **Annterra Pharma, Kristos Pharma, and Vexara Manufacturing** are configured as broadly stable.

The distinction between baseline and latest generated values matters when explaining a result. A question about "current" performance should use the latest semantic-model measures; a question about the workbook baseline should use the source values documented above.

### Current star schema

The legacy `VendorSM` semantic model used Direct Lake and a seven-table star schema:

| Table | Grain and purpose |
| --- | --- |
| `DimVendor` | One row per contract manufacturer with location, OSD experience, capacity, MOQ, inspections, and financial rating |
| `VendorPerformance` | One row per vendor per weekly snapshot with quality, regulatory, capacity, and commercial KPIs |
| `DimDate` | Daily calendar for the two-year period, marked as the date table |
| `DimLocation` | Vendor location, state or region, and country |
| `DimInspectionResult` | NAI, VAI, and OAI definitions, severity, and disqualification status |
| `DimAuditResult` | Internal audit rank and passing status |
| `DimFinancialRating` | Financial rating rank and investment-grade status |

`VendorPerformance` joins to `DimVendor` by `VendorID` and to `DimDate` by `DateKey`. Vendor location and financial rating hang from `DimVendor`; inspection and audit outcomes hang from `VendorPerformance`.

### Metrics available to Fabric and AI

The semantic model includes 18 explicit measures:

- **Vendor totals:** Vendor count and total available capacity.
- **Average KPIs:** OTIF, batch rejection, right-first-time, complaints per 1,000, utilization, lead time, cost index, technology-transfer success, and open regulatory actions.
- **Latest KPIs:** OTIF, batch rejection, right-first-time, utilization, and complaints per 1,000 at the latest date in context.
- **Four-week changes:** OTIF change and batch-rejection change against 28 days earlier.

Descriptions explain each business field to Copilot. Authored synonyms map natural language such as `suppliers`, `manufacturers`, `CMOs`, `scorecard`, `quality failures`, `delivery reliability`, and `spare capacity` to the appropriate tables and measures.

### Vendor Data Agent behavior

The legacy v3.0 notebook created and published `VendorDataAgent` over the semantic model. Its instructions established this recommendation policy:

1. Use the `Latest ...` measures for current performance.
2. Use the four-week change measures to describe improvement or decline.
3. Exclude a vendor from rankings or shortlists if it has open regulatory actions or an OAI inspection.
4. Prefer lower cost index, higher OTIF, higher right-first-time, and lower batch rejection.
5. State the vendor name and the supporting metrics behind every recommendation.

Suggested natural-language questions in the notebook include:

- Which vendors improved OTIF the most in the last month?
- Show the OTIF trend by vendor over the last two years.
- Which vendors are declining on batch rejection rate recently?
- Rank CMOs by latest OTIF, excluding any with open regulatory actions.
- Which vendors improved the most in the last month and why?
- Which vendors are trending down on quality recently?

This is a strong example of governed natural-language access to structured analytical data. The result is grounded by the semantic model's relationships, measures, descriptions, synonyms, and explicit qualification rules rather than by searching raw table text.

### Reports

The legacy **Vendor Report** is a static comparison report over the original vendor snapshot. Its visuals cover vendor names and counts, locations and countries, available capacity, and inspection outcomes.

The current export includes:

- **Vendor Performance:** A comparison report with vendor and date slicers, latest-value cards, OTIF and batch-rejection trends, quality comparisons, lead time, cost, and recent-change visuals.
- **Supplier Performance Comparison:** A Caldova-branded comparison report with a supplier map, slicers, latest OTIF and rejection cards, trend charts, and four-week change comparisons.

The current reports use the v3.0 semantic model, so their trend visuals are based on synthesized history while vendor identities and baseline attributes come from the source workbook.

### Deployment behavior and requirements

The v3.0 Fabric notebook:

1. Creates or reuses an `EnterpriseLakehouse`.
2. Writes the seven Delta tables.
3. created a Direct Lake semantic model named `VendorSM`.
4. Adds relationships, measures, descriptions, synonyms, sort behavior, and date-table metadata.
5. created and published `VendorDataAgent`.
6. Creates the Power BI report.

Important requirements and caveats:

- It runs as a Microsoft Fabric PySpark notebook.
- It installs prerelease `fabric-data-agent-sdk` and `semantic-link-labs` packages.
- The Data Agent requires paid Fabric F-SKU capacity and is not supported on Trial capacity.
- New Delta tables may take time to become visible to Direct Lake; the notebook includes retry and backoff behavior.
- The notebook overwrites its generated tables by default and recreates the semantic model and Data Agent for repeatable deployment.
- Snapshot dates are calculated relative to the notebook's run date, so generated calendar dates move when the notebook is rerun.

### How the Fabric sample could fit LTG242

The Fabric sample is well suited to the **live structured vendor-analytics source** in the Caldova narrative:

- Foundry IQ can index stable unstructured evidence such as RFP responses, contracts, quality reports, and policies.
- The Fabric semantic model can provide current vendor metrics, trends, capacity, cost, and qualification state.
- A combined answer can cite contract or policy language and retrieve current operational performance without copying fast-changing metrics into the document index.
- Work IQ can add Wonda Howard's current RFP, Teams discussions, email, meetings, and open actions.

This gives the talk a concrete progression:

1. **Indexed knowledge:** What do Caldova's approved documents say, and who may read them?
2. **Federated operational data:** What is each supplier's current performance and qualification state in Fabric?
3. **Working context:** What is the sourcing manager doing and deciding now?

Candidate cross-source questions include:

- Which qualifying supplier has enough current capacity, and what contract terms would Caldova need to accept?
- Which suppliers are improving operationally, and do their RFP responses satisfy Caldova's quality requirements?
- Why was Telsin previously disqualified, what has changed recently, and which approved documents are needed before reconsideration?
- Which supplier has the strongest current delivery performance, and what open actions appear in the sourcing manager's work context?

The Fabric sample does not contain contracts, RFP documents, SharePoint ACLs, user work context, invoices, or purchase orders. Waypoint covers many of the contract and invoice gaps, while user work context and permissions still require separate assets.

## Candidate source: Waypoint contract and invoice corpus

The public [Waypoint corpus](https://github.com/caldova/waypoint/tree/045637b6eea72550ce3aad61bfac851356ca824a/modules/corpus) is a second candidate data source. This reference uses pinned commit `045637b6eea72550ce3aad61bfac851356ca824a` so its contents do not drift while the talk is planned. Its status as official LTG242 data is not yet confirmed.

Waypoint is designed as an evidence puzzle for a contracts and invoice-assurance agent. The expected findings are stored outside the supplier-facing contracts and invoices, allowing the agent to demonstrate retrieval and reconciliation rather than merely repeat an answer embedded in a document.

### Corpus inventory

| Asset | Contents | Retrieval role |
| --- | --- | --- |
| Suppliers | 15 fictional pharmaceutical suppliers, `sup-001` through `sup-015` | Stable join key and supplier metadata |
| Contracts | 15 supplier-specific agreements or statements of work in source Markdown and generated DOCX | Foundry IQ document knowledge |
| Policies | Three invoice, dispute, and quality-billability policies in source Markdown and generated DOCX | Foundry IQ document knowledge |
| Canonical supplier invoices | 15 invoices with 60 total lines and supplier-specific presentation profiles | Relational facts plus rendered HTML/PDF evidence |
| Designed discrepancies | One non-matching line per invoice, or 15 of 60 lines | Expected scenario coverage for evaluation |
| Scenario metadata | Expected state, scenario ID, and issue category kept outside supplier-facing documents | Test oracle, not agent evidence |
| Waypoint seed | Import-shaped JSON containing suppliers, documents, policies, scenarios, invoices, lines, findings, and evidence | Ready source for a relational database or service |

The supplier set spans contract manufacturing, fill-finish, packaging, API supply, quality laboratories, clinical supply, cold-chain logistics, biologics, device assembly, sterilization, process development, excipients, regional manufacturing, and regulatory services. This breadth supports more varied retrieval questions than a CMO scorecard alone.

### Relational structure and join keys

The corpus consistently uses `supplier_id` values from `sup-001` through `sup-015` to connect suppliers, contracts, invoices, findings, and evidence. Other useful identifiers include:

- `invoice_id` for invoices, lines, findings, and evidence.
- `scenario_id` for the reconciliation pattern being tested.
- `contract_document_ids`, `policy_ids`, and `evidence_ids` for the basis of a finding.
- Purchase-order, batch, shipment, quality, and milestone references for operational reconciliation.

The JSON can be normalized into relational tables such as `Supplier`, `ContractDocument`, `Policy`, `Invoice`, `InvoiceLine`, `Finding`, and `Evidence`. An agent can query current invoice and supplier facts through an API or MCP tool while retrieving the governing contract and policy language from Foundry IQ.

### Aster Ridge example

Waypoint's `sup-001` is **Aster Ridge Biomanufacturing**, a North American contract manufacturer specializing in high-volume tablet compression and coating.

Its October 2026 supplier invoice, `INV-SUP-001-2026-10`, totals **$1,418,200** and contains four lines:

- Two matched tablet-production lines totaling $1,308,720.
- One matched $9,600 batch-release administration line.
- One disputed **$99,880 blister-packaging surcharge** whose scenario is `scn-sup-001-packaging-authorization` and issue category is `off_contract_packaging`.

This is a particularly strong LTG242 example because the agent must combine a live invoice fact with contract authorization language and return the evidence behind the discrepancy. It also aligns with the approximately $100K unauthorized-charge proof point in the Caldova planning storyline. The separate $5.7K figure in that storyline is not represented by this invoice and should not be conflated with it.

Waypoint also includes a separate generated Waypoint import payload with smaller demonstration invoices and decisions. For Aster Ridge, that payload contains an approved $512,000 production invoice and an $8,300 recoverable overtime premium. Treat this import payload as a derived application seed, not as the same invoice ledger as the canonical 15 supplier invoices.

### Evidence and decision coverage

The invoice set exercises multiple retrieval patterns: off-contract packaging, unreleased-batch billing, unsupported logistics surcharges, invalid true-ups, early milestone billing, included services billed separately, invalid storage periods, duplicate billing, supplier-caused quality costs, excess scrap, premature release documentation, wrong rates, escalation-cap violations, and unapproved country scope.

The separate Waypoint seed demonstrates decision states including `approved`, `recover`, `review`, and `escalate`. Evidence can point to indexed contracts and invoice PDFs or to operational records such as purchase orders, batch records, approval email, production plans, quality logs, and supplier submissions.

### How the Waypoint corpus could fit LTG242

Waypoint is well suited to a compact hybrid-retrieval demo:

1. Load supplier, invoice, and line-item facts into a relational store.
2. Index contracts, policies, and selected invoice PDFs in Foundry IQ.
3. Expose relational lookup through an MCP server or application tool.
4. Ask the agent to review an invoice, identify unsupported charges, and cite the contract or policy evidence.
5. Evaluate the result against scenario metadata that the agent cannot retrieve.

This architecture does not require Fabric IQ. Fabric, Azure SQL, PostgreSQL, or another approved relational service could hold the structured facts. The key talk concept is the retrieval split: stable document knowledge is indexed, while current transaction facts are queried at request time.

## Unified sample-data source

The authoritative sample-data repository now combines the document corpus,
canonical supplier registry, Fabric analytics model, medicinal-product ontology,
and provisioning workflows. The registry uses `sup-001` through `sup-018`
consistently across structured data. Procurement bidders Aster Ridge, Summit
Dose, and Atlas Regional retain those same IDs in their RFP responses,
agreements, analytics, and ontology relationships.

Use stable PDFs from the named corpora for indexed knowledge and use `SupplierSM`,
the ontology, or narrow MCP tools for current structured facts. No supplier
crosswalk is required.

## Caldova RFP reference facts

The canonical supporting RFP is issued by **Global Strategic Sourcing, Manufacturing & External Supply**. Its named fictional contact is **Efe Abugo** at `EfeAbugo@CaldovaPharma.com`.

### Evaluation weights

| Category | Weight |
| --- | ---: |
| Technical and operational | 25% |
| Quality and regulatory | 25% |
| Capacity and supply | 20% |
| Commercial | 20% |
| Implementation and risk | 10% |

### Commercial baseline

- Firm pricing for a 12-month term.
- Net 60 payment terms.
- Prices in USD.
- At least four weeks of safety stock.
- Subcontracting requires written approval.

### Contract manufacturer questionnaire

- Regulatory and GMP.
- Quality systems.
- Capacity and supply.
- Commercial and risk.

The RFP template supports the sourcing narrative but is not itself a required on-stage demo.

## Data opportunities for LTG242

These options adapt canonical Caldova data to the talk outline. They are planning recommendations, not claims that the source PDF specifies these exact demos.

### Scenario 1: Internal knowledge assistant

**Best-fit business need:** Help sourcing, procurement, finance, and engineering employees answer questions across approved contract-manufacturer documents while preserving document access.

**Candidate indexed SharePoint corpus:**

- Contract manufacturer agreements and amendments.
- RFP and supplier responses.
- Quality and regulatory certificates.
- GMP audit reports.
- Supplier onboarding and technology-transfer documents.
- Manufacturing specifications and operating procedures.
- Product images, facility diagrams, scanned certificates, and multilingual supplier documents.

**Useful retrieval examples:**

- Which approved manufacturers can provide the required capacity and safety stock?
- What subcontracting restrictions apply to a particular supplier?
- Which contracts require written approval before subcontracting?
- What quality certifications are present in a scanned or multilingual attachment?
- Which users may see commercial terms versus quality documentation?

**Why it fits:** This corpus naturally supports indexing, skill-based enrichment, vectorization, hybrid search, multilingual content, multimodal content, and ACL preservation.

### Scenario 2: Customer support agent with a remote source

The Caldova storyline does not define a customer-support demo. To keep this section in narrative, frame the user as an internal sourcing or supplier-support agent rather than inventing an unrelated consumer support story.

**Best-fit business need:** Answer a supplier or sourcing manager's question by combining stable indexed documents with current operational data.

**Indexed knowledge:**

- RFP terms and response documents.
- Contracts, amendments, policies, and onboarding guides.
- Quality manuals and regulatory documentation.

**Candidate MCP-backed remote source:**

- Live supplier status, capacity, or performance system.
- Dynamics 365 supplier and procurement records.
- Invoice, purchase-order, or payment-status service.
- Current onboarding workflow or case-management system.

**Useful retrieval examples:**

- Is this invoice line allowed by the supplier's contract, and what is the current purchase-order status?
- Which contract manufacturer meets the documented requirements and currently has available capacity?
- What does the onboarding policy require, and which steps remain open for this supplier?

**Federation versus indexing:**

- Index relatively stable, unstructured documents that benefit from enrichment and semantic retrieval.
- Federate current transactional or operational values that must be read at request time.
- Combine both when an answer needs documentary evidence and live business state.

### Scenario 3: Enterprise assistant with Work IQ

**Best-fit business need:** Help Wonda Howard or another authorized employee move from reusable enterprise knowledge to their current work context.

**Indexed SharePoint knowledge:**

- Contracts, RFP responses, policies, quality reports, and approved supplier documentation.

**Work IQ context:**

- The Teams handoff that starts the RFP.
- Relevant emails and vendor communications.
- The user's current Word RFP and Excel shortlist.
- Meetings, stakeholders, and near-term actions.

**Useful retrieval examples:**

- Summarize the approved supplier requirements, then identify the open actions from my recent conversations.
- Compare the contract terms in the knowledge base with the supplier commitments discussed by my team this week.
- Which approved documents support this shortlist, and what decisions are still pending in my work context?

**Contrast to land:** Foundry IQ provides reusable, curated knowledge for many agents; Work IQ adds the authorized employee's current organizational and working context.

### Production architecture

The Caldova story supports discussing:

- Separation of commercial, quality, engineering, finance, and security data.
- ACL and sensitivity-label preservation for indexed content.
- Tenant boundaries for a global organization and external manufacturers.
- Network isolation around regulated and financially sensitive systems.
- Freshness requirements for operational supplier and invoice data.
- Auditable retrieval evidence and agent traces.
- Shared reusable knowledge across multiple agents.
- Serverless versus dedicated deployment choices based on isolation, scale, predictability, and governance requirements.

The source establishes these business pressures but does not provide the technical selection criteria or topology. Those details remain to be validated against current product guidance.

## Candidate synthetic data package

A compact, coherent demo dataset could include the following. Reuse equivalent Waypoint assets if that corpus is selected rather than generating duplicates:

1. One Caldova sourcing policy.
2. One RFP using the canonical evaluation weights and commercial baseline.
3. Three fictional supplier responses with different capacity, quality, price, language, and attachment formats.
4. Three contract manufacturer agreements with different access groups and subcontracting terms.
5. One contract amendment.
6. One multilingual quality certificate.
7. One scanned GMP report with a facility diagram or product image.
8. Two invoices, including the Aster Ridge example with its verified $99,880 disputed packaging surcharge or a separately sourced and verified $5.7K overstatement.
9. One purchase order and one live supplier-status record exposed through a remote service.
10. A small set of fictional Teams messages, emails, meetings, and open actions for Wonda Howard.
11. ACL metadata separating sourcing, finance, quality, engineering, and executive access.
12. Expected answers and citations for each demo query.

All data should be synthetic. Do not use real patient, employee, supplier, contract, invoice, or regulated pharmaceutical data.

## Canonical proof points

- Approximately 2,600 credits, or $26, to score the RFP.
- A $5.7K invoice overstatement detected.
- An approximately $100K unauthorized charge detected.
- Agent quality improving from 67% to 85% in one optimization pass.
- A smaller fine-tuned model retaining approximately 82% quality at approximately 70% lower cost.
- A shadow agent discovered two hops from the internal payment system.

These figures come from the confidential planning storyline. Confirm approval before using them in public session materials.

## Product mapping

| Story area | Products and layers in the source |
| --- | --- |
| Sourcing sprint | Microsoft 365 Copilot, Cowork, Scout, Fabric IQ, Work IQ, Purview, Dynamics 365 |
| Invoice-audit agent | GitHub Copilot, Microsoft Foundry, Foundry IQ, Agent 365 FinOps |
| Securing the fleet | Microsoft Defender, Agent 365, MDASH, Project Perception |

## Open validation items

- Confirm which Caldova names, logos, images, proof points, and documents are approved for public AI Tour use.
- Confirm that the canonical sample-data repository and its fictional supplier
  identities are approved for public LTG242 use.
- Confirm whether the canonical RFP template and demo repo can be used or adapted.
- Confirm the public terminology and current capabilities for Foundry IQ, Work IQ, Fabric IQ, MCP integration, ACL ingestion, and deployment models.
- Confirm whether the remote source should be Dynamics 365, a supplier system, an invoice system, or another approved service.
- Confirm the exact ACL groups and tenant boundaries to demonstrate.
- Confirm whether the customer-support label in the source outline may be reframed as supplier support to preserve the Caldova narrative.
