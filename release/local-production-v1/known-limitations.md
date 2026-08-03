# Local Production-v1 Known Limitations

These limitations apply to the exact candidate recorded in `candidate-manifest.json`.

- The candidate is unpublished and untagged. `1.0.0`, the wheel name, and passing checks do not
  establish a public release or final owner acceptance.
- L9 complete local automation, clean-install, lifecycle, security, and performance checks passed
  on the owner's Windows machine. Native Codex and Claude Code UI behavior still requires explicit
  owner-observed evidence, and extended real-project usability remains unaccepted.
- The exact artifacts were built on the owner's Windows machine. Historical cross-platform M6
  evidence remains useful, but it is not evidence for these exact local-v1 bytes.
- The pre-alpha package classifier remains deliberate while the candidate is unpublished. Project
  URLs and a dated public changelog section remain intentionally absent.
- Runtime dependencies are not vendored. A clean installation can resolve different compatible
  dependency versions unless the owner supplies an independently controlled package cache or lock.
- Direct Codex and Claude Code workspace agents operate with the owner's same-user filesystem
  access. FORGE ceremony records configured authority and operator provenance; it does not
  authenticate the human or isolate a hostile same-user process.
- Secret and credential screening is heuristic. A clean result cannot prove that content is safe to
  govern, commit, or share.
- The scratchpad and generated recap, transaction receipts, explanations, handoffs, protocol text,
  and successor briefs are derived views. They do not create governance authority or replace the
  canonical journal and records.
- Warm recap intentionally reports registered metadata and digests rather than embedding artifact
  content. The owner or agent must open the exact registered working files when content is needed.
- Provider CLI and native-application behavior can change independently of FORGE. Manual fallback
  remains the portable baseline when an adapter is unavailable or incompatible.
- The installed Codex CLI `0.139.0` is outside FORGE's supported managed-adapter range and therefore
  falls back safely to manual handoff. This does not block direct native Codex workspace use, which
  is the primary local-v1 surface; Claude Code CLI `2.1.207` passed the bounded adapter diagnostic.
- Nine symbolic-link tests are skipped on this Windows account because it lacks symbolic-link
  creation privilege. The remaining complete suite passes, and path-refusal coverage that does not
  require that privilege remains active.
- Public package-index, GitHub Release, publisher, public support, and service-level channels are
  outside this local candidate and have not been configured.
