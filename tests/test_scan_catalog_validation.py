from backend.web_app import app


def test_scan_rejects_unknown_tool_id():
    client = app.test_client()
    response = client.post(
        "/scan",
        json={"cities": ["tehran"], "tool_ids": ["not_a_real_tool"]},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "INVALID_SCAN_INPUT"
    assert payload["unknown_tool_ids"] == ["not_a_real_tool"]
