import { useState, useRef, useEffect } from "react";
import { api } from "../api/client";
import MessageBubble from "./MessageBubble";
import ActionCard from "./TypingIndicator";
import TypingIndicator from "./TypingIndicator";

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
                <button onClick={sendQuestion} disabled={loading}>
                    Ask
                </button>
            </div>
        </div>
    );
}
