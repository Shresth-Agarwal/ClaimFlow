import { Navigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

/**
 * Used on the login page — if a user is already logged in,
 * redirect them to the correct dashboard based on their role.
 * This prevents logged-in users from seeing the login page.
 */
export default function RoleRedirect({ children }) {
  const { token, user } = useAuthContext();

  if (!token) return children; // not logged in — show login page

  // Already logged in — send to correct dashboard
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  if (user?.role === 'agent') return <Navigate to="/agent" replace />;
  return <Navigate to="/dashboard" replace />;
}
