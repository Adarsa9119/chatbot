import { Outlet } from 'react-router-dom';
import '../styles/auth.css';

export default function AuthLayout() {
  return (
    <div className="auth-layout">
      <div className="auth-panel-left">
        <div className="auth-brand">
          <div className="auth-brand-icon">📄</div>
          <div className="auth-brand-name">DocChat</div>
          <div className="auth-brand-sub">AI-powered document intelligence</div>
        </div>
        <div className="auth-features">
          {[
            { icon: '🔍', text: 'Ask questions across all your documents' },
            { icon: '🧠', text: 'RAG-powered accurate responses' },
            { icon: '🔒', text: 'Secure, private document storage' },
            { icon: '⚡', text: 'Fast vector similarity search' },
          ].map((f, i) => (
            <div className="auth-feature" key={i}>
              <div className="auth-feature-icon">{f.icon}</div>
              <div className="auth-feature-text">{f.text}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="auth-panel-right">
        <Outlet />
      </div>
    </div>
  );
}