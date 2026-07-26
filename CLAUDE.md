# self-skills deployment repository

This repository synchronizes personal Agent Skills, CLI helpers, and the global Claude Code prompt across machines.

## Git workflow

- Work directly on `main` for every change in this repository.
- Commit and push to `origin/main`; do not create feature branches or pull requests unless the user explicitly requests one.
- If the working tree is on another branch, switch to `main` before making or committing changes.

## Deploy requests

When the user asks to deploy or synchronize this repository, run the relevant command and report its output:

```bash
./deploy.sh                  # Claude Code
./deploy.sh --target codex   # Codex
./deploy.sh --target both    # both runtimes
```

The script is idempotent. It links `bin/*`, links all standard `skills/*` directories, deploys `notify-win`, and links `global/CLAUDE.md` only for targets that include Claude. Existing non-symlink targets are timestamp-backed up before replacement.

After Claude deployment, remind the user that terminal scroll settings require restarting Claude Code; `/tui default` switches the current session immediately.

## Repository structure

- `skills/` contains canonical Skill directories.
- `docs/skills/` contains human-facing manuals, not agent instructions.
- `scripts/validate_skills.py` validates the repository structure.
- `scripts/package_skills.py` builds chat-importable `dist/<skill>.zip` archives.
- `.github/workflows/release-skills.yml` packages the same archives in CI and attaches them to a GitHub Release on a `v*` tag or a manual dispatch with a `tag` input.
- `bin/` contains standalone CLI tools linked to `~/bin`.
- `global/CLAUDE.md` is the canonical user-level Claude prompt.
- `deploy.sh` performs installation through symlinks.

## Adding or updating a Skill

1. Use a lowercase kebab-case directory matching the `name` in `SKILL.md`.
2. Keep `SKILL.md` frontmatter to `name` and `description` for maximum Claude/Codex compatibility.
3. Add `agents/openai.yaml` with `display_name`, `short_description`, and a `default_prompt` that explicitly mentions `$<skill-name>`.
4. Put executables in `scripts/`, on-demand guidance in `references/`, and output templates/resources in `assets/`.
5. Put user manuals in `docs/skills/<skill-name>.md`; keep legal attribution beside vendored code.
6. Run `python3 scripts/validate_skills.py` before committing.
