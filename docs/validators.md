# Trusted Local Validator Declarations

M4 Increment 1 adds disabled-by-default local validator declarations and exact owner approval.
Increment 2 adds explicit supervised execution and immutable check-result capture without creating
evidence, verification, or acceptance.

## Declare a profile

Add a validator to tracked `forge.yaml`:

```yaml
capabilities:
  local_validators:
    - schema_version: "1.0"
      id: validator.project.tests
      version: 1.0.0
      provider: Project test runner
      provider_version: declared-1
      purpose: Run the project test suite against current artifact revisions
      executable: python
      arguments:
        - -m
        - pytest
        - -q
      working_directory: null
      timeout_seconds: 300
      expected_outputs:
        - exit-status
        - stdout
        - stderr
      environment_access:
        - PATH
      side_effect_class: read_only
```

`working_directory: null` means the repository root. Otherwise use one normalized
repository-relative directory. `provider_version` is owner-declared metadata in this increment;
inspection never runs an unapproved executable merely to discover a version.

The executable and every argument are separate YAML values. FORGE intentionally has no shell
command-string field. Environment access contains variable names only; credentials and values do
not belong in tracked configuration.

## Inspect and approve

```console
forge capability list
forge capability inspect validator.project.tests
forge capability approve validator.project.tests \
  --scope approved-once \
  --rationale "Run this exact local test profile"
forge capability approve validator.project.tests \
  --scope approved-once \
  --rationale "Run this exact local test profile" \
  --apply
```

Inspection resolves the executable but does not start it. Approval is preview-first, owner-only,
and binds the complete profile. Changing the provider/version, executable, arguments, working
directory, timeout, expected outputs, environment access, or side-effect class makes every prior
validator approval inapplicable, including `approved-for-project`.

Missing executables and Windows `.bat` or `.cmd` command shims fail closed. Use a native
executable with an explicit argument vector—for example, a Python executable plus `-m pytest`.

## Trust boundary

A trusted-data pack may declare that a workflow requires a capability ID. It cannot add a local
validator profile, approve a process, or execute code. Validator declaration in `forge.yaml`,
owner capability approval, future execution, a resulting check record, evidence, verification,
and owner acceptance remain separate facts.

Declaration and approval create no run, `CheckResult`, evidence packet, lifecycle transition, or
acceptance.

## Run one declared check

After a worker claim moves the current step to `awaiting_verification`, select one configured
validator for one check listed in that step's locked `check_requirements`:

```console
forge check run discover outputs-present \
  --validator validator.project.tests
forge check list
forge check show <check-result-id>
```

Before process creation, FORGE commits an immutable approval-bound validator `RunRecord`. This
consumes an `approved-once` approval even if launch or execution fails. The child receives the exact
approved executable and argument vector with shell execution disabled, the approved repository
working directory, the declared timeout, and a fresh environment containing only declared
non-credential names plus limited platform essentials and a FORGE-owned temporary directory.

Credential-like environment channels such as API keys, access keys, tokens, secrets, passwords,
private keys, and credentials make the profile unavailable. Environment values are never written
to governed records.

Stdout and stderr are captured under:

```text
.forge/local/validator-runs/<run-id>/
```

The combined capture is limited to 1 MiB. Those raw bytes are local-only, Git-ignored diagnostic
material and are never printed by `forge check run|show`. The governed `CheckResult` retains the
capture paths, byte counts, and SHA-256 digests alongside the approval, invocation digest,
timestamps, exit status, normalized execution state, outcome, and exact target artifact revisions.

The mapping is intentionally structural:

- exit status 0 records `passed`;
- nonzero exit records `failed`;
- timeout, output overflow, launch error, or supervision failure records `error`.

A zero exit status does not prove semantic quality or factual truth. After a passing result, the
normal sequence remains explicit:

```console
forge evidence add discover ...
forge verify discover
forge acceptance record discover ...
```

Validator execution performs none of those actions automatically and leaves the step
`awaiting_verification`.
