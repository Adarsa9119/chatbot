import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { passwordApi } from '../api/passwordApi';

export default function PasswordResetForm() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const validate = () => {
    if (!token) return 'Reset token is missing. Please use the link from your email.';
    if (password.length < 8) return 'Password must be at least 8 characters.';
    if (!/[A-Z]/.test(password)) return 'Password must contain at least one uppercase letter.';
    if (!/[0-9]/.test(password)) return 'Password must contain at least one number.';
    if (password !== confirm) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) { setError(validationError); return; }

    setError('');
    setLoading(true);
    try {
      await passwordApi.resetPassword({ token, new_password: password });
      setSuccess(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(', '));
      } else {
        setError(detail || 'Failed to reset password. The link may have expired.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>✅</div>
          <h2 className="auth-title">Password Reset!</h2>
          <p className="auth-subtitle" style={{ marginBottom: 24 }}>
            Your password has been updated successfully. You can now log in with your
            new password.
          </p>
          <button className="btn btn-primary auth-submit" onClick={() => navigate('/login')}>
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-card">
      <h2 className="auth-title">Set New Password</h2>
      <p className="auth-subtitle">
        Enter a strong new password for your account.
      </p>

      {!token && (
        <div className="alert alert-error" style={{ marginBottom: 16 }}>
          ⚠️ Invalid or missing reset token. Please use the link sent to your email.
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-group">
          <label className="form-label">New Password</label>
          <div style={{ position: 'relative' }}>
            <input
              className="form-input"
              type={showPw ? 'text' : 'password'}
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPw(!showPw)}
              style={{
                position: 'absolute', right: 12, top: '50%',
                transform: 'translateY(-50%)',
                background: 'none', border: 'none',
                cursor: 'pointer', color: 'var(--text2)',
                fontSize: '0.85rem', padding: 0,
              }}
            >
              {showPw ? 'Hide' : 'Show'}
            </button>
          </div>
          <div className="form-hint" style={{ marginTop: 6 }}>
            Min 8 chars, one uppercase letter, one number.
          </div>
        </div>

        {/* Password strength indicator */}
        {password && (
          <div style={{ display: 'flex', gap: 4, marginTop: -8 }}>
            {[
              password.length >= 8,
              /[A-Z]/.test(password),
              /[0-9]/.test(password),
              /[^A-Za-z0-9]/.test(password),
            ].map((met, i) => (
              <div
                key={i}
                style={{
                  flex: 1, height: 3, borderRadius: 2,
                  background: met ? 'var(--success, #22c55e)' : 'var(--border)',
                  transition: 'background 0.2s',
                }}
              />
            ))}
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Confirm Password</label>
          <input
            className="form-input"
            type={showPw ? 'text' : 'password'}
            placeholder="Repeat your new password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password"
            required
          />
          {confirm && password !== confirm && (
            <span className="form-hint" style={{ color: 'var(--danger, #ef4444)' }}>
              Passwords do not match
            </span>
          )}
        </div>

        <button
          className="btn btn-primary auth-submit"
          type="submit"
          disabled={loading || !token}
        >
          {loading ? 'Resetting…' : 'Reset Password'}
        </button>
      </form>

      <div className="auth-footer" style={{ marginTop: 20 }}>
        <a href="/login">← Back to Login</a>
      </div>
    </div>
  );
}