from __future__ import annotations

import json

from gallica import operational_contracts


if __name__ == "__main__":
    print(json.dumps(operational_contracts(), ensure_ascii=False, indent=2))
