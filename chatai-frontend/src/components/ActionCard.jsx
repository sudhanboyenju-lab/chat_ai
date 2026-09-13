export default function ActionCard({ action }) {
    if (!action) return null;

    return (
        <div className="row ai">
            <div className="avatar ai">✓</div>
            <div className="bubble ai action-card">
                <p><strong>Application Started</strong></p>
                <p>{action.service} — ID: <strong>{action.application_id}</strong></p>
                <p>{action.next_step}</p>
            </div>
        </div>
    );
}
