import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import InputField from '../ui/InputField';
import PasswordInput from '../ui/PasswordInput';
import Button from '../ui/Button';

export default function RegisterForm() {
  const navigate = useNavigate();
  const { handleRegister, loading, error } = useAuth();

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user',
    terms: false,
  });

  const set = (field) => (e) =>
    setForm((prev) => ({
      ...prev,
      [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
    }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.terms) return;
    try {
      await handleRegister({
        username: form.username,
        email: form.email,
        password: form.password,
        role: form.role,
      });
      navigate('/');
    } catch {
      // error is already set in the hook
    }
  };

  return (
    <div className="w-full md:w-7/12 p-[48px] md:p-[80px] flex flex-col justify-center bg-white">
      {/* Mobile logo */}
      <div className="md:hidden flex items-center justify-center gap-[4px] mb-[48px]">
        <span className="material-symbols-outlined symbol-fill text-[28px] text-[#1a365d]">
          shield_person
        </span>
        <span className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#1a365d] tracking-tight">
          ClaimFlow
        </span>
      </div>

      <div className="mb-[48px] text-center md:text-left">
        <h1 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#002045] mb-[4px]">
          Create an Account
        </h1>
        <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
          Enter your details to get started with your secure dashboard.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-[24px] p-3 rounded-lg bg-[#ffdad6] text-[#93000a] text-[14px] font-['Work_Sans']">
          {error}
        </div>
      )}

      <form className="flex flex-col gap-[24px]" onSubmit={handleSubmit}>
        {/* Full Name → maps to username */}
        <InputField
          id="fullname"
          label="Full Name"
          icon="person"
          type="text"
          placeholder="As per your official documents"
          value={form.username}
          onChange={set('username')}
          required
          autoComplete="name"
        />

        {/* Email */}
        <InputField
          id="email"
          label="Email Address"
          icon="mail"
          type="email"
          placeholder="your.name@example.com"
          value={form.email}
          onChange={set('email')}
          required
          autoComplete="email"
        />

        {/* Mobile — removed */}

        {/* Password */}
        <PasswordInput
          id="password"
          label="Password"
          placeholder="Create a strong password"
          value={form.password}
          onChange={set('password')}
          required
          hint="Must be at least 8 characters long."
        />

        {/* Role selector */}
        <div className="flex flex-col gap-[4px]">
          <label className="font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] text-[#43474e] ml-1">
            Role
          </label>
          <div className="flex bg-[#eceef0] p-1 rounded-lg">
            {['user', 'agent'].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setForm((prev) => ({ ...prev, role: r }))}
                className={`flex-1 py-2 px-4 rounded-md text-center capitalize transition-all font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] ${
                  form.role === r
                    ? 'bg-white shadow-[0px_4px_20px_rgba(26,54,93,0.05)] text-[#002045]'
                    : 'text-[#43474e] hover:text-[#002045]'
                }`}
              >
                {r === 'user' ? 'User' : 'Agent'}
              </button>
            ))}
          </div>
        </div>

        {/* Terms */}
        <div className="flex items-start gap-[12px] mt-[4px]">
          <input
            id="terms"
            type="checkbox"
            checked={form.terms}
            onChange={set('terms')}
            required
            className="mt-1 h-[18px] w-[18px] rounded border-[#c4c6cf] text-[#fea619] focus:ring-[#fea619] focus:ring-offset-0 cursor-pointer"
          />
          <label
            htmlFor="terms"
            className="font-['Work_Sans'] text-[16px] leading-tight text-[#43474e] cursor-pointer"
          >
            I agree to ClaimFlow's{' '}
            <a href="#" className="text-[#1a365d] font-semibold hover:underline">
              Terms &amp; Conditions
            </a>{' '}
            and{' '}
            <a href="#" className="text-[#1a365d] font-semibold hover:underline">
              Privacy Policy
            </a>
            .
          </label>
        </div>

        <Button type="submit" loading={loading} className="mt-[12px]">
          <span>Sign Up</span>
          <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
        </Button>
      </form>

      {/* Login link */}
      <div className="mt-[48px] text-center border-t border-[#e0e3e5] pt-[48px]">
        <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
          Already have an account?{' '}
          <Link
            to="/"
            className="font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] text-[#1a365d] hover:text-[#003762] hover:underline transition-colors ml-1"
          >
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}
