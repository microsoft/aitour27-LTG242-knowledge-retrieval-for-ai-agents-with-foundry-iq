# LTG242 talk plan

## Outline transcription

**FY27 AI Tour | Tech Frontier Lightning Talk | LTG242**

- **Conversation:** Amplify your intelligence
- **Customer Speaker(s)?:** __ #
- **Local Customer Story?:** No
- **Level:** 200
- **As of:** 7/16/2026

### Title

Knowledge retrieval for AI agents with Foundry IQ

### Abstract

Discover how Foundry IQ connects knowledge across diverse data sources while preserving access controls and maximizing retrieval quality. Explore AI-optimized ingestion pipelines and knowledge architectures that unify indexed and remote sources.

### Objectives

- Understand agentic knowledge bases.
- Learn when to use built-in skills, custom skills, indexers, CU.
- Understand how to preserve data ACLs in indexed content.
- Explore MCP servers and Microsoft IQ integrations.
- Compare serverless and dedicated deployment models.

### Notes

Also discuss: MCP servers, Microsoft IQs, multi-tenant environments, network isolation, and serverless versus dedicated deployments.

### Session authors

- Pamela Fox


#### Act one: Retrieval patterns for AI agents

**Scenario 1 (Graphics/Demo): Internal Knowledge assistant**

- **Time:** 4 min
- **Speaker:** TBD
- Use indexers, skills, vectorization, hybrid search, Multilingual, multimodal.
- Index SharePoint documents into Foundry IQ with ACLs.

**Scenario 2 (Graphics/Demo): Customer Support Agent**

- **Time:** 4 min
- **Speaker:** TBD
- Combine with MCP remote source.
- Discuss federation vs indexing.

#### Act two: Enterprise knowledge retrieval

**Scenario 3 (Graphics/Demo): Enterprise assistant**

- **Time:** 3 min
- **Speaker:** TBD
- Add Work IQ.
- Contrast with indexed SharePoint.

**Productionizing (Slides): Architecture decisions**

- **Time:** 2 min
- **Speaker:** TBD
- Multi-tenancy.
- Serverless vs dedicated deployments.

#### Act three: Key takeaways

**Next Steps: Additional Sessions, Learning, Resource**

- **Time:** 2 min
- **Speaker:** TBD

**Evaluation Slide**

- Ask attendees to complete one.

## Practical talk plan

The practical scenarios below adapt the source outline to the Caldova
procurement and supplier corpus. They intentionally replace the generic
customer-support scenario and keep Work IQ outside the live demo.

### Timing

| Act | Segment | Time | Cumulative time |
|---|---|---:|---:|
| Act one | Scenario 1: Invoice Investigation Agent | 4 min | 4 min |
| Act one | Scenario 2: Sourcing Review Agent with ACLs | 4 min | 8 min |
| Act two | Scenario 3: Supplier Intelligence Agent with MCP | 3 min | 11 min |
| Act two | Productionizing: Architecture decisions | 2 min | 13 min |
| Act three | Key takeaways, next steps, and evaluation | 2 min | 15 min |
|  | **Total** | **15 min** | **15 min** |

### Demo narrative and data strategy

The demo uses Caldova Pharmaceuticals, a fictional company, and three
purpose-built knowledge bases. Each knowledge base has a corresponding agent
and a distinct reason to exist:

1. A document knowledge base demonstrates retrieval across many documents in
   one index.
2. An ACL-protected knowledge base demonstrates security trimming over
   confidential sourcing documents.
3. A federated knowledge base adds current relational data through MCP.

Work IQ is not part of the live demo. Mention it on an architecture slide as an
option for permission-aware Microsoft 365 grounding without adding its tenant,
content, identity, and permission setup to the demo.

#### Indexed-corpus boundary

Index the generated PDFs under `data/**/pdf/`, not the JSON source records,
HTML previews, templates, or image assets. This keeps the demo representative
of enterprise document ingestion and prevents the knowledge base from
answering OCR, multilingual, or diagram questions from easier structured
surrogates.

#### Knowledge bases and agents

