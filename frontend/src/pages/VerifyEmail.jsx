import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { verificationApi } from '../api/verificationApi';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Verification token is missing.');
      return;
    }
    verificationApi.verifyEmail(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Verification failed. The link may have expired.');
      });
  }, [token]);

  if (status === 'verifying') {
    return (
      <div className="auth-card" style={{ textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto 20px' }} />
        <p className="auth-subtitle">Verifying your email…</p>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="auth-card" style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 44, marginBottom: 16 }}>✅</div>
        <h2 className="auth-title">Email Verified!</h2>
        <p className="auth-subtitle" style={{ marginBottom: 24 }}>
          Your email has been successfully verified. Your account is now fully active.
        </p>
        <Link className="btn btn-primary" style={{ display: 'inline-block' }} to="/login">
          Continue to Login
        </Link>
      </div>
    );
  }

  return (
    <div className="auth-card" style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 44, marginBottom: 16 }}>❌</div>
      <h2 className="auth-title">Verification Failed</h2>
      <p className="auth-subtitle" style={{ marginBottom: 24 }}>
        {message}
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'center' }}>
        <ResendButton />
        <Link to="/login" style={{ fontSize: '0.85rem', color: 'var(--accent)' }}>
          Back to Login
        </Link>
      </div>
    </div>
  );
}

function ResendButton() {
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const resend = async () => {
    setLoading(true);
    try {
      await verificationApi.resendEmail();
      setSent(true);
    } catch {
      setSent(true); // show success regardless
    } finally {
      setLoading(false);
    }
  };

  if (sent) return <p style={{ fontSize: '0.85rem', color: 'var(--text2)' }}>Verification email sent!</p>;

  return (
    <button className="btn btn-secondary" onClick={resend} disabled={loading}>
      {loading ? 'Sending…' : 'Resend Verification Email'}
    </button>
  );
}