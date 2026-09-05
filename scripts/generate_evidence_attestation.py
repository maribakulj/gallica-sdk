from __future__ import annotations

import json
import os
from pathlib import Path

from gallica import build_evidence_attestation


def main() -> None:
    commit = os.environ.get("GITHUB_SHA", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    if not commit or not repository or not run_id:
        raise SystemExit("GITHUB_SHA, GITHUB_REPOSITORY and GITHUB_RUN_ID are required")
    run_url = f"{server}/{repository}/actions/runs/{run_id}"
    attestation = build_evidence_attestation(commit=commit, run_url=run_url)
    output = Path(os.environ.get("EVIDENCE_ATTESTATION_PATH", "evidence-attestation.json"))
    output.write_text(
        json.dumps(attestation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
