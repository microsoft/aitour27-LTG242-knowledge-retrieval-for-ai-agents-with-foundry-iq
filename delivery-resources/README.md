# Delivery resources

Presenter, re-delivery, and train-the-trainer materials for this session.

## Core materials

| Item | Link | Notes |
| --- | --- | --- |
| Delivery deck | Pending | A public URL is required before publication |
| Session recording | Not available | Optional URL when available |
| Attendee landing page | [Session README](../README.md) | Public starting point |

## Delivery checklist

- Review the session README
- Open the deck when its public URL is available
- Review the presenter guidance when it is available
- Complete the [infrastructure setup](../infra/README.md)
- Validate all three demo agents before presenting

## Session preparation

- Review the attendee entry point from the root README.
- Review the delivery deck when its public URL is available.
- Create or select an azd environment for the session deployment.
- Configure the MCP API key and both sourcing-review Entra group IDs.
- Run `azd up` and complete the demo validation below.

## Run of show

Pending.

## Demo reproducibility

This session uses three hosted agents deployed by `azd up`:

- Invoice Investigation Agent retrieves evidence from the indexed invoice corpus.
- Sourcing Review Agent applies caller-specific ACL filtering.
- Supplier Intelligence Agent combines indexed evidence with the PostgreSQL MCP
  knowledge source.

Before presenting, invoke each agent with the prompt planned for the session.
For the sourcing-review demo, use the member-group account and confirm that the
agent cites shared and Summit Dose evidence without revealing Aster Ridge or
Atlas Regional evidence.

## Setup notes

Follow the [infrastructure deployment guide](../infra/README.md) for prerequisites,
required azd environment values, deployment, validation, and troubleshooting.
Tenant-specific group IDs and the MCP API key must remain in the selected azd
environment and must not be committed.

## Support

Content owner or contact: [Pamela Fox](https://github.com/pamelafox)
