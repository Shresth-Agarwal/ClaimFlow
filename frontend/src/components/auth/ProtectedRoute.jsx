import { Navigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

/**
 * Wraps a route and redirects to "/" if no token is present.
 */
export default function ProtectedRoute({ children }) {
  const { token } = useAuthContext();
  if (!token) return <Navigate to="/" replace />;
  return children;
}
