# Writing architecture documentation that stays true

Most architecture documents start out accurate and go stale within a few months. This guide and the
`archkit` linter aim at documentation that is **small, versioned with the code, reviewed in pull
requests and checked in CI**.

## Three tools, three jobs

| Tool | Answers | Changes |
|---|---|---|
| [arc42](https://arc42.org) sections (`docs/architecture/`) | *How is the system built and why does it work this way?* | When the architecture changes |
| [C4](https://c4model.com) diagrams (Mermaid, inside arc42) | *What talks to what?* at four zoom levels | With the building blocks |
| ADRs (`docs/adr/`) | *Why did we decide X, and what did it cost?* | Never edited, only superseded |

## C4 in practice

Draw only the levels that help. Most systems need the first two.

| Level | Diagram | arc42 section | Audience |
|---|---|---|---|
| 1 | System context: the system as one box, with its users and external systems | 3. Context and scope | everyone |
| 2 | Containers: deployable units (services, databases, brokers) and protocols | 5. Building block view | engineers, operations |
| 3 | Components inside one container | 5. (only where it is complex) | the team that owns it |
| 4 | Code | not drawn; the code is the diagram | – |

Rules that keep diagrams useful:

- **Every arrow has a label** that says what flows and how (`charges card, HTTPS/JSON`).
- **Every box names its technology** at level 2 (`payments, Go`, `PostgreSQL 18`).
- **Diagrams live in Mermaid inside Markdown**, not as PNG files, so a pull request that changes the
  architecture changes the diagram in the same diff. `archkit lint` rejects unknown diagram types.
- **Runtime views** (section 6) use sequence diagrams for the 2–4 most important or most risky flows,
  **including the failure path**.

## When to write an ADR

Write one when a decision is **hard to reverse**, **affects more than one component**, or **changes a
quality attribute** (reliability, security, performance, cost, operability). For example:

- choosing PostgreSQL over Redis to store idempotency keys;
- signing tokens with EdDSA instead of RS256;
- using a monorepo instead of repositories per service.

Skip it for choices that are local and cheap to change, such as a library's internal helper.

Writing good ADRs:

- **Context is neutral.** Describe the forces, not the answer.
- **The decision is one sentence** you could put on a slide: "We will …".
- **Consequences include the costs.** An ADR without downsides is a sales pitch.
- **Alternatives say why they lost**, not only that they existed.
- **Never edit an accepted ADR's decision.** Write a new one and set the old one to
  `superseded by [NNNN](NNNN-title.md)`. History is the point.

## Review checklist

- [ ] Does the change alter a building block, a protocol or a quality scenario? Then update sections
      5, 6 or 10 in the same pull request.
- [ ] Is there a decision with trade-offs? Then add an ADR (`archkit adr new "…"`).
- [ ] Is each quality scenario in section 10 backed by a test or an alert? Link it.
- [ ] Does `archkit lint docs` pass? (CI enforces it.)
