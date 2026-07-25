# Script-free native interactions

Generated documents are static and **must not contain JavaScript**. The template CSP uses `script-src 'none'`, and the validator rejects every `<script>` element, including scripts nested in SVG or MathML. Do not add inline event-handler attributes, meta refresh, external runtimes, or code that navigates, loads resources, submits data, or changes the CSP.

Prefer a fully static presentation. When a small interaction materially improves reading, use native HTML behavior only. Both profiles are light-only: do not add a theme toggle, dark-mode CSS, or `prefers-color-scheme` recommendation.

Every control must be keyboard reachable, visibly focused, and accurately labeled. Respect `prefers-reduced-motion` through the shared base CSS.

## Collapsible section

Use `<details>` and `<summary>`. This gives keyboard activation and state management without script. Keep a heading inside the expanded content so the document outline remains explicit.

```html
<details class="collapsible">
  <summary>Implementation details</summary>
  <div class="collapsible-body">
    <h2 id="implementation-details">Implementation details</h2>
    <p>…</p>
  </div>
</details>
```

Do not add a redundant custom button or manually set `aria-expanded`; the native element exposes its state.

## Long code or command blocks

Do not add a copy button: clipboard access requires JavaScript and is intentionally outside the generated-document contract. Make code easy to select and provide a concise instruction when useful.

```html
<div class="code-block">
  <p class="component-label">Command · select and copy</p>
  <pre id="command-example"><code>command --flag</code></pre>
</div>
```

## Large comparison tables

Do not add client-side filtering or sorting. Use one or more of these static alternatives:

- group rows under clear subheadings;
- split a large table into smaller labeled tables;
- provide a short summary list before the full table;
- keep the `.table-wrap` overflow contract for narrow viewports.

If the document truly requires dynamic filtering, sorting, clipboard access, live status, or scroll-state updates, it is outside this static-document Skill's output contract and should be implemented as an application instead.

## Table of contents

Generate a static TOC from the document skeleton. Fragment links provide native navigation without script.

```html
<nav class="toc" aria-label="On this page">
  <a href="#scope">Scope</a>
  <a href="#method">Method</a>
</nav>
```

Do not synthesize runtime IDs or use scroll observers to mutate `aria-current`.

## No submission forms or automatic navigation

Do not generate `<form>` elements, submit buttons, or `meta[http-equiv="refresh"]`. The output CSP sets `form-action 'none'`, and this Skill is for self-contained documents rather than data collection or redirects.

## Disallowed patterns

- Any `<script>` element, including inside SVG or MathML.
- Inline event-handler attributes such as `onclick` or `onload`.
- Meta refresh or other automatic navigation.
- Theme toggles or dark-mode variants.
- Clickable non-interactive elements.
- Figure zoom that traps the user.
- Dynamic filtering, sorting, copying, or TOC state implemented with JavaScript.
- Any mechanism that sends data, loads runtime resources, or changes the CSP.
