export default function UserTable({ users = [], onRoleChange, onDelete }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Verified</th>
            <th>Joined</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.user_id}>
              <td style={{ fontWeight:500 }}>{u.user_name}</td>
              <td className="text-muted">{u.user_email}</td>
              <td>
                <span className={`badge ${u.user_role === 'admin' ? 'badge-blue' : 'badge-gray'}`}>
                  {u.user_role}
                </span>
              </td>
              <td>
                <span className={`badge ${u.is_verified ? 'badge-green' : 'badge-yellow'}`}>
                  {u.is_verified ? 'Yes' : 'No'}
                </span>
              </td>
              <td className="text-muted text-sm">{new Date(u.created_at).toLocaleDateString()}</td>
              <td>
                <div style={{ display:'flex', gap:8 }}>
                  {onRoleChange && (
                    <button className="btn btn-sm btn-secondary"
                      onClick={() => onRoleChange(u.user_id, u.user_role === 'admin' ? 'user' : 'admin')}>
                      Make {u.user_role === 'admin' ? 'User' : 'Admin'}
                    </button>
                  )}
                  {onDelete && (
                    <button className="btn btn-sm btn-danger" onClick={() => onDelete(u.user_id)}>Delete</button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}