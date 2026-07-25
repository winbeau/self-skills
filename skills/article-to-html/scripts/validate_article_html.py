#!/usr/bin/env python3
"""Validate article-to-html assets and generated self-contained HTML."""

from __future__ import annotations

import argparse
import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
STYLES = ASSETS / "styles"
MANIFEST_PATH = STYLES / "manifest.json"
TEMPLATE_PATH = ASSETS / "template.html"
ICON_PATH = ASSETS / "icons" / "lucide-subset.svg"
CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")

FORBIDDEN_TAGS = {
    "applet",
    "base",
    "embed",
    "form",
    "frame",
    "frameset",
    "iframe",
    "object",
    "portal",
}
SVG_FORBIDDEN_TAGS = {"animate", "animatemotion", "animatetransform", "discard", "foreignobject", "set"}
URL_ATTRS = {"action", "cite", "data", "formaction", "href", "poster", "src", "xlink:href"}
REMOTE_ASSET_TAGS = {"audio", "embed", "iframe", "image", "img", "link", "object", "script", "source", "track", "video"}
ALLOWED_NAV_SCHEMES = {"http", "https", "mailto", "tel"}
DANGEROUS_JS_PATTERNS = {
    "innerHTML": re.compile(r"\binnerHTML\b", re.I),
    "outerHTML": re.compile(r"\bouterHTML\b", re.I),
    "insertAdjacentHTML": re.compile(r"\binsertAdjacentHTML\b", re.I),
    "document.write": re.compile(r"\bdocument\s*\.\s*write(?:ln)?\s*\(", re.I),
    "eval": re.compile(r"\beval\s*\(", re.I),
    "Function constructor": re.compile(r"\bnew\s+Function\b|\bFunction\s*\(", re.I),
    "string timer": re.compile(r"\bset(?:Timeout|Interval)\s*\(\s*['\"]", re.I),
    "fetch": re.compile(r"\bfetch\s*\(", re.I),
    "XMLHttpRequest": re.compile(r"\bXMLHttpRequest\b", re.I),
    "WebSocket": re.compile(r"\bWebSocket\b", re.I),
    "EventSource": re.compile(r"\bEventSource\b", re.I),
    "sendBeacon": re.compile(r"\bsendBeacon\s*\(", re.I),
    "dynamic import": re.compile(r"\bimport\s*\(", re.I),
}
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")


@dataclass
class Element:
    tag: str
    attrs: dict[str, str]
    index: int


class ArticleAuditParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.counts: dict[str, int] = {}
        self.elements: list[Element] = []
        self.ids: list[str] = []
        self.headings: list[tuple[int, dict[str, str], int]] = []
        self.styles: list[str] = []
        self.scripts: list[str] = []
        self.csp: str | None = None
        self.html_lang = ""
        self.title_text: list[str] = []
        self.document_title_count = 0
        self.color_scheme = ""
        self.viewport = ""
        self._stack: list[str] = []
        self._in_style = 0
        self._in_script = 0
        self._in_title = 0
        self.svg_depth = 0
        self.svgs: list[dict[str, object]] = []
        self._svg_stack: list[int] = []
        self.tables: list[dict[str, object]] = []
        self._table_stack: list[int] = []
        self.controls: list[dict[str, object]] = []
        self._control_stack: list[int] = []
        self.labels_for: set[str] = set()

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key.lower(): (value or "") for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        attr_map = self.attrs_dict(attrs)
        index = len(self.elements)
        self.elements.append(Element(lower, attr_map, index))
        self.counts[lower] = self.counts.get(lower, 0) + 1
        self._stack.append(lower)

        if lower in FORBIDDEN_TAGS:
            self.errors.append(f"forbidden tag: <{lower}>")
        if self.svg_depth and lower in SVG_FORBIDDEN_TAGS:
            self.errors.append(f"forbidden active SVG tag: <{lower}>")
        for name in attr_map:
            if name.startswith("on"):
                self.errors.append(f"inline event handler is forbidden: {lower}.{name}")
            if name in {"srcdoc"}:
                self.errors.append(f"raw HTML attribute is forbidden: {lower}.{name}")

        if lower == "html":
            self.html_lang = attr_map.get("lang", "").strip()
        elif lower == "meta":
            if attr_map.get("http-equiv", "").lower() == "content-security-policy":
                self.csp = attr_map.get("content", "")
            if attr_map.get("name", "").lower() == "viewport":
                self.viewport = attr_map.get("content", "")
            if attr_map.get("name", "").lower() == "color-scheme":
                self.color_scheme = attr_map.get("content", "")
        elif lower == "style":
            self._in_style += 1
            if attr_map.get("src"):
                self.errors.append("style tag must not have a src")
        elif lower == "script":
            self._in_script += 1
            if attr_map.get("src"):
                self.errors.append("external script is forbidden")
            if attr_map.get("type", "").lower() == "module":
                self.errors.append("module scripts are forbidden in generated output")
        elif lower == "title" and not self.svg_depth:
            self.document_title_count += 1
            self._in_title += 1

        heading = re.fullmatch(r"h([1-6])", lower)
        if heading:
            self.headings.append((int(heading.group(1)), attr_map, index))

        element_id = attr_map.get("id", "")
        if element_id:
            self.ids.append(element_id)

        if lower == "svg":
            svg = {
                "attrs": attr_map,
                "title_ids": [],
                "desc_ids": [],
                "external_images": [],
                "index": index,
            }
            self.svgs.append(svg)
            self._svg_stack.append(len(self.svgs) - 1)
            self.svg_depth += 1
        elif self.svg_depth and self._svg_stack:
            current = self.svgs[self._svg_stack[-1]]
            if lower == "title" and element_id:
                current["title_ids"].append(element_id)  # type: ignore[index, union-attr]
            elif lower == "desc" and element_id:
                current["desc_ids"].append(element_id)  # type: ignore[index, union-attr]
            elif lower == "image":
                href = attr_map.get("href") or attr_map.get("xlink:href") or ""
                if href:
                    current["external_images"].append(href)  # type: ignore[index, union-attr]

        if lower == "table":
            table = {"attrs": attr_map, "caption": False, "headers": [], "index": index}
            self.tables.append(table)
            self._table_stack.append(len(self.tables) - 1)
        elif self._table_stack:
            table = self.tables[self._table_stack[-1]]
            if lower == "caption":
                table["caption"] = True
            elif lower == "th":
                table["headers"].append(attr_map)  # type: ignore[index, union-attr]

        if lower == "label" and attr_map.get("for"):
            self.labels_for.add(attr_map["for"])
        if lower in {"button", "input", "select", "textarea"}:
            control = {"tag": lower, "attrs": attr_map, "text": []}
            self.controls.append(control)
            if lower in {"button", "select", "textarea"}:
                self._control_stack.append(len(self.controls) - 1)

        self._audit_url(lower, attr_map)
        self._audit_control(lower, attr_map)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "style" and self._in_style:
            self._in_style -= 1
        elif lower == "script" and self._in_script:
            self._in_script -= 1
        elif lower == "title" and self._in_title and not self.svg_depth:
            self._in_title -= 1
        elif lower == "svg" and self.svg_depth:
            self.svg_depth -= 1
            if self._svg_stack:
                self._svg_stack.pop()
        elif lower == "table" and self._table_stack:
            self._table_stack.pop()
        if lower in {"button", "select", "textarea"} and self._control_stack:
            self._control_stack.pop()
        if self._stack:
            if self._stack[-1] == lower:
                self._stack.pop()
            elif lower in self._stack:
                self._stack = self._stack[: len(self._stack) - 1 - self._stack[::-1].index(lower)]

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.styles.append(data)
        if self._in_script:
            self.scripts.append(data)
        if self._in_title and not self.svg_depth:
            self.title_text.append(data)
        if self._control_stack:
            self.controls[self._control_stack[-1]]["text"].append(data)  # type: ignore[index, union-attr]

    def _audit_url(self, tag: str, attrs: dict[str, str]) -> None:
        for key in URL_ATTRS:
            if key not in attrs:
                continue
            value = attrs[key].strip()
            if not value:
                continue
            lowered = re.sub(r"[\x00-\x20]+", "", value).lower()
            if lowered.startswith("//"):
                self.errors.append(f"protocol-relative URL is forbidden: {tag}.{key}={value}")
                continue
            if lowered.startswith(("javascript:", "vbscript:", "file:")):
                self.errors.append(f"unsafe URL scheme: {tag}.{key}={value}")
                continue
            parsed = urlparse(value)
            scheme = parsed.scheme.lower()
            if scheme == "data":
                if not lowered.startswith(("data:image/", "data:audio/", "data:video/")):
                    self.errors.append(f"unsafe data URL: {tag}.{key}")
                elif tag not in {"img", "image", "audio", "video", "source", "track"}:
                    self.errors.append(f"data URL is not allowed on <{tag}>")
                continue
            if scheme and scheme not in ALLOWED_NAV_SCHEMES:
                self.errors.append(f"unknown URL scheme: {tag}.{key}={scheme}")
            if tag in REMOTE_ASSET_TAGS and scheme in {"http", "https"}:
                self.errors.append(f"remote runtime asset is forbidden: <{tag}> {value}")
            if tag == "img" and not value.startswith("data:"):
                self.errors.append(f"image must be embedded as a data URL: {value}")

    def _audit_control(self, tag: str, attrs: dict[str, str]) -> None:
        if tag == "img" and "alt" not in attrs:
            self.errors.append("image is missing alt text")
        role = attrs.get("role", "").lower()
        if role in {"button", "link", "checkbox", "menuitem", "switch", "tab"} and tag not in {
            "a",
            "button",
            "input",
            "select",
            "textarea",
        }:
            if "tabindex" not in attrs:
                self.errors.append(f"custom {role} control is not keyboard focusable")


