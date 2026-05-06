import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import { useAuth } from '../../hooks/useAuth';
import { loginUser, verifyAgentIdProof } from '../../services/api';
import InputField from '../ui/InputField';
import PasswordInput from '../ui/PasswordInput';
import Button from '../ui/Button';

const ID_TYPES = [
  { value: 'aadhaar', label: 'Aadhaar Card' },
  { value: 'pan', label: 'PAN Card' },
  { value: 'license', label: 'Driving License' },
  { value: 'voter', label: 'Voter ID' },
];

export default function RegisterForm({ role = 'user', onRoleChange }) {
  const navigate = useNavigate();
  const { login } = useAuthContext();
  const { handleRegister, loading, error } = useAuth();

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    terms: false,
    // agent-only
    id_type: '',
    id_number: '',
    id_file: null,
  });
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyError, setVerifyError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const set = (field) => (e) =>
    setForm((prev) => ({
      ...prev,
      [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
    }));

  const handleFile = (file) => {
    if (!file) return;
    setForm((prev) => ({ ...prev, id_file: file }));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.terms) return;

    setVerifyError(null);

    try {
      // Step 1 — Register the user
      await handleRegister({
        username: form.username,
        email: form.email,
        password: form.password,
        role,
      });

      if (role === 'user') {
        // Users go straight to login
        navigate('/');
        return;
      }

      // Step 2 (agent only) — Auto-login to get token
      setVerifyLoading(true);
      let token;
      try {
        const loginData = await loginUser({ email: form.email, password: form.password });
        token = loginData.access_token;
      } catch {
        // Registration succeeded but auto-login failed — send to login page
        navigate('/');
        return;
      }

      // Step 3 (agent only) — Submit ID proof for verification
      if (form.id_file && form.id_type && form.id_number) {
        try {
          await verifyAgentIdProof(
            { file: form.id_file, id_type: form.id_type, id_number: form.id_number },
            token
          );
        } catch (err) {
          // Verification failed — block access, show error, do NOT redirect
          setVerifyError(`ID verification failed: ${err.message}. Please check your ID details and try again.`);
          setVerifyLoading(false);
          return; // hard stop — no token stored, no redirect
        }
      }

      // Step 4 — Store session and redirect to agent dashboard
      const base64Payload = token.split('.')[1];
      const decoded = JSON.parse(atob(base64Payload.replace(/-/g, '+').replace(/_/g, '/')));
      localStorage.setItem('cf_token', token);
      localStorage.setItem('cf_user', JSON.stringify({
        id: decoded.id,
        email: decoded.email,
        role: decoded.role,
        verified: decoded.verified,
      }));
      navigate('/agent');
    } catch {
      // handleRegister error is already set in the hook
    } finally {
      setVerifyLoading(false);
    }
  };

  const isLoading = loading || verifyLoading;

  return (
    <div className="w-full md:w-7/12 p-[48px] md:p-[80px] flex flex-col justify-center bg-white overflow-y-auto">
      {/* Mobile logo */}
      <div className="md:hidden flex items-center justify-center gap-[4px] mb-[48px]">
        <span className="material-symbols-outlined symbol-fill text-[28px] text-[#1a365d]">
          shield_person
        </span>
        <span className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#1a365d] tracking-tight">
          ClaimFlow
        </span>
      </div>

      <div className="mb-[32px] text-center md:text-left">
        <h1 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#002045] mb-[4px]">
          {role === 'agent' ? 'Join as an Agent' : 'Create an Account'}
        </h1>
        <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
          {role === 'agent'
            ? 'Register to start your professional journey with our secure platform.'
            : 'Enter your details to get started with your secure dashboard.'}
        </p>
      </div>

      {/* Role toggle */}
      <div className="flex flex-col gap-[4px] mb-[24px]">
        <label className="font-['Work_Sans'] text-[14px] font-semibold text-[#43474e]">
          I am registering as a:
        </label>
        <div className="flex p-1 bg-[#eceef0] rounded-xl w-full">
          {['user', 'agent'].map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => onRoleChange?.(r)}
              className={`flex-1 py-2 px-4 rounded-lg font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] transition-all duration-200 capitalize ${
                role === r
                  ? 'bg-white text-[#002045] shadow-sm'
                  : 'text-[#43474e] hover:bg-[#e6e8ea]'
              }`}
            >
              {r === 'user' ? 'User' : 'Agent'}
            </button>
          ))}
        </div>
      </div>

      {/* Error banners */}
      {error && (
        <div className="mb-[24px] p-3 rounded-lg bg-[#ffdad6] text-[#93000a] text-[14px] font-['Work_Sans']">
          {error}
        </div>
      )}
      {verifyError && (
        <div className="mb-[24px] p-3 rounded-lg bg-[#ffddb8] text-[#684000] text-[14px] font-['Work_Sans']">
          {verifyError}
        </div>
      )}

      <form className="flex flex-col gap-[24px]" onSubmit={handleSubmit}>
        {/* Agent: 2-col layout for name + email */}
        {role === 'agent' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-[24px]">
            <InputField
              id="fullname"
              label="Full Name"
              icon="person"
              type="text"
              placeholder="Official Name"
              value={form.username}
              onChange={set('username')}
              required
              autoComplete="name"
            />
            <InputField
              id="email"
              label="Email Address"
              icon="mail"
              type="email"
              placeholder="email@example.com"
              value={form.email}
              onChange={set('email')}
              required
              autoComplete="email"
            />
          </div>
        ) : (
          <>
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
          </>
        )}

        <PasswordInput
          id="password"
          label="Password"
          placeholder={role === 'agent' ? 'Create Password' : 'Create a strong password'}
          value={form.password}
          onChange={set('password')}
          required
          hint="Must be at least 8 characters long."
        />

        {/* Agent-only: Professional Verification */}
        {role === 'agent' && (
          <div className="mt-[8px] pt-[24px] border-t border-[#e0e3e5]">
            <h3 className="font-['Work_Sans'] text-[14px] font-semibold text-[#002045] mb-[24px] uppercase tracking-wider">
              Professional Verification
            </h3>

            <div className="flex flex-col gap-[24px]">
              {/* ID Type + ID Number */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-[24px]">
                {/* ID Type dropdown */}
                <div className="flex flex-col gap-[4px]">
                  <label
                    htmlFor="id_type"
                    className="font-['Work_Sans'] text-[14px] font-semibold text-[#43474e]"
                  >
                    ID Type
                  </label>
                  <div className="relative flex items-center">
                    <span className="material-symbols-outlined absolute left-3 text-[#74777f] pointer-events-none">
                      badge
                    </span>
                    <select
                      id="id_type"
                      value={form.id_type}
                      onChange={set('id_type')}
                      required={role === 'agent'}
                      className="w-full h-12 pl-10 pr-8 rounded-lg border border-[#c4c6cf] bg-white text-[#191c1e] font-['Work_Sans'] text-[16px] focus:border-[#1a365d] focus:ring-1 focus:ring-[#1a365d] outline-none appearance-none transition-colors shadow-sm"
                    >
                      <option value="">Select ID Type</option>
                      {ID_TYPES.map(({ value, label }) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <span className="material-symbols-outlined absolute right-3 text-[#74777f] pointer-events-none">
                      expand_more
                    </span>
                  </div>
                </div>

                {/* ID Number */}
                <InputField
                  id="id_number"
                  label="ID Number"
                  icon="pin"
                  type="text"
                  placeholder="Enter ID number"
                  value={form.id_number}
                  onChange={set('id_number')}
                  required={role === 'agent'}
                />
              </div>

              {/* File upload — drag and drop */}
              <div className="flex flex-col gap-[4px]">
                <label className="font-['Work_Sans'] text-[14px] font-semibold text-[#43474e]">
                  Upload ID Photo
                </label>
                <label
                  htmlFor="id_photo"
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
                    dragOver
                      ? 'border-[#1a365d] bg-[#d6e3ff]/20'
                      : form.id_file
                      ? 'border-green-400 bg-green-50'
                      : 'border-[#c4c6cf] bg-[#f2f4f6] hover:bg-[#eceef0]'
                  }`}
                >
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    {form.id_file ? (
                      <>
                        <span className="material-symbols-outlined text-green-600 mb-2 text-[32px]">
                          check_circle
                        </span>
                        <p className="font-['Work_Sans'] font-semibold text-[14px] text-green-700">
                          {form.id_file.name}
                        </p>
                        <p className="font-['Work_Sans'] text-[12px] text-[#74777f] mt-1">
                          Click to change
                        </p>
                      </>
                    ) : (
                      <>
                        <span className="material-symbols-outlined text-[#74777f] mb-2 text-[32px] transition-colors group-hover:text-[#1a365d]">
                          cloud_upload
                        </span>
                        <p className="font-['Work_Sans'] font-semibold text-[14px] text-[#43474e]">
                          Click to upload or drag and drop
                        </p>
                        <p className="font-['Work_Sans'] text-[12px] text-[#74777f] mt-1">
                          PNG, JPG or PDF (Max. 5MB)
                        </p>
                      </>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    id="id_photo"
                    type="file"
                    accept="image/png,image/jpeg,application/pdf"
                    className="hidden"
                    required={role === 'agent'}
                    onChange={(e) => handleFile(e.target.files[0])}
                  />
                </label>
              </div>
            </div>
          </div>
        )}

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
            {role === 'agent' ? (
              <>
                I agree to the Agent{' '}
                <a href="#" className="text-[#1a365d] font-semibold hover:underline">
                  Partnership Agreement
                </a>{' '}
                and{' '}
                <a href="#" className="text-[#1a365d] font-semibold hover:underline">
                  Privacy Policy
                </a>
                .
              </>
            ) : (
              <>
                I agree to ClaimFlow's{' '}
                <a href="#" className="text-[#1a365d] font-semibold hover:underline">
                  Terms &amp; Conditions
                </a>{' '}
                and{' '}
                <a href="#" className="text-[#1a365d] font-semibold hover:underline">
                  Privacy Policy
                </a>
                .
              </>
            )}
          </label>
        </div>

        <Button type="submit" loading={isLoading} className="mt-[12px]">
          <span>{role === 'agent' ? 'Complete Registration' : 'Sign Up'}</span>
          <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
        </Button>
      </form>

      {/* Login link */}
      <div className="mt-[48px] text-center border-t border-[#e0e3e5] pt-[48px]">
        <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
          {role === 'agent' ? 'Already registered? ' : 'Already have an account? '}
          <Link
            to="/"
            className="font-['Work_Sans'] text-[14px] font-semibold leading-[1.2] tracking-[0.02em] text-[#1a365d] hover:text-[#003762] hover:underline transition-colors ml-1"
          >
            {role === 'agent' ? 'Login to Portal' : 'Login here'}
          </Link>
        </p>
      </div>
    </div>
  );
}
