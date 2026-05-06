import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { useProfile } from '../hooks/useProfile';
import { verifyAgent } from '../services/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuthContext();
  const { profile, orders, loading, error } = useProfile();

  // Optimistic UI state for agent verification
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(null);
  const [optimisticVerified, setOptimisticVerified] = useState(null);

  const isVerified =
    optimisticVerified !== null ? optimisticVerified : profile?.verified;

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleVerify = async () => {
    // Optimistic update — flip to verified immediately
    setOptimisticVerified(true);
    setVerifying(true);
    setVerifyError(null);
    try {
      await verifyAgent(token);
    } catch (err) {
      // Rollback on failure
      setOptimisticVerified(false);
      setVerifyError(err.message);
    } finally {
      setVerifying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f7f9fb]">
        <div className="flex flex-col items-center gap-4 text-[#43474e]">
          <span className="material-symbols-outlined text-5xl animate-spin text-[#002045]">
            progress_activity
          </span>
          <p className="font-['Work_Sans'] text-[16px]">Loading your dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f7f9fb] antialiased">
      {/* Top nav */}
      <header className="bg-white border-b border-[#e0e3e5] px-[24px] py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[#002045]">
          <span className="material-symbols-outlined symbol-fill text-2xl">shield_person</span>
          <span className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold tracking-tight">
            ClaimFlow
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-['Work_Sans'] text-[14px] text-[#43474e]">
            {profile?.username || user?.username || user?.email}
          </span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-semibold bg-[#d6e3ff] text-[#002045] capitalize">
            {user?.role}
          </span>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 text-[14px] font-['Work_Sans'] text-[#43474e] hover:text-[#ba1a1a] transition-colors"
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

        {/* Profile card */}
        <section className="bg-white rounded-xl border border-[#e0e3e5] p-[24px] mb-6 shadow-[0px_4px_20px_rgba(26,54,93,0.05)]">
          <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045] mb-4">
            Profile
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

        {/* Agent verification section */}
        {user?.role === 'agent' && (
          <section className="bg-white rounded-xl border border-[#e0e3e5] p-[24px] mb-6 shadow-[0px_4px_20px_rgba(26,54,93,0.05)]">
            <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045] mb-2">
              Verification
            </h2>
            <p className="font-['Work_Sans'] text-[16px] text-[#43474e] mb-4">
              Status:{' '}
              <span
                className={`font-semibold ${
                  isVerified ? 'text-green-600' : 'text-[#855300]'
                }`}
              >
                {isVerified ? 'Verified ✓' : 'Not Verified'}
              </span>
            </p>
            {verifyError && (
              <p className="text-[14px] text-[#ba1a1a] mb-3">{verifyError}</p>
            )}
            {!isVerified && (
              <button
                onClick={handleVerify}
                disabled={verifying}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#fea619] text-[#684000] font-['Work_Sans'] text-[14px] font-semibold rounded-lg hover:bg-[#855300] hover:text-white transition-all disabled:opacity-60"
              >
                {verifying ? (
                  <>
                    <span className="material-symbols-outlined text-[18px] animate-spin">
                      progress_activity
                    </span>
                    Verifying…
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">verified</span>
                    Verify My Account
                  </>
                )}
              </button>
            )}
          </section>
        )}

        {/* Orders section — user role only */}
        {user?.role === 'user' && (
          <section className="bg-white rounded-xl border border-[#e0e3e5] p-[24px] shadow-[0px_4px_20px_rgba(26,54,93,0.05)]">
            <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045] mb-4">
              Order History
            </h2>
            {orders.length === 0 ? (
              <p className="font-['Work_Sans'] text-[16px] text-[#43474e]">
                No orders found.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left font-['Work_Sans'] text-[14px]">
                  <thead>
                    <tr className="border-b border-[#e0e3e5]">
                      {Object.keys(orders[0]).map((col) => (
                        <th
                          key={col}
                          className="pb-2 pr-4 font-semibold text-[#74777f] uppercase tracking-wider text-[12px]"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order, i) => (
                      <tr key={i} className="border-b border-[#f2f4f6] hover:bg-[#f7f9fb]">
                        {Object.values(order).map((val, j) => (
                          <td key={j} className="py-3 pr-4 text-[#191c1e]">
                            {String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