def load_manifest() -> tuple[dict, list[str]]:
    errors: list[str] = []
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"cannot read manifest: {exc}"]
    if not isinstance(data, dict):
        return {}, ["manifest root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    styles = data.get("styles")
    aliases = data.get("aliases")
    default = data.get("default_style")
    if not isinstance(styles, dict) or not styles:
        errors.append("manifest styles must be a non-empty object")
        styles = {}
    if default not in styles:
        errors.append("manifest default_style must name a registered style")
    if not isinstance(aliases, dict):
        errors.append("manifest aliases must be an object")
        aliases = {}
    for alias, target in aliases.items():
        if target not in styles:
            errors.append(f"alias {alias!r} points to unknown style {target!r}")
        if alias in styles:
            errors.append(f"alias {alias!r} collides with a style name")
    for name, record in styles.items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            errors.append(f"invalid style name: {name!r}")
        if not isinstance(record, dict):
            errors.append(f"style {name!r} must be an object")
            continue
        css_files = record.get("css")
        if not isinstance(css_files, list) or len(css_files) != 2:
            errors.append(f"style {name!r} must list base.css and one profile CSS")
            continue
        if css_files[0] != "base.css":
            errors.append(f"style {name!r} must put base.css first")
        for relative in css_files:
            if not isinstance(relative, str) or Path(relative).name != relative:
                errors.append(f"style {name!r} has unsafe CSS path: {relative!r}")
                continue
            path = STYLES / relative
            if not path.is_file():
                errors.append(f"style {name!r} references missing CSS: {relative}")
        example = record.get("example")
        if not isinstance(example, str):
            errors.append(f"style {name!r} must declare an example")
        else:
            example_path = (STYLES / example).resolve()
            try:
                example_path.relative_to(SKILL_ROOT.resolve())
            except ValueError:
                errors.append(f"style {name!r} example leaves skill root")
            else:
                if not example_path.is_file():
                    errors.append(f"style {name!r} example is missing: {example}")
    data["styles"] = styles
    data["aliases"] = aliases
    return data, errors


def validate_assets() -> list[str]:
    manifest, errors = load_manifest()
    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return errors + [f"cannot read template: {exc}"]
    required_placeholders = {
        "{{LANG}}",
        "{{STYLE_NAME}}",
        "{{DOC_TITLE}}",
        "{{STYLE_CSS}}",
        "{{EYEBROW}}",
        "{{DOC_SUBTITLE}}",
        "{{STATUS}}",
        "{{DATE}}",
        "{{AUTHOR}}",
        "{{TLDR_BODY}}",
        "{{SECTION_1_TITLE}}",
        "{{SECTION_1_BODY}}",
        "{{REFERENCE_1}}",
    }
    for placeholder in sorted(required_placeholders):
        if placeholder not in template:
            errors.append(f"template missing placeholder: {placeholder}")
    if "Content-Security-Policy" not in template:
        errors.append("template is missing CSP")
    if "assets/styles/base.css" not in template or "assets/styles/manifest.json" not in template:
        errors.append("template does not document CSS inlining order")
    legacy = SKILL_ROOT / "references" / "template.html"
    if legacy.exists():
        errors.append("legacy references/template.html still exists")

    xju = STYLES / "xju-notion.css"
    if xju.is_file():
        text = xju.read_text(encoding="utf-8")
        for required in (
            "fd4d4ac61fa70901a4c34e5601aec5f9a4c66a27",
            "MIT License",
            "--radius-sm: 6px",
            "--radius-md: 8px",
            "--radius-lg: 12px",
            "--shadow-card: 0 1px 2px rgba(0, 0, 0, 0.04)",
            "--transition: 150ms ease",
            "max-width: 720px",
        ):
            if required not in text:
                errors.append(f"xju-notion.css missing required contract: {required}")
        for forbidden in ("@tailwind", "fonts.googleapis.com", "@import", "::highlight", ".anchor-mark", "prose-claude--dark"):
            if forbidden in text:
                errors.append(f"xju-notion.css contains excluded source feature: {forbidden}")

    paper = STYLES / "paper-proposal.css"
    if paper.is_file():
        text = paper.read_text(encoding="utf-8")
        for required in (
            "--paper: #f7f7f5",
            "--ink: #1a1a1a",
            ".doc-meta",
            ".tldr",
            "h2 .num",
            ".fig-num",
            ".cards",
            ".callout",
            "table",
            "footer",
        ):
            if required not in text:
                errors.append(f"paper-proposal.css missing visual contract: {required}")

    base = STYLES / "base.css"
    if base.is_file():
        text = base.read_text(encoding="utf-8")
        for required in (":focus-visible", "prefers-reduced-motion", ".table-wrap", ".icon"):
            if required not in text:
                errors.append(f"base.css missing shared contract: {required}")

    try:
        icons = ICON_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read icon subset: {exc}")
    else:
        symbols = re.findall(r'<symbol\s+id="([^"]+)"[^>]*>', icons)
        expected = {"icon-copy", "icon-check", "icon-chevron-down", "icon-external-link"}
        if set(symbols) != expected or len(symbols) != len(expected):
            errors.append(f"Lucide subset symbols must be exactly {sorted(expected)}")
        for symbol_tag in re.findall(r"<symbol\b[^>]*>", icons):
            for required in (
                'fill="none"',
                'stroke="currentColor"',
                'stroke-width="1.75"',
                'stroke-linecap="round"',
                'stroke-linejoin="round"',
            ):
                if required not in symbol_tag:
                    errors.append(f"Lucide symbol missing {required}: {symbol_tag[:80]}")
        for required in ("Lucide v0.468.0", "ISC License", "Copyright (c) 2020-present Lucide Contributors"):
            if required not in icons:
                errors.append(f"Lucide subset missing attribution: {required}")

    if manifest:
        for style_name, record in manifest.get("styles", {}).items():
            example_path = (STYLES / record["example"]).resolve()
            if example_path.is_file():
                example_text = example_path.read_text(encoding="utf-8")
                marker = f'data-article-style="{style_name}"'
                if marker not in example_text:
                    errors.append(f"example for {style_name!r} is missing {marker}")
                for css_name in record["css"]:
                    css_text = (STYLES / css_name).read_text(encoding="utf-8")
                    if css_text not in example_text:
                        errors.append(f"example for {style_name!r} does not inline {css_name}")
    return errors


def validate_csp(csp: str | None) -> list[str]:
    if not csp:
        return ["missing Content Security Policy meta tag"]
    errors: list[str] = []
    directives: dict[str, list[str]] = {}
    for chunk in csp.split(";"):
        tokens = chunk.strip().split()
        if tokens:
            directives[tokens[0].lower()] = tokens[1:]
    exact_none = ("default-src", "base-uri", "connect-src", "font-src", "frame-src", "object-src", "form-action", "frame-ancestors")
    for name in exact_none:
        if directives.get(name) != ["'none'"]:
            errors.append(f"CSP {name} must be exactly 'none'")
    if directives.get("style-src") != ["'unsafe-inline'"]:
        errors.append("CSP style-src must allow only 'unsafe-inline'")
    if directives.get("script-src") != ["'unsafe-inline'"]:
        errors.append("CSP script-src must allow only 'unsafe-inline'")
    for name in ("img-src", "media-src"):
        values = directives.get(name)
        if values not in (["data:"], ["'none'"]):
            errors.append(f"CSP {name} must be data: or 'none'")
    return errors


def validate_generated_html(path: Path, expected_style: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read input: {exc}"]
    if not re.match(r"(?is)^\s*<!doctype\s+html>", raw):
        errors.append("missing HTML doctype")
    if PLACEHOLDER_RE.search(raw):
        errors.append("unresolved template placeholder remains")
    parser = ArticleAuditParser()
    try:
        parser.feed(raw)
        parser.close()
    except Exception as exc:
        errors.append(f"HTML parser failed: {exc}")
    errors.extend(parser.errors)

    for tag, expected in (("html", 1), ("head", 1), ("body", 1), ("main", 1), ("h1", 1)):
        actual = parser.counts.get(tag, 0)
        if actual != expected:
            errors.append(f"expected exactly {expected} <{tag}>, found {actual}")
    if parser.document_title_count != 1:
        errors.append(f"expected exactly 1 document <title>, found {parser.document_title_count}")
    if not parser.html_lang or not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", parser.html_lang):
        errors.append("html lang must be a non-empty valid language tag")
    if not "".join(parser.title_text).strip():
        errors.append("document title is empty")
    if "width=device-width" not in parser.viewport.lower():
        errors.append("viewport meta must include width=device-width")
    if parser.color_scheme.strip().lower() != "light":
        errors.append("color-scheme meta must be light")
    errors.extend(validate_csp(parser.csp))
    if not parser.styles or not "".join(parser.styles).strip():
        errors.append("missing inline CSS")
    css = "\n".join(parser.styles)
    if ":focus-visible" not in css:
        errors.append("inline CSS is missing visible focus treatment")
    if "prefers-reduced-motion" not in css:
        errors.append("inline CSS is missing reduced-motion treatment")
    if re.search(r"@import\b|url\(\s*['\"]?https?://", css, re.I):
        errors.append("inline CSS contains a remote import or URL")
    if re.search(r"prefers-color-scheme|\.dark\b|data-theme\s*=|theme-toggle", css, re.I):
        errors.append("dark-mode behavior is forbidden")

    script = "\n".join(parser.scripts)
    for label, pattern in DANGEROUS_JS_PATTERNS.items():
        if pattern.search(script):
            errors.append(f"dangerous JavaScript API is forbidden: {label}")

    if len(set(parser.ids)) != len(parser.ids):
        duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
        errors.append(f"duplicate ids: {', '.join(duplicates)}")
    id_set = set(parser.ids)
    for control in parser.controls:
        tag = str(control["tag"])
        attrs = control["attrs"]  # type: ignore[assignment]
        if tag == "input" and attrs.get("type", "").lower() == "hidden":  # type: ignore[union-attr]
            continue
        explicit = attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip()  # type: ignore[union-attr]
        label_for = attrs.get("id", "") in parser.labels_for  # type: ignore[union-attr]
        text_label = " ".join(str(part) for part in control["text"]).strip()
        input_native = tag == "input" and attrs.get("type", "").lower() in {"submit", "reset", "button"} and bool(attrs.get("value", "").strip())  # type: ignore[union-attr]
        if not (explicit or label_for or text_label or input_native):
            errors.append(f"interactive <{tag}> requires an accessible label")
    for element in parser.elements:
        for attr in ("aria-labelledby", "aria-describedby", "aria-controls"):
            for reference in element.attrs.get(attr, "").split():
                if reference and reference not in id_set:
                    errors.append(f"{element.tag}.{attr} references missing id {reference!r}")
        if element.attrs.get("aria-hidden", "").lower() == "true" and element.tag in {"button", "input", "select", "textarea", "a"}:
            errors.append(f"interactive <{element.tag}> must not be aria-hidden")

    previous = 0
    for level, _, _ in parser.headings:
        if previous and level > previous + 1:
            errors.append(f"invalid heading order: h{previous} followed by h{level}")
        previous = level

    skip_links = [
        element
        for element in parser.elements
        if element.tag == "a" and "skip-link" in element.attrs.get("class", "").split() and element.attrs.get("href", "").startswith("#")
    ]
    if not skip_links:
        errors.append("missing skip link")
    else:
        target = skip_links[0].attrs["href"][1:]
        if target not in id_set:
            errors.append("skip link target does not exist")

    for svg in parser.svgs:
        attrs = svg["attrs"]  # type: ignore[assignment]
        if attrs.get("aria-hidden", "").lower() == "true":  # type: ignore[union-attr]
            continue
        if attrs.get("role", "").lower() != "img":  # type: ignore[union-attr]
            errors.append("informative SVG must have role=img")
            continue
        labelled = attrs.get("aria-labelledby", "").split()  # type: ignore[union-attr]
        title_ids = svg["title_ids"]
        desc_ids = svg["desc_ids"]
        if not title_ids or not desc_ids:
            errors.append("informative SVG requires titled <title> and <desc> elements")
        for required in [*title_ids, *desc_ids]:  # type: ignore[arg-type]
            if required not in labelled:
                errors.append(f"SVG aria-labelledby is missing {required!r}")
        for href in svg["external_images"]:  # type: ignore[union-attr]
            if not str(href).startswith("data:image/"):
                errors.append(f"SVG image is not embedded: {href}")

    parent_by_index: dict[int, Element | None] = {}
    stack: list[Element] = []
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    # html.parser does not expose parent links; approximate from source-order start elements.
    # Direct wrapper enforcement is also checked textually below.
    for element in parser.elements:
        parent_by_index[element.index] = stack[-1] if stack else None
        if element.tag not in void:
            stack.append(element)
    for table in parser.tables:
        attrs = table["attrs"]
        if not table["caption"] and not attrs.get("aria-label") and not attrs.get("aria-labelledby"):  # type: ignore[union-attr]
            errors.append("table requires a caption, aria-label, or aria-labelledby")
        headers = table["headers"]
        if not headers:
            errors.append("table requires header cells")
        for header in headers:  # type: ignore[union-attr]
            if header.get("scope") not in {"col", "row", "colgroup", "rowgroup"}:
                errors.append("every table header requires a valid scope")
    if parser.tables:
        table_openings = len(re.findall(r'<div\b[^>]*class="[^"]*\btable-wrap\b[^"]*"[^>]*>\s*<table\b', raw, re.I | re.S))
        if table_openings != len(parser.tables):
            errors.append("every table must be directly wrapped in .table-wrap")

    style_marker = re.search(r'<html\b[^>]*\bdata-article-style="([^"]+)"', raw, re.I)
    style_name = style_marker.group(1) if style_marker else ""
    manifest, manifest_errors = load_manifest()
    errors.extend(f"asset registry: {error}" for error in manifest_errors)
    styles = manifest.get("styles", {}) if manifest else {}
    if not style_name:
        errors.append("html is missing data-article-style")
    elif style_name not in styles:
        errors.append(f"html declares unknown style: {style_name}")
    if expected_style and style_name != expected_style:
        errors.append(f"expected style {expected_style!r}, found {style_name!r}")
    if style_name in styles:
        for css_name in styles[style_name].get("css", []):
            try:
                required_css = (STYLES / css_name).read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"cannot read registered CSS {css_name}: {exc}")
            else:
                if required_css not in raw:
                    errors.append(f"generated HTML does not inline registered CSS: {css_name}")
    return errors


def find_chrome() -> str | None:
    for name in CHROME_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None


def render_screenshot(chrome: str, html_path: Path, screenshot: Path, width: int, height: int) -> str | None:
    if screenshot.exists():
        return f"screenshot already exists: {screenshot}"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="article-html-check-") as profile:
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            f"--screenshot={screenshot}",
            html_path.as_uri(),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"headless Chrome failed: {exc}"
    if result.returncode != 0:
        return f"headless Chrome exited {result.returncode}: {result.stderr.strip()}"
    if not screenshot.is_file() or screenshot.stat().st_size < 1000:
        return "headless Chrome did not produce a non-empty PNG"
    if screenshot.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        return "screenshot is not a PNG"
    os.chmod(screenshot, 0o600)
    return None


