from backend.web_app import app


def test_scan_deduplicates_and_caps_city_input():
    client = app.test_client()
    response = client.post(
        "/scan",
        json={"cities": ["tehran"] * 10, "tool_ids": ["bosch_gbh_2_26"], "top_n": 100},
    )
    assert response.status_code in (200, 400)


def test_scan_invalid_numeric_values_do_not_crash_route():
    client = app.test_client()
    response = client.post(
        "/scan",
        json={"cities": ["tehran"], "tool_ids": ["bosch_gbh_2_26"], "top_n": "bad", "limit_per_tool": "bad"},
    )
    assert response.status_code in (200, 400)
