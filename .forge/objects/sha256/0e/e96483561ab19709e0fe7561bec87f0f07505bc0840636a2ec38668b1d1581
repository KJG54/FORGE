# Local Production-v1 Release-Readiness Record

Date: 2026-08-09  
Status: **ready for bounded extended owner testing as an unpublished local candidate**

## Decision boundary

This record covers the exact local FORGE 1.0.0 candidate identified by:

- wheel: `forge_governance-1.0.0-py3-none-any.whl`;
- wheel SHA-256: `a9c010a92d146300de7f59852d8c7181039a3c45246f615d8f7666072c672349`;
- sdist SHA-256: `3907c86f25b3ad36c650c6888074ed1e8148451cd861ef42ddee1af26cf12b88`;
- clean candidate source commit: `6e222985c57a9f6e74b33cf5146cb51c80e42744`; and
- installed direct-agent protocol: `1.3.0`, SHA-256
  `34ee8ddcda6ae147f87caf5863aa4e7ca20c34310807e441b065d8d8553eaa00`.

The candidate is ready for the extended personal/local owner-testing phase defined by the
initiative. This statement does not publish FORGE, grant final owner acceptance, establish
multi-user security, or authorize tags, package-index uploads, GitHub Releases, signing, naming
clearance, hosted operation, or public support commitments.

## Accepted foundation

Closeout is based on the accepted verification and risk-review chain, including verification-report
revision `438eebe8-39e4-460d-94dd-bd3fba0ef469`, friction-report revision
`d60d46b7-cc69-44fd-b2ae-d7509619804e`, residual-risk-report revision
`7b4a300e-d6ef-4a63-8859-123c363d0957`, and risk-review acceptance
`98352c82-9b54-43bb-b2dc-d82852585b1c`. The accepted risk boundary was progression into closeout
preparation only; this record does not retroactively broaden it.

## Current-candidate closeout results

All of the following results were bound to the exact wheel digest above unless explicitly noted as
source- or service-level evidence:

| Surface | Result | Important binding or limitation |
|---|---|---|
| Candidate manifest | Passed | Wheel and sdist hashes and sizes matched the preserved manifest. |
| Source quality | Passed | Ruff passed; Pyright 1.1.411 reported zero errors and warnings; schema/model/command consistency passed. |
| Complete test suite | Passed | 413 passed, 9 skipped, 1 optional pytest-cache warning. The skips are the documented Windows symbolic-link privilege cases. |
| Clean virtual environment | Passed | Exact wheel installed and reported FORGE 1.0.0 on CPython 3.14. |
| pipx installation | Passed | Exact wheel installed and exercised through pipx. |
| Maintained procedures | Passed | Abandonment, archive access, backup, migration, restore, snapshot recovery, and successor rehearsal passed; report digest `5562c1589ac7720a36aae8906762f6d53763c271152e3d57d52d06d1d5b93c66`. |
| Example workflows | Passed | Research and software examples completed and archived healthily. |
| Security review | Passed | Dependency audit reported zero findings; Git-history and snapshot secret scans passed with the existing narrow historical exception; report digest `183027cf28fc8b14d8b9eb4f02bdfda3318fc4abe7342af425c2440956e205e7`. |
| Maintained performance | Passed | All five cases passed; active-status p95 was 817.346 ms against the 1500 ms budget; report digest `afe2efed5fb337a4078c836ba827edb2b09c804a0791e8c2b1bea5cdfe512892`. |
| GitHub integration | Passed as directly observed external evidence | PR 42 head `505522744aba5974f314267ecab714af3654968b` CI run 31325645202 and PR 43 head `8c944b2b7c18986ebeea3aaa3f6c0318ee8e4f3e` CI run 31327236376 both completed successfully. These observations are not represented as FORGE-authenticated cloud attestations. |

## Native direct-agent replacement smoke

The owner supplied final reports from fresh Codex and Claude Code workspaces. Both reports bind the
installed candidate to the full current wheel digest, Python 3.14.4, FORGE 1.0.0, and protocol
1.3.0. Neither smoke used the FORGE source checkout or its virtual environment.

