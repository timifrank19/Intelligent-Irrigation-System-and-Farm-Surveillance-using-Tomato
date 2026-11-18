# =============================================================================
# FILE:      recommendation.py
# LOCATION:  Intelligent_Tomato_Farm/recommendation.py
# PURPOSE:   Convert the FINAL disease decision (from the supervisor) into an
#            agricultural recommendation. This module NEVER diagnoses disease
#            independently — it only reads the supervisor's decision.
# =============================================================================

from __future__ import annotations


# Covers both leaf classes and fruit classes. Unknown classes get a default.
_RECOMMENDATIONS = {
    # ---- Tomato FRUIT classes ----
    "Anthracnose": "Remove affected fruits. Apply a labelled fungicide. "
                   "Avoid overhead irrigation and sanitise tools.",
    "Bacterial_Spot": "Remove and destroy infected fruits. Apply copper-based "
                      "bactericide. Rotate crops and avoid working with wet plants.",
    "Blossom end rot": "Maintain consistent soil moisture and adequate calcium. "
                       "Mulch to stabilise water levels. Do not over-fertilise with nitrogen.",
    "Healthy Tomato": "No action required. Continue standard monitoring and "
                      "balanced irrigation.",
    "Spotted wilt Virus": "Remove and destroy infected plants. Control thrips "
                          "(the main vector). Avoid planting near infected fields.",

    # ---- Tomato LEAF classes ----
    "Tomato_Bacterial_spot": "Remove infected leaves. Apply copper-based spray. "
                             "Avoid overhead watering.",
    "Tomato_Early_Blight": "Remove affected leaves. Apply chlorothalonil or "
                           "mancozeb. Improve air circulation.",
    "Tomato_Late_Blight": "Act immediately. Remove infected plants. Apply "
                          "protective fungicide. Avoid working when foliage is wet.",
    "Tomato_Healthy": "No action required. Maintain normal care.",
    "Tomato_Leaf_Mold": "Increase ventilation. Reduce humidity. Apply a labelled "
                        "fungicide if symptoms persist.",
    "Tomato_Septoria_Spot": "Remove infected lower leaves. Apply fungicide. "
                            "Mulch to reduce soil splash.",
    "Tomato_Spider_Mite": "Spray with water to raise humidity. Apply insecticidal "
                          "soap or miticide. Avoid drought stress.",
    "Tomato_Taget_Spot": "Remove affected foliage. Apply a labelled fungicide. "
                         "Improve air flow. Rotate crops.",
    "Tomato_Target_Spot": "Remove affected foliage. Apply a labelled fungicide. "
                          "Improve air flow. Rotate crops.",   # corrected spelling
    "Tomato_Mosaic_Virus": "Remove and destroy infected plants. Disinfect tools. "
                           "Do not save seed from infected plants.",
    "Tomato_Leaf_Curl_Virus": "Control whiteflies. Remove infected plants. Use "
                              "tolerant varieties where possible.",

    # ---- Sentinel ----
    "unsure": "Evidence is insufficient or contradictory. Please capture a "
              "clearer RGB image of the affected leaf or fruit and try again.",
}


def recommend(primary_class: str, uncertain: bool = False) -> str:
    if uncertain:
        return ("Supervisor is uncertain about this result. "
                "Recommendation withheld until evidence is clearer. "
                "Capture a new RGB image of the affected area.")

    if primary_class in _RECOMMENDATIONS:
        return _RECOMMENDATIONS[primary_class]

    return (f"No specific recommendation is available for '{primary_class}'. "
            f"Consult a local agricultural extension officer.")


def available_classes() -> list:
    return sorted(_RECOMMENDATIONS.keys())
