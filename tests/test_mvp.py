from backend.api import analyze_single_ad


def run(name, ad, expected_tool=None, expected_error=None):
    result = analyze_single_ad(ad)
    if expected_error:
        assert result.get("error") == expected_error, (name, result)
    else:
        assert "error" not in result, (name, result)
        assert result.get("tool") == expected_tool, (name, result)
        assert result.get("decision") in {"BUY", "REVIEW", "DON'T BUY"}, (name, result)
        assert 0 <= result.get("buy_score", -1) <= 100, (name, result)
        assert 0 <= result.get("risk_score", -1) <= 100, (name, result)
    print("PASS:", name)


run("Bosch GBH 2-26", {"title":"Bosch GBH 2-26", "description":"دریل بتن کن بوش GBH 2-26 سالم با امکان تست", "price":8500000, "seller_type":"personal", "testing":True, "warranty":False, "condition":"used"}, "bosch_gbh_2_26")
run("Bosch GSH500", {"title":"Bosch GSH500", "description":"بتن کن بوش مدل GSH500 سالم", "price":9000000, "seller_type":"personal", "testing":False, "warranty":False, "condition":"used"}, "bosch_gsh500")
run("Makita HR2470", {"title":"Makita HR2470", "description":"بتن کن ماکیتا 2470 سالم", "price":8000000, "seller_type":"personal", "testing":True, "warranty":False, "condition":"used"}, "makita_hr2470")
print("ALL REGRESSION TESTS PASSED")
