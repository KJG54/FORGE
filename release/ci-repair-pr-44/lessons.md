# PR 44 CI Repair Lessons

## Repository-state tests must follow lifecycle transitions

When an initiative is terminal and archived, tests that validate its historical state should load the immutable archive instead of depending on an active workspace initiative. Lifecycle transitions can make an otherwise valid active-state test assumption stale without indicating a production-code defect.

## Preserve history while changing the lookup

Replacing an active-state lookup should not weaken historical assertions. The repaired test continues to require both predecessor identities, their distinct terminal outcomes, the locked pack and workflow, trusted pack data, and the exact terminal archive digest.

## Bind historical tests to immutable identity

An archive digest converts a general state assertion into an assertion about exact preserved history. This reduces the risk that a test silently validates a different archive or a rewritten fixture.

## Focused verification and matrix verification serve different purposes

The focused test provides fast evidence that the bounded assumption is repaired. It does not replace the Windows, Ubuntu, and macOS matrix, which remains necessary to establish the remote CI outcome after publication.

## Keep governance and Git authority separate

FORGE acceptance establishes the governed status of exact local revisions, checks, evidence, limitations, and scope. It does not create a commit or authorize a push. Git publication remains a separate owner-controlled action and should publish only the exact accepted candidate.

## Reusable closeout principle

For future terminal-state repairs, explicitly classify local readiness, remote publication, and remote CI observation as three separate facts. This prevents a passing local command from being overstated as a completed cross-platform repair.
