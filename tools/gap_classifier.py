def classify_field(field: str, metadata: dict) -> dict:
    """
    Checks field across Gold → Silver → Bronze.
    Returns classification + where it was found.
    """
    field_upper = field.upper()
    for layer in ["GOLD", "SILVER", "BRONZE"]:
        for table, cols in metadata[layer].items():
            if any(field_upper in col.upper() or col.upper() in field_upper for col in cols):
                level_map = {"GOLD": "L1", "SILVER": "L2", "BRONZE": "L3"}
                return {
                    "field": field,
                    "level": level_map[layer],
                    "found_in_layer": layer,
                    "found_in_table": table,
                    "action": {
                        "L1": "Ready for reporting",
                        "L2": "Promote to Gold — build aggregation",
                        "L3": "Transform Bronze → Silver → Gold pipeline needed",
                    }[level_map[layer]]
                }
    return {
        "field": field,
        "level": "L4",
        "found_in_layer": None,
        "found_in_table": None,
        "action": "Net new — needs sourcing from upstream"
    }