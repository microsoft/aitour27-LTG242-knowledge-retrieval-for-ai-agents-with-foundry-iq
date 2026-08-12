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

### Timing

| Act | Segment | Time | Cumulative time |
|---|---|---:|---:|
| Act one | Scenario 1: Internal Knowledge assistant | 4 min | 4 min |
| Act one | Scenario 2: Customer Support Agent | 4 min | 8 min |
| Act two | Scenario 3: Enterprise assistant | 3 min | 11 min |
| Act two | Productionizing: Architecture decisions | 2 min | 13 min |
| Act three | Key takeaways, next steps, and evaluation | 2 min | 15 min |
|  | **Total** | **15 min** | **15 min** |

### Act one: Retrieval patterns for AI agents

#### Scenario 1: Internal Knowledge assistant (4 minutes)

**Purpose**

Introduce an agentic knowledge base through an internal knowledge assistant and show how indexed enterprise content can retain its access controls.

**Key points**

- Position Foundry IQ as the knowledge layer for the assistant.
- Cover indexers, built-in and custom skills, vectorization, and hybrid search.
- Include multilingual and multimodal content.
- Emphasize indexing SharePoint documents with ACLs preserved.
- Identify where CU fits in the retrieval choices; exact treatment is TBD.

**Suggested graphics/demo beats**

1. Show the Internal Knowledge assistant scenario.
2. Show SharePoint documents being indexed into Foundry IQ.
3. Show the ingestion and retrieval elements named in the outline: indexers, skills, vectorization, and hybrid search.
4. Show that document ACLs remain part of the indexed-content design.
5. Include multilingual and multimodal retrieval in the graphic or demo; exact assets and interactions are TBD.

**Transition**

Move from an indexed internal source to a customer-support scenario that combines the knowledge base with a remote source through MCP.

#### Scenario 2: Customer Support Agent (4 minutes)

**Purpose**

Demonstrate how an agent can combine indexed knowledge with an MCP remote source, then frame the choice between federation and indexing.

**Key points**

- Introduce the Customer Support Agent scenario.
- Combine Foundry IQ retrieval with an MCP remote source.
- Compare federation with indexing without prescribing a choice that is not in the source outline.
- Connect the comparison to the session theme of unifying indexed and remote sources.

**Suggested graphics/demo beats**

1. Show the Customer Support Agent using indexed content.
2. Add an MCP remote source to the retrieval path.
3. Contrast the federation path with the indexing path in one graphic or demo sequence.
4. Keep the exact MCP server, remote source, data, and query flow as TBD.

**Transition**

Expand from one remote source to enterprise knowledge retrieval with Work IQ and a direct contrast to indexed SharePoint content.

### Act two: Enterprise knowledge retrieval

#### Scenario 3: Enterprise assistant (3 minutes)

**Purpose**

Extend the retrieval architecture to an enterprise assistant by adding Work IQ and clarifying how that approach differs from indexed SharePoint.

**Key points**

- Introduce the Enterprise assistant scenario.
- Add Work IQ as the next knowledge integration.
- Contrast Work IQ with indexed SharePoint.
- Relate the contrast to Microsoft IQ integrations and enterprise knowledge retrieval.

**Suggested graphics/demo beats**

1. Reuse or extend the retrieval architecture from Act one.
2. Add Work IQ to the Enterprise assistant flow.
3. Place Work IQ and indexed SharePoint side by side for a direct contrast.
4. Keep the exact Microsoft IQ integration, tenant setup, content, and query as TBD.

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

**Suggested slide beats**

1. Show a compact architecture-decision view covering multi-tenancy and network isolation.
2. Compare serverless and dedicated deployments.
3. Keep selection criteria, topology, limits, and recommendations as TBD unless they are confirmed in the session materials.

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
- [ ] Create or select the Internal Knowledge assistant graphic/demo. Exact asset and interaction: **TBD**
- [ ] Create or select the Customer Support Agent graphic/demo. Exact asset and interaction: **TBD**
- [ ] Create or select the Enterprise assistant graphic/demo. Exact asset and interaction: **TBD**
- [ ] Create the Productionizing architecture-decision slides. Exact diagrams and decision details: **TBD**
- [ ] Define the SharePoint content, indexing configuration, skills, vectorization, hybrid-search query, multilingual example, and multimodal example. **TBD**
- [ ] Define how ACL preservation will be shown. **TBD**
- [ ] Define the MCP server and remote source used in Scenario 2. **TBD**
- [ ] Define how federation versus indexing will be visualized or demonstrated. **TBD**
- [ ] Define the Work IQ integration and indexed SharePoint comparison used in Scenario 3. **TBD**
- [ ] Confirm the multi-tenant and network-isolation architecture details. **TBD**
- [ ] Confirm the serverless and dedicated deployment comparison details. **TBD**
- [ ] Confirm all demo environments, accounts, permissions, data, connectivity, and prerequisites. **TBD**
- [ ] Confirm additional sessions, learning resources, and resource links. **TBD**
- [ ] Confirm the evaluation slide wording, link or mechanism, and display requirements. **TBD**
- [ ] Rehearse to the segment limits: 4, 4, 3, 2, and 2 minutes.
- [ ] Verify that the complete run of show ends at exactly 15 minutes.

## Open decisions

### Speaker assignments

- Scenario 1 speaker: **TBD**
- Scenario 2 speaker: **TBD**
- Scenario 3 speaker: **TBD**
- Productionizing speaker: **TBD**
- Next Steps and Evaluation Slide speaker: **TBD**
- Customer speaker participation: **TBD** (`__ #` in the source outline)

### Graphics and demo assets

- Internal Knowledge assistant graphic/demo: **TBD**
- Customer Support Agent graphic/demo: **TBD**
- Enterprise assistant graphic/demo: **TBD**
- Productionizing architecture-decision slides: **TBD**
- Evaluation slide: **TBD**

### Environment and prerequisites

- Demo environment and tenant configuration: **TBD**
- SharePoint source content and ACL setup: **TBD**
- Foundry IQ configuration: **TBD**
- MCP server and remote-source configuration: **TBD**
- Work IQ configuration: **TBD**
- Multi-tenant and network-isolation setup: **TBD**
- Serverless and dedicated deployment setup: **TBD**

### Resources and links

- Additional sessions: **TBD**
- Learning resources: **TBD**
- Other resources: **TBD**
- Public delivery deck URL: **TBD**

### Evaluation slide details

- Evaluation wording: **TBD**
- Evaluation link or mechanism: **TBD**
- Evaluation display requirements: **TBD**