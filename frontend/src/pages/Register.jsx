import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { useAuth } from '../context/AuthContext';
import { extractApiError, checkPasswordStrength } from '../utils/helpers';

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPw, setShowPw] = useState(false);

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const validate = () => {
    if (!form.name.trim()) return 'Full name is required.';
    if (!form.email) return 'Email is required.';
    if (form.password.length < 8) return 'Password must be at least 8 characters.';
    if (!/[A-Z]/.test(form.password)) return 'Password must include an uppercase letter.';
    if (!/[0-9]/.test(form.password)) return 'Password must include a number.';
    if (form.password !== form.confirm) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) { setError(validationError); return; }
    setError('');
    setLoading(true);
    try {
      const res = await authApi.register({
        user_name: form.name.trim(),
        user_email: form.email,
        user_password: form.password,
      });
      const user = res.data?.user || res.data;
      login(user);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(extractApiError(err, 'Registration failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const strength = checkPasswordStrength(form.password);
  const metCount = strength.filter((r) => r.met).length;

  return (
    <div className="auth-card">
      <h2 className="auth-title">Create account</h2>
      <p className="auth-subtitle">Join DocChat to access document Q&A</p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-group">
          <label className="form-label">Full Name</label>
          <input
            className="form-input"
            type="text"
            placeholder="Your full name"
            value={form.name}
            onChange={set('name')}
            autoComplete="name"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            className="form-input"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={set('email')}
            autoComplete="email"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <div style={{ position: 'relative' }}>
            <input
              className="form-input"
              type={showPw ? 'text' : 'password'}
              placeholder="At least 8 characters"
              value={form.password}
              onChange={set('password')}
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
                fontSize: '0.8rem', padding: 0,
              }}
            >
              {showPw ? 'Hide' : 'Show'}
            </button>
          </div>
          {/* Strength bar */}
          {form.password && (
            <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
              {strength.map((rule, i) => (
                <div
                  key={i}
                  title={rule.label}
                  style={{
                    flex: 1, height: 3, borderRadius: 2,
                    background: rule.met ? (metCount >= 4 ? '#22c55e' : metCount >= 2 ? '#f59e0b' : '#ef4444') : 'var(--border)',
                    transition: 'background 0.2s',
                  }}
                />
              ))}
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Confirm Password</label>
          <input
            className="form-input"
            type={showPw ? 'text' : 'password'}
            placeholder="Repeat password"
            value={form.confirm}
            onChange={set('confirm')}
            autoComplete="new-password"
            required
          />
          {form.confirm && form.password !== form.confirm && (
            <span className="form-hint" style={{ color: 'var(--danger, #ef4444)' }}>
              Passwords do not match
            </span>
          )}
        </div>

        <button className="btn btn-primary auth-submit" type="submit" disabled={loading}>
          {loading ? 'Creating account…' : 'Create Account'}
        </button>
      </form>

      <div className="auth-footer">
        Already have an account? <Link to="/login">Sign in</Link>
      </div>
    </div>
  );
}