### Codex

- workspace: `forge-closeout-codex-a9c010a9`;
- smoke initiative: `4f54a4e6-4a71-4af5-99fb-f7cee876e317`;
- claim operator: `direct-codex` with caller-declared, non-authenticating attribution;
- result: protocol-first bootstrap, pre-init pack inspection, distinct required artifacts, truthful
  missing-role readiness, and truthful awaiting-verification check blocker all passed;
- context result: two authorized applies recorded zero governed events; journal stayed at sequence 6
  with head `sha256:555c1a371be48972a7ab07f4d7f0727d74ea39a7cf0e5ca748cef756f94309f3`;
- unmanaged bytes: the 53-byte owner prefix and one-byte suffix remained byte-identical.

### Claude Code

- workspace: `forge-closeout-claude-a9c010a9`;
- smoke initiative: `141a30b7-f951-4212-9d44-5237f3ba841a`;
- claim operator: `direct-claude` with caller-declared, non-authenticating attribution;
- result: protocol-first bootstrap, uninitialized pack inspection, distinct required artifacts,
  truthful missing-role readiness, and truthful awaiting-verification check blocker all passed;
- context result: two separately authorized applies recorded zero governed events; journal stayed at
  sequence 6 with head `sha256:9ab8f7b23383a57f18f02a6657ae0b65afb40cc8e9a14b58a27c413dae739ef3`;
- unmanaged bytes: the 54-byte owner prefix and one-byte suffix remained byte-identical.

Both reports stopped before checks, evidence, verification, acceptance, or closure as required.
Their owner-gate statements are owner-supplied task evidence and same-user attribution, not proof of
authenticated human identity.

## Residual-risk disposition

| Risk | Closeout disposition |
|---|---|
| RR-01: deferred exact-wheel matrix | Resolved for this candidate and Windows CPython 3.14 environment by the passing closeout matrix. |
| RR-02: replacement native smoke | Resolved for the bounded direct Codex and Claude journeys. The sentinel reapply used the no-change path; native rewrite-path coverage remains a non-blocking evidence limitation because automated exact-byte coverage passed and no preservation defect was observed. |
| RR-03: privileged Windows symlinks | Retained. Do not make a broader privileged-symlink platform claim until those cases run on a suitably privileged host. |
| RR-04: context freshness | Operationally reconciled for both tracked vendor files during closeout. Automatic freshness remains future work; governed status remains authoritative. |
| RR-05: managed adapters | Retained. Direct native operation passed, but adapter compatibility was not established. |
| RR-06: same-user authority | Retained by design. Labels and session references remain attribution, not authentication. |
| RR-07: ignored local binaries | Retained. Preserve and hash-check the exact wheel and sdist; any rebuild invalidates this record. |
| RR-08: host-specific performance | Retained. Results cover this Windows CPython 3.14 host and are not real-time guarantees. |
| RR-09: external CI | Directly observed as successful for the relevant merged heads; not converted into an authenticated FORGE cloud attestation. |
| RR-10: public release exclusions | Retained in full. Public release requires a separate owner-approved initiative and evidence set. |

## Non-blocking closeout observations

- Installing with `--no-index` and only the FORGE wheel available cannot resolve runtime
  dependencies; ordinary exact-wheel installation with dependency resolution passed.
- Disposable native repositories outside Git correctly warn that governed records are not versioned.
- The initiative-title separator rendered as a replacement character in the Codex console and
  should receive a focused Windows encoding follow-up.
- The current native sentinel reapply reported `Action: no-change`; a future purpose-built test
  should force a managed-block change while an unmanaged sentinel is present.
- Claude's report identified minor vocabulary and ergonomics opportunities: document target-to-file
  mapping prominently, make inspection verbs more consistent, consider Markdown media-type
  inference, and surface direct operator provenance earlier in compact receipt rendering.

## Readiness conclusion

No unresolved candidate-blocking defect was observed in the current closeout matrix or replacement
native smoke. The exact candidate is suitable for extended personal/local owner testing within the
accepted residual risks. It remains unpublished and is not represented as finally accepted or
public-release ready.
