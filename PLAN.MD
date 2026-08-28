# LTG242 talk plan

## Outline transcription

**FY27 AI Tour | Tech Frontier Lightning Talk | LTG242**

- **Conversation:** Amplify your intelligence
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

Also discuss: MCP servers, Microsoft IQs, multi-tenant environments, and
serverless versus dedicated deployments.

### Session authors

- Pamela Fox


#### Act one: Retrieval patterns for AI agents

**Scenario 1 (Graphics/Demo): Invoice Investigation Agent**

- **Time:** 4 min
- Use Foundry IQ knowledge retrieval and Code Interpreter over the Caldova
  invoice-evidence index.
- Show cloud-based ingestion, multimodal extraction, hybrid search, and
  citations and traces from an evidence-heavy invoice question.

**Scenario 2 (Graphics/Demo): Sourcing Review Agent with ACLs**

- **Time:** 4 min
- Use ACL-protected sourcing documents in ADLS Gen2.
- Show the complete indexed corpus administratively, then show caller-specific
  security trimming for the signed-in user and explain how ACLs preserve
  document-level access controls during retrieval.

**Scenario 3 (Graphics/Demo): Supplier Intelligence Agent with MCP**

- **Time:** 3 min
- Combine the session document search index with current supplier data through
  a remote PostgreSQL MCP server.
- Show retrieval planning, merged results, source labels, and the Meridian
  cross-source question.

**Productionizing (Slides): Architecture decisions**

- **Time:** 2 min
- Multi-tenancy.
- Serverless vs dedicated deployments.

#### Act three: Key takeaways

**Next Steps: Additional Sessions, Learning, Resource**

- **Time:** 2 min

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

Select PDF groups from `sample-data/corpora.json` and index the committed files
under `sample-data/pdfs/`, not the JSON source records, HTML previews, templates,
or image assets in the upstream sample-data repository. This keeps the demo
representative of enterprise document ingestion and prevents the knowledge base
from answering OCR, multilingual, or diagram questions from easier structured
surrogates.

#### Knowledge bases and agents

| Configuration | Indexed content | Security or additional source | Corresponding agent | Agent tools | Demo purpose |
|---|---|---|---|---|---|
| **KB 1: Invoice evidence** | Complete: 25 PDFs comprising 15 invoices, 2 temperature reports, 6 operational reports, 1 Spanish certificate, and 1 scanned GMP inspection report. | None | **Invoice Investigation Agent** | Knowledge retrieval and Code Interpreter | Answer evidence-heavy invoice questions across searchable, multilingual, and scanned documents; calculate exposure and generate charts |
| **KB 2: Confidential sourcing** | Generated: 12 PDFs comprising 9 procurement-chain documents and 3 policy or diagram documents. | ADLS Gen2 POSIX-like ACL metadata enforced with the caller's Microsoft Entra token | **Sourcing Review Agent** | ACL-aware knowledge retrieval and Code Interpreter | Show that the full corpus remains indexed while the signed-in user retrieves only authorized evidence |
| **KB 3: Supplier intelligence** | The session document index used by KB 1. | PostgreSQL through a custom MCP server | **Supplier Intelligence Agent** | Knowledge retrieval, MCP, and Code Interpreter | Combine indexed evidence with current structured supplier facts |

KB 3 keeps the indexed document corpus and live relational data as separate
sources. This makes the federation story easy to explain: retrieve signed
document evidence from the index, then retrieve current structured facts through
MCP without copying them into the index. ACL retrieval remains the separate KB 2
scenario.

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
| “The certificate of analysis for lot `LOT-MD-1026-A` says every test passed. How narrow were those passes?” Restrict to tests with an upper limit and no lower limit, and exclude results reported as “less than” a value. | Retrieve all 33 numbered tests from the Spanish certificate, translate the names to English, and rank the 19 usable tests by result as a percentage of limit. Hausner ratio is closest to failing at 96.30% of its 1.35 limit, leaving 3.70% margin, followed by angle of repose at 86.50% and particle size D90 at 78.89%. | Markdown table of the ten closest to failing, worst first. No image, so it renders in the Foundry playground. |

