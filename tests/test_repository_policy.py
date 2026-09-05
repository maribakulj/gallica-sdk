from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "repository-policy" / "main-ruleset.json"


def _policy() -> dict[str, object]:
    data = json.loads(POLICY.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_main_ruleset_targets_only_main_and_is_active() -> None:
    policy = _policy()
    assert policy["target"] == "branch"
    assert policy["enforcement"] == "active"
    conditions = policy["conditions"]
    assert isinstance(conditions, dict)
    ref_name = conditions["ref_name"]
    assert isinstance(ref_name, dict)
    assert ref_name["include"] == ["refs/heads/main"]
    assert ref_name["exclude"] == []


def test_main_ruleset_requires_pr_and_blocks_destructive_updates() -> None:
    policy = _policy()
    rules = policy["rules"]
    assert isinstance(rules, list)
    by_type = {rule["type"]: rule for rule in rules if isinstance(rule, dict)}

    assert "deletion" in by_type
    assert "non_fast_forward" in by_type
    pull_request = by_type["pull_request"]
    parameters = pull_request["parameters"]
    assert parameters["allowed_merge_methods"] == ["squash"]
    assert parameters["required_approving_review_count"] == 0
    assert parameters["required_review_thread_resolution"] is True


def test_main_ruleset_requires_deterministic_ci_but_not_external_live_checks() -> None:
    policy = _policy()
    rules = policy["rules"]
    assert isinstance(rules, list)
    status_rule = next(rule for rule in rules if rule["type"] == "required_status_checks")
    parameters = status_rule["parameters"]
    contexts = {
        check["context"]
        for check in parameters["required_status_checks"]
    }

    assert contexts == {
        "coverage",
        "test (3.11)",
        "test (3.12)",
        "test (3.13)",
        "test (3.14)",
        "platform-smoke (windows-latest)",
        "platform-smoke (macos-latest)",
        "package",
    }
    assert parameters["strict_required_status_checks_policy"] is True
    assert "live" not in contexts
    assert "notebooks" not in contexts


def test_required_status_contexts_exist_in_ci_workflow() -> None:
    policy = _policy()
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    rules = policy["rules"]
    status_rule = next(rule for rule in rules if rule["type"] == "required_status_checks")
    contexts = [
        check["context"]
        for check in status_rule["parameters"]["required_status_checks"]
    ]

    for context in contexts:
        if context.startswith("test ("):
            version = context.removeprefix("test (").removesuffix(")")
            assert version in workflow
        else:
            assert context.split(" (")[0] in workflow
