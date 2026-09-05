# Repository governance

The repository treats CI as part of its release policy, not as decorative telemetry. The desired protection for `main` is versioned in `repository-policy/main-ruleset.json` so the intended governance can be reviewed like code instead of existing only as mutable GitHub UI state.

## Desired `main` ruleset

The checked-in ruleset targets only `refs/heads/main` and requires:

- changes through pull requests;
- squash as the allowed merge method;
- resolved review conversations before merge;
- successful deterministic CI checks;
- the PR head to be up to date with `main` before merge;
- no deletion of `main`;
- no force pushes.

The policy deliberately requires zero approving reviews. This is currently a single-maintainer repository: forcing the author to obtain an impossible second-person approval would turn governance into theatre rather than add assurance. The pull-request boundary still matters because it is what gives required checks a ref on which they can run before `main` changes.

## Required checks

The required status checks are:

- `coverage`;
- `test (3.11)`;
- `test (3.12)`;
- `test (3.13)`;
- `test (3.14)`;
- `platform-smoke (windows-latest)`;
- `platform-smoke (macos-latest)`;
- `package`.

These checks are deterministic with respect to the repository code and build environment.

`live` and `notebooks` are intentionally **not** branch-protection requirements. Both exercise public Gallica services and can therefore fail because of external availability, throttling or anti-bot behavior even when a proposed code change is sound. They remain normal CI signals, and the live evidence workflow also runs periodically. A release candidate should still be accepted only when the relevant live validations are green.

## Applying the ruleset

`repository-policy/main-ruleset.json` is shaped as the request body for GitHub's repository-ruleset API. It can also be used as a checklist when configuring the same policy in the GitHub web interface.

The repository must not claim that the policy is enforced merely because this file exists. Enforcement is established only when GitHub reports an active ruleset or branch protection targeting `main`.

After the ruleset is applied, verify from GitHub that:

1. `main` is protected;
2. a direct push is rejected;
3. a PR cannot merge while a required check is missing or failing;
4. force-push and deletion are blocked;
5. squash remains available as the normal merge path.

Issue #25 tracks this external repository-setting step.
