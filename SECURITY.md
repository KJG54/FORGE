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

