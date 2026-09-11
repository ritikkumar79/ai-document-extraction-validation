from pathlib import Path
import sys

# Allow tests to be run from the repository root with `pytest backend/tests -q`.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
