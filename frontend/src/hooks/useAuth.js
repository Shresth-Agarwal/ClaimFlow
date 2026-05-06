import { useState } from 'react';
import { useAuthContext } from '../context/AuthContext';

/**
 * Custom hook for login/register form submission.
 * Manages loading, error, and data states.
 */
export function useAuth() {
  const { login, register } = useAuthContext();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const handleLogin = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const user = await login(credentials);
      setData(user);
      return user;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const user = await register(payload);
      setData(user);
      return user;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { handleLogin, handleRegister, loading, error, data };
}
