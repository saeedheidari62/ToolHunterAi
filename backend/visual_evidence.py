def build_visual_evidence(image_result):
    """
    Convert image analysis results into
    a standardized visual-evidence structure.
    """

    if not image_result:
        return {
            "available": False,
            "confidence": 0,
            "evidence": [],
            "warnings": [
                "No image analysis result available."
            ]
        }

    quality_score = image_result.get(
        "quality_score",
        0
    )

    image_risk = image_result.get(
        "image_risk",
        0
    )

    evidence = []
    warnings = []

    if quality_score >= 80:
        evidence.append(
            "Image quality is sufficient for visual inspection."
        )

    elif quality_score >= 50:
        evidence.append(
            "Image quality is partially suitable for visual inspection."
        )

        warnings.append(
            "Image quality may limit visual analysis."
        )

    else:
        warnings.append(
            "Image quality is too low for reliable visual analysis."
        )

    if image_risk >= 20:
        warnings.append(
            "Image risk is elevated."
        )

    confidence = max(
        0,
        min(
            100,
            round(
                quality_score - (image_risk * 0.5)
            )
        )
    )

    return {
        "available": True,
        "confidence": confidence,
        "evidence": evidence,
        "warnings": warnings
    }
