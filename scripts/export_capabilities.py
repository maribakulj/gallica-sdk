from __future__ import annotations

import json

from gallica.agent import capabilities


if __name__ == "__main__":
    print(json.dumps(capabilities(), ensure_ascii=False, indent=2, sort_keys=True))
