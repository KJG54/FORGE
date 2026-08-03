# Local Production-v1 L7 - Milestone and Successor Brief

## Authorized boundary

L7 adds a terminal-archive transition view without changing the active-step worker handoff. The new
read-only command is:

```console
forge successor brief --archive <archived-initiative-id>
```

It validates the selected closed or abandoned archive before deriving any content. The generated
Markdown keeps governed predecessor facts, durable governed carryover, exact reusable terminal
revision references, and fresh repository observations in distinct sections. It does not persist a
brief, read the local conversation scratchpad, create a successor, or import predecessor progress,
checks, evidence, decisions, acceptance, or authority.

## Derived content

The governed section includes initiative identity, objective, effective scope, terminal outcome,
archive digest, journal head, lineage, closing or abandonment facts, accepted artifacts, current
decisions, accepted checks and evidence, declared limitations, residual risks, and accepted
`lessons` artifacts. Every reusable revision is bounded by the terminal archive manifest and names
its archive record, preserved object, digest, byte size, acceptance status, and exact
`--predecessor-revision` option.

The separately labeled observation section probes the installed FORGE version, active-initiative
relationship, Git availability, branch, commit, and worktree state at rendering time. These values
are explicitly non-governed observations. The startup section gives the receiving agent exact
read-only revalidation commands and identifies successor creation and artifact reuse as later,
distinct owner-reviewed actions.

## Focused validation

Focused L7 tests cover a closed predecessor in a Git-clean archive-only checkout, confirm that brief
generation changes no archive or worktree bytes, create a fresh successor with explicit lineage,
and validate the same archive again from that successor. A separate abandoned-predecessor scenario
proves partial revisions remain labeled unaccepted, unresolved terminal risk survives, and local
scratchpad content does not transfer.

Passing focused checks establishes only L7 implementation evidence. The encompassing Local
Production-v1 `implement` step remains in progress; candidate integration and full milestone
validation remain L8 and L9 work. The repository-owned fast quality gate remains required before
publication, while the complete test, build, installation, and release matrices remain deferred to
milestone closeout.
