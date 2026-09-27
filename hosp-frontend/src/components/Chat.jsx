import { useState, useRef, useEffect } from "react";
import { api } from "../api/client";

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Namaste! Ask me about our doctors - specialization, fees, or availability.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || busy) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setBusy(true);

    try {
      const result = await api.ask(question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, action: result.action },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Something went wrong: ${err.message}`, isError: true },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-log" ref={listRef}>
        {messages.map((m, i) => (
          <div key={i} className={`bubble-row ${m.role}`}>
            {m.role === "assistant" && <span className="avatar">SH</span>}
            <div className={`bubble ${m.role} ${m.isError ? "error" : ""}`}>
              <p>{m.text}</p>
              {m.action?.status === "started" && (
                <p className="bubble-note">Appointment request started for {m.action.entity}.</p>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="bubble-row assistant">
            <span className="avatar">SH</span>
            <div className="bubble assistant typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
      </div>

      <form className="composer" onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Who should I see for a heart checkup?"
          disabled={busy}
        />
        <button type="submit" className="primary-btn" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