| Configuration | Indexed content | Security or additional source | Corresponding agent | Agent tools | Demo purpose |
|---|---|---|---|---|---|
| **KB 1: Invoice evidence** | Complete: 25 PDFs comprising 15 invoices, 2 temperature reports, 6 operational reports, 1 Spanish certificate, and 1 scanned GMP inspection report. | None | **Invoice Investigation Agent** | Knowledge retrieval and Code Interpreter | Answer evidence-heavy invoice questions across searchable, multilingual, and scanned documents; calculate exposure and generate charts |
| **KB 2: Confidential sourcing** | Generated: 11 PDFs comprising a purchasing policy, 9 procurement-chain documents, and `CAL-MAP-EVD-001.pdf`. | ADLS Gen2 POSIX-like ACL metadata enforced with the caller's Microsoft Entra token | **Sourcing Review Agent** | ACL-aware knowledge retrieval and Code Interpreter | Show that the same sourcing question returns different evidence and analysis for users with different access |
| **KB 3: Supplier intelligence** | Generated document assets: the KB 2 corpus plus `CAL-MAP-SUP-001.pdf`. | PostgreSQL through a custom MCP server | **Supplier Intelligence Agent** | Knowledge retrieval, MCP, and Code Interpreter | Combine signed sourcing documents with current structured supplier performance and visualize the comparison |

KB 3 intentionally builds on KB 2. This makes the progression easy to explain:
first secure the indexed documents, then federate current operational facts
without copying them into the index.

#### KB 1 content and questions

The Invoice Investigation Agent retrieves across all 25 target documents in one
index. Code Interpreter receives only the grounded facts needed for a
calculation or visualization.

| Query | Expected grounded response | Code Interpreter output |
|---|---|---|
| “Shipment `SHIP-VC-1026-BOS-FRA` exceeded its temperature range. What happened, and can the 4,800 units be distributed?” | A 150-minute high-temperature excursion reached 10.7 C during the Frankfurt transfer. The inventory was quarantined, reviewed against stability allowance, and released for distribution. | Plot the temperature series with the approved 2-8 C band highlighted. |
| “Was lot `LOT-MD-1026-A` released, and should Caldova pay the $125,600 yield adjustment?” | The Spanish certificate releases the lot. Actual released quantity was 7,200 kg and overall yield was 87.8%, within the approved 85-92% range. The adjustment used an 8,000 kg forecast and should be rejected. | Generate a stage-by-stage yield chart and show the $125,600 avoided charge. |
| “Should Caldova approve BluePeak's $111,000 contamination-investigation charge? Cite the cause, inspection evidence, supply restriction, and corrective actions.” | Reject the pass-through fee because the supplier-maintained `TC-4` connection was reassembled with a pinched gasket and lacked a documented pressure-hold result. The scanned report identifies two major deficiencies and conditionally blocks new `BR-04` runs pending controls and verified CAPA. | Produce a compact evidence timeline or cause-and-effect graphic. |
| “Review the supplier invoices and associated evidence. Which disputed charges should Caldova reject, and what is the total avoided cost?” | Synthesize the supported decisions across the invoice and evidence packets, cite each decision, and calculate the total only from retrieved supported amounts. | Generate a bar chart of disputed and approved amounts by supplier. |

#### Verified KB 1 status (agent version 3, toolbox version 4)

- The live Search index contains exactly the intended 25 KB 1 document titles and no sourcing, policy, or map documents.
- All four headline questions return grounded answers with inline document and page citations where page metadata is available.
- The temperature, yield, BluePeak, and aggregate prompts each produce the planned Code Interpreter visual.
- Multilingual retrieval returns the Spanish certificate facts, and multimodal/OCR retrieval returns facts from the scanned GMP inspection report.
- The four-case `builtin.response_completeness` evaluation completed with passing scores of 5, 4, 5, and 5. The yield case's only noted omission was the exact 87.8% figure in that evaluation response; a direct validation prompt returned it correctly.
- Raw hosted responses currently contain inline citation text but no machine-readable citation annotations (`annotations` is empty).

#### KB 2 ACL design and questions

