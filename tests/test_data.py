from src.data.generator import generate_demo_data
from src.data.loader import RetailDataLoader

def test_demo_data_shape():
    data = generate_demo_data(seed=1, days=10)
    assert data["products"].sku.nunique() == 50
    assert data["inventory"].location.nunique() == 5

def test_loader_fallback(tmp_path):
    data = RetailDataLoader(tmp_path).load()
    assert not data["sales"].empty
    assert not data["inventory"].empty
