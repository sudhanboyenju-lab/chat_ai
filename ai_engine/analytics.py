"""
Generic "most asked questions" logging, shared by every project's Flask app.
Works with any db_connector, since it only relies on db_connector.get_connection()
(a zero/one-arg callable returning a live DB connection) - same thing
MySQLConnector already wraps for each project's own database.
"""


def ensure_log_table(db_connector):
    """Creates the question_log table if it doesn't exist yet. Safe to call
    every time the app starts - CREATE TABLE IF NOT EXISTS is a no-op after
    the first run."""
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            question_normalized VARCHAR(500) NOT NULL,
            answer TEXT,
            asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def log_question(db_connector, question, answer):
    """Call this once per question asked, after you have the answer."""
    normalized = question.strip().lower()[:500]
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO question_log (question, question_normalized, answer) VALUES (%s, %s, %s)",
        (question, normalized, answer),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_top_questions(db_connector, limit=5):
    """Returns the most frequently asked questions (exact match on the trimmed,
    lowercased text), each shown with its MOST RECENT wording and answer.
    Near-duplicate phrasings ("what's in the momo" vs "what is in the momo")
    are counted separately - this is a simple exact-match MVP."""
    limit = int(limit)  # not user-supplied in the route, but stay defensive
    conn = db_connector.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""
        SELECT
            (
                SELECT TRIM(l.question)
                FROM question_log l
                WHERE l.question_normalized = g.question_normalized
                ORDER BY l.id DESC
                LIMIT 1
            ) AS question,
            (
                SELECT l.answer
                FROM question_log l
                WHERE l.question_normalized = g.question_normalized
                ORDER BY l.id DESC
                LIMIT 1
            ) AS answer,
            g.ask_count AS ask_count,
            g.last_asked AS last_asked
        FROM (
            SELECT
                question_normalized,
                COUNT(*) AS ask_count,
                MAX(asked_at) AS last_asked
            FROM question_log
            GROUP BY question_normalized
            ORDER BY ask_count DESC, last_asked DESC
            LIMIT {limit}
        ) g
        ORDER BY g.ask_count DESC, g.last_asked DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