#### Verified KB 1 status (agent version 3, toolbox version 5)

- The live Search index contains exactly the intended 25 KB 1 document titles and no sourcing, policy, or map documents.
- All headline questions return grounded answers with inline document and page citations where page metadata is available.
- Code Interpreter runs and returns correct calculations, but generated images do not display in the Foundry playground. The model emits a markdown link to a sandbox path such as `/mnt/data/plot.png`, which the browser cannot load. Prefer prompts that end in a markdown table rather than a chart.
- Multilingual retrieval returns the Spanish certificate facts, and multimodal/OCR retrieval returns facts from the scanned GMP inspection report.
- The four-case `builtin.response_completeness` evaluation completed with passing scores of 5, 4, 5, and 5. The yield case's only noted omission was the exact 87.8% figure in that evaluation response; a direct validation prompt returned it correctly.
- Raw hosted responses currently contain inline citation text but no machine-readable citation annotations (`annotations` is empty).
- Semantic chunking uses `maximumLength` 2000 tokens. At 500 the certificate's analytical table split into four fragments and the agent reported missing rows; at 2000 the whole table is retrievable.
- `COA-MD-1026-A` was restructured upstream so the acceptance criteria occupy separate `LÍMITE INFERIOR`, `LÍMITE SUPERIOR`, and `UNIDAD` columns and the three qualitative tests sit in their own preceding table. All 33 rows index with no gaps or duplicates.
- The `gpt-5.4` deployment runs at capacity 200. At 50 the demo prompts hit the rate limit when run back to back.
- Use `scripts/debug_chunks.py` to inspect how a document chunked, including a side-by-side PDF and chunk viewer via `--html`.

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
| Aster Ridge representative | RFP, Aster Ridge response, and Aster Ridge agreement |
| Summit Dose representative | RFP, Summit Dose response, Summit Dose agreement, and any awarded documents intentionally shared with Summit Dose |
| Atlas Regional representative | RFP, Atlas Regional response, and Atlas Regional agreement |

Run the same prompt through two views:

> Can you review the bids for `RFP-CAL-OSD-2026-01` and recommend a supplier?

The administrative Search view should show that all 12 documents are indexed.
The signed-in user, acting as a Summit Dose representative, must not retrieve
competitors' responses or confidential evaluation evidence; the agent should
state that it cannot make a complete comparison from the accessible evidence
rather than infer the missing bids. Code Interpreter must operate only on the
ACL-filtered retrieved facts.

The demo uses one signed-in user because the session owner cannot create or
manage additional tenant users. It therefore demonstrates corpus completeness
and caller-specific trimming, not a live comparison between multiple user
accounts.

#### KB 3 PostgreSQL and MCP design

The remote database contains current, structured facts about medicinal products,
active substances, marketing authorizations, and manufacturers. The deployed MCP
server exposes four narrow, read-only search tools: `search_products`,
`search_substances`, `search_authorizations`, and `search_manufacturers`. It does
not expose arbitrary SQL.

Headline query:

> Which Caldova product uses the active substance in Meridian API Works' invoiced
> `AUR-API-7` lot? Summarize the lot and Meridian's current manufacturer profile.

Validation queries:

| Query | Expected grounded response | Required knowledge sources |
|---|---|---|
| “What's the dosage form, strength, and route of administration for Caldovex?” | Tablet, 50 mg, and oral. | PostgreSQL MCP |
| “Which Caldova product uses the active substance in Meridian API Works' invoiced `AUR-API-7` lot? Summarize the lot and Meridian's current manufacturer profile.” | Label the invoice and CoA mapping of `AUR-API-7` to Caldovexine (`SUB-001`), lot `LOT-MD-1026-A`, and the 7,200 kg released quantity as indexed document claims. Label the mapping from `SUB-001` to Caldovex (`CALD-201`) and Meridian's current API-manufacturing profile and substance associations as MCP claims. | Supplier-specific indexed knowledge source over the KB 1 PDFs and PostgreSQL MCP |

The Supplier Intelligence Agent should label document claims and MCP claims.

#### Headline demo sequence

