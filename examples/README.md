# FORGE Example Repositories

These two examples are ordinary, uninitialized project directories:

- `software-project` follows the bundled six-step `software-basic` workflow.
- `research-project` follows the bundled seven-step `research-basic` workflow.

They contain synthetic starting artifacts only. They intentionally contain no `.forge` state,
owner identity, acceptance, check result, evidence packet, journal, archive, credential, executable
script, or generated identifier.

Install FORGE as described in [`docs/installation.md`](../docs/installation.md), copy one example
to a writable directory, and follow its README. For each workflow row, the human-directed cycle is:

1. `forge begin <step> -C <copy>`
2. register every listed file with `forge artifact add` and retain each revision ID;
3. `forge complete <step>` and retain the reported claim ID;
4. record every declared check and retain each check-result ID;
5. register one evidence packet bound to the current artifact revisions, claim, and checks;
6. `forge verify <step>`; and
7. inspect the exact records before the owner runs `forge acceptance record <step>`.

The command pattern for one step is:

```console
forge begin <step> -C <copy>
forge artifact add <file> --role <role> --title "<title>" \
  --media-type text/markdown -C <copy>
forge complete <step> --assertion "<bounded worker claim>" \
  --limitation "<known claim limitation>" -C <copy>
forge check record <step> <check-id> --invocation "<what was reviewed>" \
  --outcome passed --exit-status 0 --limitation "<check limitation>" -C <copy>
forge evidence add <step> --purpose "<bounded support purpose>" \
  --artifact-revision <revision-id> --check-result <check-result-id> \
  --claim <claim-id> --limitation "<evidence limitation>" -C <copy>
forge verify <step> -C <copy>
forge acceptance record <step> --scope "<exact accepted scope>" \
  --known-limitation "<accepted limitation>" --residual-risk "<remaining risk>" -C <copy>
```

Repeat `--artifact-revision` and `--check-result` for every current output and declared check.
Before acceptance, use `forge artifact show`, `forge check show`, and `forge evidence show` with the
reported IDs. Replace every placeholder with an exact, truthful value; do not copy the synthetic
rehearsal's acceptance language into real work.

The repository-local `tools/example_workflow_smoke.py` harness performs that cycle only in a fresh
temporary copy with a synthetic owner. It exists for release testing and must not be used to
manufacture acceptance for real work.
