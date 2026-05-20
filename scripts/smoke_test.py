"""Basic TRS Platform smoke tests. Run from project root: python scripts/smoke_test.py"""
from fastapi.testclient import TestClient
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app

client = TestClient(app.app)

def check(path: str, expected=(200, 302, 303)):
    r = client.get(path, follow_redirects=False)
    assert r.status_code in expected, f"{path} returned {r.status_code}: {r.text[:200]}"
    print(f"OK {path} -> {r.status_code}")

if __name__ == "__main__":
    check("/api/status", (200,))
    check("/login", (200,))
    check("/", (200,302,303))
    check("/job-files", (200,302,303))
    check("/equipment-maintenance", (200,302,303))
    print("TRS smoke test passed")
