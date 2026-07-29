# Supply-Chain and Secret Review

M6 Increment 5 adds a reproducible release-review boundary for declared dependencies, installed
dependency licenses, known vulnerabilities, and repository secrets. It does not modify runtime
dependencies or claim that any point-in-time scan guarantees future safety.

## Policy and scopes

`release/security-review-policy.json` binds:

- the exact build, runtime, and development dependency declarations in `pyproject.toml`;
- the allowed SPDX license expressions;
- two exact version-and-license-file-digest overrides for legacy ambiguous BSD metadata;
- minimum supported versions of PyPA `pip-audit` and Gitleaks; and
- one exact historical Gitleaks fingerprint for a synthetic secret-screening fixture.

Unknown policy fields, changed dependency declarations, missing installed packages, ambiguous
licenses, changed reviewed license bytes, unapproved licenses, older tools, broad secret
exceptions, vulnerability findings, or secret findings fail closed.

The license inventory follows the dependencies installed for each declared scope. This local
result is environment-specific; the final clean-wheel environments must repeat the review at M6
closeout.

## Run the review

Install development dependencies, PyPA `pip-audit` 2.10 or newer, and Gitleaks 8.30 or newer.
Neither scanner is a FORGE runtime dependency.

```console
python -m tools.release_security_review
```

The harness:

1. validates the strict policy against `pyproject.toml`;
2. walks the installed build, runtime, and development dependency closures;
3. resolves every license from SPDX metadata, an unambiguous legacy field/classifier, or one exact
   reviewed license-file digest;
4. writes an exact installed runtime requirement set in a temporary directory;
5. invokes `pip-audit` with no dependency re-resolution and queries PyPI advisory data;
6. invokes Gitleaks with full redaction over complete Git history;
7. copies only Git-tracked and non-ignored untracked review files into a bounded temporary snapshot
   and scans that snapshot; and
8. emits JSON containing package names, versions, license expressions, tool versions, counts,
   status, and limitations.

Every subprocess uses a fixed argument vector with `shell=False`. Temporary requirements, secret
reports, and snapshot copies are deleted when the process exits. The JSON output contains no
matched secret or absolute repository path.

Use `--output <fresh-path>` to retain a machine-readable report. The harness refuses to overwrite
an existing report.

## Exact synthetic-secret exception

Commit `d73226943b208c8482e0fd7e919cb4070cf14b47` introduced a high-entropy fake `api_key` value to
prove that governed artifact registration rejects recognizable credentials. Gitleaks correctly
detects that historical test line.

`.gitleaksignore` contains only the complete commit/path/rule/line fingerprint for that one
historical finding. The current source line carries `gitleaks:allow` beside the synthetic fixture.
The policy and tests reject path-wide, rule-wide, or incomplete exceptions. This is not an
acceptance of a real credential.

## Interpretation

- A dependency inventory proves what the observed environment contained, not what every allowed
  future resolution will contain.
- An allowed license means it passed this project's policy review, not that legal obligations have
  been satisfied automatically.
- No known advisory means the selected service returned no finding at scan time.
- Gitleaks is heuristic. A clean scan does not prove the repository secret-free.
- Scanner process success is release evidence only after its result, scope, version, limitations,
  and exact review commit are recorded and owner-reviewed.

Any vulnerability or suspected live secret is release-blocking until the owner records remediation
or an explicit bounded residual-risk decision. Credential revocation and rotation happen at the
provider, outside FORGE.
