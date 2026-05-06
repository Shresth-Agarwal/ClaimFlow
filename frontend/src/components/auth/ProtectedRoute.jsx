import { Navigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

/**
 * Protects routes for "user" role only.
 * - No token → /
 * - agent role → /agent
 * - admin role → /admin
 */
export default function ProtectedRoute({ children }) {
  const { token, user } = useAuthContext();
  if (!token) return <Navigate to="/" replace />;
  if (user?.role === 'agent') return <Navigate to="/agent" replace />;
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  return children;
}
