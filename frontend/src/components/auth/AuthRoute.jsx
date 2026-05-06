import { Navigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

/**
 * Allows any authenticated user regardless of role.
 * Only redirects to login if no token.
 * Used for shared pages like /chatbot.
 */
export default function AuthRoute({ children }) {
  const { token } = useAuthContext();
  if (!token) return <Navigate to="/" replace />;
  return children;
}
