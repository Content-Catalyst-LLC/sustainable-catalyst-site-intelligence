"""Regression checks for source-labeled economics fallback."""
from unittest.mock import patch
import json
from app.economics_world_bank_fallback_v4563 import get_country_records

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return b''
def test_world_bank_value_and_attribution():
    payload=[{"page":1},[{"date":"2024","value":12345,"country":{"value":"Kenya"}}]]
    class Stub:
        def __enter__(self): return self
        def __exit__(self,*args): return False
    with patch("app.economics_world_bank_fallback_v4563.urlopen", return_value=Stub()), patch("app.economics_world_bank_fallback_v4563.json.load", return_value=payload):
        rows=get_country_records("KEN","NY.GDP.MKTP.CD")
    assert len(rows)==1
    assert rows[0]["value_number"]==12345
    assert rows[0]["source_id"]=="world-bank"
    assert "not been ingested" in rows[0]["notes"]
def test_invalid_country_makes_no_network_calls():
    with patch("app.economics_world_bank_fallback_v4563.urlopen") as req:
        assert get_country_records("KE")==[]
        req.assert_not_called()
