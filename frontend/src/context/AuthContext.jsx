import { createContext, useContext, useState, useCallback } from 'react';
import { loginUser, registerUser } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('cf_token'));
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('cf_user'));
    } catch {
      return null;
    }
  });

  /**
   * Calls POST /auth/login, stores JWT + user payload.
   * Backend returns { access_token, token_type }.
   * User info (id, email, role, verified) is decoded from the JWT payload.
   * Returns the user object on success.
   */
  const login = useCallback(async ({ email, password }) => {
    const data = await loginUser({ email, password });

    const jwt = data.access_token;
    if (!jwt) throw new Error('No token received from server');

    // Decode the JWT payload (base64 middle segment) — no verification needed client-side
    let userPayload;
    try {
      const base64Payload = jwt.split('.')[1];
      // atob needs standard base64 — replace URL-safe chars
      const decoded = JSON.parse(atob(base64Payload.replace(/-/g, '+').replace(/_/g, '/')));
      userPayload = {
        id: decoded.id,
        email: decoded.email,
        role: decoded.role,
        verified: decoded.verified,
      };
    } catch {
      throw new Error('Failed to parse authentication token');
    }

    localStorage.setItem('cf_token', jwt);
    localStorage.setItem('cf_user', JSON.stringify(userPayload));
    setToken(jwt);
    setUser(userPayload);
    return userPayload;
  }, []);

  /**
   * Calls POST /auth/register.
   * Returns the created user object on success.
   */
  const register = useCallback(async ({ username, email, password, role }) => {
    const data = await registerUser({ username, email, password, role });
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('cf_token');
    localStorage.removeItem('cf_user');
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used inside <AuthProvider>');
  return ctx;
}
