import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/authApi';
import { STORAGE_KEYS } from '../utils/constants';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [error, setError] = useState('');

  // ── Theme preference (stored in localStorage) ─────────────────────────────
  const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || 'dark';
  const [theme, setTheme] = useState(savedTheme);

  const handleThemeChange = (value) => {
    setTheme(value);
    localStorage.setItem(STORAGE_KEYS.THEME, value);
    document.documentElement.setAttribute('data-theme', value);
  };

  const handleDeleteAccount = async () => {
    setDeleteLoading(true);
    setError('');
    try {
      await authApi.logout();
      logout();
    } catch {
      setError('Failed to delete account. Contact an administrator.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const Section = ({ title, children }) => (
    <div className="card" style={{ padding: '24px', marginBottom: 24 }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 20 }}>{title}</h2>
      {children}
    </div>
  );

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Preferences and account management</p>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 24 }}>{error}</div>}

      {/* Appearance */}
      <Section title="Appearance">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 340 }}>
          <label className="form-label">Theme</label>
          <div style={{ display: 'flex', gap: 10 }}>
            {['dark', 'light'].map((t) => (
              <button
                key={t}
                className={`btn ${theme === t ? 'btn-primary' : 'btn-secondary'}`}
                style={{ flex: 1, textTransform: 'capitalize' }}
                onClick={() => handleThemeChange(t)}
              >
                {t === 'dark' ? '🌙 Dark' : '☀️ Light'}
              </button>
            ))}
          </div>
          <p className="form-hint">Theme preference is saved locally in your browser.</p>
        </div>
      </Section>

      {/* Account info */}
      <Section title="Account">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 440 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text2)', fontSize: '0.9rem' }}>Name</span>
            <span style={{ fontWeight: 500 }}>{user?.user_name}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text2)', fontSize: '0.9rem' }}>Email</span>
            <span style={{ fontWeight: 500 }}>{user?.user_email}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
            <span style={{ color: 'var(--text2)', fontSize: '0.9rem' }}>Role</span>
            <span className={`badge ${user?.user_role === 'admin' ? 'badge-blue' : 'badge-gray'}`}>
              {user?.user_role}
            </span>
          </div>
        </div>
      </Section>

      {/* Notifications info */}
      <Section title="Email Notifications">
        <p className="text-sm text-muted" style={{ maxWidth: 440 }}>
          System notifications (password resets, email verifications) are sent automatically.
          You will receive an email at <strong>{user?.user_email}</strong> for security events.
        </p>
      </Section>

      {/* Danger zone */}
      <div
        className="card"
        style={{
          padding: '24px',
          borderColor: 'rgba(239,68,68,0.3)',
          background: 'rgba(239,68,68,0.04)',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--danger, #ef4444)', marginBottom: 8 }}>
          Danger Zone
        </h2>
        <p className="text-sm text-muted" style={{ marginBottom: 16 }}>
          Sign out of your account immediately. To permanently delete your account, contact an administrator.
        </p>
        {!confirmDelete ? (
          <button
            className="btn btn-danger"
            onClick={() => setConfirmDelete(true)}
            style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.4)' }}
          >
            Sign Out
          </button>
        ) : (
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', color: 'var(--text2)' }}>Are you sure?</span>
            <button className="btn btn-secondary btn-sm" onClick={() => setConfirmDelete(false)}>
              Cancel
            </button>
            <button
              className="btn btn-sm"
              style={{ background: '#ef4444', color: '#fff', border: 'none' }}
              onClick={handleDeleteAccount}
              disabled={deleteLoading}
            >
              {deleteLoading ? 'Signing out…' : 'Yes, Sign Out'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}