1. **Scenario 1:** Use the Invoice Investigation Agent to answer the temperature
  excursion question across the temperature report and supporting evidence,
  then show the citations and tool traces.
2. **Scenario 2:** Ask the Sourcing Review Agent the bidder-comparison question
  as the signed-in restricted user, then show in the administrative Search view
  that the inaccessible documents exist in the complete sourcing corpus.
3. **Scenario 3:** Use the Supplier Intelligence Agent to combine Meridian's
  indexed invoice and certificate evidence with current manufacturer and
  substance relationships through MCP.

Every answer shown on stage should include citations. For cross-source answers,
the speaker should explicitly identify whether each material claim came from
the index or MCP. Mention Work IQ as a slide-only extension to the architecture.

### Demo recording script

Record each demo as a separate clip. Start from a clean conversation, keep the
browser zoom and window size consistent, and pause briefly after opening each
activity or citation panel so it remains readable in the recording. Keep a
capture of each validated result as a backup for the live presentation.

#### Recording 1: Invoice Investigation Agent (4 minutes)

##### 0:00-0:35 - Establish the agent and corpus

From the repository root, get the agent details and playground link with:

```bash
azd ai agent show invoice-investigation-agent
```

On screen: Open `invoice-investigation-agent` in the Foundry playground and
show its Foundry IQ and Code Interpreter tools.

Say:

> Foundry IQ is the knowledge layer for this Invoice Investigation Agent. Its
> index contains 25 PDFs: invoices, operational reports, a Spanish certificate,
> and a scanned inspection report. The agent retrieves grounded evidence first,
> then uses Code Interpreter when the evidence requires calculation.

##### 0:35-0:50 - Submit the question

```text
For lot LOT-MD-1026-A, how close were the passing tests to their upper limits? Calculate each test's upper-limit utilization and remaining margin and return the ten closest to their limits.
```

##### 0:50-2:45 - Review the grounded answer

On screen: Expand the tool activity, then show the Markdown table and inline
certificate citations.

Expected result: The agent retrieves all 33 tests, identifies 19 usable tests,
and ranks the ten closest to their upper limit. Hausner ratio leads at 96.30%
of its 1.35 limit, leaving a 3.70% margin; angle of repose follows at 86.50%,
then particle size D90 at 78.89%.

Say:

> This is an English question over a Spanish certificate. Foundry IQ retrieves
> the semantically chunked certificate, and Code Interpreter performs the row
> filtering and ranking over grounded values. The response stays readable as a
> Markdown table and cites the source document.

##### 2:45-4:00 - Explain the retrieval path and transition

Say:

> The ingestion path combines Content Understanding, multilingual embeddings,
> vector and keyword retrieval, semantic ranking, and page metadata. The
> important design choice is that calculation happens after retrieval and only
> over retrieved facts. Now let's move from broad document retrieval to evidence
> that changes with the caller's access.

Fallback: Use a validated capture of the complete table, tool activity, and
citations if the response is slow or incomplete. Do not request a chart;
generated image artifacts do not render in the Foundry playground.

#### Recording 2: Sourcing Review Agent with ACLs (4 minutes)

**Pre-recording gate:** Do not record this as a successful ACL demo until the
administrative Search Explorer view shows all 12 documents and the signed-in
member-group user retrieves only shared and Summit Dose evidence. The result
must explicitly report unavailable competitor evidence and must not reveal or
infer Aster Ridge or Atlas Regional response content.

##### 0:00-0:20 - Submit the restricted-user question

