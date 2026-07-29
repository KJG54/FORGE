# Objective and Constraints

## Objective

Define a deterministic formatter that turns a small list of release-note entries into stable
Markdown grouped by category.

## Constraints

- Accept only already-parsed title and category text.
- Do not access the network or filesystem.
- Preserve input order within each category.
- Treat unsupported categories as an explicit error.
- This example produces a reviewed design, not production software.
