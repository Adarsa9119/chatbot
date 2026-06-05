import { useState } from 'react';
import { verificationApi } from '../api/verificationApi';

export default function EmailVerificationBanner({ email }) {
  const [sent, setSent]   = useState(false);
  const [loading, setLoading] = useState(false);

  const resend = async () => {
    setLoading(true);
    try {
      await verificationApi.resendEmail();
      setSent(true);
    } catch (_) {}
    setLoading(false);
  };

  return (
    <div className="alert alert-warning" style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:12 }}>
      <span>⚠️ Please verify your email address <strong>{email}</strong></span>
      {sent
        ? <span className="badge badge-green">Email sent ✓</span>
        : <button className="btn btn-sm btn-secondary" onClick={resend} disabled={loading}>
            {loading ? 'Sending...' : 'Resend email'}
          </button>
      }
    </div>
  );
}