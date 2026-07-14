# FORGE

**Framework for Orchestrated Reasoning, Governance, and Execution**

FORGE is a local-first governance framework for human-directed, AI-assisted work. It embeds a
versioned initiative in an ordinary repository and records how work is scoped, authorized,
claimed, checked, evidenced, accepted, paused, recovered, closed, or abandoned.

FORGE governs work. It is not the worker, an autonomous agent runtime, a hosted project manager,
or a same-user security sandbox.

> **Pre-alpha foundation:** The name, distribution name, public marks, contracts, and CLI remain
> provisional. Milestone 1 is being delivered in bounded internal increments and is not a public
> production release.

## Current capabilities

M1 Increments 1 through 4 provide strict versioned data contracts, deterministic JSON Schema export,
project configuration validation, owner identity bootstrap, repository discovery, safe path
resolution, non-destructive `forge init`, ordered event journals, deterministic replay, atomic
snapshot replacement, explicit journal/snapshot mismatch detection, safe declarative pack loading,
immutable workflow locks, owner-authorized initiative creation, manual runs, and restart-safe status
and next-action reporting. Increment 4 adds immutable artifact revisions, conservative exact-byte
preservation, working-copy drift reporting, worker claims, manual structured checks, evidence
packets, dependency references, and record-backed verification transitions.

It deliberately does not yet implement owner acceptance or revocation, stale-record propagation,
handoffs, imports, or closure. Those behaviors belong to later M1 increments. M2 remains
responsible for event hash chains, recovery, concurrency, and interruption hardening.

Initialize an ordinary project repository with:

```console
forge init --owner-name "Repository Owner"
forge config validate
forge pack validate software-basic
forge create "Objective" --scope "Bounded scope" --trust-pack-data
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
- [Repository initialization](docs/user-guide/initialization.md)
- [M1 internal execution increments](docs/milestones/m1-execution-increments.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
