const LINKS = ['About Us', 'Privacy Policy', 'Terms & Conditions', 'Help Center', 'Contact Us', 'Careers'];

export default function DashboardFooter() {
  return (
    <footer className="bg-slate-50 text-xs text-slate-500 border-t border-slate-200 w-full py-12 px-6 mt-auto flex flex-col items-center gap-6">
      <div className="text-lg font-bold text-[#1a365d] font-['Be_Vietnam_Pro']">ClaimFlow</div>
      <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
        {LINKS.map((link) => (
          <a
            key={link}
            href="#"
            className="text-slate-600 hover:text-[#1a365d] underline transition-all duration-300"
          >
            {link}
          </a>
        ))}
      </div>
      <div className="text-center w-full">
        © 2024 ClaimFlow Insurance Broking. IRDAI Registered.
      </div>
    </footer>
  );
}
