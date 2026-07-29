# Project Artifacts

## Interface sketch

`format_release_notes(entries) -> markdown`

Each entry contains a supported category and title. Validation completes before output is emitted.

## Example

Input:

- `added`: Export schema index
- `fixed`: Reject unknown category

Expected output:

```text
## Added
- Export schema index

## Fixed
- Reject unknown category
```

This is a design artifact only; no executable implementation is included.
