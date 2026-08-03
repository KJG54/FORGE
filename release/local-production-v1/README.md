# Local Production-v1 Candidate

This directory defines the current FORGE v1 deliverable: one feature-complete, unpublished local
candidate for extended owner testing. It does not define or authorize a public release.

The exact candidate consists of:

- `forge_governance-1.0.0-py3-none-any.whl` for every downstream installation test;
- `forge_governance-1.0.0.tar.gz` as the matching source distribution;
- [`candidate-manifest.json`](candidate-manifest.json), which records their exact names, sizes, and
  SHA-256 digests; and
- [`SHA256SUMS`](SHA256SUMS), a simple checksum view of the same identity.

The binary artifacts are machine-local under `dist/local-production-v1/` and are intentionally not
committed. They can be verified against the tracked identity without rebuilding:

```console
python -m tools.local_candidate verify
```

Do not replace either artifact during L9. A rebuild creates different candidate inputs even when
the source appears unchanged. If either artifact is missing or its digest differs, stop and return
to L8 integration rather than silently creating a substitute.

Read the [known limitations](known-limitations.md), [residual risks](residual-risks.md), and
[owner test guide](owner-test-guide.md) before using the candidate. The historical public-M7 scope
and ADRs remain evidence of an abandoned initiative, not current instructions.
