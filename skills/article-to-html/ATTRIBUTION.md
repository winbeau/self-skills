# Attribution — article-to-html

This Skill contains first-party material plus a portable style adaptation and a small icon subset. Generated documents should preserve the attribution comments included with copied CSS or SVG source. User-facing attribution in the rendered page is optional unless the document itself discusses these sources.

## XJU Notion style source

The `xju-notion` profile in `assets/styles/xju-notion.css` adapts a portable subset of styles from the local `xju-feiyue` project.

- **Repository working copy**: `/home/winbeau/Projects/xju-feiyue`
- **Revision**: `fd4d4ac61fa70901a4c34e5601aec5f9a4c66a27`
- **Source paths**:
  - `frontend/src/styles/tokens.css`
  - `frontend/src/styles/globals.css`
  - `frontend/src/styles/prose-claude.css`
- **Copyright**: Copyright (c) 2026 winbeau
- **License**: MIT License

Only the warm neutral surface/text/border/link tokens, 6/8/12 px radii, subtle card shadow, 150 ms transition, local-first sans/serif/monospace stacks, and the 720 px serif prose contract were adapted. The profile intentionally excludes Google Fonts imports, Tailwind directives, shadcn HSL bridge variables, category and feature variables, page-specific CSS, comment-anchor and flash-highlight CSS, React/rehype/next-themes behavior, dark-mode placeholders, and raw-HTML rendering behavior.

MIT notice:

```text
MIT License

Copyright (c) 2026 winbeau

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Lucide icon subset

`assets/icons/lucide-subset.svg` contains only four icons from Lucide `0.468.0`: `copy`, `check`, `chevron-down`, and `external-link`. Generated SVG uses `currentColor`, `fill="none"`, round line caps and joins, and stroke width `1.75` through the shared `.icon` contract. Do not copy the full icon package into output.

- **Project**: Lucide
- **Version**: `0.468.0`
- **Website**: <https://lucide.dev/>
- **Source**: <https://github.com/lucide-icons/lucide/tree/0.468.0>
- **Copyright**: Copyright (c) 2020-present Lucide Contributors
- **License**: ISC License

ISC notice:

```text
ISC License

Copyright (c) 2020-present Lucide Contributors

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
```
