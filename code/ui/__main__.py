"""Launch: PYTHONPATH=code python3 -m ui"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent / "app.py"
CODE = Path(__file__).resolve().parents[1]


def main() -> int:
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(CODE) if not path else f"{CODE}{__import__('os').pathsep}{path}"
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", str(APP), "--server.headless=true"],
        env=env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
