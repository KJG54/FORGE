# Pack-Author Guide

A FORGE pack is versioned declarative data. It can define workflows, inline explanations,
templates, structural validators, and capability identifiers. It cannot contain executable code,
approve a process, run a hook, grant owner authority, create evidence, or accept work.

Pack authoring extends domain language without adding Python domain logic. The bundled
`software-basic` and `research-basic` directories under `src/forge/packs/bundled/` are maintained
reference implementations. The repository-local `community-research` fixture under
`tests/fixtures/packs/` demonstrates a Python-free extension.

## Directory contract

```text
my-pack/
|-- manifest.yaml
|-- workflows/
|   `-- my-workflow.yaml
|-- templates/                 # optional, declared UTF-8 text
|   `-- review-record.md
`-- validators/                # optional, declared structural-validator YAML
    `-- review-structure.yaml
```

Every regular file must be declared. Symbolic links, irregular files, executable suffixes,
undeclared files, missing files, YAML anchors and aliases, non-UTF-8 text, oversized files, and an
incorrect complete-pack digest fail closed.

Register a repository-local directory in tracked `forge.yaml`:

```yaml
packs:
  local_paths:
    - packs/my-pack
```

Paths are normalized repository-relative paths and remain subject to the ordinary path and secret
boundaries.

## Manifest

`manifest.yaml` uses schema version `1.0` and contains:

- a symbolic `id` and semantic `version`;
- `schema_compatibility`, currently including `forge-contracts-1`;
- the exact `provided_workflow_ids`;
- exact `template_paths`, `explanation_paths`, and `data_resource_paths`;
- optional `declared_capability_ids`; and
- `integrity_digest`, a SHA-256 digest over the canonical manifest-without-digest, workflows, and
  declared resource digests.

External explanation files are not currently supported, so `explanation_paths` must be empty.
Templates are bounded UTF-8 text. `data_resource_paths` currently contains only declarative
structural-validator definitions.

Any byte or declared field change requires a new digest. Treat a released pack version as
immutable: change the semantic version as well when publishing revised behavior. FORGE locks exact
pack and resource bytes with an initiative, so later source-pack edits cannot silently change
active governance.

## Workflow definition

Each `workflows/<id>.yaml` document declares:

- its schema, ID, version, pack ID, name, and description;
- an ordered, acyclic set of steps;
- exact prerequisite, input-role, output-role, claim, check, acceptance, actor, transition, and
  cancellation declarations;
- the shared begin, submit, rework, verify, and accept transition semantics;
- optional gates and required artifact/evidence classes;
- inline explanation text; and
- compatibility constraints.

Every workflow must provide at least Standard and Guided explanation content. Minimal and Mentored
are recommended for parity with the bundled packs. Explanation changes presentation only; all
profiles must preserve identical actors, permissions, checks, gates, transitions, and acceptance.

Use domain-specific role and step names, but preserve the governance sequence. A pack cannot make a
caller-supplied assertion satisfy a derived transition condition.

## Templates and structural validators

Templates are inspectable text:

```console
forge pack template list my-pack
forge pack template show my-pack templates/review-record.md
```

Showing a template does not write a project file or make its content safe, true, accepted, or
legally reusable.

Structural validators may require exact Markdown headings and non-empty field prefixes for current
UTF-8 artifact revisions. They cannot declare executables, arguments, expressions, regular
expressions, environment access, hooks, or network access. A structural pass is a check result,
not evidence, factual truth, verification, or acceptance. See [validators](validators.md).

## Digest and validation loop

Calculate the digest with the same installed Python package version that will validate the pack.
The canonical implementation is `forge.packs.validation.calculate_pack_digest`; loading helpers
are in `forge.packs.loader`. Do not create a different JSON/YAML hashing convention.

After placing the resulting `sha256:<lowercase-hex>` value in the manifest, validate from the
repository:

```console
forge config validate
forge pack validate my-pack
forge pack inspect my-pack
forge pack template list my-pack
forge pack validator list my-pack
```

Validation is necessary but not owner trust. Initiative creation or `forge pack trust --apply`
records a separate owner decision for the exact locked data.

## Author review checklist

- The pack contains only declared, bounded, UTF-8 declarative files.
- IDs are unique and every workflow references its own pack.
- Step prerequisites are acyclic and every declared transition exists.
- Required inputs are produced by reachable prerequisite steps.
- Allowed actors and cancellation behavior reflect the real risk boundary.
- Checks and gates do not imply semantic truth or owner acceptance.
- All explanation profiles preserve identical governance.
- Template and validator paths are exact, regular, non-symbolic, and non-executable.
- Capability IDs refer only to separately configured and separately approved project capabilities.
- The semantic version and complete digest match the reviewed bytes.
- Tests exercise valid loading, changed-byte rejection, undeclared-file rejection, and the intended
  lifecycle with the generic FORGE services.

See [packs and workflows](workflows.md) for the runtime boundary and
[security](security.md) before distributing third-party pack data.
