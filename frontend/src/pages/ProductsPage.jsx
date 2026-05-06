/**
 * ProductsPage  (/products)
 *
 * Comprehensive Insurance Product Overview — the step that follows the
 * Interactions (ChatBot) dashboard.
 *
 * Inherited state (via React Router location.state):
 *   - chatContext  : { policyType, policyNumber, insuredAmount } — claim context from chatbot
 *   - messages     : ChatMessage[]  — the full conversation history
 *   - recommendation: string | null — AI-suggested plan name (optional)
 */

import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import TopAppBar from '../components/dashboard/TopAppBar';
import ProductsHero from '../components/products/ProductsHero';
import InsuranceDomains from '../components/products/InsuranceDomains';
import WhyClaimFlow from '../components/products/WhyClaimFlow';
import ProductsFooter from '../components/products/ProductsFooter';
import { getProductRecommendation } from '../services/api';

export default function ProductsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuthContext();

  // ── Inherited state from ChatbotPage ──────────────────────────────────────
  const {
    chatContext = null,
    messages = [],
    recommendation: inheritedRec = null,
  } = location.state || {};

  // ── Local state ───────────────────────────────────────────────────────────
  const [recommendation, setRecommendation] = useState(inheritedRec);
  const [isLoadingRec, setIsLoadingRec] = useState(false);
  const [recError, setRecError] = useState(null);

  // ── Fetch AI recommendation if not already provided ───────────────────────
  useEffect(() => {
    if (recommendation || !chatContext) return;

    const fetchRec = async () => {
      setIsLoadingRec(true);
      setRecError(null);
      try {
        const data = await getProductRecommendation(
          {
            policy_type: chatContext.policyType,
            policy_number: chatContext.policyNumber,
            insured_amount: chatContext.insuredAmount,
            message_count: messages.length,
          },
          token
        );
        setRecommendation(data.recommended_plan || null);
      } catch (err) {
        setRecError(err.message);
      } finally {
        setIsLoadingRec(false);
      }
    };

    fetchRec();
  }, [chatContext, messages, recommendation, token]);

  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] min-h-screen flex flex-col">
      <TopAppBar activePage="Product" />

      {/* Context banner — shown when arriving from chatbot with claim data */}
      {chatContext && (
        <div className="fixed top-16 left-0 right-0 z-40 bg-[#ffddb8] border-b border-[#fea619]/40">
          <div className="max-w-[1280px] mx-auto px-[24px] py-[10px] flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-[12px]">
              <span
                className="material-symbols-outlined text-[#855300]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                info
              </span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-[#653e00]">
                Continuing from your claim consultation —{' '}
                <span className="font-bold">{chatContext.policyType}</span> ·{' '}
                {chatContext.policyNumber}
              </span>
            </div>
            <button
              onClick={() => navigate('/chatbot', { state: { chatContext, messages } })}
              className="flex items-center gap-1 font-['Work_Sans'] text-[12px] font-semibold text-[#653e00] hover:underline"
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              Back to Chat
            </button>
          </div>
        </div>
      )}

      <main className={`flex-grow flex flex-col ${chatContext ? 'pt-[104px]' : 'pt-16'}`}>
        <ProductsHero />

        {/* Recommendation loading / error feedback */}
        {isLoadingRec && (
          <div className="max-w-[1280px] mx-auto px-[24px] pt-[24px]">
            <div className="flex items-center gap-3 text-[#43474e] font-['Work_Sans'] text-[14px]">
              <svg className="animate-spin h-4 w-4 text-[#fea619]" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Fetching AI recommendation for your profile…
            </div>
          </div>
        )}
        {recError && (
          <div className="max-w-[1280px] mx-auto px-[24px] pt-[24px]">
            <div className="flex items-center gap-2 text-[#ba1a1a] font-['Work_Sans'] text-[14px] bg-[#ffdad6] px-[16px] py-[10px] rounded-lg">
              <span className="material-symbols-outlined text-[18px]">error</span>
              Could not load recommendation: {recError}
            </div>
          </div>
        )}

        <InsuranceDomains recommendation={recommendation} chatContext={chatContext} messages={messages} />
        <WhyClaimFlow />

        {/* ── Proceed to Advisors banner ── */}
        <div className="max-w-[1280px] mx-auto px-[24px] py-[48px] w-full">
          <div className="bg-white border border-[#fea619]/40 rounded-2xl shadow-md px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span
                className="material-symbols-outlined text-[#fea619] text-[32px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
              <div>
                <p className="font-['Be_Vietnam_Pro'] font-semibold text-[16px] text-[#002045]">
                  Ready to connect with an expert?
                </p>
                <p className="font-['Work_Sans'] text-[13px] text-[#43474e]">
                  Browse our network of certified advisors and book a consultation.
                </p>
              </div>
            </div>
            <button
              onClick={() =>
                navigate('/advisors', {
                  state: { chatContext, messages, recommendation },
                })
              }
              className="flex-shrink-0 flex items-center gap-2 bg-[#002045] text-white px-6 py-3 rounded-xl font-['Work_Sans'] font-semibold text-[14px] hover:bg-[#1a365d] active:scale-95 transition-all"
            >
              Find an Advisor
              <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </main>

      <ProductsFooter />

      {/* Floating chat button — from updated HTML */}
      <button
        onClick={() => navigate('/chatbot')}
        className="fixed bottom-[24px] right-[24px] w-14 h-14 bg-[#fea619] text-[#684000] rounded-full shadow-[0px_10px_30px_rgba(26,54,93,0.12)] flex items-center justify-center z-50 hover:scale-110 transition-transform"
        aria-label="Open chat"
      >
        <span className="material-symbols-outlined text-[24px]">chat</span>
      </button>
    </div>
  );
}
