from flask import Flask, request, render_template

from backend.api import analyze_single_ad
from backend.history_manager import save_history, get_history


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    url = request.form.get(
        "url",
        ""
    ).strip()

    if not url:
        return "لینک آگهی دیوار وارد نشده است"

    try:
        from backend.diwar_fetcher import DiwarFetcher

        raw_ad = DiwarFetcher().fetch(url)

        result = analyze_single_ad(
            raw_ad
        )

        if "error" in result:
            return render_template(
                "result.html",
                result=result
            )

        save_history({
            "tool_name": result.get(
                "tool",
                ""
            ),
            "price": raw_ad.get(
                "price",
                0
            ),
            "decision": result.get(
                "decision",
                ""
            ),
            "buy_score": result.get(
                "buy_score",
                0
            ),
            "risk_score": result.get(
                "risk_score",
                0
            ),
            "ad_score": result.get(
                "ad_score",
                0
            )
        })

        return render_template(
            "result.html",
            result=result
        )

    except Exception as e:
        return f"خطا در تحلیل آگهی: {e}"


@app.route("/history")
def history():

    return render_template(
        "history.html",
        history=get_history()
    )


@app.route("/dashboard")
def dashboard():

    data = get_history()

    total = len(data)

    buy = len([
        x for x in data
        if x["decision"] == "BUY"
    ])

    review = len([
        x for x in data
        if x["decision"] == "REVIEW"
    ])

    dont_buy = len([
        x for x in data
        if x["decision"] == "DON'T BUY"
    ])

    avg_buy = (
        round(
            sum(
                x["buy_score"]
                for x in data
            ) / total,
            1
        )
        if total
        else 0
    )

    return render_template(
        "dashboard.html",
        total=total,
        buy=buy,
        review=review,
        dont_buy=dont_buy,
        avg_buy=avg_buy
    )


if __name__ == "__main__":
    app.run(
        debug=True
    )
