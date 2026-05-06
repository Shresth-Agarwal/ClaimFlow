import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import Sidebar from '../components/admin/Sidebar';
import MetricCard from '../components/admin/MetricCard';
import TopPlansTable from '../components/admin/TopPlansTable';

const METRICS = [
  {
    label: 'Total Users',
    value: '45,231',
    icon: 'group',
    iconBg: 'bg-[#d6e3ff]',
    iconColor: 'text-[#002045]',
    blobBg: 'bg-[#d6e3ff]/20',
    trend: '+12.5%',
    trendLabel: 'vs last month',
  },
  {
    label: 'Total Policies',
    value: '12,845',
    icon: 'policy',
    iconBg: 'bg-[#d2e4ff]',
    iconColor: 'text-[#00213e]',
    blobBg: 'bg-[#d2e4ff]/20',
    trend: '+8.2%',
    trendLabel: 'vs last month',
  },
  {
    label: 'Total Revenue',
    value: '₹2.4M',
    icon: 'payments',
    iconBg: 'bg-[#ffddb8]',
    iconColor: 'text-[#855300]',
    blobBg: 'bg-[#ffddb8]/20',
    trend: '+24.1%',
    trendLabel: 'vs last month',
  },
  {
    label: 'Active Claims',
    value: '843',
    icon: 'assignment_late',
    iconBg: 'bg-[#ffdad6]',
    iconColor: 'text-[#ba1a1a]',
    blobBg: 'bg-[#ffdad6]/20',
    trend: '-2.4%',
    trendLabel: 'vs last month',
  },
];

export default function AdminPage() {
  const navigate = useNavigate();
  const { user } = useAuthContext();

  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] min-h-screen flex font-['Work_Sans']">
      <Sidebar />

      {/* Main content — offset by sidebar width on md+ */}
      <main className="flex-1 ml-0 md:ml-64 p-[24px] pt-8">
        {/* Header */}
        <div className="mb-[48px] flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h1 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#1a365d] mb-2">
              Dashboard Overview
            </h1>
            <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">
              Welcome back,{' '}
              <span className="font-semibold text-[#1a365d]">
                {user?.email || 'Admin'}
              </span>
              . Here is the daily summary of operations.
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

        {/* Metrics grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[24px] mb-[48px]">
          {METRICS.map((m) => (
            <MetricCard key={m.label} {...m} />
          ))}
        </div>

        {/* Top plans table */}
        <TopPlansTable />
      </main>
    </div>
  );
}
