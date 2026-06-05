import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { documentApi } from '../api/documentApi';
import { sessionApi } from '../api/sessionApi';
import { useAuth } from '../context/AuthContext';
import DocumentList from '../components/DocumentList';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatDateTime } from '../utils/helpers';

export default function UserDashboard() {
  const { user } = useAuth();
  const [docs, setDocs] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      documentApi.getReady(),
      sessionApi.getAll(),
    ])
      .then(([docsRes, sessionsRes]) => {
        setDocs(docsRes.data?.documents || docsRes.data || []);
        setSessions(sessionsRes.data?.sessions || sessionsRes.data || []);
      })
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    { label: 'Documents Available', value: docs.length, icon: '📄', color: 'var(--accent)' },
    { label: 'Chat Sessions', value: sessions.length, icon: '💬', color: '#a78bfa' },
    {
      label: 'Last Session',
      value: sessions[0] ? formatDateTime(sessions[0].created_at) : '—',
      icon: '🕒',
      color: '#34d399',
      small: true,
    },
  ];

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Welcome back, <strong>{user?.user_name}</strong>
        </p>
      </div>

      {!user?.is_verified && (
        <div className="alert alert-warning" style={{ marginBottom: 24 }}>
          ⚠️ Your email is not verified. Some features may be restricted.{' '}
          <Link to="/verify-email" style={{ color: 'inherit', fontWeight: 600, textDecoration: 'underline' }}>
            Resend verification
          </Link>
        </div>
      )}

      {error && <div className="alert alert-error" style={{ marginBottom: 24 }}>{error}</div>}

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
                <div className={`stat-value${s.small ? ' stat-value-sm' : ''}`}>{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Quick actions */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 32, flexWrap: 'wrap' }}>
            <Link className="btn btn-primary" to="/chat">
              💬 Start Chatting
            </Link>
          </div>

          {/* Available documents */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>
                Available Documents ({docs.length})
              </h2>
            </div>
            {docs.length === 0 ? (
              <p className="text-muted text-sm" style={{ padding: '12px 0' }}>
                No documents are available yet. Ask an admin to upload some.
              </p>
            ) : (
              <DocumentList docs={docs} />
            )}
          </div>
        </>
      )}
    </div>
  );
}