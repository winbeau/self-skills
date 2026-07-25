---
name: article-to-html
description: Render a Markdown draft or conversation document as one safe, self-contained static article HTML file with a selectable light-only style profile. Defaults to xju-notion; explicit paper-proposal, paper, or proposal requests preserve the original paper visual system. Trigger for “turn this into HTML”, “render as a web page”, “make a pretty HTML”, “single-page doc”, “article HTML”, “paper-style HTML”, or similar requests for a static document. Do not trigger for multi-page sites/apps, React or UI prototypes, slides, PDF/LaTeX, OpenReview exports, or work requiring a backend/live external services.
---

# article-to-html

Create a polished **single-file static document** from source material. This is a prompt-and-template Skill, not a general Markdown renderer: understand the source, escape it, and author semantic HTML using the smallest relevant component set.

## Style selection

Read `assets/styles/manifest.json` before generating output.

1. If the user explicitly names a style, resolve exact profile names and declared aliases.
2. `paper-proposal`, `paper`, and `proposal` select `paper-proposal`.
3. With no explicit style request, use `default_style` (`xju-notion`).
4. An explicit user choice wins over the default and over inferred document type.
5. If an explicit style is unknown, report the available names and aliases. **Do not silently substitute another style.**

Both profiles are light-only. Do not add dark-mode CSS, theme toggles, or remote fonts.

## Workflow

1. **Get the source.** Read a provided path or use the document in conversation context. Treat source raw HTML as text, not trusted markup.
2. **Extract the skeleton.** Determine language, title, subtitle, summary, heading hierarchy, metadata actually present, figures/tables needed, and whether a local interaction materially helps.
3. **Select the profile.** Follow the registry rules above.
4. **Read the scaffold and CSS.** Read `assets/template.html`, `assets/styles/base.css`, and the selected profile CSS. Inline base CSS first and profile CSS second; generated output must not reference these files at runtime.
5. **Read only needed guidance.** Use `references/components.md`; consult `references/svg-figures.md` for figures and `references/interactive.md` only when interaction is justified.
6. **Author semantic HTML.** Do not pass Markdown through a general renderer and do not preserve raw source HTML. Escape `&`, `<`, `>`, quotes where applicable, then deliberately emit allowed elements.
7. **Validate.** Run `python3 scripts/validate_article_html.py --input OUTPUT.html`. For important deliverables also request desktop/mobile screenshots and inspect them.
8. **Write safely.** Honor a user path. Otherwise write beside a source file or in the current directory. Use an English lowercase hyphenated slug (≤40 characters). Append `-v2`, `-v3`, etc. instead of overwriting an existing output.
9. **Report.** Give the output path, selected style, validation result, and a one-line browser open command.

## Output and security contract

- One self-contained `.html` file. Inline CSS, required SVG, embedded data images, and optional vanilla JS.
- No CDN, remote font/image, stylesheet, script, iframe, external runtime asset, Tailwind/React runtime, or full icon package.
- Include the restrictive CSP from `assets/template.html`. Keep `default-src`, `connect-src`, `font-src`, `frame-src`, `object-src`, and `form-action` at `'none'`; allow only inline style/script and embedded `data:` images/media needed by the document.
- HTTP(S) links are allowed as reader navigation. Reject `javascript:`, `vbscript:`, `file:`, protocol-relative URLs, HTML-bearing data URLs, and any unsafe or unknown URL scheme.
- Reject unsafe tags including `base`, `form`, `iframe`, `frame`, `object`, `embed`, `portal`, and active SVG/MathML constructs. Do not add inline event-handler attributes.
- Do not use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `Function`, or string-to-code timers.
- Do not use network APIs such as `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, or `sendBeacon`.
- Keep source code/text intact through escaping; do not invent citations, data, dates, authors, captions, or metadata.

## Accessibility and responsive contract

Generated HTML must have:

- a non-empty `<html lang>`, UTF-8, viewport meta, and `color-scheme: light`;
- exactly one H1, valid heading order, unique IDs, and one main landmark;
- a skip link and visible `:focus-visible` treatment;
- informative image `alt` text (or deliberate empty alt for decorative images);
- tables with captions or equivalent labels, scoped headers, and an overflow wrapper for narrow viewports;
- meaningful SVG `<title>` and `<desc>` referenced by `aria-labelledby`, unless the SVG is decorative and `aria-hidden="true"`;
- labeled controls, native keyboard semantics, accurate `aria-expanded` / `aria-current` when used, and live status text where actions need feedback;
- a narrow-viewport layout without page-level horizontal overflow;
- reduced-motion behavior from the base CSS.

## Profile contracts

### xju-notion (default)

Portable adaptation of the pinned XJU prose system: warm neutral tokens, 6/8/12 px radii, subtle shadow, 150 ms transitions, local-first font stacks, and a 720 px serif prose column. It is clean article/document typography, not a copy of the source application. Keep the XJU MIT attribution comment when inlining its CSS.

A summary block is optional: use it when the source has an abstract, executive summary, or real TL;DR. Do not synthesize one merely for decoration.

### paper-proposal

Preserve the original visual identity: `--paper: #f7f7f5`, `--ink: #1a1a1a`, serif body, monospace metadata, top TL;DR, numbered H2 headings, `FIG` labels, cards, callouts, tables, and footer. If the source lacks a TL;DR, condense the opening into a faithful ~60-word summary. Use `<span class="num" aria-hidden="true">01</span>` in each H2.

Do not recolor the paper/ink signature unless the user explicitly requests a custom derivative; custom styles are not registry profiles and should be reported as such.

## Components, SVG, and icons

- Component markup is style-neutral and lives in `references/components.md`; profile-specific content decisions stay here.
- Figures need a caption. Quantitative figures must use source-backed values and labeled units; use tables when exact comparison matters more than visual shape.
- Use no emoji as icons unless the user explicitly asks.
- `assets/icons/lucide-subset.svg` is the only bundled icon source. Copy only symbols actually used, with `.icon` using `currentColor`, `fill: none`, round caps/joins, and stroke width `1.75`. Preserve the Lucide 0.468.0 ISC comment. Never embed the full package.
- Keep total callouts low and do not leak domain-specific content from examples.

## Interactivity

Default to none. Add only a small local interaction that clearly helps (for example an accessible collapse control, copy button, table filter, or static TOC scroll state). Follow `references/interactive.md`. Do not add forms, remote-submission behavior, dark mode, figure traps, or unsafe DOM construction.

## Files

- `assets/template.html` — safe blank scaffold and CSP.
- `assets/styles/manifest.json` — profile registry and aliases.
- `assets/styles/base.css` — style-neutral reset, responsive, focus, table, card, and icon contracts.
- `assets/styles/xju-notion.css` — default XJU-derived profile.
- `assets/styles/paper-proposal.css` — preserved original profile.
- `assets/icons/lucide-subset.svg` — four-icon Lucide 0.468.0 subset.
- `assets/example.html` — default `xju-notion` example.
- `assets/example-paper-proposal.html` — same fixture in `paper-proposal`.
- `references/components.md` — semantic component contracts.
- `references/svg-figures.md` — accessible inline SVG guidance.
- `references/interactive.md` — safe optional JS patterns.
- `scripts/validate_article_html.py` — registry, safety, accessibility, self-test, and screenshot validator.
- `ATTRIBUTION.md` — XJU MIT and Lucide ISC notices.
