/**
 * ProductsFooter — dark footer with dark logo variant.
 */
import ClaimFlowLogo from '../ui/ClaimFlowLogo';

const LINKS = [
  'Privacy Policy',
  'Terms & Conditions',
  'Compliance',
  'Fraud Awareness',
  'Disclosures',
];

export default function ProductsFooter() {
  return (
    <footer className="bg-[#1a365d] w-full mt-[80px]">
      <div className="w-full py-[48px] px-[24px] flex flex-col md:flex-row justify-between items-center max-w-[1280px] mx-auto">
        <div className="mb-[24px] md:mb-0">
          <ClaimFlowLogo variant="dark" height={34} />
          <p className="font-['Work_Sans'] text-[12px] text-white/60 mt-[8px]">
            IRDAI Registration No. 123
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-[24px] mb-[24px] md:mb-0">
          {LINKS.map((link) => (
            <a
              key={link}
              href="#"
              className="text-[#86a0cd]/80 hover:text-white font-['Work_Sans'] text-[12px] hover:underline decoration-[#fea619] decoration-2 transition-all duration-300"
            >
              {link}
            </a>
          ))}
        </div>
      </div>

      <div className="border-t border-white/10 w-full py-[8px]">
        <div className="max-w-[1280px] mx-auto px-[24px] text-center">
          <p className="font-['Work_Sans'] text-[12px] text-white/50">
            © 2024 ClaimFlow Insurance. All rights reserved. Insurance is the subject matter of
            solicitation.
          </p>
        </div>
      </div>
    </footer>
  );
}
