import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const userLinks = [
  { to: '/dashboard', icon: '⬛', label: 'Dashboard' },
  { to: '/chat', icon: '💬', label: 'Chat' },
  { to: '/profile', icon: '👤', label: 'Profile' },
  { to: '/settings', icon: '⚙️', label: 'Settings' },
];

const adminLinks = [
  { to: '/admin', icon: '🛡️', label: 'Admin Dashboard' },
  { to: '/admin/chat', icon: '💬', label: 'Chat' },
  { to: '/admin/audit', icon: '📋', label: 'Audit Logs' },
  { to: '/profile', icon: '👤', label: 'Profile' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const links = user?.user_role === 'admin' ? adminLinks : userLinks;

  return (
    <aside className="dashboard-sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">📄</div>
        <span className="sidebar-logo-name">DocChat</span>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section">Menu</div>
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/dashboard' || link.to === '/admin'}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <span className="sidebar-link-icon">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">
            {user?.user_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name truncate">{user?.user_name}</div>
            <div className="sidebar-user-role">{user?.user_role}</div>
          </div>
          <button className="btn-icon" onClick={logout} title="Logout">⏏</button>
        </div>
      </div>
    </aside>
  );
}