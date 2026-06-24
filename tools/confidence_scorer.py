def compute_confidence(
    match_type: str,       # "exact" | "partial" | "semantic"
    layer: str,            # "GOLD" | "SILVER" | "BRONZE" | None
    similarity: float,     # 0.0 - 1.0
    null_pct: float,       # 0.0 - 100.0
    quality: str           # "CLEAN" | "DEGRADED" | "POOR" | "UNKNOWN"
) -> dict:
    """
    Computes confidence score for a gap classification.
    Returns score (0-100) + label.
    """
    # Base score from match type
    base = {"exact": 90, "partial": 70, "semantic": 50}.get(match_type, 30)

    # Layer bonus
    layer_bonus = {"GOLD": 10, "SILVER": 5, "BRONZE": 0}.get(layer or "", 0)

    # Similarity adjustment (for semantic matches)
    sim_score = similarity * 20 if match_type == "semantic" else 0

    # Data quality penalty
    quality_penalty = {"CLEAN": 0, "DEGRADED": 10, "POOR": 25, "UNKNOWN": 15}.get(quality, 15)

    # Null penalty
    null_penalty = min(null_pct * 0.3, 20)

    raw_score = base + layer_bonus + sim_score - quality_penalty - null_penalty
    score = round(max(0, min(100, raw_score)), 1)

    label = (
        "High" if score >= 75 else
        "Medium" if score >= 50 else
        "Low"
    )

    return {"score": score, "label": label}