On screen: Open the
[Sourcing Review Agent playground](https://ai.azure.com/nextgen/r/eogHKHDTSdCt3kJQcWz9lA,rg-pf-ltg242,,ai-account-uqu2yu2cnxuys,ai-project-pf-ltg242/build/agents/sourcing-review-agent/build?version=2)
while signed in as the configured member-group user, then submit:

```text
Can you review the bids for RFP-CAL-OSD-2026-01 and recommend a supplier?
```

##### 0:20-2:15 - Review the security-trimmed result

On screen: Show the answer, citations, and retrieved document titles.

Expected result after the pre-recording gate passes: Only shared and Summit
Dose evidence appears. The agent states that it cannot complete a three-bidder
comparison because competing responses or confidential evaluation evidence are
unavailable. It does not invent scores or recommend a winner from missing bids.

Say:

> The agent cannot make a complete comparison because this signed-in user
> cannot retrieve the competing bids or confidential evaluation evidence. Now
> let's confirm that those documents exist in the indexed corpus.

##### 2:15-3:10 - Reveal the complete administrative corpus

On screen: Open the
[Search service](https://portal.azure.com/#view/Microsoft_Azure_Search/Index.ReactView/id/%2Fsubscriptions%2F7a880728-70d3-49d0-adde-4250716cfd94%2FresourceGroups%2Frg-pf-ltg242%2Fproviders%2FMicrosoft.Search%2FsearchServices%2Fsearch-uqu2yu2cnxuys%23sourcing-documents/location/West%20US/sku/standard).
In Search Explorer, query `sourcing-documents` administratively and show the 12
indexed document titles, including the competitor responses and evaluation
documents that the signed-in agent could not retrieve.

Say:

> The administrative view confirms that all 12 sourcing documents are indexed.
> The documents the agent reported as inaccessible are present here. Search
> Explorer is showing the complete corpus with administrative access; it does
> not represent what the signed-in agent was allowed to retrieve. Foundry IQ
> applied the caller's delegated identity at retrieval time, so the agent saw
> only the ACL-filtered evidence available to that user.

##### 3:10-4:00 - Transition

Say:

> ACL-aware indexing is the right pattern for protected document evidence. For
> current relational facts, we can keep the data remote and let Foundry IQ
> retrieve from it when needed.

Fallback: If the pre-recording gate does not pass, replace the live result with
the ACL architecture slide and say, “This tenant's end-to-end ACL result is
still awaiting validation, so I'm showing the configured security path rather
than claiming a live result.” After a successful validation, retain that
recording as the event-day fallback.

#### Recording 3: Supplier Intelligence Agent with MCP (3 minutes)

##### 0:00-0:35 - Establish the federated knowledge base

On screen: Open `supplier-intelligence-agent` and show its separate
`supplier-session-documents` and `postgres-ontology-suppliers` knowledge
sources.

Say:

> This knowledge base keeps signed documents in the search index and current
> structured facts in the Caldova suppliers database. Foundry IQ can plan
> retrieval across both without copying relational data into the document
> index.

##### 0:35-0:50 - Submit the cross-source question

```text
Which Caldova product uses the active substance in Meridian API Works' invoiced AUR-API-7 lot? Summarize the lot and Meridian's current manufacturer profile. Clearly distinguish indexed document claims from Caldova suppliers database claims and cite each material claim.
```

##### 0:50-2:25 - Review the merged result

On screen: Show retrieval planning, generated searches, selected sources,
citations, and the **Merged results** view.

Expected result: Indexed documents establish that `AUR-API-7` is Caldovexine
(`SUB-001`), lot `LOT-MD-1026-A`, with 7,200 kg released. Database records map
`SUB-001` to Caldovex (`CALD-201`) and identify Meridian's current API
manufacturer profile and substance associations.

Say:

> The invoice and certificate establish the lot identity, substance, and
> released quantity. The Caldova suppliers database establishes the
> substance-to-product relationship and Meridian's current manufacturer
> record. The answer labels which source supports each part of the join.

##### 2:25-3:00 - Explain the observed score and transition

On screen: Point to the activity-log field only if it is present in this
response.

Say:

> In this specific retrieval response, an included MCP reference has a
> `rerankerScore` of zero, while indexed references have nonzero values. That is
> only an observed value in this response; it is not a general claim about
> whether or how remote results are reranked. I'll call the combined view
> “Merged results.”

Fallback: Use a capture from the validated Meridian run. If the remote source
is unavailable and no capture is ready, show the federation architecture and
do not claim a live cross-source result.

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
- Show where Content Understanding fits in the ingestion and retrieval choices.

**Suggested graphics/demo beats**

1. Show the Invoice Investigation Agent with Foundry IQ knowledge retrieval and
  Code Interpreter as its two tools.
2. Demonstrate the temperature-excursion question and show that the agent cites
  the evidence, calls the tools needed for the answer, and exposes those calls
  in traces.
3. Explain the cloud ingestion path: Azure Blob Storage, Azure Content
  Understanding, Azure OpenAI embeddings, and the Foundry IQ search index.
4. Show multimodal extraction from the temperature report, including HTML table
  output, image or chart descriptions, JSON chart data, metadata, and semantic
  chunk boundaries.
5. Show hybrid retrieval for the yield-and-powder-flow question, contrasting
  keyword results, vector results, RRF fusion, and reranking.

**Transition**

Move from broad document retrieval to a separate sourcing knowledge base where
the same query produces different evidence based on the user's access.

#### Scenario 2: Sourcing Review Agent with ACLs (4 minutes)

**Purpose**

Demonstrate ACL indexing and security trimming over confidential supplier bids,
agreements, evaluations, and award documents.

**Key points**

- Use a separate knowledge base sourced from ACL-protected ADLS Gen2 content.
- Contrast the complete administrative corpus with the signed-in user's
  ACL-trimmed retrieval result.
- Show that inaccessible competitor evidence is neither cited nor inferred.
- Add Code Interpreter only after retrieval so charts reflect the caller's accessible evidence.

**Suggested graphics/demo beats**

1. Ask the bidder-comparison question through the Sourcing Review Agent as the
  signed-in Summit Dose representative.
2. Show the reduced evidence set and the agent's explicit statement that it
  cannot make a complete comparison.
3. Open the administrative Search view and show that all 12 source documents,
  including the inaccessible competitor evidence, are present in the index.

**Presentation status**

The deck includes ACL-specific ingestion and query-time security-trimming
slides showing ADLS Gen2 document ACLs, Microsoft Entra group access, and the
caller token passed to retrieval.

**Transition**

Keep the secure sourcing documents and add current structured supplier facts
through a remote MCP source.

### Act two: Enterprise knowledge retrieval

#### Scenario 3: Supplier Intelligence Agent with MCP (3 minutes)

**Purpose**

Extend the sourcing architecture with a PostgreSQL-backed MCP server and show
why frequently changing relational facts are federated rather than indexed.

**Key points**

- Use the session document search index together with a remote supplier database
  through MCP.
- Show that retrieval planning can generate multiple searches and select the
  sources needed for a cross-source question.
- Distinguish indexed document claims from current supplier-database claims.

**Suggested graphics/demo beats**

1. Show the Supplier Intelligence Agent with the session document search index
  and remote supplier database as separate knowledge sources.
2. Explain the knowledge-base flow: retrieval planning, generated search
  queries, selected sources, merged results, and the activity log.
3. Demonstrate the Meridian `AUR-API-7` question and show the indexed invoice
  and certificate evidence alongside the current supplier-database relationship.
4. Show the activity log and merged results, including filenames, snippets,
  source labels, and document reranker scores.
5. Label the combined output **Merged results**, not **Reranked results**. The
  observed MCP reference score is not documented well enough to present as
  comparable to the indexed-document scores.

The Scenario 3 slide intentionally uses “Merged results” for the combined
output and “Reranked results” for the post-ranking view because those labels are
clearer for the audience. The slide shows three selected results from the full
retrieval response.

**Transition**

Shift from retrieval capabilities to the architecture decisions required to productionize them.

#### Productionizing: Architecture decisions (2 minutes)

**Purpose**

Summarize the enterprise architecture choices that shape a production deployment.

**Key points**

- Discuss multi-tenant environments.
- Compare serverless and dedicated deployment models.
- Tie deployment choices back to the indexed, federated, and enterprise retrieval patterns already shown.
- Mention Work IQ as a permission-aware Microsoft 365 grounding option that was intentionally kept out of the live demo.

**Suggested slide beats**

1. Show a compact architecture-decision view covering indexing, ACLs, federation, and multi-tenancy.
2. Compare serverless and dedicated deployments.
3. Place Work IQ on the broader enterprise-source map as a slide-only option.

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
- Recap multi-tenancy and serverless versus dedicated deployments.
- Point to the confirmed learning and resource links on the final slide.
- Ask attendees to complete the event evaluation.

**Suggested slide beats**

1. Show one concise takeaway for each retrieval and production theme.
2. Show confirmed learning and resource links.
3. End on the evaluation slide and ask attendees to complete the event evaluation.

**Transition**

End the session at 15:00.

## Preparation checklist

- [x] Build the Invoice Investigation Agent with KB 1 and Code Interpreter.
- [x] Build the Sourcing Review Agent with KB 2, ACL-aware retrieval, and Code Interpreter.
- [x] Build the Supplier Intelligence Agent with KB 3, read-only PostgreSQL MCP tools, and Code Interpreter.
- [x] Create the Productionizing architecture-decision slides.
- [x] Define the three knowledge-base boundaries, agents, tools, and headline questions.
- [x] Generate KB 1's Spanish certificate and scanned GMP inspection report, bringing the corpus from 23 to 25 PDFs.
- [x] Upload KB 1's 25 target PDFs without uploading JSON, HTML, templates, or image assets.
- [x] Configure and validate hybrid, multilingual, OCR, and multimodal retrieval for the KB 1 questions.
- [x] Generate KB 2's 12 procurement, policy, and diagram PDFs.
- [x] Implement upload of KB 2's 12 PDFs to ADLS Gen2 with member and non-member Microsoft Entra group ACLs.
- [x] Configure the ADLS Gen2 indexer, permission-filter index field, ACL metadata synchronization, and caller-token query enforcement using the applicable preview API.
- [ ] Validate that the administrative Search view contains all 12 documents and the signed-in Sourcing Review Agent retrieves only the member group's authorized evidence.
- [x] Implement and validate the narrow read-only MCP tools for KB 3.
- [x] Validate the Meridian `AUR-API-7` cross-source question and source labeling.
- [x] Add a slide-only comparison of indexed ADLS Gen2, MCP federation, and Work IQ.
- [x] Confirm the multi-tenant architecture details.
- [x] Confirm the serverless and dedicated deployment comparison details.
- [ ] Confirm all demo environments, accounts, permissions, data, connectivity, and prerequisites. **TBD**
- [x] Confirm the final learning and resource links.
- [x] Add the event evaluation request to the final slide.
- [ ] Rehearse to the segment limits: 4, 4, 3, 2, and 2 minutes.
- [ ] Verify that the complete run of show ends at exactly 15 minutes.

## Open technical issues

### Azure AI Search SDK support for Content Understanding

- Tracking issue: [Azure SDK for Python #48555](https://github.com/Azure/azure-sdk-for-python/issues/48555)
- The project uses `azure-search-documents==12.1.0b1`, the latest released preview SDK as of August 12, 2026. The next listed preview, `12.1.0b2`, is unreleased.
- The SDK defaults to the `2026-05-01-preview` Search API and supports semantic Content Understanding chunking, but its typed `ContentUnderstandingSkill` model does not expose the `modelName` and `modelDeployment` properties required to generate descriptions for embedded images, charts, and diagrams.
- Stage 1 must therefore create or update the affected skillset through the SDK client's authenticated `send_request` method using a `2026-05-01-preview` REST payload. Other supported Search resources can continue to use typed SDK models.
- Recheck the SDK when `12.1.0b2` or a newer version is released. Replace the REST payload with typed models once both properties are supported and the serialized request has been verified.

### Code Interpreter charts do not display in the Foundry playground

- Code Interpreter generates chart images correctly, but the playground does not render them. The model returns a markdown image link to a sandbox path, for example `![Temperature series](/mnt/data/ship_vc_1026_temp_plot.png)`, and the browser cannot load a file from the tool's isolated execution environment.
- The documented retrieval path is to read the generated file back through the SDK, which is not available from the playground UI. See [Code Interpreter for Foundry agents](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter?pivots=python).
- The playground also has no file-attachment affordance, so prompts cannot supply a CSV for the tool to chart.
- Consequence for the demo: any question whose payoff is a rendered chart will appear to fail on stage. Prefer questions that end in a markdown table, a ranking, or an explicit calculation. The certificate-of-analysis spec-margin question was written for this reason.
- Code Interpreter is also not invoked for small calculations, since the model does the arithmetic directly. It engages when the task involves enough rows to be worth parsing, such as the 30-row analytical results table.
- Recheck whether the playground gains artifact rendering or file attachment. If it does, restore the temperature, yield, BluePeak, and aggregate-invoice questions to their charted form.

## Appendix: verified material that did not fit the 15-minute run of show

Findings below are measured against the live KB 1 index. They are kept for
follow-up content, questions from the audience, and any longer version of this
session. None of them has a slide.

### Cross-lingual retrieval measured directly

Three English queries, none containing a Spanish word, run against the index as
keyword-only and vector-only. Keyword search never returns the Spanish
certificate; vector search returns it first every time.

| English query | Keyword-only top 3 | Vector-only top 3 |
|---|---|---|
| `powder flowability test results` | GMP-INS-BPB-2027-01, INV-SUP-005, INV-SUP-011 | COA-MD-1026-A (all three chunks) |
| `heavy metal contamination limits` | DEV-BPB-1026, INV-SUP-009, GMP-INS-BPB-2027-01 | COA-MD-1026-A, COA-MD-1026-A, DEV-BPB-1026 |
| `batch release certificate of analysis` | INV-SUP-005, INV-SUP-004, INV-SUP-011 | COA-MD-1026-A, COA-MD-1026-A, YLD-MAW-1026 |

The third row is the most useful illustration. Keyword search returns three
invoices because their line items contain the English phrase "certificate of
analysis"; the certificate itself stays invisible to it.

Cross-lingual matching comes from `text-embedding-3-large` being multilingual,
not from Content Understanding. The hybrid-search slide already carries this
point implicitly, because reranked result 4 is the Spanish certificate.

### Content Understanding output that the extraction slide omits

- The chart-to-Chart.js conversion is derived from the rendered image, not read
  from the file. The PDF's text layer contains no JSON keys and no data values,
  and decompressing every stream in the file (347,742 bytes) finds none either.
- The extracted series is an estimate and is not stable between runs. The same
  unchanged `TL-VCL-1026.pdf` produced `[5.1, 5.0, 4.9, 5.3, 8.2, 8.6, 5.4]` on
  one indexing run and `[5.1, 5.0, 4.9, 5.2, 8.2, 7.0, 5.4]` on another. Summary
  values taken from real text, such as the 10.7 C peak and the 2 hr 30 min
  excursion, are exact. Do not build a demo answer on an interpolated point.
- The plotted series is a 7-point summary of the chart. The logger recorded 37
  points at 30-minute intervals.
- `ChartFormat.ChartJs` is a documented enum in `Azure.AI.ContentUnderstanding`,
  described as "Represent charts as Chart.js code blocks," so the format is a
  deliberate contract rather than a coincidence.
- The analyzer defaults also extract formulas as LaTeX, hyperlinks, and PDF
  annotations with authors and comments. Nothing in this corpus exercises them.
- The Search skill exposes only `extractionOptions`, `modelName`,
  `modelDeployment`, and `chunkingProperties`. Chart and table formats are not
  settable from the skillset.
- `GMP-INS-BPB-2027-01.pdf`, the scanned inspection report, is the richest
  multimodal example in the corpus: 4 chunks, 13 generated figure descriptions,
  6 tables, and 27 page markers.

### Retrieval-quality observations

- Semantic reranking is a model and does not uniformly improve results. On one
  phrasing of the hybrid-slide query it demoted a relevant document and promoted
  an unrelated invoice. Re-run the exact demo query before the deck is final
  rather than assuming a previously captured ordering still holds.
- Small changes in query wording move the rankings noticeably. Substituting the
  product name for the invoice identifier removed the failure-and-recovery
  pattern that makes the hybrid slide readable.
- `scripts/debug_chunks.py` renders a side-by-side PDF and chunk view with
  `--html` and is the fastest way to re-check any of this after reindexing.
