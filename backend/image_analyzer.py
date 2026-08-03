def analyze_image(image_file):

    reasons = []
    risk_score = 0

    if image_file:

        reasons.append("Image provided.")

        # نسخه اولیه:
        # در آینده تحلیل هوش مصنوعی تصویر اضافه می‌شود

        risk_score = 0

    else:

        reasons.append("No image provided.")
        risk_score = 10


    return {
        "image_risk": risk_score,
        "image_reasons": reasons
    }