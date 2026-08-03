# Local Production-v1 L8 - Candidate Integration

## Authorized boundary

L8 integrates L1-L7 into one current-facing local-v1 definition. It updates the README,
installation, user, continuity, handoff, acceptance, security, recovery, compatibility, and local
release guidance while preserving the abandoned public-M7 scope, ADRs, and archive as historical
evidence. Public publication, tagging, publisher configuration, and final owner acceptance remain
outside this increment.

The package, runtime, schema, pack, CLI, and installation contracts remain aligned at
`forge-governance==1.0.0`, schema version `1.0`, 51 public models, and the existing M1/M2
compatibility boundary. The pre-alpha classifier remains an honest unpublished-candidate marker;
project URLs and a dated public changelog section are deliberately incomplete.

## Exact artifact contract

One source distribution and one wheel are built locally into `dist/local-production-v1/`. The
wheel is built from that source distribution. The tracked
`release/local-production-v1/candidate-manifest.json` and `SHA256SUMS` bind exact filenames, byte
sizes, and SHA-256 digests. `python -m tools.local_candidate verify` checks embedded distribution
metadata and exact local bytes, rejects extra distributions, and confirms that downstream
installation names the recorded wheel.

The tracked manifest and checksum records are excluded from the sdist to avoid circular
self-hashing. Machine-local `.forge/local/` state is also pruned before traversal. Binary artifacts
remain ignored and must be preserved locally; rebuilding them creates new candidate inputs.

## Handoff records

The local release directory includes:

- the candidate manifest and checksum view;
- known limitations that distinguish incomplete validation and non-guarantees;
- a severity-ranked residual-risk register with candidate dispositions; and
- a 13-journey owner test guide covering new and existing projects, research, ordinary and formal
  resumption, rejection and plan change, scope amendment, recovery, abandonment, closure, archive,
  fresh-agent succession, and real-machine backup/restore.

## Validation boundary

Focused L8 validation covers manifest rules, artifact metadata and digests, sdist exclusions,
documentation links, version-contract consistency, Ruff, and Pyright. It does not run the complete
pytest/CI matrix, clean-install cells, release scenarios, or native Codex/Claude owner campaign.
Those are L9 responsibilities. Passing L8 establishes an exact candidate input, not candidate
readiness for extended use and not final Local Production-v1 acceptance.
