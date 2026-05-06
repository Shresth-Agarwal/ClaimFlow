import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminRoute from './components/auth/AdminRoute';
import AgentRoute from './components/auth/AgentRoute';
import RoleRedirect from './components/auth/RoleRedirect';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import AgentPage from './pages/AgentPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Login — redirect away if already logged in */}
          <Route
            path="/"
            element={
              <RoleRedirect>
                <LoginPage />
              </RoleRedirect>
            }
          />
          <Route path="/register" element={<RegisterPage />} />

          {/* User dashboard — role: user only */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Agent dashboard — role: agent only */}
          <Route
            path="/agent"
            element={
              <AgentRoute>
                <AgentPage />
              </AgentRoute>
            }
          />

          {/* Admin dashboard — role: admin only */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
