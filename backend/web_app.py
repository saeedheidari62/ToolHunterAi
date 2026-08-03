from flask import Flask, request
from ad_analyzer import analyze_ad
from decision_engine import make_decision
from image_analyzer import analyze_image
from history_manager import save_history, get_history


app = Flask(__name__)


@app.route("/")
def home():

    return """
<!DOCTYPE html>
<html lang="fa" dir="rtl">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>ToolHunterAI</title>

<style>

body {
    font-family: Arial;
    background:#f2f2f2;
    padding:20px;
}

.box {
    background:white;
    max-width:500px;
    margin:auto;
    padding:20px;
    border-radius:15px;
}

input, textarea {
    width:100%;
    padding:12px;
    margin:8px 0;
    box-sizing:border-box;
}

button {
    width:100%;
    padding:15px;
    background:#111;
    color:white;
    border:none;
    border-radius:10px;
}

a {
    display:block;
    margin-top:15px;
}

</style>

</head>


<body>


<div class="box">


<h1>🔧 ToolHunterAI</h1>


<form action="/analyze" method="post" enctype="multipart/form-data">


شناسه ابزار

<input name="tool_id" placeholder="bosch_gbh_2_26">


قیمت

<input name="price" type="number">


نوع فروشنده

<input name="seller_type" placeholder="Personal">


تست دارد؟

<input name="has_test" placeholder="yes/no">


گارانتی دارد؟

<input name="has_warranty" placeholder="yes/no">


وضعیت

<input name="condition" placeholder="Used">


توضیحات آگهی

<textarea name="description"></textarea>


عکس آگهی

<input type="file" name="image">


<button>
تحلیل آگهی
</button>


</form>


<a href="/history">
تاریخچه تحلیل‌ها
</a>


</div>


</body>

</html>
"""


@app.route("/analyze", methods=["POST"])
def analyze():

    tool_id = request.form.get("tool_id","").strip()


    if not tool_id:
        return "شناسه ابزار وارد نشده است"



    ad_data = {

        "tool_name": tool_id,

        "asking_price":
        int(request.form.get("price",0)),

        "seller_type":
        request.form.get("seller_type","").title(),

        "has_test":
        request.form.get("has_test","").lower()
        in ["yes","y"],

        "has_warranty":
        request.form.get("has_warranty","").lower()
        in ["yes","y"],

        "condition":
        request.form.get("condition","").title(),

        "description":
        request.form.get("description","")

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



    reasons = ""

    for r in result["reasons"]:
        reasons += f"<li>{r}</li>"



    return f"""

<html lang="fa" dir="rtl">

<head>
<meta charset="UTF-8">
</head>


<body>


<h1>نتیجه تحلیل</h1>


<h2>{result['decision']}</h2>


<p>
Buy Score: {result['buy_score']}
</p>


<p>
Risk Score: {result['risk_score']}
</p>


<p>
Ad Score: {result['ad_score']}
</p>


<h3>دلایل:</h3>


<ul>

{reasons}

</ul>


<a href="/">
بازگشت
</a>


</body>

</html>

"""



@app.route("/history")
def history():

    data = get_history()


    items = ""


    for item in data:

        items += f"""

<hr>

ابزار: {item['tool_name']}<br>

قیمت: {item['price']}<br>

نتیجه: {item['decision']}<br>

Buy Score: {item['buy_score']}<br>

Risk Score: {item['risk_score']}<br>

تاریخ: {item['date']}

"""


    return f"""

<html lang="fa" dir="rtl">

<head>
<meta charset="UTF-8">
</head>


<body>


<h1>
تاریخچه تحلیل‌ها
</h1>


{items}


<br>

<a href="/">
بازگشت
</a>


</body>


</html>

"""



if __name__ == "__main__":

    app.run(debug=True)