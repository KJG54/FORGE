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

Workflow deviations bind the exact locked workflow and remain observations rather than execution
or bypass authority. A current owner review decision is required before successful closure, but
review does not waive checks, evidence, acceptance, or gates. Emergency override and risk
acceptance are separate governance facts and are not implied by a deviation or its review.

Emergency overrides are exact locked-workflow, owner-attributed exception records. They do not
weaken transition checks or fabricate claims, checks, evidence, gates, verification, or
acceptance. A separate owner risk acceptance must bind the exact override record and clears only
its residual-risk closure blocker. Scope amendments affecting the governed target stale both
records. An immutable owner revocation reopens the exact blocker without changing workflow state;
stale or already revoked acceptance cannot authorize or be revoked again. This fail-closed
behavior is governance enforcement, not isolation from a same-user process that can directly
modify repository files.

General decision withdrawal is owner-only and append-only. The reserved withdrawal decision binds
the exact canonical digest and affected facts of one current prior decision; arbitrary records
cannot masquerade as withdrawals. Replay removes the prior decision from current authority without
editing it or granting the withdrawal any progression authority. Withdrawing a current workflow-
deviation review therefore fails closed by reopening that deviation's closure blocker.

Formal run cancellation is append-only and binds the exact immutable run, locked cancellation
policy, side-effect classification, actor, and derived destination. An adapter-attributed run
cannot be declared cancelled until a preceding hash-sealed execution event proves FORGE-managed
execution is already terminal. FORGE does not signal, terminate, or prove the absence of a live
cross-process worker; external process supervision and operating-system isolation remain separate
security controls.

Handled CLI failures are observed through local `LocalAuditEvent` files when the repository can be
safely identified. They classify the operation and stable exit code but persist only a SHA-256
digest of the displayed detail, not raw error text, arguments, environment, credentials, content,
or provider output. Recording is best effort and cannot replace the original refusal. These
Git-ignored files are diagnostic rather than governed evidence: they are not hash chained,
archived, or accepted as workflow support, and same-user processes can alter or remove them.

Pack templates are declarative UTF-8 text, not executable capability declarations. FORGE rejects
symbolic, irregular, executable-suffixed, undeclared, oversized, binary, missing, and additional
template content; binds accepted bytes into the complete pack digest; and preserves exact locked
copies with the initiative. `forge pack template show` renders owner-requested validated text only
and creates no project file or governance fact. These controls do not make template content true,
safe for every audience, free of secrets, legally reusable, or immune to a malicious same-user
process. Owners must review template content and any research entered into it.
