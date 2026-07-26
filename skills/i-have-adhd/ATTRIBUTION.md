# Attribution — i-have-adhd

This directory is a **vendored copy of a third-party skill**. It is *not* original work in this
repo; it is redistributed here under its upstream MIT license. The rule text in `SKILL.md` is
upstream's, unchanged.

## Upstream source

- **Repo**: https://github.com/ayghri/i-have-adhd
- **Author**: Ayoub Ghriss (`ayghri`)
- **License**: MIT — full text preserved verbatim in [`LICENSE`](LICENSE)
- **Vendored at**: commit `16a42a01f7783e29db8557dfc46226baf8015618` (2026-07-23), fetched
  2026-07-26 via `git clone --depth 1`
- **Upstream credit**: upstream states the skill is loosely based on *The Adult ADHD Tool Kit*
  by J. Russell Ramsay and Anthony L. Rostain, adapted for LLM responses rather than for how a
  human organizes their day.

## What it does

An output-style skill. Once invoked it applies for the rest of the session: lead with the next
action, number multi-step work, end with one concrete next step, suppress tangents, restate
"step N of M" every turn, give estimates in concrete units, make finished work visible, state
errors matter-of-factly, cap lists at five items, and drop preamble/recap/closers. It also
carries explicit override cases (explain requests, destructive actions, debug spirals,
ambiguity, harness constraints) and a pre-send checklist.

## Modifications made in this repo

1. **Frontmatter reduced to `name` + `description`** to satisfy this repo's portability rule
   (`CLAUDE.md`: "Keep `SKILL.md` frontmatter to `name` and `description` for maximum
   Claude/Codex compatibility") and `scripts/validate_skills.py`, which rejects any other
   top-level key. Dropped keys: `disable-model-invocation: true`, `license: MIT`, and the
   `metadata.hermes` block.
   - **Behavioral consequence**: `disable-model-invocation` was the mechanism that stopped
     Claude from auto-loading the skill. To preserve that intent without the key, the
     `description` now states explicitly that the skill is user-invoked only. This is a weaker
     guarantee than the frontmatter flag — a model *could* still self-invoke. Restore the key
     locally if you want the hard block.
   - `license: MIT` is not lost: it is recorded here and in `LICENSE`.
2. **Body text unchanged.** All 10 rules, the "When to break the rules" section, and the
   pre-send check are upstream's verbatim.
3. **Plugin/marketplace scaffolding not vendored.** Upstream ships `plugin.json`,
   `.claude-plugin/`, `.codex-plugin/`, `.agents/`, `.cursor/`, an `evals/` harness, GitHub
   workflows, and a `hooks/` SessionStart hook that auto-enables the style when
   `~/.claude/.i-have-adhd-always` exists. None of that fits this repo's `skills/<name>/`
   layout, and this repo installs skills by symlink rather than as a Claude Code plugin. The
   always-on hook is therefore **not** installed here — see `docs/skills/i-have-adhd.md`.
4. **`agents/gemini.toml` not vendored** (this repo targets Claude Code and Codex);
   `agents/openai.yaml` is copied verbatim.

## License notice

Copyright (c) 2026 Ayoub Ghriss — i-have-adhd, MIT License.
The MIT license text is reproduced verbatim in [`LICENSE`](LICENSE) in this directory. This
vendored copy is redistributed under the same terms; the parent repo's top-level `LICENSE`
covers only the first-party skills, not this directory.
