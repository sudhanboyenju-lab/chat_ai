"""
Situation-based guidance: turns "my father passed away and I want to
transfer his land" into an ordered, step-by-step answer covering every
service involved.

Split of responsibilities, on purpose:
- The LLM's ONLY job is recognizing which known services are relevant to
  the person's situation. It never invents a service id, and it never
  decides the order.
- The order comes entirely from your `dependency_table` data (set up by an
  admin), via resolve_order()'s prerequisite-following.
- Each step's actual content (documents, fee, office) comes from your
  existing rule_engine_answer() - the same trusted source used everywhere
  else - so guidance can't hallucinate details either.
"""

import json
import re

from .rag import get_response_text
from .rule_engine import rule_engine_answer


def detect_services(question, entities, config):
    """Ask the LLM which known services/entities this situation involves.
    Returns a list of entity ids that actually exist - anything the model
    invents is silently dropped."""
    entity_list = "\n".join(
        f"- {eid}: {data[config.entity_name_field]}" for eid, data in entities.items()
    )
    prompt = f"""You are matching a citizen's message to a list of known government services.

    Known services:
    {entity_list}

    Message: "{question}"

    Which of the services above are directly relevant to what the person needs to do?
    Reply with ONLY a JSON array of service ids from the list above, e.g. ["birth_registration"].
    If none of the services are clearly relevant, reply with [].
    Do not include any service id that isn't in the list above.
    """
    # Guidance is a nice-to-have layered on top of a working system - any
    # failure here (API error, safety filter block, malformed response shape)
    # must fall back to plain RAG instead of crashing the whole request.
    try:
        response = config.llm.invoke(prompt)
        text = get_response_text(response).strip()

        # Be tolerant of the model wrapping the array in markdown fences or a
        # sentence, even though the prompt asks it not to.
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            text = match.group(0)

        ids = json.loads(text)
        if not isinstance(ids, list):
            return []

        return [i for i in ids if isinstance(i, str) and i in entities]
    except Exception as e:  # noqa: BLE001 - intentional: any LLM failure here must fall back to RAG, not crash
        print(f"[detect_services] LLM call failed for question {question!r}: {type(e).__name__}: {e}")
        return []


def resolve_order(service_ids, dependencies):
    """Given starting service ids, follow their prerequisites backwards and
    return a full ordered list (prerequisites first), no duplicates.
    Guards against circular dependencies in the admin-entered data."""
    ordered = []
    visited = set()

    def visit(service_id, trail):
        if service_id in visited:
            return
        if service_id in trail:
            return  # circular dependency guard - stop instead of looping forever
        for dep in dependencies.get(service_id, []):
            visit(dep["requires"], trail | {service_id})
        visited.add(service_id)
        ordered.append(service_id)

    for sid in service_ids:
        visit(sid, set())

    return ordered


def build_guidance_answer(service_ids, entities, config, dependencies):
    """Builds a numbered, step-by-step answer covering a service and
    everything it depends on, in the correct order. Returns None if none
    of the resolved ids still exist (e.g. all were deleted since)."""
    ordered = resolve_order(service_ids, dependencies)
    ordered = [sid for sid in ordered if sid in entities]  # drop stale ids

    if not ordered:
        return None

    # A dependency's note explains why the step it points to is needed -
    # attach it to that step, not to the one that declared the requirement.
    reason_for = {}
    for deps in dependencies.values():
        for dep in deps:
            if dep.get("note"):
                reason_for[dep["requires"]] = dep["note"]

    lines = [f"This looks like it involves {len(ordered)} step(s):\n"]
    for i, sid in enumerate(ordered, start=1):
        name = entities[sid][config.entity_name_field]
        step_text, _ = rule_engine_answer(sid, entities, config)
        header = f"Step {i}: {name}"
        if sid in reason_for:
            header += f" ({reason_for[sid]})"
        lines.append(f"{header}\n{step_text}")

    lines.append("Confirm exact requirements with your ward office, as procedures can vary.")
    return "\n\n".join(lines)


def ensure_dependency_table(db_connector, config):
    """Creates the dependency table if it doesn't exist yet. Safe to call on
    every app startup. No-op if this project hasn't configured one."""
    if not config.dependency_table:
        return
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {config.dependency_table} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            {config.dependency_from_field} VARCHAR(50) NOT NULL,
            {config.dependency_requires_field} VARCHAR(50) NOT NULL,
            {config.dependency_note_field} VARCHAR(255)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
