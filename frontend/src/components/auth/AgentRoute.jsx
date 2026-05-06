import { Navigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

/**
 * Allows access only to role === 'agent'.
 * Redirects everyone else to their correct dashboard.
 */
export default function AgentRoute({ children }) {
  const { token, user } = useAuthContext();
  if (!token) return <Navigate to="/" replace />;
  if (user?.role === 'agent') return children;
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  return <Navigate to="/dashboard" replace />;
}
