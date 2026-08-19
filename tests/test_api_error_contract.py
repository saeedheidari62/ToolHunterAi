from backend.api import analyze_single_ad


def test_invalid_input_error_contract():
    result = analyze_single_ad({"title": "Bosch GBH 2-26"})
    assert result["error"] == "INVALID_AD"
    assert result["message"] == "Invalid advertisement data."
    assert isinstance(result.get("errors"), list)


def test_unknown_tool_error_contract():
    result = analyze_single_ad({"title": "Unknown Tool XYZ 9999", "description": "unknown", "price": 1000000, "seller_type": "personal", "condition": "used"})
    assert result["error"] == "TOOL_NOT_RECOGNIZED"
    assert result["message"] == "Tool not recognized."
    assert result.get("matched_tools") == []


def test_divar_fetch_failure_has_structured_diagnostics(monkeypatch):
    from backend import api
    monkeypatch.setattr(api.diwar_fetcher, "fetch", lambda _: (_ for _ in ()).throw(RuntimeError("fetch failed")))
    result = analyze_single_ad({"url": "https://divar.ir/v/INVALID_TEST_URL"})
    assert result["error"] == "FETCH_FAILED"
    assert result["message"] == "Divar advertisement could not be fetched."
    assert result["diagnostics"]["fetch_attempts"] == 3
    assert result["diagnostics"]["last_stage"] == "fetch"
