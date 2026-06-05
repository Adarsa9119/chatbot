export default function SourceViewer({ chunk, onClose }) {
  if (!chunk) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-title">📄 Source Chunk</div>
        <p className="text-sm text-muted" style={{ marginBottom:12 }}>
          Document ID: {chunk.doc_id} · Chunk #{chunk.chunk_index}
        </p>
        <div style={{
          background:'var(--bg3)', borderRadius:'var(--radius)',
          padding:'14px', fontSize:'0.85rem', lineHeight:1.7,
          color:'var(--text)', maxHeight:300, overflowY:'auto',
          fontFamily:'var(--mono)',
        }}>
          {chunk.chunk_text}
        </div>
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}