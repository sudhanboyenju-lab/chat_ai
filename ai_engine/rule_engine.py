def rule_engine_answer(entity_id, entities, config):
    """Build a direct, formatted answer straight from structured data - no LLM call."""
    data = entities[entity_id]

    lines = [f"**{data[config.entity_name_field]}**", ""]

    if data.get("documents"):
        lines.append("Details:")
        lines.extend(f"- {doc}" for doc in data["documents"])
        lines.append("")

    for field_name in config.detail_fields:
        if field_name in data:
            label = field_name.replace("_", " ").title()
            lines.append(f"{label}: {data[field_name]}")

    return "\n".join(lines), [entity_id]
