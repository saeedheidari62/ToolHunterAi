from pathlib import Path

from PIL import Image, UnidentifiedImageError

from image_quality_analyzer import analyze_image_quality


ALLOWED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP"
}


MIN_WIDTH = 300
MIN_HEIGHT = 300


def analyze_image(image_file):

    if not image_file:
        return {
            "image_risk": 10,
            "quality_score": 0,
            "quality_risk": 10,
            "image_reasons": [
                "No image provided."
            ]
        }

    path = Path(image_file)

    if not path.exists():
        return {
            "image_risk": 15,
            "quality_score": 0,
            "quality_risk": 15,
            "image_reasons": [
                "Image file was not found."
            ]
        }

    if path.stat().st_size == 0:
        return {
            "image_risk": 15,
            "quality_score": 0,
            "quality_risk": 15,
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
                    "quality_score": 0,
                    "quality_risk": 15,
                    "image_reasons": [
                        "Unsupported image format."
                    ]
                }

            try:
                image.verify()

            except Exception:
                return {
                    "image_risk": 20,
                    "quality_score": 0,
                    "quality_risk": 20,
                    "image_reasons": [
                        "Image file is corrupted."
                    ]
                }

    except UnidentifiedImageError:

        return {
            "image_risk": 15,
            "quality_score": 0,
            "quality_risk": 15,
            "image_reasons": [
                "Image file is not a valid image."
            ]
        }

    except Exception:

        return {
            "image_risk": 20,
            "quality_score": 0,
            "quality_risk": 20,
            "image_reasons": [
                "Image could not be analyzed."
            ]
        }

    reasons = [
        "Valid image provided.",
        f"Image format: {image_format}.",
        f"Image resolution: {width}x{height}."
    ]

    validation_risk = 0

    if width < MIN_WIDTH or height < MIN_HEIGHT:

        validation_risk += 5

        reasons.append(
            "Image resolution is low."
        )

    quality_result = analyze_image_quality(
        str(path)
    )

    quality_score = quality_result.get(
        "quality_score",
        0
    )

    quality_risk = quality_result.get(
        "quality_risk",
        0
    )

    quality_reasons = quality_result.get(
        "quality_reasons",
        []
    )

    reasons.extend(
        quality_reasons
    )

    image_risk = max(
        validation_risk,
        quality_risk
    )

    image_risk = max(
        0,
        min(
            100,
            round(image_risk)
        )
    )

    return {
        "image_risk": image_risk,
        "quality_score": quality_score,
        "quality_risk": quality_risk,
        "brightness": quality_result.get(
            "brightness"
        ),
        "contrast": quality_result.get(
            "contrast"
        ),
        "sharpness": quality_result.get(
            "sharpness"
        ),
        "resolution": quality_result.get(
            "resolution",
            f"{width}x{height}"
        ),
        "image_reasons": reasons
    }
