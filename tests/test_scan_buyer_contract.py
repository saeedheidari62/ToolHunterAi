from backend.web_app import app


def test_scan_route_exposes_buyer_opportunity_contract(monkeypatch):
    class FakeScanner:
        def scan_cities(self, cities, limit_per_tool=5, top_n=10, tool_ids=None):
            return {
                "cities": cities,
                "cities_scanned": 2,
                "tools_scanned": 8,
                "opportunities": 1,
                "ranking": [],
                "best_choice": None,
                "buyer_opportunities": [
                    {
                        "status": "BUY_NOW",
                        "tool_id": "bosch_gbh_2_26",
                        "tool_name": "Bosch GBH 2-26",
                        "city": "tehran",
                        "url": "https://divar.ir/v/gbh226",
                        "price": 8500000,
                        "buy_score": 94,
                        "risk_score": 30,
                        "opportunity_score": 91,
                        "evidence": {
                            "price": "18% below market",
                            "tool_match": True,
                            "testing": True,
                            "warranty": False,
                        },
                    }
                ],
                "buyer_best_choice": {
                    "status": "BUY_NOW",
                    "tool_id": "bosch_gbh_2_26",
                    "url": "https://divar.ir/v/gbh226",
                },
                "errors": [],
                "scan_health": {"status": "HEALTHY"},
            }

    monkeypatch.setattr("backend.web_app.auto_scanner", FakeScanner())
    client = app.test_client()
    response = client.post("/scan", json={"cities": ["tehran", "karaj"]})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["buyer_opportunities"][0]["status"] == "BUY_NOW"
    assert payload["buyer_opportunities"][0]["url"].startswith("https://divar.ir/")
    assert payload["buyer_opportunities"][0]["evidence"]["tool_match"] is True
    assert payload["buyer_best_choice"]["tool_id"] == "bosch_gbh_2_26"
    assert payload["scan_health"]["status"] == "HEALTHY"
