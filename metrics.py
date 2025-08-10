import json

def calculate_custom_metrics(axe_results):
    violations = axe_results.get("violations", [])
    passes = axe_results.get("passes", [])

    metrics = {
        "alternative_text": 0,
        "color_contrast": 0,
        "subtitles_audio": 0,
        "keyboard_navigation": 0,
        "structured_navigation": 0,
        "clear_instructions": 0,
        "input_assistance": 0,
        "error_feedback": 0,
        "localization_score": 0  # to be filled later
    }

    # Simplified scoring: 1 if pass found for rule, 0 otherwise
    for item in passes:
        if item["id"] == "image-alt":
            metrics["alternative_text"] = 1
        if item["id"] == "color-contrast":
            metrics["color_contrast"] = 1
        if item["id"] in ["video-caption", "audio-caption"]:
            metrics["subtitles_audio"] = 1
        if item["id"] == "keyboard":
            metrics["keyboard_navigation"] = 1
        if item["id"] == "page-has-heading-one":
            metrics["structured_navigation"] = 1
        if item["id"] == "label":
            metrics["clear_instructions"] = 1
        if item["id"] == "autocomplete-valid":
            metrics["input_assistance"] = 1
        if item["id"] == "aria-valid-attr-value":
            metrics["error_feedback"] = 1

    return metrics

def compute_overall_score(metrics):
    weights = {
        "alternative_text": 0.3,
        "color_contrast": 0.3,
        "subtitles_audio": 0.4,
        "keyboard_navigation": 0.6,
        "structured_navigation": 0.4,
        "clear_instructions": 0.4,
        "input_assistance": 0.3,
        "error_feedback": 0.3,
        "localization_score": 1.0
    }

    sub_scores = {
        "perceptiveness": (
            metrics["alternative_text"] * weights["alternative_text"] +
            metrics["color_contrast"] * weights["color_contrast"] +
            metrics["subtitles_audio"] * weights["subtitles_audio"]
        ),
        "operability": (
            metrics["keyboard_navigation"] * weights["keyboard_navigation"] +
            metrics["structured_navigation"] * weights["structured_navigation"]
        ),
        "understandability": (
            metrics["clear_instructions"] * weights["clear_instructions"] +
            metrics["input_assistance"] * weights["input_assistance"] +
            metrics["error_feedback"] * weights["error_feedback"]
        ),
        "localization": metrics["localization_score"] * weights["localization_score"]
    }

    overall = (
        0.3 * sub_scores["perceptiveness"] +
        0.3 * sub_scores["operability"] +
        0.4 * sub_scores["understandability"]
    )

    full_accessibility_score = 0.6 * overall + 0.4 * sub_scores["localization"]

    return full_accessibility_score, sub_scores