Use the procurement story because bids and evaluations have a natural
confidentiality model. Store the documents in an ADLS Gen2 account with
hierarchical namespace enabled, assign POSIX-like file or directory ACLs through
Microsoft Entra groups, and use the Azure AI Search ADLS Gen2 indexer to ingest
the permission metadata. At query time, pass the caller's token through
`x-ms-query-source-authorization` so Azure AI Search trims results against the
synchronized ACL metadata.

| Principal | Intended access |
|---|---|
| Procurement evaluation team | Policy, RFP, all three responses, all agreements, evidence map, amendment, and purchase order |
| Finance or executive approver | Policy, RFP, evaluation evidence, agreements, amendment, and purchase order; bidder responses only if explicitly granted |
| Annterra representative | RFP, Annterra response, and Annterra agreement |
| Kristos representative | RFP, Kristos response, Kristos agreement, and any awarded documents intentionally shared with Kristos |
| Sabyn representative | RFP, Sabyn response, and Sabyn agreement |

Run the same prompt as at least two principals:

> Compare the bidders for `RFP-CAL-OSD-2026-01`. Which supplier should be
> selected, what are the key tradeoffs, and what evidence supports the answer?
> Create a weighted-score chart.

The procurement evaluator should retrieve all three bids and support the
Kristos award. A supplier principal must not retrieve competitors' responses
or confidential evaluation evidence; the agent should state that it cannot
make a complete comparison from the accessible evidence rather than infer the
missing bids. Code Interpreter must operate only on the ACL-filtered retrieved
facts.

#### KB 3 PostgreSQL and MCP design

The remote database should contain current, structured facts that change more
often than signed sourcing documents. Use the existing Fabric supplier
identifiers `V001`-`V007`; do not create a crosswalk to Waypoint identifiers
`sup-001`-`sup-015`.

Recommended relational tables:

| Table | Example fields | Why it belongs remotely |
|---|---|---|
| `suppliers` | supplier ID, legal name, status, risk tier, primary site | Current supplier master data |
| `supplier_sites` | site, country, capabilities, regulatory status | Filterable current operating footprint |
| `performance_periods` | supplier ID, month, on-time delivery, right-first-time quality, lead time, defect rate | Time-series metrics for comparisons and charts |
| `capacity_snapshots` | supplier ID, as-of date, available and firm monthly capacity, utilization | Frequently changing capacity facts |
| `audits` | supplier ID, audit date, rating, open critical or major actions | Current qualification and risk status |
| `quality_events` | supplier ID, event date, severity, status, affected product | Operational risk signals |
| `subcontractors` | supplier ID, subcontractor, service, approval status | Current approval and dependency checks |

The MCP server should expose narrow read-only tools such as
`get_supplier_profile`, `get_supplier_performance`, `get_supplier_capacity`,
`get_open_quality_actions`, and `compare_suppliers`. It should not expose
arbitrary SQL.

Headline query:

> Compare Kristos's commitments in the `CALD-201` RFP response, agreement
> amendment, and purchase order with its current performance, capacity, audit
> actions, and approved subcontractors. What has changed or needs attention?
> Graph the relevant trends.

The Supplier Intelligence Agent should label document claims and MCP claims,
include the relational data's as-of date, and use Code Interpreter to chart
current trends. Expected differences must be locked after the PostgreSQL seed
data is created.

#### Headline demo sequence

1. **Scenario 1:** Use the Invoice Investigation Agent to answer the BluePeak
   question across ordinary PDFs and the image-only inspection report, then
   generate an evidence timeline.
2. **Scenario 2:** Use the Sourcing Review Agent to ask the same bidder-
   comparison question as a procurement evaluator and a supplier principal.
3. **Scenario 3:** Use the Supplier Intelligence Agent to combine the signed
   Kristos documents with current PostgreSQL facts through MCP and graph the
   trends.

Every answer shown on stage should include citations. For cross-source answers,
the speaker should explicitly identify whether each material claim came from
the index or MCP. Mention Work IQ as a slide-only extension to the architecture.

### Act one: Retrieval patterns for AI agents

#### Scenario 1: Invoice Investigation Agent (4 minutes)

**Purpose**

Introduce an agentic knowledge base through an invoice investigation and show
how one index can ground a decision across many document types.

**Key points**

