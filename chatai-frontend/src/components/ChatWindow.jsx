import { useState, useRef, useEffect } from "react";
import { api } from "../api/client";
import MessageBubble from "./MessageBubble";
import ActionCard from "./ActionCard";
import TypingIndicator from "./TypingIndicator";
import VoiceButton from "./VoiceButton";
import DocumentUpload from "./DocumentUpload";

export default function ChatWindow() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const chatBoxRef = useRef(null);

    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [messages, loading]);

    async function sendQuestion() {
        const question = input.trim();
        if (!question || loading) return;

        setMessages((prev) => [...prev, { type: "user", text: question }]);
        setInput("");
        setLoading(true);

        try {
            const data = await api.ask(question);
            setMessages((prev) => [
                ...prev,
                {
                    type: "ai",
                    text: data.answer,
                    sources: data.sources,
                    route: data.route,
                },
            ]);
            if (data.action) {
                setMessages((prev) => [...prev, { type: "action", action: data.action }]);
            }
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { type: "ai", text: "Something went wrong. Please try again." },
            ]);
        } finally {
            setLoading(false);
        }
    }

    // Called by VoiceButton with the server's JSON: { question, answer, sources, route, action }
    // Shows what the system heard as the user's message, then the answer.
    function handleVoiceResult(data) {
        setMessages((prev) => [
            ...prev,
            { type: "user", text: data.question },
            {
                type: "ai",
                text: data.answer,
                sources: data.sources,
                route: data.route,
            },
        ]);
        if (data.action) {
            setMessages((prev) => [...prev, { type: "action", action: data.action }]);
        }
    }

    // Called by DocumentUpload with the server's JSON: { text, document, needed_for }
    // The extracted text is shown so the user can check it for mistakes.
    function handleDocumentResult(data) {
        const lines = [];
        if (data.document) {
            lines.push(`This looks like: ${data.document}.`);
            if (data.needed_for && data.needed_for.length > 0) {
                lines.push(`It is needed for: ${data.needed_for.map((s) => s.name).join(", ")}.`);
            }
        } else {
            lines.push("I could not match this to a known document.");
        }
        lines.push("", "Text I read (please check it for mistakes):", data.text);

        setMessages((prev) => [
            ...prev,
            { type: "user", text: "📄 Uploaded a document" },
            { type: "ai", text: lines.join("\n") },
        ]);
    }

    function handleKeyPress(e) {
        if (e.key === "Enter") sendQuestion();
    }

    return (
        <div className="panel">
            <div className="chat-box" ref={chatBoxRef}>
                {messages.map((m, i) => {
                    if (m.type === "action") return <ActionCard key={i} action={m.action} />;
                    return (
                        <MessageBubble
                            key={i}
                            text={m.text}
                            isUser={m.type === "user"}
                            sources={m.sources}
                            route={m.route}
                        />
                    );
                })}
                {loading && <TypingIndicator />}
            </div>
            <div className="input-area">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your question..."
                    disabled={loading}
                />
                <VoiceButton onResult={handleVoiceResult} />
                <DocumentUpload onResult={handleDocumentResult} />
                <button onClick={sendQuestion} disabled={loading}>
                    Ask
                </button>
            </div>
        </div>
    );
}
