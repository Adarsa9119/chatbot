import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const titles = {
  '/dashboard': 'Dashboard',
  '/chat': 'Chat',
  '/profile': 'Profile',
  '/settings': 'Settings',
  '/admin': 'Admin Dashboard',
  '/admin/chat': 'Admin Chat',
  '/admin/audit': 'Audit Logs',
};

export default function Navbar() {
  const { pathname } = useLocation();
  const { user } = useAuth();
  const title = titles[pathname] || 'DocChat';

  return (
    <header className="dashboard-navbar">
      <span className="navbar-title">{title}</span>
      <div className="navbar-actions">
        {!user?.is_verified && (
          <span className="badge badge-yellow">Email not verified</span>
        )}
        <span className="badge badge-blue">{user?.user_role}</span>
      </div>
    </header>
  );
}