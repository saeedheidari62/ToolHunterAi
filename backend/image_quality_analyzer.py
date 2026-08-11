from PIL import Image, ImageStat, ImageFilter


MIN_WIDTH = 300
MIN_HEIGHT = 300

BRIGHTNESS_LOW = 35
BRIGHTNESS_HIGH = 225

CONTRAST_MIN = 20

SHARPNESS_LOW = 80


def analyze_image_quality(image_file):
    reasons = []
    risk_score = 0

    try:
        with Image.open(image_file) as image:
            image = image.convert("RGB")

            width, height = image.size

            gray = image.convert("L")

            brightness = ImageStat.Stat(
                gray
            ).mean[0]

            contrast = ImageStat.Stat(
                gray
            ).stddev[0]

            laplacian = gray.filter(
                ImageFilter.Kernel(
                    (3, 3),
                    (
                        -1, -1, -1,
                        -1,  8, -1,
                        -1, -1, -1
                    )
                )
            )

            sharpness = ImageStat.Stat(
                laplacian
            ).var[0]

    except Exception:
        return {
            "quality_score": 0,
            "quality_risk": 30,
            "quality_reasons": [
                "Image quality could not be analyzed."
            ]
        }

    quality_score = 100

    # Resolution
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        quality_score -= 20
        risk_score += 10

        reasons.append(
            "Image resolution is low."
        )
    else:
        reasons.append(
            "Image resolution is acceptable."
        )

    # Brightness
    if brightness < BRIGHTNESS_LOW:
        quality_score -= 15
        risk_score += 8

        reasons.append(
            "Image is too dark."
        )

    elif brightness > BRIGHTNESS_HIGH:
        quality_score -= 15
        risk_score += 8

        reasons.append(
            "Image is too bright."
        )

    else:
        reasons.append(
            "Image brightness is acceptable."
        )

    # Contrast
    if contrast < CONTRAST_MIN:
        quality_score -= 10
        risk_score += 5

        reasons.append(
            "Image contrast is low."
        )
    else:
        reasons.append(
            "Image contrast is acceptable."
        )

    # Sharpness
    if sharpness < SHARPNESS_LOW:
        quality_score -= 20
        risk_score += 10

        reasons.append(
            "Image may be blurry."
        )
    else:
        reasons.append(
            "Image sharpness is acceptable."
        )

    quality_score = max(
        0,
        min(
            100,
            round(quality_score)
        )
    )

    risk_score = max(
        0,
        min(
            100,
            round(risk_score)
        )
    )

    return {
        "quality_score": quality_score,
        "quality_risk": risk_score,
        "quality_reasons": reasons,
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "resolution": f"{width}x{height}"
    }
