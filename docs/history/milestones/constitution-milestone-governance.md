# Historical Constitution Milestone-Governance Language

The following text appeared under `## Milestone governance` in `docs/constitution.md` before
ADR-0062 made the living Constitution milestone-independent. It is preserved here as development
history, not as current workflow instruction. Existing milestone reports and ADRs were not changed.

> Each milestone requires an approved brief, bounded implementation, automated checks, a manual
> walkthrough, an implementation claim, an evidence packet, and explicit owner review. Work stops
> after each milestone. Milestone 1 is internally divided into implementation increments, but
> those increments do not create new owner gates unless scope materially changes.
>
> Milestone 1 archival proves lifecycle behavior, exact-byte preservation, and command-level
> archive immutability only. Production-strength hash-chain integrity, interruption safety,
> recovery, concurrency, and corruption detection are Milestone 2 claims.

Current workflow steps come from exact initiative locks. See the
[current governing specification](../../governing-specification.md) and
[ADR-0062](../adr/ADR-0062-typed-authority-and-specification-lifecycle.md).
