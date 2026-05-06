import { Navigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

/**
 * Allows access only to authenticated users with role === 'admin'.
 * - No token → redirect to login
 * - Wrong role → redirect to dashboard
 */
export default function AdminRoute({ children }) {
  const { token, user } = useAuthContext();
  if (!token) return <Navigate to="/" replace />;
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return children;
}
