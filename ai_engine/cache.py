"""
Generic answer cache: avoids spending an LLM call on a question that was
already answered recently. Applies to any AI-generated answer (situation
guidance or RAG) in any project - the instant rule-engine lookup never
needs this, since it doesn't call the LLM at all.

Deliberately does NOT cache fallback/error messages: those didn't cost a
successful LLM call, so there's no quota saved by caching them, and doing
so would lock in a temporary failure (like a rate limit) until the cache
entry expires. Skipping the cache on failure means the very next attempt
gets a fresh chance to succeed.
"""

import json

CACHE_MAX_AGE_DAYS = 7  # safety net in case data changes outside the admin panel


def ensure_cache_table(db_connector):
    """Creates the cache table if it doesn't exist yet. Safe to call on
    every app startup."""
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_answer_cache (
            question_normalized VARCHAR(500) PRIMARY KEY,
            answer TEXT NOT NULL,
            sources TEXT,
            route VARCHAR(20),
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def get_cached_answer(db_connector, question):
    """Returns {"answer": str, "sources": list, "route": str} if a fresh
    cached answer exists, else None."""
    normalized = question.strip().lower()
    conn = db_connector.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        f"""
        SELECT answer, sources, route
        FROM llm_answer_cache
        WHERE question_normalized = %s
          AND cached_at > NOW() - INTERVAL {CACHE_MAX_AGE_DAYS} DAY
        """,
        (normalized,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    try:
        sources = json.loads(row["sources"]) if row["sources"] else []
    except (json.JSONDecodeError, TypeError):
        sources = []

    return {"answer": row["answer"], "sources": sources, "route": row["route"]}


def save_cached_answer(db_connector, question, answer, sources, route):
    """Call this only after a SUCCESSFUL AI-generated answer - never for a
    fallback/error message (see module docstring for why)."""
    normalized = question.strip().lower()
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO llm_answer_cache (question_normalized, answer, sources, route, cached_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            answer = VALUES(answer),
            sources = VALUES(sources),
            route = VALUES(route),
            cached_at = VALUES(cached_at)
        """,
        (normalized, answer, json.dumps(sources), route),
    )
    conn.commit()
    cursor.close()
    conn.close()


def clear_cache(db_connector):
    """Called after admin add/edit/delete (via Engine.refresh()) so a
    changed fee or requirement can't be served from a stale cached answer."""
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM llm_answer_cache")
    conn.commit()
    cursor.close()
    conn.close()
