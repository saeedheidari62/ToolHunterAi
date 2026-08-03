def analyze_description(description):

    risk_score = 0
    reasons = []

    text = description.lower()


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


    for word in positive_words:
        if word in text:
            reasons.append(f"Positive description: {word}")


    for word in negative_words:
        if word in text:
            risk_score += 10
            reasons.append(f"Risk phrase detected: {word}")


    risk_score = min(risk_score, 100)


    return {
        "description_risk": risk_score,
        "description_reasons": reasons
    }