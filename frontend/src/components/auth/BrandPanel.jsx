/**
 * Left decorative brand column — shared between Login and Register pages.
 * Hidden on mobile, visible on lg+.
 */
import ClaimFlowLogo from '../ui/ClaimFlowLogo';

export default function BrandPanel({ quote, trustBadges = false }) {
  return (
    <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden bg-[#002045] flex-col justify-end p-[80px]">
      {/* Abstract background image */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-40 mix-blend-luminosity"
        style={{
          backgroundImage:
            "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDj41y2ttHjx7DMDWHmKtSsBTtIk5vgLLofp0GL36TIakwknl9_35pKfAgIDLmHZBgtKbPRLahdB1LGFJ-OkkkUOkEzBMO7BkMe-NB0jakojs5fETwRMTZ02tn-474rSnsutXAv5U0Dab36rTzsEEKiYfYTY79HkSw02sJnm116F3PU7NYcdoxYEb1-oMztRFZGZBIHkQddzo7VtI6ToLS7lo9BOYkab-Q4ySQDf90Qw_NPEYPVDkAVfLVa6q7S-F4AktvzKnsTFVop')",
        }}
      />
      {/* Gradient overlay */}
      <div className="absolute inset-0 z-10 bg-gradient-to-t from-[#002045] via-[#002045cc] to-transparent" />

      {/* Content — stacks vertically, takes full width of the panel */}
      <div className="relative z-20 text-white">
        {/* Logo row */}
        <div className="flex items-center gap-3 mb-5">
          <ClaimFlowLogo variant="dark" height={52} />
        </div>

        {/* Tagline */}
        <p className="font-['Work_Sans'] text-[18px] leading-[1.6] text-[#adc7f7]">
          {quote ||
            "Secure your future with India's most trusted insurance management platform. Intelligent coverage, simplified."}
        </p>

        {trustBadges && (
          <div className="mt-8 flex gap-6 items-center opacity-80">
            <div className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[#fea619]">verified</span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-white">
                IRDAI Registered
              </span>
            </div>
            <div className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[#fea619]">support_agent</span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-white">
                24/7 Support
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
