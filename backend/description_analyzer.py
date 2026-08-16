def analyze_description(description):
    risk_score = 0
    reasons = []

    text = (description or "").lower()

    positive_words = [
        "کم کار",
        "تمیز",
        "سالم",
        "نو",
        "تست",
        "بدون ایراد",
        "کارکرد کم"
    ]

    negative_words = [
        "تعمیر",
        "تعمیر شده",
        "سوخته",
        "ایراد",
        "خراب",
        "نیاز به تعمیر",
        "فوری",
        "زود بفروش",
        "بدون تست"
    ]

    price_request_phrases = [
        "استعلام قیمت",
        "استعلام قیمت روز",
        "قیمت روز",
        "برای استعلام قیمت",
        "برای اطلاع از قیمت",
        "جهت اطلاع از قیمت",
        "قیمت تماس",
        "تماس بگیرید",
        "با ما در تماس باشید",
        "برای قیمت تماس",
        "قیمت توافقی",
        "قیمت در تماس"
    ]

    for word in positive_words:
        if word in text:
            reasons.append(f"Positive description: {word}")

    for word in negative_words:
        if word in text:
            risk_score += 10
            reasons.append(f"Risk phrase detected: {word}")

    price_signal = "NONE"

    for phrase in price_request_phrases:
        if phrase in text:
            price_signal = "PRICE_ON_REQUEST"
            reasons.append(
                f"Price availability signal: {phrase}"
            )
            break

    if price_signal == "PRICE_ON_REQUEST":
        risk_score += 20

    risk_score = min(risk_score, 100)

    return {
        "description_risk": risk_score,
        "description_reasons": reasons,
        "price_signal": price_signal
    }
