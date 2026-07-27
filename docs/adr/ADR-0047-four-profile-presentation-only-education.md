# ADR-0047: Four-Profile Presentation-Only Education

**Status:** Accepted

**Milestone:** M5 Increment 4

## Context

FORGE already defines Minimal, Standard, Guided, and Mentored explanation profile values, but M1
authorized only Standard and Guided. The selected profile is stored in the initiative, and its text
comes from the exact locked workflow. The Production-v1 roadmap requires the two remaining
profiles and requires every profile to preserve identical governance.

Enabling another profile must not change permissions, steps, transitions, gates, checks, evidence,
acceptance, cancellation, or lifecycle outcomes. Compatibility also matters: existing locked and
local packs may contain only the earlier Standard and Guided text.

## Decision

Enable all four existing `ExplanationProfile` values at initiative creation when the selected
workflow provides matching inline `explanation_content`:

- Minimal gives the shortest boundary reminder.
- Standard gives the ordinary concise guidance.
- Guided names the required inputs, outputs, blockers, and owner decisions.
- Mentored explains why the governed records and boundaries matter.

Both bundled workflows provide all four profiles and advance with their manifests to `0.4.0`.
Explanation content remains ordinary safe-YAML workflow data, covered by the complete pack digest
and exact workflow lock. `PackManifest.explanation_paths` remains unsupported; this increment adds
no resource loader, rendering language, executable behavior, or external lookup.

The profile is selected only when creating an initiative through the existing `--explanation`
option or project default. Before writing any initiative state, creation confirms that the exact
selected workflow contains the requested profile. An unavailable profile fails without leaving a
partial initiative.

Pack validation continues to accept the established Standard/Guided baseline. This preserves old
two-profile locks and local data packs without migration. Such a pack may still create or reload a
Standard or Guided initiative, but it cannot create a Minimal or Mentored initiative until the pack
author publishes new exact workflow bytes and a new digest.

The workflow reducer, authorization services, transition conditions, record requirements, and
acceptance services never inspect explanation text. Tests compare the complete governance portion
of each bundled workflow and the initial materialized state across all four selections.

## Consequences

Users can select a concise or teaching-oriented presentation without receiving different
authority or an easier workflow. Mentored text is educational content, not advice that can approve
work, prove a claim, satisfy a check, create evidence, or replace owner acceptance.

Both bundled pack digests change because their exact manifest and workflow bytes change. Existing
initiatives remain bound to their earlier locked pack and workflow bytes. No persisted contract,
event type, materialized-state field, migration, or public schema is added; the schema export
remains at 51 models.

Shared bundled-pack conformance, profile switching after creation, explanation resource files,
long-gap resumption, bounded filesystem discovery, and later M5 work remain separate increments.
