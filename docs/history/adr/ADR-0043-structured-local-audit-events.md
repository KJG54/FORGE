# ADR-0043: Structured Local Security and Failure Audit Events

**Status:** Accepted

**Milestone:** M4 Increment 10

## Context

The governed `AuditEvent` journal is authoritative for initiative history, but a refused command
normally creates no governed event because no authorized state change occurred. Security,
authorization, transition, integrity, configuration, conflict, and external-tool failures were
therefore visible only in ephemeral terminal output.

Persisting raw failure text would create a second risk: error messages can contain repository
paths, provider details, or user-supplied names. Treating refusal observations as governed history
would also let diagnostic logging interfere with the original result or imply workflow authority.

## Decision

Add the public immutable `LocalAuditEvent` contract and store one file per observed CLI failure at:

```text
.forge/local/audit-events/<event-id>.json
```

Each event records the project and optional active initiative identity, configured owner identity,
UTC timestamp, CLI operation, stable error category, severity, refused outcome, exit code, error
type, tool version, and SHA-256 digest of the displayed error. It never stores the raw error text,
command arguments, environment, credentials, artifact content, or provider output.

All handled `ForgeError` categories are eligible once FORGE can safely discover and validate the
repository configuration. Categories map directly from stable exit codes. Successful governed
mutations continue to use the initiative event journal and are not duplicated locally.

Local event recording is best effort. Failure to create or write a local event never changes or
masks the original CLI exit code and message. UUID-named atomic files avoid shared append state.
`forge audit list|show` validates and displays the sanitized records. `forge doctor` validates the
inventory and reports its count.

These files remain below the Git-ignored `.forge/local/` boundary. They are project-local
observations, not workflow authority, journal evidence, acceptance support, or archive content.
They are not hash chained, and a process with the repository owner's operating-system permissions
can edit or delete them.

## Consequences

Operators gain stable, machine-readable evidence that a supported CLI operation was refused or
failed without copying potentially sensitive diagnostic text into tracked governance history.
External tools may read the exported schema or local files, but no exporter is enabled.

The public schema bundle grows from 49 to 50 models. This increment does not add OpenTelemetry,
network export, success telemetry, retention automation, incident recovery, live process control,
or the cumulative M4 adversarial closeout suite.
