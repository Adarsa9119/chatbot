import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function UserRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}