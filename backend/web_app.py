from flask import Flask, request, render_template

from ad_analyzer import analyze_ad
from decision_engine import make_decision
from image_analyzer import analyze_image
from history_manager import save_history, get_history

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    tool_id = request.form.get("tool_id", "").strip()

    if not tool_id:
        return "شناسه ابزار وارد نشده است"

    ad_data = {
        "tool_name": tool_id,
        "asking_price": int(request.form.get("price", 0)),
        "seller_type": request.form.get("seller_type", "").title(),
        "has_test": request.form.get("has_test", "").lower() in ["yes", "y"],
        "has_warranty": request.form.get("has_warranty", "").lower() in ["yes", "y"],
        "condition": request.form.get("condition", "").title(),
        "description": request.form.get("description", "")
    }

    analyzed_ad = analyze_ad(ad_data)

    image_file = request.files.get("image")

    image_result = analyze_image(image_file)

    analyzed_ad["analysis"].extend(
        image_result["image_reasons"]
    )

    result = make_decision(analyzed_ad)

    save_history({
        "tool_name": tool_id,
        "price": ad_data["asking_price"],
        "decision": result["decision"],
        "buy_score": result["buy_score"],
        "risk_score": result["risk_score"],
        "ad_score": result["ad_score"]
    })

    return render_template(
        "result.html",
        result=result
    )


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

    buy = len([x for x in data if x["decision"] == "BUY"])

    review = len([x for x in data if x["decision"] == "REVIEW"])

    dont_buy = len([x for x in data if x["decision"] == "DON'T BUY"])

    avg_buy = (
        round(sum(x["buy_score"] for x in data) / total, 1)
        if total else 0
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
    app.run(debug=True)