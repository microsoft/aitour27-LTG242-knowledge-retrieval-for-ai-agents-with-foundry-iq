# Sample questions

This catalog consolidates the repository's user-facing sample and demo questions. It excludes template workflow questions, rhetorical prose, and duplicate copies in generated evaluation results.

## Indexed document knowledge

These questions primarily use documents indexed by Foundry IQ, including invoices, shipment records, quality certificates, inspection reports, contracts, policies, RFP responses, and access-control metadata.

| Question | Related data |
| --- | --- |
| Shipment `SHIP-VC-1026-BOS-FRA` exceeded its temperature range. What happened, and can the 4,800 units be distributed? | Temperature time series, shipment excursion report, quarantine decision, stability allowance, and final disposition |
| Was lot `LOT-MD-1026-A` released, and should Caldova pay the $125,600 yield adjustment? | Spanish quality certificate, released quantity, manufacturing yield, forecast quantity, and supplier invoice |
| Should Caldova approve BluePeak's $111,000 contamination-investigation charge? Cite the cause, inspection evidence, supply restriction, and corrective actions. | Supplier invoice, contamination investigation, scanned GMP inspection report, supply restriction, and CAPA evidence |
| Review the supplier invoices and associated evidence. Which disputed charges should Caldova reject, and what is the total avoided cost? | Supplier invoices and supporting shipment, yield, quality, inspection, and scrap evidence |
| Compare the bidders for `RFP-CAL-OSD-2026-01`. Which supplier should be selected, what are the key tradeoffs, and what evidence supports the answer? Create a weighted-score chart. | RFP, three supplier responses, evaluation weights, agreements, evidence map, amendment, purchase order, and document ACLs |
| Which approved manufacturers can provide the required capacity and safety stock? | Manufacturer agreements, RFP responses, capacity commitments, and safety-stock requirements |
| What subcontracting restrictions apply to a particular supplier? | Supplier agreement, amendments, RFP terms, and subcontracting policy |
| Which contracts require written approval before subcontracting? | Contract clauses and procurement policy |
| What quality certifications are present in a scanned or multilingual attachment? | Scanned and multilingual quality certificates and enriched document content |
| Which users may see commercial terms versus quality documentation? | SharePoint ACLs, sensitivity boundaries, commercial documents, and quality documents |

## Fabric supplier analytics

These questions use the Fabric `SupplierSM` semantic model. Relevant data
includes supplier master records, weekly performance history, latest KPI
measures, qualification status, capacity, cost index, geography, and regulatory
actions.

| Question | Related data |
| --- | --- |
| Which suppliers improved OTIF the most in the last month? | Four-week OTIF change by supplier |
| Show the OTIF trend by supplier over the last two years. | Weekly supplier OTIF history |
| Which suppliers are declining on batch rejection rate recently? | Four-week batch-rejection change by supplier |
| Rank contract manufacturers by latest OTIF, excluding any with open regulatory actions. | Latest OTIF, open regulatory actions, and supplier qualification status |
| Which suppliers improved the most in the last month and why? | Four-week changes across OTIF, right-first-time quality, batch rejection, and other performance measures |
| Which suppliers are trending down on quality recently? | Recent right-first-time and batch-rejection trends |
| Which suppliers have the lowest cost index and no open regulatory actions? | Cost index and regulatory-action status |
| Show average OTIF by country. | OTIF performance, supplier sites, and country |
| Rank contract manufacturers by available capacity. | Current available-capacity measure |
| Which suppliers qualify and have the lowest cost index? | Qualification status and cost index |
| Rank contract manufacturers by available capacity, excluding any with open regulatory actions. | Available capacity and regulatory-action status |
| Compare OTIF and batch rejection for suppliers in the USA. | Country, OTIF, and batch-rejection measures |

## Federated operational data and indexed documents

These questions combine stable indexed documents with current structured facts from Fabric, PostgreSQL, Dynamics 365, or another MCP-backed operational source.

| Question | Related data |
| --- | --- |
| Which qualifying vendor has enough current capacity, and what contract terms would Caldova need to accept? | Current qualification and capacity plus indexed supplier contracts |
| Which vendors are improving operationally, and do their RFP responses satisfy Caldova's quality requirements? | Current performance trends plus indexed RFP responses and quality requirements |
| Why was Telsin previously disqualified, what has changed recently, and which approved documents are needed before reconsideration? | Qualification history, recent operational changes, regulatory actions, and approved supporting documents |
| Is this invoice line allowed by the supplier's contract, and what is the current purchase-order status? | Indexed contract and policy clauses plus current invoice line and purchase-order status |
| Which contract manufacturer meets the documented requirements and currently has available capacity? | Indexed RFP and contract requirements plus current capacity and qualification data |
| What does the onboarding policy require, and which steps remain open for this supplier? | Indexed onboarding policy plus current workflow or case-management state |
| Compare Summit Dose's commitments in the `CALD-201` RFP response, agreement amendment, and purchase order with its current performance, capacity, audit actions, and approved subcontractors. What has changed or needs attention? Graph the relevant trends. | Indexed Summit Dose sourcing documents plus Fabric or MCP performance, capacity, audit, and subcontractor records |

## Work IQ and working context

These questions add the authorized employee's current Microsoft 365 context to indexed enterprise knowledge and, where stated, operational data.

| Question | Related data |
| --- | --- |
| Which supplier has the strongest current delivery performance, and what open actions appear in the sourcing manager's work context? | Current delivery KPIs plus the sourcing manager's emails, Teams conversations, meetings, and tasks |
| Summarize the approved supplier requirements, then identify the open actions from my recent conversations. | Indexed supplier requirements plus recent Teams and email conversations |
| Compare the contract terms in the knowledge base with the supplier commitments discussed by my team this week. | Indexed contracts plus recent Teams messages, email, and meeting context |
| Which approved documents support this shortlist, and what decisions are still pending in my work context? | Indexed approved documents plus the user's shortlist, conversations, meetings, and open actions |

## Architecture framing questions

These questions explain the role of each retrieval source rather than test one specific record.

| Question | Related data |
| --- | --- |
| What do Caldova's approved documents say, and who may read them? | Indexed enterprise documents, ACLs, and sensitivity metadata |
| What is each supplier's current performance and qualification state in Fabric? | Fabric semantic-model performance and qualification measures |
| What is the sourcing manager doing and deciding now? | Work IQ context from Microsoft 365 |
