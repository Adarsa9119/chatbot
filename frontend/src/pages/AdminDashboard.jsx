import { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import DocumentList from '../components/DocumentList';
import UploadForm from '../components/UploadForm';
import UserTable from '../components/UserTable';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatDateTime } from '../utils/helpers';

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [actionError, setActionError] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashRes, usersRes] = await Promise.all([
        adminApi.getDashboard(),
        adminApi.getUsers(),
      ]);
      const data = dashRes.data;
      setDashboard(data?.stats || data);
      setDocs(data?.recent_documents || data?.documents || []);
      setUsers(usersRes.data?.users || usersRes.data || []);
    } catch (err) {
      setError('Failed to load admin data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleRoleChange = async (userId, newRole) => {
    setActionError('');
    try {
      await adminApi.updateUserRole(userId, { user_role: newRole });
      setUsers(prev =>
        prev.map(u => u.user_id === userId ? { ...u, user_role: newRole } : u)
      );
    } catch (err) {
      setActionError('Failed to update user role.');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Delete this user? This cannot be undone.')) return;
    setActionError('');
    try {
      await adminApi.deleteUser(userId);
      setUsers(prev => prev.filter(u => u.user_id !== userId));
    } catch (err) {
      setActionError('Failed to delete user.');
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!window.confirm('Delete this document and all its embeddings?')) return;
    try {
      await adminApi.deleteDocument(docId);
      setDocs(prev => prev.filter(d => d.doc_id !== docId));
    } catch {
      setActionError('Failed to delete document.');
    }
  };

  const handleReprocess = async (docId) => {
    try {
      await adminApi.reprocessDocument(docId);
      setDocs(prev => prev.map(d =>
        d.doc_id === docId ? { ...d, status: 'processing' } : d
      ));
    } catch {
      setActionError('Failed to reprocess document.');
    }
  };

  const stats = dashboard ? [
    { label: 'Total Users', value: dashboard.total_users ?? '—', icon: '👥', color: 'var(--accent)' },
    { label: 'Total Documents', value: dashboard.total_documents ?? '—', icon: '📄', color: '#a78bfa' },
    { label: 'Active Sessions', value: dashboard.total_sessions ?? '—', icon: '💬', color: '#34d399' },
    { label: 'Total Chats', value: dashboard.total_chats ?? '—', icon: '🗨️', color: '#f59e0b' },
  ] : [];

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Admin Dashboard</h1>
        <p className="page-subtitle">Manage documents, users, and system health</p>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 24 }}>{error}</div>}
      {actionError && <div className="alert alert-error" style={{ marginBottom: 24 }}>{actionError}</div>}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
          <LoadingSpinner />
        </div>
      ) : (
        <>
          {/* Stats */}
          <div className="stats-grid" style={{ marginBottom: 32 }}>
            {stats.map((s) => (
              <div className="stat-card" key={s.label}>
                <div className="stat-icon" style={{ color: s.color }}>{s.icon}</div>
                <div className="stat-value">{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Upload section */}
          <div className="card" style={{ padding: '20px 24px', marginBottom: 28 }}>
            <div
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: uploadOpen ? 20 : 0 }}
            >
              <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Upload Document</h2>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setUploadOpen(!uploadOpen)}
              >
                {uploadOpen ? '✕ Cancel' : '+ Upload PDF'}
              </button>
            </div>
            {uploadOpen && (
              <UploadForm
                onSuccess={() => {
                  setUploadOpen(false);
                  loadData();
                }}
              />
            )}
          </div>

          {/* Documents */}
          <div className="card" style={{ padding: '20px 24px', marginBottom: 28 }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>
              Documents ({docs.length})
            </h2>
            {docs.length === 0 ? (
              <p className="text-muted text-sm">No documents uploaded yet.</p>
            ) : (
              <DocumentList
                docs={docs}
                onDelete={handleDeleteDoc}
                onReprocess={handleReprocess}
              />
            )}
          </div>

          {/* Users */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>
              Users ({users.length})
            </h2>
            <UserTable
              users={users}
              onRoleChange={handleRoleChange}
              onDelete={handleDeleteUser}
            />
          </div>
        </>
      )}
    </div>
  );
}