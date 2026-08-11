from pathlib import Path

from PIL import Image, UnidentifiedImageError


ALLOWED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP"
}

MIN_WIDTH = 300
MIN_HEIGHT = 300


def analyze_image(image_file):

    reasons = []
    risk_score = 0

    if not image_file:
        return {
            "image_risk": 10,
            "image_reasons": [
                "No image provided."
            ]
        }

    path = Path(image_file)

    if not path.exists():
        return {
            "image_risk": 15,
            "image_reasons": [
                "Image file was not found."
            ]
        }

    if path.stat().st_size == 0:
        return {
            "image_risk": 15,
            "image_reasons": [
                "Image file is empty."
            ]
        }

    try:
        with Image.open(path) as image:

            image_format = image.format
            width, height = image.size

            if image_format not in ALLOWED_FORMATS:

                return {
                    "image_risk": 15,
                    "image_reasons": [
                        "Unsupported image format."
                    ]
                }

            try:
                image.verify()
            except Exception:

                return {
                    "image_risk": 20,
                    "image_reasons": [
                        "Image file is corrupted."
                    ]
                }

    except UnidentifiedImageError:

        return {
            "image_risk": 15,
            "image_reasons": [
                "Image file is not a valid image."
            ]
        }

    except Exception:

        return {
            "image_risk": 20,
            "image_reasons": [
                "Image could not be analyzed."
            ]
        }

    reasons.append(
        "Valid image provided."
    )

    reasons.append(
        f"Image format: {image_format}."
    )

    reasons.append(
        f"Image resolution: {width}x{height}."
    )

    if width < MIN_WIDTH or height < MIN_HEIGHT:

        risk_score += 5

        reasons.append(
            "Image resolution is low."
        )

    else:

        reasons.append(
            "Image resolution is acceptable."
        )

    return {
        "image_risk": risk_score,
        "image_reasons": reasons
    }
