from __future__ import annotations

import json

from gallica.reference import programmable_reference


if __name__ == "__main__":
    print(json.dumps(programmable_reference(), ensure_ascii=False, indent=2, sort_keys=True))
