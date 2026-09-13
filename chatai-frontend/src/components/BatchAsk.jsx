import { useState } from "react";
import { api } from "../api/client";

export default function BatchAsk() {
    const [text, setText] = useState("");
    const [results, setResults] = useState([]);
    const [elapsed, setElapsed] = useState(null);
    const [loading, setLoading] = useState(false);

    async function sendBatch() {
        const questions = text.split("\n").map((q) => q.trim()).filter(Boolean);
        if (questions.length === 0 || loading) return;

        setLoading(true);
        setResults([]);
        const start = performance.now();

        try {
            const data = await api.askBatch(questions);
            setElapsed(((performance.now() - start) / 1000).toFixed(2));
            setResults(data.results || []);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="panel">
            <h3>Ask multiple questions at once</h3>
            <p className="hint">Type one question per line — processed concurrently.</p>
            <textarea
                rows={5}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={"What documents do I need for birth registration?\nWhat is the fee for map approval?\nWho is eligible for social security allowance?"}
            />
            <button onClick={sendBatch} disabled={loading}>
                {loading ? "Processing..." : "Ask All"}
            </button>

            {elapsed && (
                <div className="timing-note">
                    Completed {results.length} questions in {elapsed}s
                </div>
            )}

            {results.map((r, i) => (
                <div className="bubble ai batch-result" key={i}>
                    <p><strong>Q: {r.question}</strong></p>
                    <p>{r.answer}</p>
                    {r.sources && r.sources.length > 0 && (
                        <div className="sources">Sources: {r.sources.join(", ")}</div>
                    )}
                </div>
            ))}
        </div>
    );
}