- Position Foundry IQ as the knowledge layer for the agent.
- Cover indexers, built-in and custom skills, vectorization, and hybrid search.
- Include multilingual and multimodal content.
- Add Code Interpreter for calculations and visual responses.
- Identify where CU fits in the retrieval choices; exact treatment is TBD.

**Suggested graphics/demo beats**

1. Show the completed 25-document invoice-evidence index.
2. Ask whether BluePeak's $111,000 charge should be paid.
3. Show citations spanning the invoice, deviation evidence, and image-only GMP inspection report.
4. Have Code Interpreter create an evidence timeline or cause-and-effect graphic.
5. Mention the Spanish Meridian certificate as the multilingual backup example.

**Transition**

Move from broad document retrieval to a separate sourcing knowledge base where
the same query produces different evidence based on the user's access.

#### Scenario 2: Sourcing Review Agent with ACLs (4 minutes)

**Purpose**

Demonstrate ACL indexing and security trimming over confidential supplier bids,
agreements, evaluations, and award documents.

**Key points**

- Use a separate knowledge base sourced from ACL-protected ADLS Gen2 content.
- Ask the same bidder-comparison question as two principals.
- Show that inaccessible competitor evidence is neither cited nor inferred.
- Add Code Interpreter only after retrieval so charts reflect the caller's accessible evidence.

**Suggested graphics/demo beats**

1. Ask the bidder-comparison question as a procurement evaluator.
2. Show the complete comparison, Kristos recommendation, citations, and weighted-score chart.
3. Ask the identical question as a supplier representative.
4. Show the reduced evidence set and the agent's explicit statement that it cannot make a complete comparison.

**Transition**

Keep the secure sourcing documents and add current structured supplier facts
through a remote MCP source.

### Act two: Enterprise knowledge retrieval

#### Scenario 3: Supplier Intelligence Agent with MCP (3 minutes)

**Purpose**

Extend the sourcing architecture with a PostgreSQL-backed MCP server and show
why frequently changing relational facts are federated rather than indexed.

**Key points**

- Reuse the ACL-protected sourcing corpus.
- Add read-only MCP tools over current supplier master, performance, capacity, audit, quality, and subcontractor data.
- Distinguish signed document claims from current MCP claims and include as-of dates.
- Use Code Interpreter to graph current performance trends against documented commitments.

**Suggested graphics/demo beats**

1. Start with Kristos's commitments in the indexed response, amendment, and purchase order.
2. Add current Kristos facts from PostgreSQL through narrow MCP tools.
3. Ask what changed or needs attention and show source labels and as-of dates.
4. Have Code Interpreter graph the relevant performance, capacity, or quality trend.

**Transition**

Shift from retrieval capabilities to the architecture decisions required to productionize them.

#### Productionizing: Architecture decisions (2 minutes)

**Purpose**

Summarize the enterprise architecture choices that shape a production deployment.

**Key points**

- Discuss multi-tenant environments.
- Discuss network isolation.
- Compare serverless and dedicated deployment models.
- Tie deployment choices back to the indexed, federated, and enterprise retrieval patterns already shown.
- Mention Work IQ as a permission-aware Microsoft 365 grounding option that was intentionally kept out of the live demo.

**Suggested slide beats**

1. Show a compact architecture-decision view covering indexing, ACLs, federation, multi-tenancy, and network isolation.
2. Compare serverless and dedicated deployments.
3. Place Work IQ on the broader enterprise-source map as a slide-only option.
4. Keep selection criteria, topology, limits, and recommendations as TBD unless they are confirmed in the session materials.

**Transition**

Move to the final takeaways, next learning resources, and evaluation request.

### Act three: Key takeaways

#### Next steps and evaluation (2 minutes)

**Purpose**

Reinforce the retrieval choices covered in the talk and direct attendees to confirmed follow-up resources before requesting an evaluation.

**Key points**

- Recap agentic knowledge bases.
- Recap built-in skills, custom skills, indexers, and CU.
- Recap ACL preservation for indexed content.
- Recap MCP servers, Microsoft IQ integrations, and federation versus indexing.
- Recap multi-tenancy, network isolation, and serverless versus dedicated deployments.
- Point to additional sessions, learning, and resources; exact items and links are TBD.
- Ask attendees to complete an evaluation; exact slide details are TBD.

