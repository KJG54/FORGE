# Contributing to FORGE

FORGE is pre-alpha and milestone-gated. Discuss material changes before investing substantial
work, and keep each contribution within an accepted milestone.

## Development

Use Python 3.12 or newer and install `.[dev]`. Before submitting a change, run:

```console
ruff check .
pyright
pytest
python -m build
```

Public interfaces must be typed. Business rules belong in core services, not CLI rendering or
data contracts. Filesystem and security-sensitive behavior requires negative and cross-platform
tests. Every practical bug fix should include a regression test.

## Governance changes

Changes to authority, trust, persistence, state machines, archives, compatibility, the threat
model, pack or adapter boundaries, or public CLI semantics require an ADR. Never rewrite an
accepted governance record silently; supersede it.

Do not add deferred infrastructure, dependencies without rationale, provider logic to the core,
or claims that exceed the documented security model.

## Contributions and licensing

By contributing, you agree that your contribution is licensed under Apache-2.0. Follow the
[Code of Conduct](CODE_OF_CONDUCT.md) and report vulnerabilities through the private process in
[SECURITY.md](SECURITY.md), not a public issue.

