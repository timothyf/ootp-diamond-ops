from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import DashboardGenerator


def main() -> None:
    generator = DashboardGenerator(
        data_dir=SRC_DIR / "data",
        out_dir=PROJECT_ROOT / "output",
    )
    generator.run()
    print("Done. Full dashboard outputs generated.")
    print(f"Saved files to: {generator.out_dir.resolve()}")


if __name__ == "__main__":
    main()