**Suggested slide beats**

1. Show one concise takeaway for each retrieval and production theme.
2. Show confirmed additional sessions, learning, and resources; content and links are TBD.
3. End on the evaluation slide and ask attendees to complete one; wording and mechanism are TBD.

**Transition**

End the session at 15:00.

## Preparation checklist

- [ ] Confirm the speaker for Scenario 1. **TBD**
- [ ] Confirm the speaker for Scenario 2. **TBD**
- [ ] Confirm the speaker for Scenario 3. **TBD**
- [ ] Confirm the speaker for Productionizing. **TBD**
- [ ] Confirm the speaker for Next Steps and the Evaluation Slide. **TBD**
- [x] Build the Invoice Investigation Agent with KB 1 and Code Interpreter.
- [ ] Build the Sourcing Review Agent with KB 2, ACL-aware retrieval, and Code Interpreter.
- [ ] Build the Supplier Intelligence Agent with KB 3, read-only PostgreSQL MCP tools, and Code Interpreter.
- [ ] Create the Productionizing architecture-decision slides. Exact diagrams and decision details: **TBD**
- [x] Define the three knowledge-base boundaries, agents, tools, and headline questions.
- [x] Generate KB 1's Spanish certificate and scanned GMP inspection report, bringing the corpus from 23 to 25 PDFs.
- [x] Upload KB 1's 25 target PDFs without uploading JSON, HTML, templates, or image assets.
- [x] Configure and validate hybrid, multilingual, OCR, and multimodal retrieval for the KB 1 questions.
- [x] Generate KB 2's 11 policy, procurement-chain, and evidence-map PDFs.
- [ ] Upload KB 2's 11 PDFs to ADLS Gen2 and apply the evaluator, approver, and supplier ACL model through Microsoft Entra groups.
- [ ] Configure the ADLS Gen2 indexer, permission-filter index field, ACL metadata synchronization, and caller-token query enforcement using the applicable preview API.
- [ ] Validate the bidder-comparison query as a procurement evaluator and at least one supplier principal.
- [ ] Seed PostgreSQL with current `V001`-`V007` supplier master, performance, capacity, audit, quality-event, and subcontractor data.
- [ ] Implement and validate the narrow read-only MCP tools for KB 3.
- [ ] Lock the expected Kristos differences and graph after the PostgreSQL seed data is final.
- [ ] Add a slide-only comparison of indexed ADLS Gen2, MCP federation, and Work IQ.
- [ ] Confirm the multi-tenant and network-isolation architecture details. **TBD**
- [ ] Confirm the serverless and dedicated deployment comparison details. **TBD**
- [ ] Confirm all demo environments, accounts, permissions, data, connectivity, and prerequisites. **TBD**
- [ ] Confirm additional sessions, learning resources, and resource links. **TBD**
- [ ] Confirm the evaluation slide wording, link or mechanism, and display requirements. **TBD**
- [ ] Rehearse to the segment limits: 4, 4, 3, 2, and 2 minutes.
- [ ] Verify that the complete run of show ends at exactly 15 minutes.

## Open technical issues

### Azure AI Search SDK support for Content Understanding

- Tracking issue: [Azure SDK for Python #48555](https://github.com/Azure/azure-sdk-for-python/issues/48555)
- The project uses `azure-search-documents==12.1.0b1`, the latest released preview SDK as of August 12, 2026. The next listed preview, `12.1.0b2`, is unreleased.
- The SDK defaults to the `2026-05-01-preview` Search API and supports semantic Content Understanding chunking, but its typed `ContentUnderstandingSkill` model does not expose the `modelName` and `modelDeployment` properties required to generate descriptions for embedded images, charts, and diagrams.
- Stage 1 must therefore create or update the affected skillset through the SDK client's authenticated `send_request` method using a `2026-05-01-preview` REST payload. Other supported Search resources can continue to use typed SDK models.
- Recheck the SDK when `12.1.0b2` or a newer version is released. Replace the REST payload with typed models once both properties are supported and the serialized request has been verified.
