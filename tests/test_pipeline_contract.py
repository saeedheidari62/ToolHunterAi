from backend.collector import AdCollector


def test_collector_preserves_marketplace_metadata():
    collector = AdCollector()
    ad = collector.collect(
        title="Makita 8281DWAE",
        description="Original Japan",
        price=27000000,
        seller_type="personal",
        testing=False,
        warranty=False,
        condition="new",
        url="https://divar.ir/v/example",
        city="karaj",
        district="gohardasht",
        brand_model="Makita 8281DWAE",
        category="cordless_drill",
        image_count=7,
        image_urls=["https://example.com/1.webp"],
    )

    assert ad["city"] == "karaj"
    assert ad["district"] == "gohardasht"
    assert ad["brand_model"] == "Makita 8281DWAE"
    assert ad["category"] == "cordless_drill"
    assert ad["image_count"] == 7
    assert ad["image_urls"] == ["https://example.com/1.webp"]


def test_collect_many_preserves_metadata():
    collector = AdCollector()
    ads = collector.collect_many([
        {
            "title": "Bosch GBH 2-26",
            "description": "Original",
            "price": 8500000,
            "seller_type": "personal",
            "city": "tehran",
            "district": "niavaran",
            "brand_model": "Bosch GBH 2-26",
        }
    ])

    assert len(ads) == 1
    assert ads[0]["city"] == "tehran"
    assert ads[0]["district"] == "niavaran"
    assert ads[0]["brand_model"] == "Bosch GBH 2-26"
