from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import reset_database


def main() -> None:
    path = reset_database()
    print(f"Reset demo database at {path}")


if __name__ == "__main__":
    main()
