import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

/**
 * Mic button: click to start recording, click again to stop and send.
 * Talks to the server through api.askVoice (src/api/client.js), so the URL,
 * cookies and error handling live in one place.
 *
 * Props:
 *   onResult   - called with { question, answer, sources, route, action }
 *   maxSeconds - auto-stop after this many seconds (default 30)
 */
export default function VoiceButton({ onResult, maxSeconds = 30 }) {
  const [state, setState] = useState("idle"); // idle | recording | processing
  const [error, setError] = useState("");
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // If the component disappears mid-recording (e.g. switching to Admin view),
  // stop the recorder and release the microphone.
  useEffect(() => {
    return () => {
      clearTimeout(timerRef.current);
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null; // don't send a recording nobody is waiting for
        recorder.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  async function start() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Voice input is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream); // browser picks webm (Chrome) or mp4 (Safari)
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop()); // release the microphone
        clearTimeout(timerRef.current);
        const type = recorder.mimeType || "audio/webm";
        const ext = type.includes("mp4") ? "mp4" : "webm";
        await send(new Blob(chunksRef.current, { type }), `question.${ext}`);
      };

      recorder.start();
      recorderRef.current = recorder;
      setState("recording");
      timerRef.current = setTimeout(stop, maxSeconds * 1000);
    } catch {
      setError("Microphone access was blocked or is unavailable.");
      setState("idle");
    }
  }

  function stop() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
      setState("processing");
    }
  }

  async function send(blob, filename) {
    if (blob.size < 1000) {
      setError("Recording was too short. Please try again.");
      setState("idle");
      return;
    }
    try {
      const data = await api.askVoice(blob, filename);
      onResult(data);
    } catch (e) {
      setError(e.message || "Something went wrong. Please try again.");
    } finally {
      setState("idle");
    }
  }

  const label =
    state === "recording" ? "⏹ Stop" : state === "processing" ? "Processing…" : "🎤 Speak";

  return (
    <span>
      <button
        type="button"
        onClick={state === "recording" ? stop : start}
        disabled={state === "processing"}
        aria-label="Ask by voice"
      >
        {label}
      </button>
      {error && <div style={{ color: "#b00020", fontSize: 13 }}>{error}</div>}
    </span>
  );
}
