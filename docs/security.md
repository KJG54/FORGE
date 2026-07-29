# Security Guide

This guide explains how to operate and review FORGE safely. The repository
[security policy](../SECURITY.md) defines vulnerability reporting and the supported-version
position.

## Threat model

FORGE provides supported-command authorization, tamper evidence, deterministic validation, path
controls, explicit trust, bounded imports, and auditable refusal. It does not protect a repository
from a malicious process running with the owner's operating-system permissions. FORGE is not a
hostile-code sandbox. It is also not a container, virtual machine, credential broker, or multi-user
authorization system.

Owner identity is governance attribution stored in repository configuration. It is not
cryptographic authentication. Protect the filesystem, Git credentials, signing keys, provider
credentials, and execution environment using operating-system and hosting controls.

## Data classification

Keep these out of governed artifacts and tracked state:

- credentials, tokens, passwords, private keys, and `.env` files;
- raw provider or validator stdout/stderr;
- local process identifiers, locks, and machine paths;
- temporary import or adapter staging;
- caches and local audit observations; and
- personal or regulated data that the project has not explicitly approved for governance.

Configured secret paths and recognizable credential patterns are screened, but detection is
heuristic. A clean screen does not prove content secret-free. Review bytes before registration,
import, acceptance, Git staging, or publication.

Machine-local material belongs below `.forge/local/`, which the hybrid Git policy ignores. If Git
already tracks such a path, inspect it for sensitive content before removing it from the index.

## Separate trust decisions

Do not collapse these boundaries:

- validating a pack proves structural conformance, not trust;
- trusting pack data authorizes exact declarative bytes, not execution;
- approving a capability authorizes one exact process profile, not its correctness;
- process success is a run outcome, not a worker claim;
- a passing check is not evidence or semantic truth;
- evidence is support with limitations, not verification;
- FORGE verification derives current record conditions, not owner judgment; and
- owner acceptance does not become milestone or release acceptance.

Pack changes, capability-profile drift, artifact revision, scope amendment, decision withdrawal,
or risk-acceptance revocation fail closed by invalidating the exact authority they affect.

## Executable workers and validators

Before approving local execution:

1. inspect the resolved executable, version, arguments, working directory, timeout, expected
   outputs, environment names, and side-effect class;
2. prefer a one-time approval;
3. remove credential-like environment channels;
4. use external isolation for code you do not trust with the owner's filesystem access;
5. inspect local captures under the project's security and retention policy; and
6. treat every returned file as untrusted until staged import and owner review.

FORGE uses separate argument vectors and disables shell execution in supported adapters and
validators. Packs cannot provide a local validator profile or approve it.

## Repository and Git controls

- Track `forge.yaml` and governed `.forge/` content.
- Ignore `.forge/local/`.
- Review `forge doctor` Git-policy errors before collaboration or closure.
- Do not hand-edit the journal, snapshot, locks, immutable records, preserved objects, or archives.
- Enable the optional clean-worktree close gate when repository review policy requires it.
- Back up hidden `.forge/` content with project files; a source-only backup is incomplete.
- Validate restored repositories and archives before relying on them.

Git history can add review, transport, and access controls. It cannot replace FORGE's validated
journal or make a tampered FORGE repository healthy.

## Imports and paths

FORGE rejects absolute paths, traversal, symbolic links, irregular files, managed-path targets,
configured secret paths, recognized credential content, inventory-limit violations, and
unresolved collisions. A preview does not apply files. Preserve failed staging only when its
diagnostic value outweighs its sensitivity, and delete it under an explicit local retention
policy.

Bounded context discovery uses filenames and metadata, not unregistered file content. It excludes
hidden, ignored, secret, dependency, build, oversized, and symbolic paths. Suggestions grant no
read, registration, execution, evidence, or acceptance authority.

## Incident response

If integrity or secret exposure is suspected:

1. stop mutation and external workers;
2. preserve the repository and relevant local captures using access-controlled storage;
3. record the exact revision, command, exit code, and observed condition without copying secrets
   into a public issue;
4. run read-only `forge doctor`, `forge status`, and appropriate history inspection;
5. use [troubleshooting](troubleshooting.md) to distinguish configuration, authorization,
   transition, integrity, conflict, security, and external-tool failures;
6. apply only the exact [recovery](recovery.md) procedure whose prerequisites are proven; and
7. report a vulnerability through the private path in [SECURITY.md](../SECURITY.md).

Do not delete a lock, truncate a journal, rewrite a record, edit a snapshot to match expectations,
or republish exposed credentials. Credential revocation and rotation occur in the credential
provider, outside FORGE.

## Reviewer checklist

- No critical governance, integrity, import, path, or secret defect is open.
- Every executable has explicit, current, exact-profile owner approval.
- Pack trust and executable trust remain separate.
- Raw local captures and credentials are absent from tracked and governed content.
- Recovery, migration, archival, backup, abandonment, and successor procedures are rehearsed on
  disposable or controlled copies.
- Platform and installation claims name the exact observed matrix cells.
- Residual risks and limitations remain explicit and owner-resolved before release progression.
