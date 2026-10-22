"""SlothSwitch — AI decision and execution engine."""

from __future__ import annotations

from pathlib import Path

# Automatically load .env if present
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

__version__ = "0.1.0"
