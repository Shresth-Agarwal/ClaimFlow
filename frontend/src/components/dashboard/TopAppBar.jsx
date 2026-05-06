import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

export default function TopAppBar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthContext();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="bg-white text-[#1a365d] font-['Be_Vietnam_Pro'] font-medium text-sm w-full sticky top-0 z-50 shadow-sm border-b border-slate-200">
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-7xl mx-auto">
        {/* Brand */}
        <a
          href="#"
          className="text-2xl font-bold text-[#1a365d] tracking-tight flex items-center gap-2 hover:bg-slate-50 transition-colors rounded-lg p-1 active:scale-95 duration-200"
        >
          <span className="material-symbols-outlined icon-fill text-[#f59e0b]">verified_user</span>
          ClaimFlow
        </a>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {['Renew', 'Products', 'Advisors', 'Support'].map((item) => (
            <a
              key={item}
              href="#"
              className={`transition-colors active:scale-95 duration-200 px-3 py-2 rounded-md ${
                item === 'Products'
                  ? 'text-[#f59e0b] border-b-2 border-[#f59e0b] pb-1 font-bold'
                  : 'text-slate-600 hover:text-[#1a365d] hover:bg-slate-50'
              }`}
            >
              {item}
            </a>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <button className="text-slate-600 hover:text-[#1a365d] hover:bg-slate-50 transition-colors active:scale-95 duration-200 p-2 rounded-full hidden md:flex">
            <span className="material-symbols-outlined">search</span>
          </button>

          {/* User info + logout */}
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
