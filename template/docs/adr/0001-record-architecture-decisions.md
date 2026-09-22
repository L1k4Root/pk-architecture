# 0001. Record architecture decisions

- Status: accepted
- Date: 2026-09-22
- Deciders: platform team

## Context

Architecture decisions are made continuously: in pull requests, meetings and chat threads. Months later,
nobody remembers why PostgreSQL was chosen over Redis for idempotency keys, or whether a constraint still
applies. New team members either repeat old debates or are afraid to change anything.

## Decision

We will record every architecturally significant decision as an Architecture Decision Record (ADR) in
`docs/adr/`. We use the lightweight format in `0000-template.md`, create ADRs with `archkit adr new`,
and review them in pull requests like code. `archkit lint` runs in CI.

A decision is architecturally significant if it is hard to reverse, affects several components, or
changes a quality attribute (reliability, security, performance, operability).

## Consequences

- The reasoning behind the architecture survives team changes.
- Superseding a decision is explicit (`Status: superseded by [NNNN](…)`); old ADRs are never deleted.
- Writing an ADR takes 15–30 minutes. That is cheap compared to re-deciding.
- CI fails on malformed ADRs or a stale index, so the record stays trustworthy.

## Alternatives considered

- **A wiki page per decision** — not versioned with the code; drifts and gets lost.
- **Only pull request descriptions** — hard to find, no status, no supersession.
