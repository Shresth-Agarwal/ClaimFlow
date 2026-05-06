import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { useProfile } from '../hooks/useProfile';

export default function AdminPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthContext();
  const { profile, loading, error } = useProfile();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f7f9fb]">
        <div className="flex flex-col items-center gap-4 text-[#43474e]">
          <span className="material-symbols-outlined text-5xl animate-spin text-[#002045]">
            progress_activity
          </span>
          <p className="font-['Work_Sans'] text-[16px]">Loading admin panel…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f7f9fb] antialiased">
      {/* Top nav */}
      <header className="bg-[#002045] px-[24px] py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-white">
          <span className="material-symbols-outlined symbol-fill text-2xl text-[#fea619]">
            shield_person
          </span>
          <span className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold tracking-tight text-white">
            ClaimFlow
          </span>
          <span className="ml-3 inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#fea619] text-[#684000] uppercase tracking-wider">
            Admin
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-['Work_Sans'] text-[14px] text-[#adc7f7]">
            {profile?.username || user?.username || user?.email}
          </span>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 text-[14px] font-['Work_Sans'] text-[#adc7f7] hover:text-white transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-[24px] py-[48px]">
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-[#ffdad6] text-[#93000a] font-['Work_Sans'] text-[14px]">
            {error}
          </div>
        )}

        {/* Welcome banner */}
        <div className="bg-[#002045] rounded-xl p-[32px] mb-6 text-white">
          <h1 className="font-['Be_Vietnam_Pro'] text-[32px] font-semibold mb-2">
            Admin Dashboard
          </h1>
          <p className="font-['Work_Sans'] text-[16px] text-[#adc7f7]">
            Welcome back,{' '}
            <span className="text-white font-semibold">
              {profile?.username || user?.username || 'Admin'}
            </span>
            . You have full administrative access.
          </p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Total Users', icon: 'group', value: '—' },
            { label: 'Active Agents', icon: 'support_agent', value: '—' },
            { label: 'Pending Claims', icon: 'pending_actions', value: '—' },
          ].map(({ label, icon, value }) => (
            <div
              key={label}
              className="bg-white rounded-xl border border-[#e0e3e5] p-[24px] flex items-center gap-4 shadow-[0px_4px_20px_rgba(26,54,93,0.05)]"
            >
              <div className="w-12 h-12 rounded-full bg-[#d6e3ff] flex items-center justify-center">
                <span className="material-symbols-outlined text-[#002045]">{icon}</span>
              </div>
              <div>
                <p className="font-['Work_Sans'] text-[12px] font-semibold uppercase tracking-wider text-[#74777f]">
                  {label}
                </p>
                <p className="font-['Be_Vietnam_Pro'] text-[28px] font-bold text-[#002045]">
                  {value}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Admin profile */}
        <section className="bg-white rounded-xl border border-[#e0e3e5] p-[24px] shadow-[0px_4px_20px_rgba(26,54,93,0.05)]">
          <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045] mb-4">
            Admin Profile
          </h2>
          {profile ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {Object.entries(profile).map(([key, val]) => (
                <div key={key}>
                  <p className="font-['Work_Sans'] text-[12px] font-semibold uppercase tracking-wider text-[#74777f]">
                    {key}
                  </p>
                  <p className="font-['Work_Sans'] text-[16px] text-[#191c1e] mt-0.5">
                    {String(val)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-['Work_Sans'] text-[16px] text-[#43474e]">
              No profile data available.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
