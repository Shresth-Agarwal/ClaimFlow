import BrandPanel from '../components/auth/BrandPanel';
import RegisterForm from '../components/auth/RegisterForm';

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex antialiased bg-[#f7f9fb] text-[#191c1e]">
      {/* Left brand panel — register variant */}
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

        {/* Value prop */}
        <div className="relative z-10 mt-[80px]">
          <h2 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-white mb-[12px] leading-tight">
            Secure your family's tomorrow, today.
          </h2>
          <p className="font-['Work_Sans'] text-[18px] leading-[1.6] text-[#adc7f7]">
            Join thousands of trustful Indians who have chosen our platform for
            transparent, reliable, and accessible insurance solutions.
          </p>

          {/* Trust badges */}
          <div className="mt-[48px] flex gap-[24px] items-center opacity-80">
            <div className="flex items-center gap-[4px]">
              <span className="material-symbols-outlined text-[#fea619]">verified</span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-white">
                IRDAI Registered
              </span>
            </div>
            <div className="flex items-center gap-[4px]">
              <span className="material-symbols-outlined text-[#fea619]">support_agent</span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-white">
                24/7 Support
              </span>
            </div>
          </div>
        </div>
      </div>

      <RegisterForm />
    </div>
  );
}
