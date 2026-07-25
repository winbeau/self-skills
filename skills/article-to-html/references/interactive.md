# Optional local interactions

Default to static HTML. Add an interaction only when it improves comprehension or task completion. Both profiles are light-only: do not add a theme toggle, dark-mode CSS, or `prefers-color-scheme` recommendation.

Generated scripts must be inline, dependency-free, and compatible with the restrictive CSP in `assets/template.html`. They must not use network APIs (`fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `sendBeacon`), dynamic code (`eval`, `Function`), raw HTML sinks (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`), inline event-handler attributes, or externally loaded assets.

Use `textContent`, `classList`, `setAttribute`, `append`, and `replaceChildren` for DOM updates. Every control must be keyboard reachable, visibly focused, and labeled. Respect `prefers-reduced-motion` through the shared base CSS.

## Collapsible section

Use a real button inside the heading. Do not make the heading itself clickable.

```html
<section class="collapsible" aria-labelledby="details-heading">
  <h2 id="details-heading">
    Details
    <button class="icon-button section-toggle" type="button" aria-expanded="true" aria-controls="details-body">
      <span>Collapse</span>
      <svg class="icon" aria-hidden="true"><use href="#icon-chevron-down"></use></svg>
    </button>
  </h2>
  <div id="details-body">…</div>
</section>

<script>
  document.querySelectorAll(".section-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = document.getElementById(button.getAttribute("aria-controls"));
      if (!panel) return;
      const expanded = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", String(!expanded));
      panel.hidden = expanded;
      const label = button.querySelector("span");
      if (label) label.textContent = expanded ? "Expand" : "Collapse";
    });
  });
</script>
```

Copy `chevron-down` from the tiny Lucide subset only if the icon is used. The visible text is the accessible label; an icon-only variant must use `aria-label`.

## Copy button

The Clipboard API is local, but may be unavailable on `file:` pages. Provide a status message and fail gracefully.

```html
<div class="code-block">
  <button class="btn copy-button" type="button" data-copy-target="command-example">Copy</button>
  <pre id="command-example"><code>command --flag</code></pre>
  <p class="interactive-status" aria-live="polite"></p>
</div>

<script>
  document.querySelectorAll(".copy-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copyTarget || "");
      const status = button.parentElement?.querySelector(".interactive-status");
      if (!target || !status) return;
      try {
        await navigator.clipboard.writeText(target.textContent || "");
        status.textContent = "Copied to clipboard.";
      } catch {
        status.textContent = "Copy is unavailable here. Select the text manually.";
      }
    });
  });
</script>
```

## Table filter

Filtering is local and may hide rows. Announce the remaining row count.

```html
<label for="comparison-filter">Filter comparison</label>
<input id="comparison-filter" type="search" autocomplete="off" />
<p id="comparison-status" class="interactive-status" aria-live="polite"></p>

<script>
  const filter = document.getElementById("comparison-filter");
  const table = document.querySelector("table[data-filterable]");
  const status = document.getElementById("comparison-status");
  if (filter && table && status && table.tBodies[0]) {
    const rows = Array.from(table.tBodies[0].rows);
    filter.addEventListener("input", () => {
      const query = filter.value.trim().toLocaleLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const match = row.textContent?.toLocaleLowerCase().includes(query) ?? false;
        row.hidden = !match;
        if (match) visible += 1;
      });
      status.textContent = `${visible} rows shown.`;
    });
  }
</script>
```

## Static table of contents with scroll state

Prefer generating the TOC in HTML from the document skeleton. JavaScript may update `aria-current`; it must not create headings or IDs at runtime.

```html
<nav class="toc" aria-label="On this page">
  <a href="#scope">Scope</a>
  <a href="#method">Method</a>
</nav>

<script>
  const tocLinks = Array.from(document.querySelectorAll(".toc a[href^='#']"));
  const sections = tocLinks
    .map((link) => document.getElementById(link.getAttribute("href")?.slice(1) || ""))
    .filter(Boolean);
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        tocLinks.forEach((link) => {
          const active = link.getAttribute("href") === `#${entry.target.id}`;
          if (active) link.setAttribute("aria-current", "location");
          else link.removeAttribute("aria-current");
        });
      });
    }, { rootMargin: "-35% 0px -55%" });
    sections.forEach((section) => observer.observe(section));
  }
</script>
```

## No submission forms

Do not generate `<form>` elements. The output CSP sets `form-action 'none'`, and this Skill is for self-contained documents rather than data collection. If a document needs a local filter or control group, use labeled standalone inputs and buttons. If it needs actual submission, a backend, or external data flow, it is outside this Skill's scope.

## Disallowed patterns

- Theme toggles or dark-mode variants.
- Clickable non-interactive elements such as `<div onclick>` or headings with click handlers.
- Figure zoom that traps the user or lacks an Escape path and focus management.
- Sorting triggered directly by a `<th>` without a nested button and `aria-sort` updates.
- `innerHTML` templates, even when the source appears trusted.
- Any script that sends data, loads resources, or changes the CSP.
