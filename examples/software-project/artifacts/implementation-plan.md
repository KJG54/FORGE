# Implementation Plan

1. Define an immutable release-note entry with category and title.
2. Validate every category before rendering.
3. Group entries without reordering them.
4. Render the three supported headings in a fixed sequence.
5. Add examples for empty input, one category, all categories, and invalid input.
6. Review deterministic behavior and document remaining limitations.
