// Lightweight renderer: turns **bold** and "- bullet" lines into real markup
function renderAnswer(text) {
    if (!text) return null;
    const lines = text.split("\n");
    const elements = [];
    let listBuffer = [];

    function flushList(key) {
        if (listBuffer.length > 0) {
            elements.push(
                <ul key={"ul-" + key}>
                    {listBuffer.map((item, i) => (
                        <li key={i}>{formatInline(item)}</li>
                    ))}
                </ul>
            );
            listBuffer = [];
        }
    }

    lines.forEach((rawLine, idx) => {
        const line = rawLine.trim();
        const isBullet = /^[-*]\s+/.test(line);

        if (isBullet) {
            listBuffer.push(line.replace(/^[-*]\s+/, ""));
        } else {
            flushList(idx);
            if (line.length > 0) {
                elements.push(<p key={idx}>{formatInline(line)}</p>);
            }
        }
    });
    flushList("end");

    return elements;
}

function formatInline(text) {
    const parts = text.split(/(\*\*.+?\*\*)/g);
    return parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
            return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        return part;
    });
}

export default function MessageBubble({ text, isUser, sources, route }) {
    return (
        <div className={`row ${isUser ? "user" : "ai"}`}>
            <div className={`avatar ${isUser ? "user" : "ai"}`}>
                {isUser ? "🧑" : "◆"}
            </div>
            <div className={`bubble ${isUser ? "user" : "ai"}`}>
                {!isUser && route && (
                    <div className={`route-tag ${route === "rule_engine" ? "rule" : "rag"}`}>
                        {route === "rule_engine" ? "Instant lookup" : "AI generated"}
                    </div>
                )}
                {isUser ? <p>{text}</p> : renderAnswer(text)}
                {!isUser && sources && sources.length > 0 && (
                    <div className="sources">Sources: {sources.join(", ")}</div>
                )}
            </div>
        </div>
    );
}
