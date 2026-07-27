# ADR-0045: Digest-Bound Pack Templates

**Status:** Accepted

**Milestone:** M5 Increment 2

## Context

`PackManifest` has always declared template, explanation, and data-resource paths, but earlier
milestones refused every such resource because the pack integrity digest covered only the manifest
and workflow models. The research pack now requires evidence-register and citation-record templates
without turning trusted pack data into executable authority or relying on mutable installed-package
files after initiative creation.

A digest over a source template alone is insufficient for continuity. A local pack may change or
disappear, and a bundled pack may be upgraded while an initiative is active. Exact trusted bytes
must therefore be preserved with the workflow lock and validated through restart and archival.

## Decision

M5 Increment 2 enables only `PackManifest.template_paths`. Explanation and general data-resource
paths remain unsupported.

Every declared template must be a unique normalized pack-relative path to a regular, non-symbolic,
non-executable UTF-8 text file of at most 1 MiB. The complete pack inventory and 10 MiB aggregate
limit continue to apply. Each template receives a SHA-256 content digest. For a resource-bearing
pack, the canonical pack digest binds the existing manifest and workflow payload plus the sorted
template path, resource kind, and content digest.

The no-resource digest payload remains byte-for-byte unchanged. Existing pack locks and archives
with empty resource declarations therefore retain their accepted digest without migration.

Initiative creation copies the already validated template bytes to:

```text
.forge/active/pack-resources/<declared-template-path>
```

The copy occurs before the `initiative-created` event. A pre-commit failure removes the new exact
resource tree along with the other uncommitted creation records. Once the event commits, the locked
copies are governed data: restart validates exact inventory and recomputes the pack digest without
consulting the source pack. Missing, changed, additional, symbolic, irregular, oversized, or
non-UTF-8 locked content is an integrity failure.

The existing archive transaction copies `pack-resources/`, inventories every byte, and reloads the
archived initiative against those exact resources. No new event, persisted model, schema version,
migration, recovery procedure, or authority class is introduced.

Add read-only `forge pack template list|show`. When the requested pack is locked by the active
initiative, the commands use its governed copies; otherwise they use the currently available
validated pack. Showing a template does not copy project files, register an artifact, create
evidence, run a capability, verify work, or record acceptance.

## Consequences

Research templates remain data-only and usable from installed distributions while active and
archived initiatives stay independent of later pack upgrades. Trusting the pack authorizes the
exact declarative bytes only. Template completeness cannot establish citation correctness, source
quality, methodological validity, or factual truth.

Tracked governed storage grows by the exact template size for each resource-bearing initiative and
archive. Owners must explicitly restore exact bytes after corruption; FORGE does not silently
repair locked resources from a possibly changed source pack.

Executable structural validators, explanation resources, general data resources, template
instantiation, automatic artifact registration, and later M5 work remain separate boundaries.
