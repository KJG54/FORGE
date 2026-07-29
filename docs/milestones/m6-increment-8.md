# M6 Increment 8 — Release-Candidate Closeout

## Authorized scope

- record the owner's exact Increment 7 scope acceptance;
- expand tests to every supported operating-system and Python-version cell;
- execute the exact-wheel 18-cell venv/`pipx` installation matrix;
- complete both example workflows from the built wheel on every operating system;
- enforce performance budgets across all nine operating-system/Python cells;
- maintain a shell-free backup, migration, recovery, abandonment, archive, and successor rehearsal;
- run complete local source, build, wheel, security, performance, and procedure validation;
- produce governed implementation, verification, friction, residual-risk, readiness, and lessons
  artifacts;
- require explicit owner acceptance at every remaining framework-change step;
- publish the M6 evidence report only after exact remote pull-request and merged-commit evidence;
  and
- leave M7 and public release pending separate owner authorization.

## Explicit exclusions

New runtime features, public contracts, schemas, migrations, bundled pack bytes, dependencies,
automatic remediation, fabricated acceptance, package version `1.0.0`, tags, signing, package
upload, public release, post-v1 support promises, and M7 implementation are not authorized.

## Validation architecture

[ADR-0057](../adr/ADR-0057-one-wheel-release-closeout-matrix.md) records the one-wheel matrix,
scenario distribution, and trigger decision. The
[release-candidate closeout guide](../release-candidate-closeout.md) defines interpretation and
required evidence.

The procedure tool creates only synthetic temporary repositories, uses fixed subprocess argument
vectors with `shell=False`, validates expected output, and fails closed on any unsupported
condition. Successful closure remains covered by both exact-wheel example workflows.

## Governed status

The owner explicitly accepted the exact dogfood scope with the limitation that scope acceptance
does not establish M6 readiness or authorize M7, and with all Increment 8 validation, procedure,
friction, and risk work still identified as outstanding.

The owner explicitly accepted the exact `implement` artifact revision after focused validation.
The owner subsequently accepted the exact `verify-release`, `review-risk`, and `closeout` evidence.
All workflow steps are complete, and the initiative is preserved in a hardened successful archive.

## Validation evidence

Focused implementation evidence is recorded and owner-accepted. Local closeout evidence covers 348
passing tests, Ruff, strict Pyright, source and wheel builds, both installation modes, both example
workflows, all maintained procedures, performance budgets, and the supply-chain and secret review.
The corrected pull-request candidate and exact merged-`main` commit each passed all 38 jobs. The
governed friction, residual-risk, readiness, and lessons artifacts are accepted and preserved in
the [M6 evidence and release-readiness report](m6-report.md).

## Stop points

Stop at every configured-owner acceptance gate. Do not treat a claim, check, evidence packet,
green CI result, merge, or this milestone document as acceptance. This stop point is satisfied:
M6 is complete and owner-accepted. Do not begin M7, tag, sign, upload, or publish without a
separate owner-authorized scope.
