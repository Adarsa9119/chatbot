import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function NotFound() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const home = user?.user_role === 'admin' ? '/admin' : user ? '/dashboard' : '/login';

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg)',
        padding: '24px',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: '5rem',
          fontWeight: 800,
          color: 'var(--border2)',
          letterSpacing: '-0.05em',
          lineHeight: 1,
          marginBottom: 8,
        }}
      >
        404
      </div>
      <h1
        style={{
          fontSize: '1.4rem',
          fontWeight: 600,
          color: 'var(--text)',
          marginBottom: 12,
        }}
      >
        Page not found
      </h1>
      <p
        style={{
          color: 'var(--text2)',
          fontSize: '0.9rem',
          maxWidth: 360,
          marginBottom: 32,
        }}
      >
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-secondary" onClick={() => navigate(-1)}>
          ← Go back
        </button>
        <Link className="btn btn-primary" to={home}>
          Go home
        </Link>
      </div>
    </div>
  );
}