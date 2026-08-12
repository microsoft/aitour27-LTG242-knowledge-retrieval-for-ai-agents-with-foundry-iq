## Before you're done

This repo has been created for your AI Tour 2027 session. Here's how to get it ready.

**Easiest path — use the agent (recommended):**

- Open GitHub Copilot Chat and say `help me initialize repo`. The agent will walk you through getting the README populated.
- When you're ready to publish, say `help me finalize repo`. The agent will clean up unused folders, validate everything, and remove this "Before you're done" section and other extra stuff that attendees don't need to see.
- Curious how it works? Read the [agent workflow](.github/AGENT-WORKFLOW.md).

**Doing it manually?**

Fill in the sections below yourself, then:

- Delete any placeholder folders you don't need (`data/`, `infra/`, etc.)
- Delete this "Before you're done" section
- Delete `.github/agents/`, `.github/tests/`, `.github/copilot-instructions.md`, and `.github/AGENT-WORKFLOW.md` — these are template tooling, not part of your published repo

**Folder conventions:**

- Attendee step-by-step guidance goes in `instructions/`. If you use MkDocs or a docs site instead, put it in `docs/` and link to it from this README.
- Reference material and background reading go in `docs/`.
- Presenter notes, deck link, recordings, and re-delivery materials go in `delivery-resources/`. Fill in [`delivery-resources/README.md`](delivery-resources/README.md).
- You can add a `.devcontainer/` folder if needed.

---

<a name="start-building"></a>

<p align="center">
<img src="img/banner-ai-tour-27.png" alt="Microsoft AI Tour 2027" width="100%"/>
</p>

# [Microsoft AI Tour 2027](https://aitour.microsoft.com)

## 🔥 LTG242: Knowledge retrieval for AI agents with Foundry IQ

### Session description

Discover how Foundry IQ connects knowledge across diverse data sources while
preserving access controls and maximizing retrieval quality. Explore
AI-optimized ingestion pipelines and knowledge architectures that unify indexed
and remote sources.

### 🚀 Getting started

#### In a guided session

Guided session steps are pending.

#### On your own

Self-paced session steps are pending.

### 🎯 Learning outcomes

By the end of this session, you will be able to:

- Explain agentic knowledge bases and choose when to use built-in skills,
  custom skills, indexers, and CU.
- Describe how to preserve data ACLs in indexed content.
- Explore MCP servers and Microsoft IQ integrations.

### 💻 Technologies used

- Foundry IQ
- Work IQ

### 📚 Continue your learning

Pick your next step based on your learning style:

| Resource | What you'll get |
|----------|-----------------|
| **[Microsoft Learn](https://learn.microsoft.com)** | Official documentation and guided learning paths on these topics |
| **[AI Tour 2027 Resource Center](https://aka.ms/aitour27-resource-center)** | Additional session repos and materials from AI Tour 2027 |
| **[Microsoft Foundry Community](https://aka.ms/MicrosoftFoundryDiscord-AITour27)** | Connect with other learners and experts in our Discord community |

### 🌟 Microsoft Learn MCP Server

<!-- Remove this section if the Microsoft Learn MCP Server is not relevant to the session. -->

The Microsoft Learn MCP Server gives your AI agent direct access to Microsoft's official documentation — grounded, up-to-date answers about the topics in this session.

**GitHub Copilot CLI** — Install with:

```shell
copilot plugin install microsoftdocs/mcp
```

**VS Code** — One-click install:  
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Microsoft_Learn_MCP-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=microsoft-learn&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Flearn.microsoft.com%2Fapi%2Fmcp%22%7D)

For more information, visit the [Learn MCP Server repo](https://aka.ms/learnmcp).

### 👥 Content owners

<table>
<tr>
    <td align="center"><a href="https://github.com/pamelafox">
        <img src="https://github.com/pamelafox.png" width="100px;" alt="Pamela Fox"/><br />
        <sub><b>Pamela Fox</b></sub></a><br />
            <a href="https://github.com/pamelafox" title="talk">📢</a>
    </td>
</tr></table>

### Deliver this session

Presenters and re-delivery partners can find the deck, recordings, presenter
notes, and delivery guidance in [`delivery-resources/`](delivery-resources/README.md).

### ⚖️ Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general). Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.

Any use of third-party trademarks or logos are subject to those third-party's policies.
