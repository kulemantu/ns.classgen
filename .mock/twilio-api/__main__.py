"""Allow running as: python -m .mock.twilio-api"""

# When invoked via `python .mock/twilio-api/cli.py` or `python -m`,
# the package directory is on sys.path, so `from cli import main` works.
import sys
from pathlib import Path

# Ensure the package directory is on sys.path for sibling imports
pkg_dir = str(Path(__file__).parent)
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from cli import main  # noqa: E402

main()
