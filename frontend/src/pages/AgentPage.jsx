import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import MetricCard from '../components/admin/MetricCard';
import TopPlansTable from '../components/admin/TopPlansTable';

const AGENT_METRICS = [
  {
    label: 'My Clients',
    value: '128',
    icon: 'group',
    iconBg: 'bg-[#d6e3ff]',
    iconColor: 'text-[#002045]',
    blobBg: 'bg-[#d6e3ff]/20',
    trend: '+12.5%',
    trendLabel: 'vs last month',
  },
  {
    label: 'Active Policies',
    value: '84',
    icon: 'policy',
    iconBg: 'bg-[#d2e4ff]',
    iconColor: 'text-[#00213e]',
    blobBg: 'bg-[#d2e4ff]/20',
    trend: '+8.2%',
    trendLabel: 'vs last month',
  },
  {
    label: 'Commission',
    value: '₹48K',
    icon: 'payments',
    iconBg: 'bg-[#ffddb8]',
    iconColor: 'text-[#855300]',
    blobBg: 'bg-[#ffddb8]/20',
    trend: '+24.1%',
    trendLabel: 'vs last month',
  },
  {
    label: 'Pending Claims',
    value: '7',
    icon: 'assignment_late',
    iconBg: 'bg-[#ffdad6]',
    iconColor: 'text-[#ba1a1a]',
    blobBg: 'bg-[#ffdad6]/20',
    trend: '-2.4%',
    trendLabel: 'vs last month',
  },
];

const AGENT_NAV = [
  { label: 'Dashboard', icon: 'dashboard', active: true },
  { label: 'My Clients', icon: 'group' },
  { label: 'Claims', icon: 'description' },
  { label: 'Commission', icon: 'payments' },
  { label: 'Policies', icon: 'policy' },
  { label: 'Settings', icon: 'settings' },
];

export default function AgentPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthContext();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] min-h-screen flex font-['Work_Sans']">
      {/* Agent Sidebar */}
      <aside className="fixed left-0 top-0 h-screen flex flex-col z-40 bg-[#1a365d] text-white font-['Be_Vietnam_Pro'] text-sm shadow-xl border-r border-white/10 w-64 hidden md:flex">
        {/* Brand */}
        <div className="flex items-center px-6 py-6 border-b border-white/10 gap-3">
          <div className="w-10 h-10 rounded-full bg-[#fea619] flex items-center justify-center">
            <span className="material-symbols-outlined icon-fill text-white text-xl">
              support_agent
            </span>
          </div>
          <div>
            <div className="text-xl font-black text-white leading-tight">Agent Console</div>
            <div className="text-xs text-slate-300">Insurance Management</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-6 flex flex-col gap-1 overflow-y-auto">
          {AGENT_NAV.map(({ label, icon, active }) => (
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
            Download Report
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

      {/* Main content */}
      <main className="flex-1 ml-0 md:ml-64 p-[24px] pt-8">
        {/* Header */}
        <div className="mb-[48px] flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h1 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#1a365d] mb-2">
              Agent Dashboard
            </h1>
            <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
              Welcome back,{' '}
              <span className="font-semibold text-[#1a365d]">{user?.email || 'Agent'}</span>. Here
              is your daily summary.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-[#e0e3e5] rounded-full p-2 text-[#1a365d]">
              <span className="material-symbols-outlined">calendar_today</span>
            </div>
            <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#191c1e]">
              {new Date().toLocaleDateString('en-IN', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
              })}
            </span>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[24px] mb-[48px]">
          {AGENT_METRICS.map((m) => (
            <MetricCard key={m.label} {...m} />
          ))}
        </div>

        {/* Top plans table */}
        <TopPlansTable />
      </main>
    </div>
  );
}
