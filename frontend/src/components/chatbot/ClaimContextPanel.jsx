import { useState } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { clearChatSession } from '../../services/api';

// Mock document URLs — in production these come from the claim's S3 URIs
const DOCS = [
  {
    name: 'Policy_Schedule.pdf',
    icon: 'description',
    action: 'download',
    actionIcon: 'download',
    url: null, // replace with real S3 pre-signed URL
    mimeType: 'application/pdf',
  },
  {
    name: 'KYC_Verified.jpg',
    icon: 'verified',
    action: 'view',
    actionIcon: 'visibility',
    url: null,
    mimeType: 'image/jpeg',
  },
];

/**
 * Right-hand panel showing claim context for the active chat session.
 *
 * @param {{
 *   sessionId?: string | null,
 *   onSessionCleared?: () => void
 * }} props
 */
export default function ClaimContextPanel({ sessionId = null, onSessionCleared }) {
  const { token } = useAuthContext();
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState(null);
  const [clearSuccess, setClearSuccess] = useState(false);

  const handleClearSession = async () => {
    if (!sessionId) return;
    if (!window.confirm('Clear all chat history for this session?')) return;

    setClearing(true);
    setClearError(null);
    setClearSuccess(false);

    try {
      await clearChatSession(sessionId, token);
      setClearSuccess(true);
      onSessionCleared?.();
      // Reset success indicator after 2s
      setTimeout(() => setClearSuccess(false), 2000);
    } catch {
      setClearError('Failed to clear session. Please try again.');
    } finally {
      setClearing(false);
    }
  };

  const handleDocumentAction = (doc) => {
    if (!doc.url) {
      // No real URL yet — show a friendly message
      alert(`Document preview is not available in demo mode.\n\nIn production, "${doc.name}" would open from secure cloud storage.`);
      return;
    }

    if (doc.action === 'download') {
      // Trigger browser download
      const a = document.createElement('a');
      a.href = doc.url;
      a.download = doc.name;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.click();
    } else {
      // Open in new tab for viewing
      window.open(doc.url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleViewPolicyDetails = () => {
    // Navigate to the policy details page or open a modal
    // For now, open a new tab to the policy document
    alert('Full policy details will open in a dedicated policy viewer.\n\n(Policy viewer page coming soon — connect to /policy/:id route)');
  };

  return (
    <aside className="w-72 bg-white border-l border-slate-100 p-6 hidden lg:block overflow-y-auto flex-shrink-0">
      <h4 className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045] mb-6 uppercase tracking-wider">
        Claim Context
      </h4>

      <div className="space-y-6">
        {/* Policy type */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="font-['Work_Sans'] text-[12px] text-[#74777f] uppercase tracking-wider">
            Policy Type
          </span>
          <p className="font-['Work_Sans'] font-bold text-[14px] text-[#002045] mt-1">
            Comprehensive Motor
          </p>
          <p className="font-['Work_Sans'] text-[12px] text-[#43474e] mt-0.5">
            Policy: #SRK-294022
          </p>
        </div>

        {/* Insured amount */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="font-['Work_Sans'] text-[12px] text-[#74777f] uppercase tracking-wider">
            Insured Amount
          </span>
          <p className="font-['Work_Sans'] font-bold text-[14px] text-[#002045] mt-1">
            ₹ 8,45,000
          </p>
          <div className="mt-2 w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div className="bg-[#fea619] h-full w-2/3" />
          </div>
          <p className="font-['Work_Sans'] text-[10px] text-[#74777f] mt-2">68% Cover remaining</p>
        </div>

        {/* Session info */}
        {sessionId && (
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <span className="font-['Work_Sans'] text-[12px] text-[#74777f] uppercase tracking-wider">
              Active Session
            </span>
            <p
              className="font-['Work_Sans'] text-[11px] text-[#43474e] mt-1 truncate font-mono"
              title={sessionId}
            >
              {sessionId}
            </p>
          </div>
        )}

        {/* Quick documents */}
        <div>
          <h5 className="font-['Work_Sans'] text-[12px] font-semibold text-[#74777f] mb-3 uppercase tracking-wider">
            Quick Documents
          </h5>
          <div className="space-y-2">
            {DOCS.map((doc) => (
              <button
                key={doc.name}
                onClick={() => handleDocumentAction(doc)}
                title={doc.action === 'download' ? `Download ${doc.name}` : `View ${doc.name}`}
                className="w-full flex items-center justify-between p-2 hover:bg-slate-50 rounded-lg transition-colors border border-transparent hover:border-slate-200 group"
              >
                <span className="flex items-center gap-2 font-['Work_Sans'] text-[12px] font-medium text-[#191c1e]">
                  <span className="material-symbols-outlined text-[#002045] text-[18px]">
                    {doc.icon}
                  </span>
                  {doc.name}
                </span>
                <span className="material-symbols-outlined text-[#74777f] text-[18px] group-hover:text-[#002045] transition-colors">
                  {doc.actionIcon}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="pt-4 space-y-2">
          {/* View Full Policy Details */}
          <button
            onClick={handleViewPolicyDetails}
            className="w-full py-2.5 font-['Work_Sans'] text-[12px] font-semibold border-2 border-[#002045] text-[#002045] rounded-lg hover:bg-[#002045] hover:text-white transition-all"
          >
            View Full Policy Details
          </button>

          {/* Clear session — only shown when a session exists */}
          {sessionId && (
            <button
              onClick={handleClearSession}
              disabled={clearing}
              className="w-full py-2.5 font-['Work_Sans'] text-[12px] font-semibold border border-red-200 text-red-500 rounded-lg hover:bg-red-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
            >
              {clearing ? (
                <>
                  <span className="w-3 h-3 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                  Clearing…
                </>
              ) : clearSuccess ? (
                <>
                  <span className="material-symbols-outlined text-[14px] text-green-500">check_circle</span>
                  <span className="text-green-600">Cleared!</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[14px]">delete_sweep</span>
                  Clear Chat History
                </>
              )}
            </button>
          )}

          {clearError && (
            <p className="font-['Work_Sans'] text-[11px] text-red-500 text-center">{clearError}</p>
          )}
        </div>
      </div>
    </aside>
  );
}
