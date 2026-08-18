"""Legacy CLI compatibility wrapper.

The production pipeline lives in backend.api. This module intentionally delegates
to that single pipeline so the project does not maintain two decision engines.
"""

from .api import analyze_single_ad


def main():
    ads = [
        {
            "title": "Bosch GBH226",
            "description": "Used Bosch original with testing",
            "price": 8500000,
            "seller_type": "personal",
            "testing": True,
            "warranty": False,
            "condition": "used",
        },
        {
            "title": "ماکیتا 2470",
            "description": "Makita original used with testing",
            "price": 7000000,
            "seller_type": "business",
            "testing": True,
            "warranty": True,
            "condition": "used",
        },
    ]

    print("=== ToolHunterAI CLI Compatibility ===")
    for ad in ads:
        print("\nAnalyzing:")
        print(ad["title"])
        print(analyze_single_ad(ad))


if __name__ == "__main__":
    main()
