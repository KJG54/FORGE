# Idempotent Mutation Retries

Every supported command that changes governed initiative state accepts an optional
`--idempotency-key`. Use a stable key when a command may be retried by a script, CI job, or person:

```console
forge create "Objective" --scope "Bounded scope" --trust-pack-data \
  --idempotency-key create-initiative-2026-07-14
```

When the option is omitted, FORGE generates a UUID and prints it before running the mutation. Save
that value if you may need to retry. Repeating the exact command request with the same key returns
the already committed event IDs without creating another record or transition.

A key identifies one request for the entire repository, including archived initiatives. Do not
reuse it for changed arguments or changed intent. FORGE reports that reuse as a conflict. Ambient
working-copy changes do not turn an old key into a new request; use a new key when you intend to
register new content.

Completion receipts live under `.forge/idempotency/` and are governed project state. Each receipt
is checked against exact hash-chained events. Do not edit or delete these files. If an interruption
commits journal events before the completion receipt is durable, FORGE refuses retries and other
mutations with an explicit recovery-required error. The later recovery increment will own that
remediation; this increment never guesses or silently repairs it.

`forge init` keeps its existing identity-preserving repeat behavior. `forge import-result` preview
is read-only, so its key is used only when `--apply` is present.