def make_minimal_html(body: str, *, style: str = "xju-notion", extra_head: str = "", script: str = "") -> str:
    base = (STYLES / "base.css").read_text(encoding="utf-8")
    profile = (STYLES / f"{style}.css").read_text(encoding="utf-8")
    return f'''<!DOCTYPE html>
<html lang="en" data-article-style="{style}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="color-scheme" content="light" />
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; font-src 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; form-action 'none'; frame-ancestors 'none'" />
<title>Fixture</title>
{extra_head}
<style>{base}\n{profile}</style>
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<main id="main-content"><article class="doc">{body}</article></main>
{script}
</body>
</html>'''


def run_self_test() -> list[str]:
    failures: list[str] = []
    valid_body = "<h1>Fixture</h1><section><h2>Section</h2><p>Safe text.</p></section>"
    cases: list[tuple[str, str, str]] = [
        ("unsafe-script-url", valid_body + '<a href="javascript:alert(1)">bad</a>', "unsafe URL scheme"),
        ("remote-image", valid_body + '<img src="https://example.com/a.png" alt="remote" />', "remote runtime asset"),
        ("inline-handler", valid_body + '<button aria-label="Bad" onclick="alert(1)">Bad</button>', "inline event handler"),
        ("unsafe-tag", valid_body + '<iframe src="data:text/html,bad"></iframe>', "forbidden tag"),
        ("unsafe-form", valid_body + '<form><button>Submit</button></form>', "forbidden tag"),
        ("dangerous-sink", valid_body, "dangerous JavaScript API"),
        ("network-api", valid_body, "dangerous JavaScript API"),
        ("missing-alt", valid_body + '<img src="data:image/png;base64,iVBORw0KGgo=" />', "missing alt"),
        ("heading-order", '<h1>Fixture</h1><section><h3>Skipped</h3></section>', "invalid heading order"),
        ("duplicate-id", '<h1 id="same">Fixture</h1><section id="same"><h2>Section</h2></section>', "duplicate ids"),
        ("unlabeled-svg", valid_body + '<svg role="img" viewBox="0 0 10 10"></svg>', "requires titled"),
        ("unscoped-table", valid_body + '<div class="table-wrap"><table aria-label="Bad"><tr><th>A</th><td>B</td></tr></table></div>', "valid scope"),
        ("raw-source-html", valid_body + '<object data="data:text/html,bad"></object>', "forbidden tag"),
    ]
    with tempfile.TemporaryDirectory(prefix="article-html-self-test-") as temp_dir:
        temp = Path(temp_dir)
        for name, body, expected in cases:
            script = ""
            if name == "dangerous-sink":
                script = "<script>document.body.innerHTML = '<p>bad</p>';</script>"
            if name == "network-api":
                script = "<script>fetch('https://example.com');</script>"
            path = temp / f"{name}.html"
            path.write_text(make_minimal_html(body, script=script), encoding="utf-8")
            errors = validate_generated_html(path)
            if not errors:
                failures.append(f"negative self-test {name!r} unexpectedly passed")
            elif not any(expected.lower() in error.lower() for error in errors):
                failures.append(f"negative self-test {name!r} missed expected {expected!r}: {errors}")

        valid_path = temp / "valid.html"
        valid_path.write_text(make_minimal_html(valid_body), encoding="utf-8")
        valid_errors = validate_generated_html(valid_path)
        if valid_errors:
            failures.append(f"positive self-test failed: {valid_errors}")
    return failures


