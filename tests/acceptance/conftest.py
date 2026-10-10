import sys
from pathlib import Path

# The shared fakes live one folder up (tests/fake_season.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
