export default function DocumentList({ docs = [], onDelete, onReprocess }) {
  if (!docs.length) return (
    <div className="card" style={{ textAlign:'center', color:'var(--text3)', padding:40 }}>
      No documents uploaded yet.
    </div>
  );

  const statusBadge = (s) => ({
    ready:      <span className="badge badge-green">Ready</span>,
    processing: <span className="badge badge-yellow">Processing</span>,
    failed:     <span className="badge badge-red">Failed</span>,
  }[s] || <span className="badge badge-gray">{s}</span>);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Status</th>
            <th>Size</th>
            <th>Uploaded</th>
            {(onDelete || onReprocess) && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {docs.map(doc => (
            <tr key={doc.doc_id}>
              <td style={{ fontWeight:500 }}>{doc.title}</td>
              <td>{statusBadge(doc.status)}</td>
              <td className="text-muted">{doc.file_size_kb ? `${doc.file_size_kb} KB` : '—'}</td>
              <td className="text-muted text-sm">{new Date(doc.created_at).toLocaleDateString()}</td>
              {(onDelete || onReprocess) && (
                <td>
                  <div style={{ display:'flex', gap:8 }}>
                    {onReprocess && doc.status === 'failed' && (
                      <button className="btn btn-sm btn-secondary" onClick={() => onReprocess(doc.doc_id)}>Reprocess</button>
                    )}
                    {onDelete && (
                      <button className="btn btn-sm btn-danger" onClick={() => onDelete(doc.doc_id)}>Delete</button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}