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

