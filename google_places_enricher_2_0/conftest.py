import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest

@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Disable all real HTTP requests in tests."""
    try:
        import requests
        monkeypatch.delattr("requests.sessions.Session.request")
    except ImportError:
        pass  # requests not installed, nothing to patch
