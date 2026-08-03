# Local Production-v1 Residual Risks

These are candid candidate-handoff risks, not evidence of final Production-v1 acceptance.

| ID | Risk | Severity | Candidate disposition |
|---|---|---|---|
| L8-R01 | A same-user agent or process can operate with the owner's filesystem authority; the owner-shell ceremony is not authentication or isolation. | High | Accepted only for personal/local testing. Keep exact command preview, configured-owner checks, and external isolation for untrusted code. |
| L8-R02 | Extended real-project usability and conversational friction are not yet known. | High | Blocks final local-v1 acceptance, not L8 candidate handoff. Execute and record the L9 owner campaign. |
| L8-R03 | Native Codex or Claude Code behavior may differ from CLI probes or change after an application update. | Medium | Exercise both native applications in L9 and retain manual fallback. Re-test after relevant provider changes. |
| L8-R04 | Heuristic secret screening can miss sensitive content or flag safe content. | High | Owner reviews exact bytes before governance, Git, or external sharing and rotates exposed credentials outside FORGE. |
| L8-R05 | Compatible dependency resolution can drift between installations of the exact wheel. | Medium | Record the installed inventory during L9; use a controlled cache or constraints when repeatability requires it. |
| L8-R06 | A backup that omits hidden `.forge/` content can preserve project files while losing governance history. | High | Test backup and restore on the owner's actual storage path and validate the restored copy before relying on it. |
| L8-R07 | The ignored binary artifacts can be deleted locally even though their tracked identity remains. | Medium | Preserve an access-controlled local copy. A missing artifact requires explicit return to L8 and a newly recorded identity, not an implicit rebuild. |
| L8-R08 | Historical public-M7 documents could be mistaken for current publication instructions. | Medium | Current guides point to this local candidate boundary; historical scope and ADRs remain labeled and must not be executed without a new owner decision. |
| L8-R09 | Current cross-platform support evidence predates the exact L8 artifacts. | Low for owner-local use; high for external claims | Make no public cross-platform claim. Treat any later platform expansion as separately evidenced work. |
