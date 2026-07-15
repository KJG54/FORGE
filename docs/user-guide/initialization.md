# Repository Initialization

`forge init` enables an ordinary existing project repository without creating an initiative.

```console
forge init --owner-name "Repository Owner"
```

The command creates `forge.yaml`, bootstraps stable project and owner UUIDs, creates the approved
`.forge/` directory structure, and appends the hybrid Git block documented in
[`git-policy.md`](../git-policy.md). The block keeps governed configuration and records visible
while excluding `.forge/local/`. Existing unrelated files, ignore rules, bytes, and newline style
are preserved.

The configured owner is a governance identity, not authentication. A malicious process running
with the same operating-system permissions can impersonate it or alter files; FORGE does not
claim same-user isolation.

## Safety and repeat behavior

Initialization refuses to:

- overwrite an existing invalid `forge.yaml`,
- adopt a non-empty `.forge/` directory when no FORGE configuration exists,
- manage `forge.yaml`, `.forge/`, or `.gitignore` through symbolic links,
- merge a `.gitignore` that is not UTF-8,
- store a recognizable credential in tracked configuration.

Running `forge init` again validates and reuses the existing project and owner identities. It may
create a missing required directory, upgrade a legacy local-only ignore rule, or re-append the
hybrid policy after a later conflicting rule, but it does not replace configuration, change the
owner name, or mutate the Git index or history.

`forge.yaml` is strict, bounded safe YAML. Unknown fields, unsupported schema versions, anchors,
aliases, and recognizable credential patterns are rejected. Validate or inspect it with:

```console
forge config validate
forge config show
```

Initialization creates an empty `.forge/active/` directory. It does not create `events.jsonl`,
`state.json`, an initiative, or any lifecycle record; those belong to later M1 increments.
