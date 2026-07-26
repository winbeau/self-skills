#!/usr/bin/env python3
"""Package each Skill directory as a chat-importable zip archive.

Every archive contains a single top-level directory named after the Skill,
with `SKILL.md` inside it, which is the layout Claude expects when a Skill is
uploaded to a chat or to the Skills settings page.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_skills import frontmatter_text, scalar_value, validate_skill  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXCLUDED_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache", ".mypy_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp", ".swo"}
# Fixed timestamp keeps archives byte-reproducible across runs and runners.
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ALWAYS_TEXT = {".md", ".yaml", ".yml", ".json", ".txt", ".css", ".html"}


def is_excluded(relative: Path) -> bool:
    for part in relative.parts:
        if part in EXCLUDED_NAMES or part.startswith("."):
            return True
    return relative.suffix in EXCLUDED_SUFFIXES


def entries(skill: Path) -> list[tuple[str, Path]]:
    """Return (arcname, source) pairs sorted for deterministic archives."""
    collected: list[tuple[str, Path]] = []
    for path in sorted(skill.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(skill)
        if is_excluded(relative):
            continue
        collected.append((f"{skill.name}/{relative.as_posix()}", path))
    return collected


def archive_mode(path: Path) -> int:
    if path.suffix in ALWAYS_TEXT:
        return 0o644
    return 0o755 if os.stat(path).st_mode & stat.S_IXUSR else 0o644


def add_entries(archive: zipfile.ZipFile, pairs: list[tuple[str, Path]]) -> None:
    for arcname, source in pairs:
        info = zipfile.ZipInfo(arcname, date_time=ZIP_TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = archive_mode(source) << 16
        archive.writestr(info, source.read_bytes())


def write_zip(target: Path, pairs: list[tuple[str, Path]]) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        add_entries(archive, pairs)
    return target


def display(path: Path) -> str:
    """Repo-relative path when possible, absolute otherwise."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def description_of(skill: Path) -> str:
    frontmatter = frontmatter_text(skill / "SKILL.md")
    return scalar_value(frontmatter, "description") or ""


def summarize(description: str, limit: int = 160) -> str:
    text = " ".join(description.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def write_notes(path: Path, version: str, packaged: list[tuple[Path, Path]], bundle: Path | None) -> None:
    lines = [
        f"# Agent Skills {version}",
        "",
        "Each zip contains one Skill folder with its `SKILL.md`, ready to upload",
        "directly in a Claude chat or on the Skills settings page. Claude Code and",
        "Codex users can keep using `./deploy.sh` from a clone instead.",
        "",
    ]
    if bundle is not None:
        lines += [f"`{bundle.name}` bundles every Skill folder in one archive.", ""]
    lines += ["| Skill | Archive | Purpose |", "|---|---|---|"]
    for skill, archive in packaged:
        lines.append(f"| `{skill.name}` | `{archive.name}` | {summarize(description_of(skill))} |")
    lines += ["", "Verify downloads against `SHA256SUMS.txt`.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist", help="output directory (default: dist)")
    parser.add_argument("--skill", action="append", default=[], help="package only this Skill (repeatable)")
    parser.add_argument("--bundle", metavar="NAME", help="also write NAME.zip containing every Skill")
    parser.add_argument("--version", default="", help="version label used in the release notes heading")
    parser.add_argument("--notes", metavar="PATH", help="write a markdown release-notes file")
    parser.add_argument("--skip-validation", action="store_true", help="package without validating layout first")
    args = parser.parse_args()

    if not SKILLS.is_dir():
        print(f"Missing skills directory: {SKILLS}", file=sys.stderr)
        return 1

    available = {path.name: path for path in sorted(SKILLS.iterdir()) if path.is_dir()}
    if args.skill:
        unknown = [name for name in args.skill if name not in available]
        if unknown:
            print(f"Unknown skill(s): {', '.join(unknown)}", file=sys.stderr)
            return 1
        selected = [available[name] for name in args.skill]
    else:
        selected = list(available.values())

    if not args.skip_validation:
        failures = 0
        for skill in selected:
            errors = validate_skill(skill)
            if errors:
                failures += 1
                print(f"FAIL {skill.name}", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
        if failures:
            print(f"{failures}/{len(selected)} skills failed validation; nothing packaged.", file=sys.stderr)
            return 1

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    packaged: list[tuple[Path, Path]] = []
    bundle_pairs: list[tuple[str, Path]] = []
    for skill in selected:
        pairs = entries(skill)
        if not any(arcname.endswith("/SKILL.md") for arcname, _ in pairs):
            print(f"{skill.name}: SKILL.md is missing from the archive", file=sys.stderr)
            return 1
        archive = write_zip(out / f"{skill.name}.zip", pairs)
        packaged.append((skill, archive))
        bundle_pairs.extend(pairs)
        print(f"packaged {display(archive)} ({len(pairs)} files, {archive.stat().st_size} bytes)")

    bundle = None
    if args.bundle:
        bundle = write_zip(out / f"{args.bundle}.zip", bundle_pairs)
        print(f"bundled  {display(bundle)} ({len(bundle_pairs)} files, {bundle.stat().st_size} bytes)")

    checksums = out / "SHA256SUMS.txt"
    archives = sorted(path for path in out.iterdir() if path.suffix == ".zip")
    checksums.write_text("".join(f"{sha256(path)}  {path.name}\n" for path in archives), encoding="utf-8")
    print(f"wrote    {display(checksums)}")

    if args.notes:
        notes = Path(args.notes)
        if not notes.is_absolute():
            notes = ROOT / notes
        write_notes(notes, args.version or "release", packaged, bundle)
        print(f"wrote    {display(notes)}")

    print(f"\nPackaged {len(packaged)} skills into {display(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
