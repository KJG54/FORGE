# Security Policy

## Supported versions

FORGE is pre-alpha and has no supported production release. Security fixes are currently made on
the active development branch. A supported-version policy will be published before v1.0.0.

## Reporting a vulnerability

Do not open a public issue containing exploit details, secrets, or affected private repositories.
Until a private security-reporting channel is configured, contact the project owner directly and
include the affected revision, reproduction, impact, and any suggested mitigation. The public
repository must not claim a response-time service level before maintainers formally adopt one.

## Threat-model boundary

FORGE aims to provide tamper evidence, auditability, supported-command authorization, explicit
trust, path controls, and safe-default imports. It does not protect against a malicious process
running with the repository owner's operating-system permissions and is not a substitute for OS,
container, or multi-user isolation.

Secret screening is heuristic defense in depth. Known secret paths and recognizable credential
patterns may be blocked or warned on, but FORGE cannot guarantee detection of every secret. Owners
must review content before importing, governing, sharing, or accepting it.

Approved local validators start with a fresh allowlisted environment rather than inheriting the
caller's environment. Credential-like environment channels are refused, and raw bounded stdout and
stderr remain Git-ignored below `.forge/local/validator-runs/`; normal CLI output never renders
those bytes. A validator can still read any file available to its operating-system identity and
may write sensitive project content to its local captures. Owners should inspect and remove local
captures according to their repository security policy and use external sandboxing for hostile
code.

Scope amendments accept only requirement IDs from the locked workflow and current logical artifact
IDs. FORGE derives invalidation and refuses an amendment while an affected governed run is active.
This protects supported-command integrity; it does not prevent a same-user process from modifying
repository files outside FORGE or make amended scope safe by itself. Owner review and renewed
claims, checks, evidence, verification, and acceptance remain required.
