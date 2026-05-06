import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminRoute from './components/auth/AdminRoute';
import AgentRoute from './components/auth/AgentRoute';
import AuthRoute from './components/auth/AuthRoute';
import RoleRedirect from './components/auth/RoleRedirect';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import AgentPage from './pages/AgentPage';
import ChatbotPage from './pages/ChatbotPage';
import ProductsPage from './pages/ProductsPage';
import AdvisorsPage from './pages/AdvisorsPage';
import PolicyResultsPage from './pages/PolicyResultsPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<RoleRedirect><LoginPage /></RoleRedirect>} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/agent" element={<AgentRoute><AgentPage /></AgentRoute>} />
          <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
          {/* Chatbot — accessible to ALL authenticated roles */}
          <Route path="/chatbot" element={<AuthRoute><ChatbotPage /></AuthRoute>} />
          {/* Products — comprehensive insurance overview, reachable from chatbot */}
          <Route path="/products" element={<AuthRoute><ProductsPage /></AuthRoute>} />
          {/* Policy results — per-category search results, reachable from products */}
          <Route path="/policy/:category" element={<AuthRoute><PolicyResultsPage /></AuthRoute>} />
          {/* Advisors — expert network, reachable from products */}
          <Route path="/advisors" element={<AuthRoute><AdvisorsPage /></AuthRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
