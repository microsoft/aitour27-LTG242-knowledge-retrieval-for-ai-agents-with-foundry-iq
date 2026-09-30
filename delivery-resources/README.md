# Delivery resources

Presenter, re-delivery, and train-the-trainer materials for this session.

## Core materials

| Item | Link | Notes |
| --- | --- | --- |
| Delivery deck | coming soon | Final presentation deck |
| Video recording | [LTG242 Video](https://aka.ms/aitour27/LTG242/youtube) | LTG242 video |
| Attendee landing page | [Session README](../README.md) | Public starting point |

## Delivery checklist

- Review the delivery deck.
- Deploy the demos.
- Rehearse the presentation and demos.

## Session preparation

Complete the [infrastructure setup](../infra/README.md), including the two
Microsoft Entra groups required by the ACL-aware demo. A complete `azd up`
deploys these hosted agents:

- `invoice-investigation-agent`
- `sourcing-review-agent`
- `supplier-intelligence-agent`

Get each agent's details and playground link from the repository root:

```bash
azd ai agent show invoice-investigation-agent
azd ai agent show sourcing-review-agent
azd ai agent show supplier-intelligence-agent
```

## Run of show

This schedule assumes the three prerecorded demos are played in full.
Together demos use 4:15, leaving 10:45 for the other 16 slides and transitions.

| Clock | Slide | Time | Delivery beat |
| --- | ---: | ---: | --- |
| Before start | 1 | - | Hold on the Microsoft AI Tour bumper. |
| 0:00-0:20 | 2 | 0:20 | Introduce the session and yourself. |
| 0:20-0:40 | 3 | 0:20 | Introduce Caldova and its knowledge spread across formats, systems, and permissions. |
| 0:40-1:05 | 4 | 0:25 | Position Foundry IQ around relevant, current, and authorized retrieval. |
| 1:05-1:25 | 5 | 0:20 | Introduce the Invoice Investigation Agent, Foundry IQ retrieval, and Code Interpreter. |
| 1:25-3:10 | 6 | 1:45 | Play the 1:38 Invoice Investigation demo and transition back to the deck. |
| 3:10-3:50 | 7 | 0:40 | Trace the cloud ingestion path from Blob Storage through extraction, embeddings, and indexing. |
| 3:50-4:35 | 8 | 0:45 | Highlight HTML tables, chart descriptions, OCR, metadata, and semantic chunking. |
| 4:35-5:20 | 9 | 0:45 | Explain keyword and vector retrieval, RRF fusion, and semantic reranking. |
| 5:20-5:45 | 10 | 0:25 | Introduce the Sourcing Review Agent and delegated user token. |
| 5:45-7:15 | 11 | 1:30 | Play the 1:25 Sourcing Review demo and transition back to the deck. |
| 7:15-7:55 | 12 | 0:40 | Show how ADLS Gen2 ACLs become indexed `group_ids` and `user_ids`. |
| 7:55-8:35 | 13 | 0:40 | Explain query-time security trimming and emphasize that unauthorized evidence never reaches the model. |
| 8:35-9:00 | 14 | 0:25 | Introduce multi-source retrieval across indexed PDFs and the remote supplier database. |
| 9:00-10:20 | 15 | 1:20 | Play the 1:12 Supplier Intelligence demo and transition back to the deck. |
| 10:20-11:10 | 16 | 0:50 | Explain retrieval planning: generated queries, selected sources, merged results, and activity log. |
| 11:10-11:50 | 17 | 0:40 | Position Work IQ and Fabric IQ as additional remote knowledge sources; point to BRK240. |
| 11:50-13:00 | 18 | 1:10 | Compare shared index, index-per-tenant, service-per-tenant, and hybrid isolation. |
| 13:00-14:10 | 19 | 1:10 | Compare serverless and dedicated pricing and workload fit. |
| 14:10-15:00 | 20 | 0:50 | Recap the three retrieval requirements and direct attendees to the resources. |


## Demo reproducibility

Run each demo with the prompt and validation criteria below before presenting.
The linked prerecorded demos are fallbacks for the live session and examples of
the expected delivery.

For rehearsals and live delivery:

- Open all three agent playgrounds.
- Start each demo from a clean conversation.
- Keep the browser size and zoom consistent.
- Confirm every answer includes citations. In the Supplier Intelligence demo,
  confirm the answer labels indexed-document and database claims separately.

### Demo 1: Invoice Investigation Agent

[Watch the prerecorded Invoice Investigation demo](https://youtu.be/O5SL-zm1wAo).

Prompt:

```text
For lot LOT-MD-1026-A, how close were the passing tests to their upper limits? Calculate each test's upper-limit utilization and remaining margin and return the ten closest to their limits.
```

#### Invoice Investigation transcript

**[00:00]** Here's the agent in the Foundry UI. We send a question about an
investigation report, asking which of the tests were close to the limits. It
starts making tool calls and calls to the LLM, and we can see lots of logs in
the right-hand sidebar with everything going over the network.

**[00:19]** Then we see the answer streaming back. It's quite a long answer
with a lot of citations and formatting. It's trying to comprehensively answer
our question, grounded in all of that data.

**[00:34]** We can scroll back up and look for the actual answer to our
question, which is this table with all the results, and find the test that was
closest to the limit. Then we can look at the citations for all this data and
the calculations.

**[00:50]** We can look at the original document and see that this is a PDF.
It's actually in Spanish, so the agent translated the result back to English
for us when it displayed everything. That's one nice thing that LLMs can do:
they're multilingual.

**[01:06]** Then we can look at traces. The traces show all the tool calls. The
first one is to the Foundry IQ knowledge base. We can see that it gets back the
data from that PDF as a rich HTML table in Spanish.

**[01:20]** Once we have that data, we call Code Interpreter. Code Interpreter
is sent all this data as Python, then it outputs a Python list and sends that
list back to the agent. That's ultimately what the agent displays in the
formatted table to give us a nice grounded answer.

### Demo 2: Sourcing Review Agent with ACLs

Do not present this as a successful ACL demo until the administrative Search
Explorer view contains all 12 documents and the signed-in member-group user
retrieves only shared and Summit Dose evidence.

[Watch the prerecorded Sourcing Review demo](https://youtu.be/wizsTHdG0kA).

Prompt:

```text
Can you review the bids for RFP-CAL-OSD-2026-01 and recommend a supplier?
```

#### Sourcing Review transcript

**[00:00]** We open the agent in the Foundry UI playground, and we're going to
ask a question that requires access to multiple documents. We put out an RFP
and asked for bids. Each of those bids is a document, but this user only has
access to some of those documents and some of those bids. We're asking it to
review all those bids, but we shouldn't be able to access all of them.

**[00:22]** In the answer that comes back, there's an analysis of which
documents this user does have access to. It basically says, "You do not have
access to all the underlying bid documents required to make this full
comparison." The agent is revealing that it tried, but we don't have access to
the documents, so it can't give a full answer. It explains what it would need
to make the full answer.

**[00:52]** It even says which documents are missing because those are
referenced in a document we do have access to. Why did this work?

**[01:01]** If we look at the Data Lake storage, we can see that those documents
exist there, but this user does not have the ACL for those documents. We can
also see in the Search index that those documents were indexed, but they
weren't associated with this user or the user's groups. Since they weren't
associated with the user's Entra ID or groups, the agent can't access them.

### Demo 3: Supplier Intelligence Agent with MCP

[Watch the prerecorded Supplier Intelligence demo](https://youtu.be/5yJ_raNJbxk).

Prompt:

```text
Which Caldova product uses the active substance in Meridian API Works' invoiced AUR-API-7 lot? Summarize the lot and Meridian's current manufacturer profile. Clearly distinguish indexed document claims from Caldova suppliers database claims and cite each material claim.
```

#### Supplier Intelligence transcript

**[00:00]** We've got the Supplier Intelligence Agent open in the Foundry UI
playground. This agent is connected to a knowledge base that has two knowledge
sources. One is documents, and the other is a remote MCP server for a PostgreSQL
database.

**[00:15]** We're going to ask a question that requires an answer from both the
documents, the invoices, and the database of Caldova medicine products.

**[00:30]** We get back an answer with citations both to PDFs and to the
PostgreSQL tool. We can look at the answer and the citations and see that it
found everything it needed to answer the question from the different sources.

**[00:48]** In the traces, we can see that the agent first made a call that used
the knowledge base, and the knowledge base sent that query only to the document
data store. Then it made another call, and the knowledge base decided to send
that query only to the PostgreSQL database.

**[01:05]** That's what the knowledge base can decide to do. It can send queries
to all sources, or it can send a query only to the relevant source. It depends
on the question.

## Setup notes

Open issue: The Code Interpreter tool in the invoice investigation agent can
generates chart files, but those images do not render in the
Foundry playground. Use the scripted Markdown-table prompt for the Invoice
Investigation demo rather than requesting a chart.

## Support

Content owner or contact: [Pamela Fox](https://github.com/pamelafox)
