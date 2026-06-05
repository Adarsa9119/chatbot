export default function AuditTable({ logs = [] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Action</th>
            <th>User ID</th>
            <th>IP Address</th>
            <th>Time</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.log_id}>
              <td><span className="badge badge-blue">{log.action}</span></td>
              <td className="text-muted">{log.user_id || '—'}</td>
              <td className="text-muted text-sm" style={{ fontFamily:'var(--mono)' }}>{log.ip_address || '—'}</td>
              <td className="text-muted text-sm">{new Date(log.created_at).toLocaleString()}</td>
              <td className="text-sm text-muted" style={{ fontFamily:'var(--mono)' }}>
                {log.details ? JSON.stringify(log.details).slice(0, 60) + '...' : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}