from __future__ import annotations

import sys
from pathlib import Path


# Ensure `src/` is importable when running tests without an editable install.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

