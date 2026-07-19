# FORGE Glossary

These definitions are canonical for Production v1 planning and implementation.

- **Acceptance:** The owner's digest-bound decision that checked and evidenced outcomes may
  authorize progression or closure.
- **Actor:** An identified owner, contributor, CLI, adapter, external tool, migration, recovery
  process, or unknown external process associated with an action.
- **Agent adapter:** An isolated integration that invokes a separately installed worker and
  returns untrusted output through the normal import boundary.
- **Archive:** An immutable terminal initiative record referencing exact preserved revisions.
- **Artifact:** A governed logical work product with one or more immutable revisions.
- **Authority grant:** A scoped, revocable owner decision allowing an actor to perform an
  action class. It is governance identity, not cryptographic authentication.
- **Capability:** A separately defined executable operation with explicit invocation,
  permissions, side effects, and trust state.
- **Check:** A structured evaluation of a claim or exact artifact revision. A passing check is
  not owner acceptance.
- **Claim:** A worker's assertion about work performed or output produced.
- **Decision:** An append-only governance fact. A later outcome supersedes rather than edits it.
- **Evidence:** Durable, digest-bound support for a check or governance decision, including its
  limitations. Evidence does not automatically establish truth.
- **Explanation profile:** A rendering policy that changes educational depth without changing
  governance outcomes.
- **FORGE-enabled project repository:** An ordinary project containing `forge.yaml` and `.forge/`.
- **FORGE source repository:** The repository containing FORGE's own Python implementation.
- **Integrity state:** `healthy`, `recovering`, or `integrity_error`, independent of lifecycle.
- **Initiative:** One governed body of work with an immutable identity, objective, locked pack,
  workflow, owner, scope, and lifecycle.
- **Journal:** The ordered append-only event history authoritative for lifecycle ordering.
- **Materialized state:** A reconstructable current view derived from the validated journal and
  locked rules.
- **Owner:** The single Production-v1 repository authority for consequential governance actions.
- **Pack:** Versioned declarative domain data containing workflows, templates, explanations, and
  checks; pack trust never grants executable trust.
- **Pack data trust:** The owner's reversible authorization to use one initiative's exact locked
  declarative pack. Withdrawal blocks workflow-dependent mutation without erasing history or
  changing executable capability approval.
- **Preserved object:** Immutable bytes stored by SHA-256 digest for historical reproducibility.
- **Revision:** An immutable digest-bound version of an artifact or evidence file.
- **Run:** One bounded manual or tool work attempt. Process success does not imply acceptance.
- **Snapshot:** The persisted materialized state and its journal-head reference.
- **Stale:** No longer authorizing progression because a bound revision, scope, decision, check,
  evidence packet, or acceptance dependency changed.
- **Successor initiative:** New work linked to archived predecessors without inheriting approval.
- **Worker:** A human, agent, script, validator, or external tool that performs project work but
  does not gain owner authority from doing so.
- **Workflow lock:** The exact pack and workflow versions governing an initiative.
