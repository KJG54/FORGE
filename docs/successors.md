# Successor Initiatives

A successor continues work without reopening or rewriting a closed or abandoned initiative. It is
a new governed initiative with explicit lineage, not a resumed predecessor.

## Create a successor

With no active initiative and at least one archive:

```console
forge status
forge create "New objective" --scope "New bounded scope" \
  --predecessor <archived-initiative-id> --trust-pack-data
```

Repeat `--predecessor` for multiple ancestors. Every selected ID must identify a validated archive,
and every archive in the repository must pass integrity validation before creation proceeds. FORGE
sorts and records canonical `successor-of` links containing each archive path.

The successor starts at journal sequence 1 with a new initiative ID and new pack-trust decision.
Workflow steps restart from their initial states. No predecessor artifacts, checks, evidence,
decisions, revocations, acceptance, stale state, or progress are imported.

## Reuse exact artifact bytes

Artifact reuse is a separate, explicit registration after successor creation:

```console
forge artifact add outputs/input.md --role project-artifacts --title "Reused input" \
  --predecessor-revision <terminal-artifact-revision-id>
```

The revision must be listed in a declared predecessor's terminal archive manifest, and the current
project file must match its digest and size exactly. FORGE creates a new logical artifact and new
revision in the successor. Provenance binds the predecessor initiative, revision, digest, and
archive record. The predecessor archive remains unchanged, and no approval transfers.

## Safety properties

- A normal `forge create` is refused when archives exist; at least one predecessor is required.
- Duplicate, unknown, self-referential, noncanonical, or tampered links are rejected.
- Incomplete terminal archive transactions block successor creation.
- Closed and abandoned predecessors are both valid.
- A successor may itself become a predecessor after closure or abandonment.
- Artifact reuse never bypasses successor checks, evidence, or owner acceptance.
