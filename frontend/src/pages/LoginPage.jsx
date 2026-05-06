import BrandPanel from '../components/auth/BrandPanel';
import LoginForm from '../components/auth/LoginForm';

export default function LoginPage() {
  return (
    <div className="min-h-screen flex antialiased bg-[#f7f9fb] text-[#191c1e]">
      <BrandPanel />
      <LoginForm />
    </div>
  );
}
