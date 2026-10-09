import { useRef, useState } from "react";
import { api } from "../api/client";

const MAX_BYTES = 8 * 1024 * 1024; // keep in sync with MAX_IMAGE_BYTES on the server

/**
 * "Upload document" button: pick a photo, send it for OCR, hand the result to the parent.
 *
 * Props:
 *   onResult - called with { text, document, needed_for } from the server
 */
export default function DocumentUpload({ onResult }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleFile(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // lets the user pick the same file again later
    if (!file) return;

    setError("");
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Please choose a JPG, PNG or WebP photo.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("That image is too large (maximum 8 MB).");
      return;
    }

    setBusy(true);
    try {
      const data = await api.uploadDocument(file);
      onResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span>
      {/* Hidden file input; the button below opens it. On phones this offers camera or gallery. */}
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFile}
        style={{ display: "none" }}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        aria-label="Upload a document photo"
        title="Your photo is read to extract text. This app does not store it."
      >
        {busy ? "Reading…" : "📄 Upload document"}
      </button>
      {error && <div style={{ color: "#b00020", fontSize: 13 }}>{error}</div>}
    </span>
  );
}
