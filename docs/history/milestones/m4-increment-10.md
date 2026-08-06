# M4 Increment 10 — Structured Local Security and Failure Auditing

## Authorized scope

- one strict public `LocalAuditEvent` contract;
- local-only immutable event files below `.forge/local/audit-events/`;
- stable classification of handled CLI failures from FORGE exit codes;
- project, optional initiative, configured-owner, operation, severity, and tool-version metadata;
- SHA-256 detail fingerprints without raw error text or command arguments;
- best-effort recording that never replaces the original CLI result;
- atomic UUID-named writes without shared append state;
- deterministic filtered `forge audit list` and exact `forge audit show`;
- tamper, unexpected-entry, non-file, oversized-record, and symlink refusal;
- `forge doctor` inventory validation and count reporting; and
- complete separation from governed journal, workflow state, archives, and acceptance authority.

## Explicit exclusions

OpenTelemetry, network exporters, success telemetry, command-argument capture, raw diagnostic
storage, automated retention or deletion, incident recovery, live process control, executable pack
providers, provider APIs, automatic verification or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0043](../adr/ADR-0043-structured-local-audit-events.md) records the privacy-minimizing event
contract, local persistence boundary, classification, best-effort failure semantics, inspection,
and non-authority decisions.

[Security Policy](../../SECURITY.md), [Contracts](../contracts.md),
[Persistence](../persistence.md), and [Git Policy](../git-policy.md) document the threat model,
public schema, storage, and tracking boundaries.

## Test evidence

Focused tests cover a real traversal refusal, stable classification and severity, exact displayed-
detail digesting, absence of raw details, journal neutrality, filtering, list/show presentation,
doctor validation, immutable storage, tamper detection, and failure-to-record isolation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 278 tests were exercised: 272 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, refused an unsafe
  traversal with security exit 40, listed and showed the sanitized event, and passed doctor; and
- the installed wheel exported all 50 schemas, including `local-audit-event.schema.json`.

## Stop point

Stop after structured local security and failure auditing. The cumulative adversarial M4 security
suite, exit-criteria audit, built-wheel acceptance, and milestone closeout remain a separate final
M4 increment.
