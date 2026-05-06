import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: 'dashboard', active: true },
  { label: 'Users', icon: 'group' },
  { label: 'Claims', icon: 'description' },
  { label: 'Revenue', icon: 'payments' },
  { label: 'Policies', icon: 'policy' },
  { label: 'Settings', icon: 'settings' },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { logout } = useAuthContext();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <aside className="fixed left-0 top-0 h-screen flex flex-col z-40 bg-[#1a365d] text-white font-['Be_Vietnam_Pro'] text-sm shadow-xl border-r border-white/10 w-64 hidden md:flex">
      {/* Brand */}
      <div className="flex items-center px-6 py-6 border-b border-white/10 gap-3">
        <div className="w-10 h-10 rounded-full bg-[#fea619] flex items-center justify-center">
          <span className="material-symbols-outlined icon-fill text-white text-xl">verified_user</span>
        </div>
        <div>
          <div className="text-xl font-black text-white leading-tight">Admin Console</div>
          <div className="text-xs text-slate-300">Insurance Management</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-6 flex flex-col gap-1 overflow-y-auto">
        {NAV_ITEMS.map(({ label, icon, active }) => (
          <a
            key={label}
            href="#"
            className={`mx-2 my-1 rounded-lg flex items-center gap-3 px-4 py-3 transition-all ${
              active
                ? 'bg-[#fea619] text-white shadow-md font-semibold'
                : 'text-slate-300 hover:bg-white/10'
            }`}
          >
            <span
              className="material-symbols-outlined"
              style={active ? { fontVariationSettings: "'FILL' 1" } : {}}
            >
              {icon}
            </span>
            <span>{label}</span>
          </a>
        ))}
      </nav>

      {/* Bottom */}
      <div className="p-4 border-t border-white/10 flex flex-col gap-2">
        <button className="w-full bg-[#fea619] text-white py-2 px-4 rounded-lg font-['Work_Sans'] font-semibold text-[14px] hover:bg-[#ffb95f] transition-colors flex items-center justify-center gap-2">
          <span className="material-symbols-outlined text-sm">download</span>
          Generate Report
        </button>
        <button
          onClick={handleLogout}
          className="w-full text-slate-300 hover:text-white py-2 px-4 rounded-lg font-['Work_Sans'] text-[14px] hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-sm">logout</span>
          Logout
        </button>
      </div>
    </aside>
  );
}
