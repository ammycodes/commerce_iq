from fastapi.testclient import TestClient
from src.api.server import app
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_overview():
    r = client.get("/overview")
    assert r.status_code == 200 and r.json()["sku_count"] > 0
