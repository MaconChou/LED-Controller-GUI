import os
import sys
from pathlib import Path

# Headless Qt for CI, and make the package importable without installing.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
