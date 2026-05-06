import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import ClaimFlowLogo from '../ui/ClaimFlowLogo';

const NAV_ITEMS = [
  { label: 'Home', path: '/dashboard' },
  { label: 'Product', path: '/products' },
  { label: 'Advisors', path: '/advisors' },
  { label: 'ChatBot', path: '/chatbot' },
];

export default function TopAppBar({ activePage = 'Home' }) {
  const navigate = useNavigate();
  const { user, logout } = useAuthContext();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="bg-white text-[#1a365d] font-['Be_Vietnam_Pro'] font-medium text-sm w-full fixed top-0 left-0 right-0 z-50 shadow-sm border-b border-slate-200 h-16">
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-7xl mx-auto">
        {/* Brand */}
        <a
          href="#"
          onClick={(e) => { e.preventDefault(); navigate('/dashboard'); }}
          className="flex items-center hover:opacity-90 transition-opacity rounded-lg p-1 active:scale-95 duration-200"
        >
          <ClaimFlowLogo variant="full" height={36} />
        </a>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV_ITEMS.map(({ label, path }) => {
            const isActive = label === activePage;
            return (
              <a
                key={label}
                href="#"
                onClick={path ? (e) => { e.preventDefault(); navigate(path); } : (e) => e.preventDefault()}
                className={`transition-colors active:scale-95 duration-200 px-3 py-2 rounded-md ${
                  isActive
                    ? 'text-[#f59e0b] border-b-2 border-[#f59e0b] pb-1 font-bold'
                    : 'text-slate-600 hover:text-[#1a365d] hover:bg-slate-50'
                }`}
              >
                {label}
              </a>
            );
          })}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <button className="text-slate-600 hover:text-[#1a365d] hover:bg-slate-50 transition-colors active:scale-95 duration-200 p-2 rounded-full hidden md:flex">
            <span className="material-symbols-outlined">search</span>
          </button>

          {user ? (
            <div className="flex items-center gap-3">
              <span className="hidden sm:block text-sm text-slate-600 font-['Work_Sans']">
                {user.email}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1 text-sm font-['Work_Sans'] text-slate-600 hover:text-red-600 transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">logout</span>
                <span className="hidden sm:block">Logout</span>
              </button>
            </div>
          ) : (
            <a
              href="#"
              className="bg-[#1a365d] text-white px-5 py-2.5 rounded-lg font-['Be_Vietnam_Pro'] font-medium text-sm hover:bg-opacity-90 transition-colors shadow-sm active:scale-95 duration-200 hidden sm:block"
            >
              Login
            </a>
          )}
        </div>
      </div>
    </header>
  );
}
