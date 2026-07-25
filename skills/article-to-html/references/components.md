# Article components

Use these contracts inside `<article class="doc">`. They are style-neutral: `assets/styles/base.css` supplies structure and the selected profile supplies the visual treatment. Content guidance belongs in `SKILL.md`; do not choose a component merely because it looks decorative.

## Required page shell

```html
<a class="skip-link" href="#main-content">Skip to content</a>
<main id="main-content">
  <article class="doc" aria-labelledby="document-title">
    <!-- document -->
  </article>
</main>
```

The document must have a declared `lang`, exactly one H1, and valid heading order. Use one `<main>` landmark and unique IDs.

## Header

```html
<header class="doc-header">
  <div class="doc-eyebrow"><span class="mascot" aria-hidden="true"></span>Team · Document type</div>
  <h1 class="doc-title" id="document-title">Main title</h1>
  <p class="doc-subtitle">One-sentence subtitle or stance</p>
  <div class="doc-meta" aria-label="Document metadata">
    <span>STATUS · DRAFT</span>
    <span>DATE · 2026-07-25</span>
    <span>AUTHOR · Team / Author</span>
  </div>
</header>
```

Metadata is optional; omit missing facts instead of inventing them.

## Summary / TL;DR

```html
<aside class="tldr" aria-labelledby="tldr-label">
  <div class="tldr-label" id="tldr-label">TL;DR</div>
  <p>Three or four concise sentences.</p>
</aside>
```

Use this for an abstract, executive summary, or actual TL;DR. It is required only for `paper-proposal`; `xju-notion` may use a normal opening paragraph if that better matches the source.

## Section

Default and `xju-notion`:

```html
<section aria-labelledby="scope">
  <h2 id="scope">Scope</h2>
  <p>Body paragraph.</p>
  <h3>Subheading</h3>
</section>
```

`paper-proposal` keeps numbered H2 labels:

```html
<section aria-labelledby="scope-paper">
  <h2 id="scope-paper"><span class="num" aria-hidden="true">01</span>Scope</h2>
</section>
```

The visible heading text must remain meaningful without the number.

## Callouts

```html
<aside class="callout" aria-labelledby="note-label">
  <div class="callout-label" id="note-label">Note</div>
  <p>A short clarification.</p>
</aside>

<aside class="callout warn" aria-labelledby="risk-label">
  <div class="callout-label" id="risk-label">Risk</div>
  <p>A concrete warning, constraint, or deferred decision.</p>
</aside>

<blockquote class="callout cite">
  <p>“A quoted line.”</p>
  <footer class="cite-source">Author · Source</footer>
</blockquote>
```

Keep callouts scarce. Do not turn every paragraph into a card.

## Cards

Use cards for genuinely parallel concepts, not ordinary prose.

```html
<div class="cards cols-2">
  <section class="card" aria-labelledby="card-a-title">
    <div class="card-icon">ROLE A</div>
    <h3 class="card-name" id="card-a-title">Concept</h3>
    <div class="card-where">Context</div>
    <p class="card-desc">One concise explanation.</p>
  </section>
  <section class="card" aria-labelledby="card-b-title">…</section>
</div>
```

Supported grid modifiers are `.cols-2` and `.cols-4`; all profiles collapse cards at narrow widths. In `paper-proposal`, `.tone-a`, `.tone-b`, and `.tone-c` preserve the original blue, amber, and olive card accents.

## Table

Every data table needs a caption or an equivalent accessible label, column/row scopes, and a narrow-viewport wrapper.

```html
<div class="table-wrap" role="region" aria-labelledby="comparison-caption" tabindex="0">
  <table>
    <caption id="comparison-caption">Deployment option comparison</caption>
    <thead>
      <tr>
        <th scope="col">Option</th>
        <th scope="col">Startup</th>
        <th scope="col">Risk</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th scope="row">Option A</th>
        <td class="num">90 ms</td>
        <td>Storage constraint</td>
      </tr>
    </tbody>
  </table>
</div>
```

Do not use a table for layout.

## Figure and inline SVG

```html
<figure>
  <svg viewBox="0 0 760 360" role="img" aria-labelledby="figure-1-title figure-1-desc">
    <title id="figure-1-title">Request flow</title>
    <desc id="figure-1-desc">A reader-facing description of the diagram and its conclusion.</desc>
    <!-- diagram marks -->
  </svg>
  <figcaption><span class="fig-num">Figure 1.</span>Request flow from client to storage.</figcaption>
</figure>
```

Use informative `<title>` and `<desc>` text, not “diagram” or the filename. Decorative SVG must instead use `aria-hidden="true"` and must not carry meaningful content.

## Images

Generated documents cannot fetch remote images. Use an inline data URL only when the user supplied a safe local image and embedding is necessary.

```html
<figure>
  <img src="data:image/png;base64,…" alt="Concise description of the image's relevant content" />
  <figcaption>Optional visible caption.</figcaption>
</figure>
```

Never omit `alt`. Use `alt=""` only for a truly decorative image.

## Code block

```html
<div class="code-block">
  <pre><code>command --flag
output</code></pre>
</div>
```

Escape `<`, `>`, and `&` from source code. Optional copy behavior is in `interactive.md` and must use a labeled button.

## Tiny icon contract

Only copy symbols actually used from `assets/icons/lucide-subset.svg`. The shared `.icon` class supplies `currentColor`, `fill: none`, round caps/joins, and stroke width `1.75`.

```html
<button class="icon-button" type="button" aria-label="Copy code">
  <svg class="icon" aria-hidden="true"><use href="#icon-copy"></use></svg>
  <span>Copy</span>
</button>
```

Icon-only controls require `aria-label`; text plus icon is preferred. Preserve the Lucide ISC comment when a symbol is copied.

## Read-only input controls

Generated documents are static and the CSP blocks form submission, so do not emit a `<form>` element or submit buttons. For a local table filter, use a labeled standalone input and safe JavaScript from `interactive.md`:

```html
<label for="comparison-filter">Filter comparison</label>
<input id="comparison-filter" type="search" autocomplete="off" />
<p class="interactive-status" aria-live="polite"></p>
```

## Footer

```html
<footer class="doc-footer">
  <h2>References</h2>
  <ul>
    <li>Author · <a href="https://example.com" rel="noopener noreferrer">Source title</a></li>
  </ul>
</footer>
```

HTTP(S) reference links may remain clickable. They are navigation, not runtime assets. Reject unsafe schemes and do not fabricate references.
