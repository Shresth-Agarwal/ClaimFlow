import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import InputField from '../ui/InputField';
import PasswordInput from '../ui/PasswordInput';
import Button from '../ui/Button';


export default function LoginForm() {
  const navigate = useNavigate();
  const { handleLogin, loading, error } = useAuth();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const user = await handleLogin({ email: identifier, password });
      // Role-based redirect
      if (user?.role === 'admin') navigate('/admin');
      else if (user?.role === 'agent') navigate('/agent');
      else navigate('/dashboard');
    } catch {
      // error is already set in the hook
    }
  };

  return (
    <div className="w-full lg:w-[55%] flex items-center justify-center p-[24px] sm:p-[48px] lg:p-[80px] bg-white relative z-10">
      {/* Mobile logo */}
      <div className="absolute top-[24px] left-[24px] flex lg:hidden items-center gap-2 text-[#002045]">
        <span className="material-symbols-outlined text-2xl symbol-fill">shield_person</span>
        <span className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold tracking-tight">
          ClaimFlow
        </span>
      </div>

      <div className="w-full max-w-[420px] pt-12 lg:pt-0">
        {/* Header */}
        <div className="mb-[40px] text-center lg:text-left">
          <h1 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#002045] mb-2">
            Welcome Back
          </h1>
          <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
            Please enter your details to sign in.
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-[24px] p-3 rounded-lg bg-[#ffdad6] text-[#93000a] text-[14px] font-['Work_Sans']">
            {error}
          </div>
        )}

        {/* Login form */}
        <form className="flex flex-col gap-[24px]" onSubmit={handleSubmit}>
          <InputField
            id="identifier"
            label="Email"
            icon="mail"
            type="text"
            placeholder="Enter your email"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
            autoComplete="email"
          />

          <div className="flex flex-col gap-[4px]">
            <div className="flex justify-between items-center ml-1">
              <label
                htmlFor="password"
                className="font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] text-[#43474e]"
              >
                Password
              </label>
              <a
                href="#"
                className="font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] text-[#002045] hover:text-[#fea619] transition-colors"
              >
                Forgot password?
              </a>
            </div>
            <PasswordInput
              id="password"
              label=""
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <Button type="submit" loading={loading} className="mt-[12px]">
            Sign In
          </Button>
        </form>

        {/* Footer */}
        <p className="text-center mt-[80px] font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] text-[#002045] hover:text-[#fea619] transition-colors"
          >
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
