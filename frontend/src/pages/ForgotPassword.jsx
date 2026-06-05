import { useState } from 'react';
import { Link } from 'react-router-dom';
import { passwordApi } from '../api/passwordApi';
import { extractApiError } from '../utils/helpers';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) { setError('Please enter your email address.'); return; }
    setError('');
    setLoading(true);
    try {
      await passwordApi.forgotPassword({ user_email: email });
      setSent(true);
    } catch (err) {
      // Show success even on 404 to avoid user enumeration
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="auth-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>📧</div>
          <h2 className="auth-title">Check your email</h2>
          <p className="auth-subtitle" style={{ marginBottom: 24 }}>
            If an account exists for <strong>{email}</strong>, we've sent a password
            reset link. Check your inbox (and spam folder).
          </p>
          <p style={{ fontSize: '0.85rem', color: 'var(--text2)', marginBottom: 20 }}>
            The link expires in 30 minutes.
          </p>
          <Link className="btn btn-secondary" style={{ display: 'inline-block' }} to="/login">
            ← Back to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-card">
      <h2 className="auth-title">Forgot password?</h2>
      <p className="auth-subtitle">
        Enter your email and we'll send you a reset link.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-group">
          <label className="form-label">Email address</label>
          <input
            className="form-input"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </div>

        <button className="btn btn-primary auth-submit" type="submit" disabled={loading}>
          {loading ? 'Sending…' : 'Send Reset Link'}
        </button>
      </form>

      <div className="auth-footer">
        <Link to="/login">← Back to Login</Link>
      </div>
    </div>
  );
}