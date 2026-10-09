import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import "./TopQuestions.css";

const POLL_MS = 15000; // backup refresh; login/logout/ask also refresh instantly
const LONG_ANSWER_CHARS = 120;

// Fills your existing "Type your question..." box without touching ChatWindow.jsx.
function fillQuestionBox(text) {
  const input = document.querySelector('input[placeholder*="question" i]');
  if (!input) return false;
  const setValue = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value"
  ).set;
  setValue.call(input, text);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.focus();
  return true;
}

// Answers come back with **bold** markers; show them as plain text.
function cleanAnswer(text) {
  return (text || "").replace(/\*\*/g, "").trim();
}

export default function TopQuestions() {
  // null = not logged in (or server unreachable) -> the panel is not shown at all
  const [items, setItems] = useState(null);
  const [open, setOpen] = useState(() => window.innerWidth >= 1100);
  const [expanded, setExpanded] = useState({});
  const latestRequest = useRef(0);

  const load = useCallback(() => {
    const requestId = ++latestRequest.current;
    api
      .topQuestions()
      .then((result) => {
        if (requestId !== latestRequest.current) return; // a newer request already ran
        setItems(
          result && Array.isArray(result.top_questions) ? result.top_questions : null
        );
      })
      .catch(() => {
        if (requestId === latestRequest.current) setItems(null);
      });
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    window.addEventListener("topquestions:refresh", load);
    return () => {
      clearInterval(timer);
      window.removeEventListener("topquestions:refresh", load);
    };
  }, [load]);

  if (items === null) return null; // logged out -> nothing on screen

  return (
    <aside className={`top-questions-float ${open ? "open" : "closed"}`}>
      <button
        type="button"
        className="top-questions-header"
        onClick={() => setOpen(!open)}
      >
        <span>Top 5 questions</span>
        <span className="top-questions-toggle">{open ? "Hide" : "Show"}</span>
      </button>

      {open && (
        <div className="top-questions-body">
          {items.length === 0 ? (
            <p className="top-questions-empty">No questions asked yet.</p>
          ) : (
            <ol className="top-questions-list">
              {items.map((item, i) => {
                const answer = cleanAnswer(item.answer);
                const isLong =
                  answer.length > LONG_ANSWER_CHARS || answer.split("\n").length > 3;
                const isOpen = !!expanded[item.question];

                return (
                  <li key={item.question} className="top-questions-item">
                    <div className="top-questions-row">
                      <span className="top-questions-rank">{i + 1}</span>
                      <button
                        type="button"
                        className="top-questions-question"
                        onClick={() => fillQuestionBox(item.question)}
                        title="Click to put this question in the box"
                      >
                        {item.question}
                      </button>
                      <span className="top-questions-count">{item.ask_count}×</span>
                    </div>

                    {answer && (
                      <>
                        <p className={`top-questions-answer ${isOpen ? "expanded" : ""}`}>
                          {answer}
                        </p>
                        {isLong && (
                          <button
                            type="button"
                            className="top-questions-more"
                            onClick={() =>
                              setExpanded({ ...expanded, [item.question]: !isOpen })
                            }
                          >
                            {isOpen ? "Show less" : "Show more"}
                          </button>
                        )}
                      </>
                    )}
                  </li>
                );
              })}
            </ol>
          )}
        </div>
      )}
    </aside>
  );
}