def print_errors(label: str, errors: list[str]) -> None:
    print(f"{label} failed:", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="generated HTML to validate")
    parser.add_argument("--style", help="expected registered style name")
    parser.add_argument("--check-assets", action="store_true", help="validate registry, template, CSS, icons, and examples")
    parser.add_argument("--self-test", action="store_true", help="run positive and negative validator tests")
    parser.add_argument("--screenshot", help="new desktop PNG path (1440x1200)")
    parser.add_argument("--mobile-screenshot", help="new mobile PNG path (500x844)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not any((args.input, args.check_assets, args.self_test)):
        print("error: select --input, --check-assets, or --self-test", file=sys.stderr)
        return 2
    failures = 0
    if args.check_assets:
        errors = validate_assets()
        if errors:
            failures += 1
            print_errors("Asset validation", errors)
        else:
            print("Article assets: OK")
    if args.self_test:
        errors = run_self_test()
        if errors:
            failures += 1
            print_errors("Self-test", errors)
        else:
            print("Validator self-test: OK")
    if args.input:
        html_path = Path(args.input).expanduser().resolve()
        errors = validate_generated_html(html_path, args.style)
        rendered: list[Path] = []
        requested_screenshots = [value for value in (args.screenshot, args.mobile_screenshot) if value]
        if requested_screenshots:
            chrome = find_chrome()
            if not chrome:
                errors.append("Linux Chrome/Chromium was not found for screenshots")
            else:
                for value, width, height in (
                    (args.screenshot, 1440, 1200),
                    (args.mobile_screenshot, 500, 844),
                ):
                    if not value:
                        continue
                    screenshot = Path(value).expanduser().resolve()
                    error = render_screenshot(chrome, html_path, screenshot, width, height)
                    if error:
                        errors.append(error)
                    else:
                        rendered.append(screenshot)
        if errors:
            failures += 1
            print_errors(f"HTML validation for {html_path}", errors)
        else:
            print(f"Validated HTML: {html_path}")
            for screenshot in rendered:
                print(f"Screenshot: {screenshot}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
