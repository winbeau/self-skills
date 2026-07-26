# self-skills

Personal Agent Skills shared by Claude Code and Codex. Each directory under `skills/` is independently installable and follows the same layout:

```text
skills/<kebab-case-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/       # optional executable helpers
├── references/    # optional on-demand guidance
└── assets/        # optional output resources and templates
```

Human-facing manuals live in `docs/skills/`. License and attribution files remain beside vendored Skill code when redistribution requires them.

## Skills

| Skill | Purpose |
|---|---|
| [`academic-rebuttal`](skills/academic-rebuttal/) | Triage reviews, prioritize experiments, and draft evidence-grounded rebuttals |
| [`academic-writing`](skills/academic-writing/) | Audit and rewrite academic prose without inventing evidence |
| [`article-to-html`](skills/article-to-html/) | Render a safe self-contained article with xju-notion or paper-proposal styling |
| [`article-to-latex`](skills/article-to-latex/) | Create, compile, debug, and convert LaTeX/PDF documents |
| [`deploy-xray-reality`](skills/deploy-xray-reality/) | Deploy an Xray VLESS + Vision + REALITY node and emit a v2rayN link |
| [`humanizer-zh`](skills/humanizer-zh/) | Make Chinese writing natural and less formulaic |
| [`idea-scan`](skills/idea-scan/) | Map evidence-backed research gaps and opportunity signals |
| [`idea-generate`](skills/idea-generate/) | Generate testable candidates from scans and user hints |
| [`idea-check-novelty`](skills/idea-check-novelty/) | Check candidates against current online prior art |
| [`idea-review`](skills/idea-review/) | Review novelty, value, rigor, and feasibility |
| [`idea-design-experiment`](skills/idea-design-experiment/) | Design low-cost falsifiable experiments |
| [`idea-synthesize`](skills/idea-synthesize/) | Coordinate and summarize the idea discovery workflow |
| [`migrate-tencent-domain-dns-to-cloudflare`](skills/migrate-tencent-domain-dns-to-cloudflare/) | Move a Tencent Cloud or DNSPod domain's authoritative DNS to Cloudflare |
| [`notify-win`](skills/notify-win/) | Send a Windows desktop toast and sound alert |
| [`openreview-to-html`](skills/openreview-to-html/) | Capture authenticated OpenReview discussions as self-contained HTML |
| [`set-config`](skills/set-config/) | Apply the personal Claude Code settings baseline and diagnose configuration resets |
| [`set-localhost`](skills/set-localhost/) | Bind a tailnet device for the `mybox` remote workflow |
| [`ship-wpf-github-release`](skills/ship-wpf-github-release/) | Build, package, and release WPF apps on GitHub |
| [`tmux-ssh-remote`](skills/tmux-ssh-remote/) | Operate remote hosts through persistent tmux SSH sessions |
| [`update-docs`](skills/update-docs/) | Update Feiyue release notes and public documentation |
| [`xju-docx`](skills/xju-docx/) | Format, validate, and repair XJU academic DOCX files |
| [`zotero-paper-translator`](skills/zotero-paper-translator/) | Locate Zotero papers by collection path and translate them paragraph by paragraph |

The `idea-*` suite is domain-agnostic. World Model checks are loaded through optional domain profiles inside the relevant Skills.

## Install

Clone the repository and run the idempotent deployer:

```bash
git clone git@github.com:winbeau/self-skills.git
cd self-skills

./deploy.sh                  # Claude Code only
./deploy.sh --target codex   # Codex only
./deploy.sh --target both    # Claude Code and Codex
```

The deployer creates symlinks, so later `git pull` updates become visible immediately. It backs up a conflicting real file or directory before replacing it and does not modify unrelated third-party Skills.

Default destinations:

- Claude Code: `${CLAUDE_HOME:-$HOME/.claude}/skills`
- Codex: `${CODEX_HOME:-$HOME/.codex}/skills`

`bin/*` is linked to `~/bin`. The `notify-win` CLI is linked from `skills/notify-win/scripts/notify-win` to `~/bin/notify-win`.

## Release archives for chat import

Claude chat (and the Skills settings page) imports a Skill as a `.zip` whose single top-level folder holds `SKILL.md`. Build those archives locally:

```bash
python3 scripts/package_skills.py                     # dist/<skill>.zip for every Skill
python3 scripts/package_skills.py --skill notify-win  # one Skill only
python3 scripts/package_skills.py --bundle self-skills-all \
  --version v1.0.0 --notes dist/RELEASE_NOTES.md      # what CI runs
```

The packager validates layout first, skips dotfiles and runtime artifacts, keeps the executable bit on `scripts/*`, and pins entry timestamps so archives are byte-reproducible. Output includes `SHA256SUMS.txt`; `dist/` is git-ignored.

The [`release-skills`](.github/workflows/release-skills.yml) workflow builds the same archives on every push and pull request and uploads them as a build artifact. Publishing a GitHub Release with the zips attached happens when either:

```bash
git tag v1.0.0 && git push origin v1.0.0   # tag push
gh workflow run release-skills.yml -f tag=v1.0.0   # manual dispatch, creates the tag at HEAD
```

Re-running an existing tag re-uploads the assets with `--clobber` instead of failing.

## Validate

Run the repository-level structural validator:

```bash
python3 scripts/validate_skills.py
```

It checks directory names, `SKILL.md` frontmatter, matching Skill names, required `agents/openai.yaml` fields, default-prompt references, and disallowed runtime artifacts.

Useful focused checks:

```bash
bash -n deploy.sh skills/*/scripts/*.sh
python3 -m compileall -q skills scripts

python3 skills/xju-docx/scripts/build_framework.py -o /tmp/xju-smoke.docx --name 测试
python3 skills/xju-docx/scripts/validate_docx.py /tmp/xju-smoke.docx --framework
python3 skills/xju-docx/scripts/check_docx_package.py /tmp/xju-smoke.docx
```

## Documentation

Per-Skill manuals are under [`docs/skills/`](docs/skills/). Notable provenance:

- `academic-rebuttal` is vendored from [TobiasLee/Rebuttal-Skill](https://github.com/TobiasLee/Rebuttal-Skill) at a fixed commit. Upstream declared no license; see [ATTRIBUTION.md](skills/academic-rebuttal/ATTRIBUTION.md) before redistribution or modification.
- `article-to-html` provides a dependency-free safety/accessibility validator, two light-only style profiles, XJU MIT attribution, and a four-icon Lucide ISC subset; see [ATTRIBUTION.md](skills/article-to-html/ATTRIBUTION.md) and its [manual](docs/skills/article-to-html.md).
- `article-to-latex` is a vendored, modified MIT Skill; see [ATTRIBUTION.md](skills/article-to-latex/ATTRIBUTION.md).
- `deploy-xray-reality` is original; its four-script pipeline and the verification it does *not* cover are documented in [docs/skills/deploy-xray-reality.md](docs/skills/deploy-xray-reality.md).
- `humanizer-zh` keeps its upstream [LICENSE](skills/humanizer-zh/LICENSE).
- `xju-docx` is synchronized from the local working copy and includes OOXML repair diagnostics. Its upstream canonical project remains [XjuSelab/xju-feiyue](https://github.com/XjuSelab/xju-feiyue).
- `zotero-paper-translator` usage and lookup behavior are documented in [docs/skills/zotero-paper-translator.md](docs/skills/zotero-paper-translator.md).

## License

First-party content is MIT unless a Skill-local license or attribution notice says otherwise. See [LICENSE](LICENSE).
