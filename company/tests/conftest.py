"""Put the company/ root on sys.path so tests can import config, guards, repo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
