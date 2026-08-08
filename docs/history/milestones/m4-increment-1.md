# M4 Increment 1 — Declarative Local Validator Capabilities

## Authorized scope

- strict tracked `LocalValidatorDefinition` contracts in project configuration;
- domain-neutral local validator registry entries under the `validator.` namespace;
- exact read-only inspection of executable, ordered arguments, working directory, timeout,
  expected outputs, environment access, and side-effect risk;
- rejection of command strings, malformed environment permissions, unsafe paths, missing or
  irregular executables, and Windows batch-command shims;
- reuse of preview-first owner capability approval and immutable revocation;
- definition-digest binding for every validator approval scope; and
- explicit preservation of the data-pack versus executable-authority boundary.

## Explicit exclusions

Validator process execution, validator runs, automatic `CheckResult` creation, output
interpretation, evidence generation, verification, owner acceptance, executable pack providers,
background services, and later M4 security/cancellation hardening are not implemented.

## Design evidence

[ADR-0034](../adr/ADR-0034-declarative-local-validator-capabilities.md) records the tracked
declaration, non-executing inspection, exact approval, profile-drift, no-shell-string, and pack
separation decisions. [Trusted Local Validator Declarations](../validators.md) documents the
operator-facing configuration and approval workflow.

## Test evidence

Focused tests cover strict declaration shape, separate executable and argument vector, bounded
environment names, missing executables, rejected batch shims, complete CLI inspection,
non-mutating approval preview, exact owner approval, project-scope invalidation after argument
drift, absence of run/check side effects, and confirmation that a valid local trusted-data pack
cannot register validator capabilities merely by declaring an ID.

Final Windows validation recorded:

- 226 tests passed with 6 expected Windows symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- Hatchling produced both the source distribution and wheel; and
- a clean target installed-wheel smoke passed version, initialization, strict configuration
  validation, and deterministic export of 48 schemas including
  `local-validator-definition.schema.json`.

## Stop point

Stop after declarative validator registration, inspection, and exact approval are implemented and
validated. Do not execute validators or create check results until a later M4 increment explicitly
authorizes the supervised execution boundary.
