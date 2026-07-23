# Trusted Local Validator Declarations

M4 Increment 1 adds disabled-by-default local validator declarations and exact owner approval. It
does not execute validators yet.

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

Increment 1 stops before validator execution. No declaration or approval creates a run,
`CheckResult`, evidence packet, lifecycle transition, or acceptance.
