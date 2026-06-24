def parse_prd(prd: dict) -> list[str]:
    """
    Flattens PRD JSON into a single list of field names agent needs to locate.
    """
    fields = []
    for section in ["kpis", "dimensions", "filters", "metrics"]:
        fields.extend(prd.get(section, []))
    return list(set(fields))