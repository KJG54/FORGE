"""Exact presentation templates for consequential owner-personal actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OwnerActionPresentation:
    action: str
    command: str
    consequence: str


def owner_action_presentation(action: str) -> OwnerActionPresentation | None:
    """Return an exact command template and consequence for a reported owner gate."""

    if action.startswith("acceptance-record:"):
        step_id = action.removeprefix("acceptance-record:")
        return OwnerActionPresentation(
            action,
            f'forge acceptance record {step_id} --scope "<exact-accepted-scope>"',
            "accepts only the exact current revisions, checks, evidence, and named scope; "
            "it advances the step but does not authenticate the operator",
        )
    if action.startswith("pack-trust:"):
        pack_id = action.removeprefix("pack-trust:")
        return OwnerActionPresentation(
            action,
            f'forge pack trust {pack_id} --rationale "<owner-rationale>" --apply',
            "trusts only the locked declarative pack data and grants no executable authority",
        )
    if action.startswith("deviation-review:"):
        deviation_id = action.removeprefix("deviation-review:")
        return OwnerActionPresentation(
            action,
            f'forge deviation review {deviation_id} --option "<considered-option>" '
            '--outcome "<chosen-outcome>" --rationale "<owner-rationale>"',
            "records an immutable owner review; it does not erase the deviation or waive "
            "unrelated requirements",
        )
    if action.startswith("risk-accept:"):
        override_id = action.removeprefix("risk-accept:")
        return OwnerActionPresentation(
            action,
            f'forge risk accept {override_id} --rationale "<owner-rationale>" '
            '--residual-impact "<expected-impact>"',
            "accepts only this override's residual risk and grants no progression authority",
        )
    fixed = {
        "create": OwnerActionPresentation(
            action,
            'forge create "<objective>" --scope "<bounded-scope>" --pack <pack-id> '
            "--workflow <workflow-id> --explanation <profile> --trust-pack-data",
            "creates a new governed initiative and immutable workflow lock after explicit owner "
            "confirmation",
        ),
        "create-successor": OwnerActionPresentation(
            action,
            'forge create "<objective>" --scope "<bounded-scope>" --pack <pack-id> '
            "--workflow <workflow-id> --explanation <profile> --predecessor "
            "<archive-uuid> --trust-pack-data",
            "creates a fresh successor lineage; predecessor progress and acceptance are not "
            "imported",
        ),
        "resume": OwnerActionPresentation(
            action,
            "forge resume",
            "ends the governed pause after drift checks and restores only currently legal actions",
        ),
        "migrate": OwnerActionPresentation(
            action,
            "forge migrate --apply",
            "applies the previewed registered migration and preserves the legacy source for audit",
        ),
        "close": OwnerActionPresentation(
            action,
            'forge close --summary "<final-owner-summary>"',
            "creates a terminal closed archive only after all workflow requirements are accepted",
        ),
        "abandon": OwnerActionPresentation(
            action,
            'forge abandon --reason "<owner-reason>" --unfinished-work '
            '"<unfinished-work>" --risk "<unresolved-risk-or-none-known>"',
            "creates a terminal abandoned archive without claiming unfinished work was accepted",
        ),
    }
    return fixed.get(action)
