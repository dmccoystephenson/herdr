@AGENTS.md

# Fork notes: dmccoystephenson/herdr

This checkout is a **fork** of [`herdrdev/herdr`](https://github.com/herdrdev/herdr).
`AGENTS.md` (imported above) is upstream's agent guide and stays authoritative for
the codebase itself — architecture principles, multiplicative performance paths,
the runtime/client boundary, testing, docs layout, and code conventions. This
section adds only what differs because the work happens in the fork. Where the two
conflict, this section wins for work in the fork.

## Which parts of AGENTS.md apply here

- **Universal Project Rules, Testing, Docs, Code Conventions:** apply in full.
- **Maintainer Workflow** and **Local Can Machine Workflow:** do not apply. The
  acting account is not listed in `.github/MAINTAINERS`, and this is not Can's
  workstation.
- **External contributor guardrail:** applies to `herdrdev/herdr` itself. Never
  open an issue or pull request on, or push a branch to, `herdrdev/herdr` from
  this fork. Upstream issues are read-only input.

## Branches and merging

- `master` tracks `upstream/master` plus any fork-only commits merged here.
  Remotes: `origin` = `dmccoystephenson/herdr`, `upstream` = `herdrdev/herdr`.
- Never commit to `master` directly. Work on a `fix/<short-description>`
  branch, open a PR against `dmccoystephenson/herdr` `master`, and squash-merge.
- Upstream syncs land on `master` as a fast-forward when the fork has no
  divergent commits, and as a merge (verified green before pushing) once it does.
- Keep divergence in upstream-owned files to a minimum, since every fork-only
  change is a future merge conflict. Put fork-specific agent guidance in this
  file, not in `AGENTS.md`.

## Commits and PRs

- Keep upstream's commit-subject format: lowercase conventional commits, no
  emojis. CI's `conventional-commits` job checks PR titles and pushed subjects,
  and `.githooks/commit-msg` checks the same thing locally.
- Follow upstream's "no AI co-author lines" rule: fork commits carry no
  `Co-Authored-By:` or other AI-attribution trailer (including a
  `Claude-Session:` line), even where the harness would normally append one.
  This keeps fork commits clean enough to send upstream unchanged.
- Override: the autonomous dev loop does not stop to propose each commit message
  for alignment first. The PR is the review point.
- Fork issues are referenced from PR bodies with `Closes #N`; there is no fork
  release CI to close them later. Upstream issues are referenced as
  `herdrdev/herdr#N` and never closed from here.

## Files the fork does not touch

These belong to upstream's release process, which is gated to
`github.repository == 'herdrdev/herdr'` and never runs here:

- `docs/next/CHANGELOG.md`, root `CHANGELOG.md`, root `README.md`
- `docs/preview/`, `docs/versions/`, `distribution/*.json`
- `skills/herdr/SKILL.md`
- `Cargo.toml` `version`

## Build and CI

- Use the `just` recipes from AGENTS.md. `just check` is the full local gate.
  It needs the pinned toolchain from `rust-toolchain.toml`, `cargo-nextest`,
  `just`, `bun`, `zig`, and `python3`. Its `windows-lint` stage also needs the
  Windows SDK from `just setup-windows-cross`.
- When the Windows SDK is unavailable locally, run `just ci` and rely on CI's
  `check (windows-latest)` job for the Windows target. Say which one you ran.
- CI on a fork PR: `conventional-commits`, `check (ubuntu-latest)`,
  `check (macos-latest)`, `check (windows-latest)`, and `Windows ConPTY package`,
  plus path-filtered `nix`, `distribution`, and `windows-arm64` jobs.
- `website-deploy.yml` and `label-next-release-issues.yml` run on every push to
  `master` but need upstream-only secrets, so they are expected to fail here.
  They do not reflect on the change being pushed.

## Dev loop

The autonomous dev loop for this fork is `/herdr-dev-loop`
(skill repo: `dmccoystephenson/herdr-dev-loop`). It syncs upstream first every
cycle, then works fork issues and upstream issues through fork PRs.
