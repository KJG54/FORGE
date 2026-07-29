# Dependency Rationale

M0 uses the smallest dependency set mandated by the approved specification.

| Dependency | Requirement | Why the standard library is insufficient | Maintenance/platform note |
|---|---|---|---|
| Hatchling | Standards-based wheel and source builds | Python does not include a build backend | PyPA-maintained and cross-platform |
| Typer | Typed, discoverable CLI | `argparse` would require more presentation plumbing | Built on Click; isolate it in `cli/` |
| Pydantic v2 | Versioned validated contracts and JSON Schema | Dataclasses do not provide equivalent validation/schema export | Keep orchestration out of models |
| PyYAML | Declarative pack workflows | Python has no YAML parser | Use bounded safe loading; YAML remains untrusted input |
| pytest | Unit through acceptance testing | `unittest` lacks the selected fixture/plugin ergonomics | Test-only dependency |
| Ruff | Formatting-independent static linting | No equivalent standard tool | Test-only, single binary, cross-platform |
| Pyright | Public-interface type checking | Python does not ship a static type checker | Test-only; CI pins the declared range |
| build | Validate wheel and source distributions | Build front-end is not in the standard library | Test-only PyPA tooling |

New dependencies require an updated rationale and owner-visible milestone report.

## M6 release review

M6 Increment 5 adds a separate review of the exact declared dependency strings and the build,
runtime, and development closures installed in the observed environment. The machine-readable
policy, license allowlist, exact legacy-license overrides, advisory scan, and redacted secret scan
are documented in [`supply-chain-security-review.md`](supply-chain-security-review.md).

`pip-audit` and Gitleaks are release-review tools, not project runtime or development dependencies.
Their results are point-in-time evidence and must be repeated against the exact clean-wheel
environment and review commit at M6 closeout.
