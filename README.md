# FORGE

**Framework for Orchestrated Reasoning, Governance, and Execution**

FORGE is a local-first governance framework for human-directed, AI-assisted work. It embeds a
versioned initiative in an ordinary repository and records how work is scoped, authorized,
claimed, checked, evidenced, accepted, paused, recovered, closed, or abandoned.

FORGE governs work. It is not the worker, an autonomous agent runtime, a hosted project manager,
or a same-user security sandbox.

> **Unpublished local candidate:** Milestones 1 through 6 are complete and owner-accepted. Local
> Production-v1 increments L1 through L8 are integrated, and L9 automated candidate validation is
> complete. Native-app owner observations and extended owner testing remain separate. The
> candidate is not tagged, publicly distributed, or finally accepted as Production v1.

The current v1 definition is the
[Local Production-v1 candidate](release/local-production-v1/README.md): a personal, local-first
workflow for direct Codex and Claude Code workspace use. The abandoned public-M7 plan remains
historical evidence and creates no current publication requirement or authority.

## Workspace agents start here

If you are an AI workspace agent (Claude Code, Codex, or similar) helping an owner work with
FORGE, run `forge agent protocol` first — before `forge init`, `forge create`, or any project
work — read it in full, and follow it. It requires no initialized repository. Begin with first
contact and state detection, then conduct the document-first interview with the six coverage
headings. Do not run `forge init`, `forge pack trust`, or `forge create` until the owner has
confirmed your coverage playback; those and the other owner-gate commands belong to the owner.

## What using FORGE looks like

You describe the project to your workspace agent in ordinary language. The agent reads the
protocol, interviews you about what you want to build, and plays back a proposal. You confirm the
consequential decisions — initialization, pack trust, initiative creation, acceptance — as
explicitly displayed commands; the agent handles the routine mechanics. FORGE records everything
in an append-only, hash-chained journal inside your repository, and every mutation returns a
concise receipt you can spot-check.

The one boundary that everything else protects:

```text
worker claim -> check -> evidence -> FORGE verification -> owner acceptance
```

These stay distinct facts. Green tests never become acceptance by implication, and nothing the
agent does speaks with your authority.

## Install

FORGE requires Python 3.12 or newer. Install once per machine (or per container):

```console
pip install git+https://github.com/KJG54/FORGE.git@main
```

`pipx install` works the same way if you prefer isolated CLI installs. Verify with
`forge --version`. See [installation and supported environments](docs/installation.md) for
exact-wheel installs and details.

## Start your first project

Read [Your first FORGE project](docs/quickstart.md) — a start-to-finish walkthrough covering:

- where a project should live so its records survive (your machine, or a private remote for
  cloud workspaces);
- what the agent's interview asks and why;
- the owner gates — what runs only on your word; and
- how to read receipts, come back after a gap, and finish or archive an initiative.

## Capabilities at a glance

- Owner-authorized initiatives with immutable pack and workflow locks, manual runs, and
  restart-safe status and next-action reporting.
- Immutable artifact revisions with exact-byte preservation, drift detection, worker claims,
  structured checks, evidence packets, and record-backed verification.
- Owner-only acceptance and revocation, append-only decisions, scope amendments, deviations,
  overrides, risk acceptances, and deterministic staleness propagation.
- Canonical transaction receipts, a repository-independent workspace-agent protocol, managed
  `CLAUDE.md`/`AGENTS.md` context, a safe local scratchpad, and `forge recap` warm resume.
- Honest authority/operator provenance for direct agent sessions, plus provider-neutral handoffs
  and two-phase untrusted result import.
- Bundled declarative `software-basic` and `research-basic` packs; data-only pack trust that never
  grants execution.
- Atomic closure and abandonment, hardened immutable archives, successor initiatives with exact
  predecessor references, and archive-derived successor briefs.
- Journal hash chaining, deterministic replay, idempotent retries, snapshot recovery, stale-lock
  remediation, backups, and schema migrations.

The complete capability record, with per-increment evidence, lives in the
[development record](docs/history/README.md).

## Documentation

Start at the [documentation index](docs/README.md), which routes by audience. Frequently used:

- [Your first FORGE project](docs/quickstart.md)
- [User guide](docs/user-guide/README.md)
- [Canonical glossary](docs/glossary.md)
- [Constitution](docs/constitution.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Security model](docs/security.md)
- [Software and research example repositories](examples/README.md)

## Development setup

```console
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"  # Windows
```

On macOS or Linux, use `.venv/bin/python` instead. Then run:

```console
python -m tools.quality_gate
pytest
python -m build
forge --help
```

## Development record

FORGE's own development history — architecture decision records, milestone evidence, and session
handoffs — is preserved under [docs/history/](docs/history/README.md). Release evidence for the
current candidate lives in [release/local-production-v1/](release/local-production-v1/README.md),
and changes are summarized in the [changelog](CHANGELOG.md).

- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
