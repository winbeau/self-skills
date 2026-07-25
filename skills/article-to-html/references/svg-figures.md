# Inline SVG figures

Figures are content, not style. Use inline SVG only when a diagram materially improves comprehension. Prefer semantic HTML for tables and lists. Do not fetch images, icon packages, fonts, or scripts.

## Required contract

```html
<figure>
  <svg viewBox="0 0 760 360" role="img" aria-labelledby="flow-title flow-desc">
    <title id="flow-title">Request flow</title>
    <desc id="flow-desc">Requests move from the browser through an API service to durable storage; tool execution happens in an isolated worker.</desc>
    <!-- marks -->
  </svg>
  <figcaption><span class="fig-num">Figure 1.</span>Request flow and isolation boundary.</figcaption>
</figure>
```

Rules:

- Give each meaningful SVG a unique `<title>` and `<desc>` pair. The description should state the relationship or conclusion a sighted reader gets from the figure.
- Use `role="img"` plus `aria-labelledby`. Decorative SVG uses `aria-hidden="true"` instead.
- Keep text as SVG `<text>` where practical. Do not use `<foreignObject>` or raw HTML.
- Never include `<script>`, external `<image href>`, event attributes, animation tags, or links inside SVG.
- Avoid color-only meaning. Pair color with labels, shapes, line styles, or direct annotations.
- Keep contrast readable, labels large enough, and the viewBox responsive. At a 500 px viewport the entire figure should fit without horizontal page overflow.
- Use no more than five distinct semantic colors per figure.

## Profile palettes

### xju-notion

- Background: `#ffffff`
- Subtle surface: `#f7f6f3`
- Text: `#37352f`
- Muted text: `#787774`
- Border: `#edece9`
- Strong border: `#dcdad4`
- Link blue: `#2383e2`
- Accent teal: `#0f7b6c`
- Warning orange: `#d9730d`

### paper-proposal

- Background: `#ffffff`
- Paper: `#f7f7f5`
- Ink: `#1a1a1a`
- Soft ink: `#4a4a4a`
- Faint ink: `#7a7a7a`
- Rule: `#d8d8d2`
- Blue: `#6f9bb8`
- Amber: `#b88a4a`
- Olive: `#6b7560`

SVG presentation attributes may use CSS variables, but literal hex values make copied figures more portable. Keep the palette consistent with the selected profile.

## Architecture skeleton

```html
<figure>
  <svg viewBox="0 0 760 300" role="img" aria-labelledby="architecture-title architecture-desc">
    <title id="architecture-title">Three-stage architecture</title>
    <desc id="architecture-desc">Input is normalized by the API, processed by an isolated worker, and written to durable storage.</desc>
    <rect width="760" height="300" fill="#ffffff" />
    <defs>
      <marker id="architecture-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0 0 10 5 0 10z" fill="#0f7b6c" />
      </marker>
    </defs>
    <g fill="none" stroke="#0f7b6c" stroke-width="1.5" marker-end="url(#architecture-arrow)">
      <path d="M220 150H300" />
      <path d="M460 150H540" />
    </g>
    <g font-family="ui-monospace, Menlo, monospace" font-size="13" text-anchor="middle">
      <rect x="60" y="105" width="160" height="90" rx="8" fill="#f7f6f3" stroke="#dcdad4" />
      <text x="140" y="145" fill="#37352f">INPUT</text>
      <text x="140" y="166" fill="#787774" font-size="11">normalize</text>
      <rect x="300" y="105" width="160" height="90" rx="8" fill="#ffffff" stroke="#0f7b6c" />
      <text x="380" y="145" fill="#37352f">WORKER</text>
      <text x="380" y="166" fill="#787774" font-size="11">isolated execution</text>
      <rect x="540" y="105" width="160" height="90" rx="8" fill="#f7f6f3" stroke="#dcdad4" />
      <text x="620" y="145" fill="#37352f">STORAGE</text>
      <text x="620" y="166" fill="#787774" font-size="11">durable state</text>
    </g>
  </svg>
  <figcaption><span class="fig-num">Figure 1.</span>Three-stage architecture.</figcaption>
</figure>
```

## Timeline skeleton

```html
<figure>
  <svg viewBox="0 0 760 260" role="img" aria-labelledby="timeline-title timeline-desc">
    <title id="timeline-title">Old and new request timing</title>
    <desc id="timeline-desc">The old path waits for infrastructure before useful work begins; the new path overlaps setup with interactive work.</desc>
    <rect width="760" height="260" fill="#ffffff" />
    <line x1="170" y1="220" x2="710" y2="220" stroke="#787774" />
    <g font-family="ui-monospace, Menlo, monospace" font-size="12">
      <text x="150" y="90" text-anchor="end" fill="#d9730d">OLD</text>
      <rect x="170" y="72" width="260" height="28" rx="6" fill="rgba(217,115,13,0.1)" stroke="#d9730d" />
      <text x="300" y="91" text-anchor="middle" fill="#37352f">blocking setup</text>
      <text x="150" y="170" text-anchor="end" fill="#0f7b6c">NEW</text>
      <rect x="170" y="152" width="100" height="28" rx="6" fill="rgba(15,123,108,0.1)" stroke="#0f7b6c" />
      <text x="220" y="171" text-anchor="middle" fill="#37352f">start</text>
      <rect x="270" y="152" width="260" height="28" rx="6" fill="rgba(15,123,108,0.1)" stroke="#0f7b6c" />
      <text x="400" y="171" text-anchor="middle" fill="#37352f">interactive work</text>
    </g>
  </svg>
  <figcaption><span class="fig-num">Figure 2.</span>Setup leaves the critical path.</figcaption>
</figure>
```

## Quantitative figures

Before drawing a bar chart, timeline with values, or any quantitative graphic, verify every number from the source. Label units, baselines, and uncertainty. Use a semantic table instead when exact comparison matters more than shape. Do not infer missing values.

## Tiny Lucide subset

For interface controls around a figure, copy only the symbol needed from `assets/icons/lucide-subset.svg`. Preserve its Lucide 0.468.0 ISC comment. Do not use the icon subset as decorative content inside explanatory diagrams unless an icon genuinely improves comprehension.
