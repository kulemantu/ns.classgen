"""Allow running as: python -m .mock.e2e"""

import sys
from pathlib import Path

pkg_dir = str(Path(__file__).parent)
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from cli import main  # noqa: E402

main()
