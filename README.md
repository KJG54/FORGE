# FORGE

**Framework for Orchestrated Reasoning, Governance, and Execution**

FORGE is a local-first governance framework for human-directed, AI-assisted work. It embeds a
versioned initiative in an ordinary repository and records how work is scoped, authorized,
claimed, checked, evidenced, accepted, paused, recovered, closed, or abandoned.

FORGE governs work. It is not the worker, an autonomous agent runtime, a hosted project manager,
or a same-user security sandbox.

> **Pre-alpha foundation:** The name, distribution name, public marks, contracts, and CLI remain
> provisional. Milestone 1 is accepted and Milestone 2 implementation is in progress; this is not
> a public production release.

## Current capabilities

M1 Increments 1 through 8 provide strict versioned data contracts, deterministic JSON Schema export,
project configuration validation, owner identity bootstrap, repository discovery, safe path
resolution, non-destructive `forge init`, ordered event journals, deterministic replay, atomic
snapshot replacement, explicit journal/snapshot mismatch detection, safe declarative pack loading,
immutable workflow locks, owner-authorized initiative creation, manual runs, and restart-safe status
and next-action reporting. Increment 4 adds immutable artifact revisions, conservative exact-byte
preservation, working-copy drift reporting, worker claims, manual structured checks, evidence
packets, dependency references, and record-backed verification transitions. Increment 5 adds
owner-only acceptance and revocation, append-only decisions and supersession, deterministic stale
propagation after revision or revocation, and an explicit rework path for invalidated steps.
Increment 6 adds provider-neutral manual handoffs and a two-phase staged result-import pipeline with
bounded schemas, path and symlink controls, secret screening, previews, explicit collision actions,
and single-event artifact registration.

Increment 7 adds owner-only successful closure, complete-step and current-acceptance gates,
exact-byte archive manifests, preserved-object verification, read-only archived status and history,
and terminal immutability through supported commands.

Increment 8 adds read-only repository diagnostics, event-derived run inspection and cancellation,
selectable Standard/Guided presentation, a restarted-process end-to-end software acceptance
walkthrough, and a data-only synthetic community-research workflow proving the core is not
software-specific. The complete evidence and limitations are recorded in the
[M1 evidence report](docs/milestones/m1-report.md).

M2 Increment 1 adds canonical event serialization, SHA-256 previous-hash chaining, snapshot
journal-head binding, and explicit read-only compatibility for complete M1 journals. Migration,
recovery, and the remaining M2 hardening are not yet implemented.

M2 Increment 2 adds repository-wide cross-process locking for supported mutations, inspectable
owner metadata, live contention refusal, and non-destructive stale-lock diagnostics.

M2 Increment 3 adds optional or generated mutation idempotency keys, journal-bound request
identity, completion receipts tied to exact event hashes, duplicate-free successful retry, and
conservative interruption diagnostics. Explicit recovery remains later M2 work.

The M1 archive is explicitly preliminary. Later M2 increments remain responsible for explicit
recovery, atomic archive hardening, stale-lock remediation, pause/resume, migration, abandonment,
and successor initiatives.

Initialize an ordinary project repository with:

```console
forge init --owner-name "Repository Owner"
forge config validate
forge pack validate software-basic
forge create "Objective" --scope "Bounded scope" --trust-pack-data \
  --idempotency-key create-objective
forge status
forge artifact add requirements.md --role requirements --title "Requirements"
forge schema export --output schemas
```

## Development setup

Python 3.12 or newer is required.

```console
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"  # Windows
```

On macOS or Linux, use `.venv/bin/python` instead. Then run:

```console
ruff check .
pyright
pytest
python -m build
forge --help
```

## Governing documents

- [Constitution](docs/constitution.md)
- [Canonical glossary](docs/glossary.md)
- [Architecture decisions](docs/adr/README.md)
- [Dependency rationale](docs/dependencies.md)
- [Versioned contracts](docs/contracts.md)
- [Journal and materialized state](docs/persistence.md)
- [Packs, initiatives, and manual runs](docs/workflows.md)
- [Artifacts, claims, checks, and evidence](docs/artifacts-and-evidence.md)
- [Acceptance, decisions, and invalidation](docs/acceptance-and-invalidation.md)
- [Manual handoffs and safe result import](docs/handoffs-and-imports.md)
- [Preliminary closure and archive inspection](docs/closure-and-archives.md)
- [Idempotent mutation retries](docs/idempotency.md)
- [Repository initialization](docs/user-guide/initialization.md)
- [M1 internal execution increments](docs/milestones/m1-execution-increments.md)
- [M1 evidence report](docs/milestones/m1-report.md)
- [M2 Increment 1 integrity boundary](docs/milestones/m2-increment-1.md)
- [M2 Increment 2 locking boundary](docs/milestones/m2-increment-2.md)
- [M2 Increment 3 idempotency boundary](docs/milestones/m2-increment-3.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
