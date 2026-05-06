import { useState } from 'react';
import RegisterForm from '../components/auth/RegisterForm';

const PANEL_CONTENT = {
  user: {
    heading: "Secure your family's tomorrow, today.",
    body: 'Join thousands of trustful Indians who have chosen our platform for transparent, reliable, and accessible insurance solutions.',
    badges: [
      { icon: 'verified', label: 'IRDAI Registered' },
      { icon: 'support_agent', label: '24/7 Support' },
    ],
  },
  agent: {
    heading: 'Empower your career with ClaimFlow.',
    body: 'Become a certified partner and help thousands of Indians secure their future with transparent, reliable, and accessible insurance solutions.',
    badges: [
      { icon: 'verified', label: 'IRDAI Partner' },
      { icon: 'support_agent', label: '24/7 Support' },
    ],
  },
};

export default function RegisterPage() {
  const [role, setRole] = useState('user');
  const panel = PANEL_CONTENT[role];

  return (
    <div className="min-h-screen flex antialiased bg-[#f7f9fb] text-[#191c1e]">
      {/* Left brand panel */}
      <div className="hidden md:flex w-full md:w-5/12 relative bg-[#1a365d] flex-col justify-between p-[48px] overflow-hidden">
        {/* Background image */}
        <div className="absolute inset-0 z-0">
          <img
            alt="Family securing their future"
            className="w-full h-full object-cover opacity-40 mix-blend-overlay"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuCVDZ1P4c_CqOQVXV1V9lclXBztboyBwgVRtruezMfzwWf52PfY311l36GyLcVdFFPBGHPQOFHXYh49CFrbd5SaymEsrSjF88x9U0FEFYvTGp6-uWROyFwgUxCsf5PzAroyN0gFIp8QQYtUgZE10o8YmFFTkAW9R0GZIJRT0AEHHaVV5iRwcTxm2sguSiBoqmQDj9CqkQA_s2713-PM7Bd13JPI3Sgy7f44grSHMb906KU_wRQuooLiRMXMMu7posq_fg88NqS5nJkj"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#1a365d] via-[#1a365dcc] to-[#1a365d33]" />
        </div>

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-[4px] text-white">
          <span className="material-symbols-outlined symbol-fill text-[32px] text-[#fea619]">
            shield_person
          </span>
          <span className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold tracking-tight text-white">
            ClaimFlow
          </span>
        </div>

        {/* Value prop — updates based on role */}
        <div className="relative z-10 mt-[80px]">
          <h2 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-white mb-[12px] transition-all duration-300">
            {panel.heading}
          </h2>
          <p className="font-['Work_Sans'] text-[18px] leading-[1.6] text-[#adc7f7] transition-all duration-300">
            {panel.body}
          </p>

          {/* Trust badges */}
          <div className="mt-[48px] flex gap-[24px] items-center opacity-80">
            {panel.badges.map(({ icon, label }) => (
              <div key={label} className="flex items-center gap-[4px]">
                <span className="material-symbols-outlined text-[#fea619]">{icon}</span>
                <span className="font-['Work_Sans'] text-[14px] font-semibold text-white">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pass role state down so form and panel stay in sync */}
      <RegisterForm role={role} onRoleChange={setRole} />
    </div>
  );
}
