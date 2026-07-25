# article-to-html Skill

`article-to-html` turns a Markdown draft, pasted document, or conversation-context document into one safe, self-contained static HTML file. It is prompt-driven rather than a general Markdown renderer: the agent understands the document, escapes source markup, and deliberately authors semantic HTML.

## Styles

The style registry is `assets/styles/manifest.json`.

- **Default: `xju-notion`** — a light-only, warm-neutral 720 px serif document profile adapted from the pinned XJU prose system. It uses local-first fonts, 6/8/12 px radii, subtle card shadows, and restrained 150 ms transitions.
- **`paper-proposal`** — the original visual system: paper palette, serif body, monospace metadata, TL;DR, numbered H2 headings, FIG labels, cards, callouts, tables, and footer.
- **Aliases:** `paper` and `proposal` both select `paper-proposal`.

An explicit style request wins. Unknown explicit styles are reported with the available names instead of silently falling back.

Examples:

```text
Turn this draft into one self-contained HTML document.
Use article-to-html with the paper-proposal style for docs/rfc.md.
Render this as article HTML, style paper.
```

## Scope

Use this Skill for generic self-contained article/document HTML such as reports, proposals, RFCs, tutorials, and long-form notes.

Do not use it for:

- multi-page sites or web applications;
- React/UI prototypes;
- slides;
- PDF or LaTeX output;
- OpenReview exports (use `openreview-to-html`);
- documents requiring a backend or live external services.

## Output contract

The output is one `.html` file with:

- inline CSS, inline SVG, and, only when necessary, embedded `data:` images;
- no JavaScript, CDN, remote font/image, external runtime asset, Tailwind/React runtime, or full icon package;
- a restrictive Content Security Policy with `script-src 'none'`;
- escaped source raw HTML and rejected scripts, meta refresh, unsafe tags (including forms), URL schemes, event attributes, DOM sinks, and network APIs;
- a declared language, exactly one H1, valid heading order, unique IDs, a skip link, keyboard focus, reduced-motion behavior, and narrow-viewport handling;
- image alt text, labeled/scoped tables, informative SVG titles/descriptions, and labeled controls.

Both profiles are light-only. The Skill does not recommend or generate dark mode.

## Output location

- A source file path produces output beside the source unless the user specifies another path.
- Conversation-context input produces output in the current directory.
- The default filename is an English lowercase hyphenated title slug, at most 40 characters.
- Existing files are not silently overwritten; `-v2`, `-v3`, and so on are used.

## Repository structure

```text
skills/article-to-html/
├── SKILL.md
├── ATTRIBUTION.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── template.html
│   ├── example.html
│   ├── example-paper-proposal.html
│   ├── icons/
│   │   └── lucide-subset.svg
│   └── styles/
│       ├── manifest.json
│       ├── base.css
│       ├── xju-notion.css
│       └── paper-proposal.css
├── references/
│   ├── components.md
│   ├── svg-figures.md
│   └── interactive.md
└── scripts/
    └── validate_article_html.py
```

- `assets/template.html` is the safe blank scaffold with the CSP.
- `assets/styles/base.css` defines style-neutral component, focus, responsive, table, card, and icon contracts.
- The two profile stylesheets contain visual treatment only.
- `assets/example.html` and `assets/example-paper-proposal.html` render the same fixture with different profiles.
- `assets/icons/lucide-subset.svg` contains only four Lucide 0.468.0 symbols. See `ATTRIBUTION.md` for XJU MIT and Lucide ISC notices.

## Validation

The validator has no third-party Python dependency.

```bash
python3 -m py_compile skills/article-to-html/scripts/validate_article_html.py
python3 skills/article-to-html/scripts/validate_article_html.py --check-assets
python3 skills/article-to-html/scripts/validate_article_html.py --self-test

python3 skills/article-to-html/scripts/validate_article_html.py \
  --input skills/article-to-html/assets/example.html \
  --style xju-notion \
  --screenshot /tmp/article-xju-desktop.png \
  --mobile-screenshot /tmp/article-xju-mobile.png
```

Screenshot checks require a Linux Chrome/Chromium binary. The mobile smoke viewport is 500×844 because headless Chrome clamps very narrow desktop windows.

## Development notes

This Skill has no renderer package or build system. When changing it:

1. keep the registry and examples consistent;
2. inline `base.css` before exactly one selected profile;
3. preserve required attribution comments in copied CSS/SVG;
4. keep component guidance style-neutral and style/content policy in `SKILL.md`;
5. run the focused validator plus the repository-wide `python3 scripts/validate_skills.py`.
