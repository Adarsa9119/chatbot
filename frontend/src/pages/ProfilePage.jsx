import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { passwordApi } from '../api/passwordApi';
import { extractApiError, checkPasswordStrength } from '../utils/helpers';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();

  const [pwForm, setPwForm] = useState({ current: '', new: '', confirm: '' });
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');
  const [showPw, setShowPw] = useState(false);

  const setPw = (field) => (e) =>
    setPwForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPwError(''); setPwSuccess('');

    if (!pwForm.current) { setPwError('Current password is required.'); return; }
    if (pwForm.new.length < 8) { setPwError('New password must be at least 8 characters.'); return; }
    if (!/[A-Z]/.test(pwForm.new)) { setPwError('New password must include an uppercase letter.'); return; }
    if (!/[0-9]/.test(pwForm.new)) { setPwError('New password must include a number.'); return; }
    if (pwForm.new !== pwForm.confirm) { setPwError('New passwords do not match.'); return; }
    if (pwForm.current === pwForm.new) { setPwError('New password must differ from current password.'); return; }

    setPwLoading(true);
    try {
      await passwordApi.changePassword({
        current_password: pwForm.current,
        new_password: pwForm.new,
      });
      setPwSuccess('Password changed successfully.');
      setPwForm({ current: '', new: '', confirm: '' });
    } catch (err) {
      setPwError(extractApiError(err, 'Failed to change password.'));
    } finally {
      setPwLoading(false);
    }
  };

  const strength = checkPasswordStrength(pwForm.new);

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Profile</h1>
        <p className="page-subtitle">Your account information</p>
      </div>

      {/* User info card */}
      <div className="card" style={{ padding: '24px', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div
            style={{
              width: 52, height: 52, borderRadius: '50%',
              background: 'var(--accent-dim)',
              border: '1px solid var(--accent)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent)',
            }}
          >
            {user?.user_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1rem' }}>{user?.user_name}</div>
            <div style={{ color: 'var(--text2)', fontSize: '0.85rem' }}>{user?.user_email}</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            { label: 'Role', value: user?.user_role },
            { label: 'Email Verified', value: user?.is_verified ? '✅ Yes' : '❌ No' },
          ].map(({ label, value }) => (
            <div key={label} style={{
              background: 'var(--bg3)', borderRadius: 'var(--radius)',
              padding: '12px 14px',
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text2)', marginBottom: 4 }}>{label}</div>
              <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Change password */}
      <div className="card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 20 }}>Change Password</h2>

        <form
          onSubmit={handlePasswordChange}
          style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 440 }}
        >
          {pwError && <div className="alert alert-error">{pwError}</div>}
          {pwSuccess && <div className="alert alert-success">{pwSuccess}</div>}

          <div className="form-group">
            <label className="form-label">Current Password</label>
            <input
              className="form-input"
              type={showPw ? 'text' : 'password'}
              value={pwForm.current}
              onChange={setPw('current')}
              autoComplete="current-password"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">New Password</label>
            <input
              className="form-input"
              type={showPw ? 'text' : 'password'}
              value={pwForm.new}
              onChange={setPw('new')}
              autoComplete="new-password"
              placeholder="At least 8 characters"
              required
            />
            {pwForm.new && (
              <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
                {strength.map((r, i) => (
                  <div key={i} title={r.label} style={{
                    flex: 1, height: 3, borderRadius: 2,
                    background: r.met ? '#22c55e' : 'var(--border)',
                    transition: 'background 0.2s',
                  }} />
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Confirm New Password</label>
            <input
              className="form-input"
              type={showPw ? 'text' : 'password'}
              value={pwForm.confirm}
              onChange={setPw('confirm')}
              autoComplete="new-password"
              required
            />
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--text2)', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showPw}
              onChange={() => setShowPw(!showPw)}
              style={{ cursor: 'pointer' }}
            />
            Show passwords
          </label>

          <button className="btn btn-primary" type="submit" disabled={pwLoading} style={{ alignSelf: 'flex-start' }}>
            {pwLoading ? 'Updating…' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  );
}