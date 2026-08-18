from backend.technical_intelligence_collector import TechnicalIntelligenceCollector


def test_collect_normalizes_standard_technical_fields():
    collector = TechnicalIntelligenceCollector()
    result = collector.collect(
        {
            "technical_data": {
                "voltage_v": 14.4,
                "power_w": 500,
                "max_torque": 30,
                "chuck_size": "10 mm",
            },
            "technical_sources": ["manufacturer"],
        }
    )

    assert result["success"] is True
    assert result["technical"]["voltage"] == 14.4
    assert result["technical"]["power"] == 500
    assert result["technical"]["torque"] == 30
    assert result["technical"]["chuck"] == "10 mm"
    assert result["technical_sources"] == ["manufacturer"]


def test_collect_does_not_invent_missing_specs():
    collector = TechnicalIntelligenceCollector()
    result = collector.collect({"brand": "Makita", "model": "8281DWAE"})

    assert result["success"] is True
    assert result["technical"] == {}
    assert result["technical_confidence"] == "NONE"


def test_collect_preserves_extra_specifications():
    collector = TechnicalIntelligenceCollector()
    result = collector.collect(
        {
            "technical": {
                "specifications": {
                    "country": "Japan",
                    "gear_count": 2,
                }
            }
        }
    )

    assert result["technical"]["country"] == "Japan"
    assert result["technical"]["gear_count"] == 2


def test_merge_keeps_existing_and_new_facts():
    collector = TechnicalIntelligenceCollector()
    result = collector.merge(
        {
            "technical": {"voltage": 14.4},
            "technical_sources": ["manufacturer"],
        },
        {
            "technical": {"torque": 30},
            "technical_sources": ["catalog"],
            "technical_confidence": "HIGH",
        },
    )

    assert result["technical"] == {"voltage": 14.4, "torque": 30}
    assert result["technical_sources"] == ["manufacturer", "catalog"]
    assert result["technical_confidence"] == "HIGH"
