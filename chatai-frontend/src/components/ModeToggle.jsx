export default function ModeToggle({ mode, setMode }) {
    return (
        <button
            className="mode-toggle-btn"
            onClick={() => setMode(mode === "single" ? "batch" : "single")}
        >
            {mode === "single"
                ? "✦ Ask multiple questions instead"
                : "✦ Ask a single question instead"}
        </button>
    );
}
