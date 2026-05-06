/**
 * PolicyResultsPage  (/policy/:category)
 *
 * Insurance policy search results — the step that follows the Products dashboard
 * when a user clicks on a specific domain (Health, Motor, Agriculture, Property).
 *
 * Inherited state (via React Router location.state from ProductsPage):
 *   - chatContext     : { policyType, policyNumber, insuredAmount }
 *   - recommendation  : string | null
 *   - messages        : ChatMessage[]
 *
 * URL param:
 *   - category : 'health' | 'motor' | 'agriculture' | 'property'
 *
 * Features:
 *   - Category-specific filter sidebar (fully client-side)
 *   - Policy cards with Buy Now (mock 900ms delay) + Compare toggle
 *   - Sticky comparison bar when ≥1 policy selected
 *   - Floating chat FAB
 *   - Context banner when arriving from the Products flow
 */

import { useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import TopAppBar from '../components/dashboard/TopAppBar';
import PolicyFilters from '../components/policy/PolicyFilters';
import PolicyCard from '../components/policy/PolicyCard';
import MotorPolicyCard from '../components/policy/MotorPolicyCard';
import ComparisonBar from '../components/policy/ComparisonBar';
import CompareDrawer from '../components/policy/CompareDrawer';
import CompareModal from '../components/policy/CompareModal';
import { POLICY_CATEGORIES } from '../data/policyData';

/** No longer needed — PDF is generated client-side, no mock purchase flow. */

export default function PolicyResultsPage() {
  const { category: categorySlug } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // ── Inherited state from ProductsPage ─────────────────────────────────────
  const {
    chatContext = null,
    recommendation = null,
    messages = [],
  } = location.state || {};

  // ── Category data ─────────────────────────────────────────────────────────
  const category = POLICY_CATEGORIES[categorySlug] ?? POLICY_CATEGORIES.health;

  // ── Local state ───────────────────────────────────────────────────────────
  const [selected, setSelected] = useState([]);   // policies in comparison tray
  const [showDrawer, setShowDrawer] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleCompare = (policy) => {
    setSelected((prev) => {
      const exists = prev.find((p) => p.id === policy.id);
      if (exists) return prev.filter((p) => p.id !== policy.id);
      if (prev.length >= 3) return prev; // max 3
      return [...prev, policy];
    });
  };

  // Motor list rows use the same selected state — look up full policy object by id
  const handleMotorListCompare = (listPolicy) => {
    // Build a minimal comparable object from list data
    const comparable = {
      id: listPolicy.id,
      name: listPolicy.logoText ?? `Policy ${listPolicy.id}`,
      logo: listPolicy.logo ?? null,
      price: listPolicy.premium,
      features: [
        `IDV: ${listPolicy.idv}`,
        `Claims Settled: ${listPolicy.claimsSettled}`,
        listPolicy.keyFeatures,
      ],
    };
    handleCompare(comparable);
  };

  const handleOpenDrawer = () => setShowDrawer(true);
  const handleDrawerConfirm = () => { setShowDrawer(false); setShowModal(true); };
  const handleDrawerCancel = () => setShowDrawer(false);
  const handleModalClose = () => setShowModal(false);

  const isMotor = categorySlug === 'motor';

  return (
    <div className="bg-[#f8fafc] text-[#191c1e] min-h-screen flex flex-col">
      <TopAppBar activePage="Product" />

      {/* Context banner */}
      {chatContext && (
        <div className="fixed top-16 left-0 right-0 z-40 bg-[#ffddb8] border-b border-[#fea619]/40">
          <div className="max-w-[1280px] mx-auto px-[24px] py-[10px] flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-[12px]">
              <span className="material-symbols-outlined text-[#855300]" style={{ fontVariationSettings: "'FILL' 1" }}>info</span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-[#653e00]">
                {recommendation
                  ? <>Recommended: <span className="font-bold">{recommendation}</span> · Browsing {category.label}</>
                  : <>Browsing {category.label} — {chatContext.policyType} · {chatContext.policyNumber}</>
                }
              </span>
            </div>
            <button
              onClick={() => navigate('/products', { state: { chatContext, messages, recommendation } })}
              className="flex items-center gap-1 font-['Work_Sans'] text-[12px] font-semibold text-[#653e00] hover:underline"
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              Back to Products
            </button>
          </div>
        </div>
      )}

      <main className={`flex-grow flex ${chatContext ? 'pt-[104px]' : 'pt-16'}`}>
        <div className="max-w-[1280px] mx-auto flex w-full">

          {/* Filters sidebar */}
          <PolicyFilters category={category} onReset={() => {}} />

          {/* Main content */}
          <section className="flex-1 p-[24px] bg-[#f7f9fb]">

            {/* Header */}
            <div className="mb-[48px] flex flex-col md:flex-row md:items-end justify-between gap-[24px]">
              <div>
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 font-['Work_Sans'] text-[12px] text-[#43474e] mb-2">
                  <button onClick={() => navigate('/products', { state: { chatContext, messages, recommendation } })}
                    className="hover:text-[#002045] transition-colors">Products</button>
                  <span className="material-symbols-outlined text-xs">chevron_right</span>
                  <span className="text-[#002045] font-bold">{category.label}</span>
                </div>
                <h1 className="font-['Be_Vietnam_Pro'] text-[32px] font-semibold text-[#002045]">
                  {isMotor ? `Car Insurance for ${chatContext?.policyNumber ?? 'Your Vehicle'}` : `Best ${category.label} Plans for You`}
                </h1>
                <p className="font-['Work_Sans'] text-[18px] text-[#43474e]">{category.subtitle}</p>
              </div>

              {/* Motor IDV chip */}
              {isMotor && category.vehicleInfo && (
                <div className="bg-[#e6e8ea] px-[24px] py-[12px] rounded-xl border border-[#c4c6cf] flex items-center gap-[24px]">
                  <div className="flex flex-col">
                    <span className="font-['Work_Sans'] text-[12px] text-[#43474e]">{category.vehicleInfo.label}</span>
                    <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045]">{category.vehicleInfo.value}</span>
                  </div>
                  <button className="font-['Work_Sans'] font-bold text-[14px] text-[#855300] hover:underline">Edit Info</button>
                </div>
              )}
            </div>

            {/* ── Motor layout: bento featured + list ── */}
            {isMotor ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-[24px] mb-[48px]">
                  {(category.featuredPolicies || []).map((p) => (
                    <MotorPolicyCard key={p.id} policy={p} />
                  ))}
                </div>

                <div className="space-y-[12px]">
                  {(category.listPolicies || []).map((p) => {
                    const isMotorSelected = !!selected.find((s) => s.id === p.id);
                    return (
                      <div key={p.id} className={`bg-white p-[8px] px-[24px] rounded-xl shadow-sm flex flex-col md:flex-row items-center gap-[24px] border transition-all ${isMotorSelected ? 'border-[#fea619]' : 'border-[#c4c6cf] hover:border-[#002045]/30'}`}>
                        {p.logo
                          ? <img src={p.logo} alt="" className="h-12 w-24 object-contain" />
                          : <div className="h-12 w-24 bg-[#eceef0] flex items-center justify-center rounded font-['Work_Sans'] text-[12px] font-bold text-[#43474e]">{p.logoText}</div>
                        }
                        <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-[12px] items-center">
                          {[['IDV', p.idv], ['Claims Settled', p.claimsSettled], ['Key Features', p.keyFeatures], ['Premium', p.premium]].map(([label, val]) => (
                            <div key={label} className="flex flex-col">
                              <span className="font-['Work_Sans'] text-[12px] text-[#43474e]">{label}</span>
                              <span className={`font-['Work_Sans'] font-semibold text-[14px] text-[#002045] ${label === 'Key Features' ? 'truncate text-[12px]' : ''}`}>{val}</span>
                            </div>
                          ))}
                        </div>
                        <div className="flex items-center gap-[12px] w-full md:w-auto">
                          <button onClick={() => handleMotorListCompare(p)} className="flex items-center gap-2 cursor-pointer">
                            <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${isMotorSelected ? 'bg-[#002045] border-[#002045]' : 'border-[#74777f]'}`}>
                              {isMotorSelected && <span className="material-symbols-outlined text-white text-[12px]">check</span>}
                            </div>
                            <span className="font-['Work_Sans'] text-[12px] font-bold text-[#43474e]">Compare</span>
                          </button>
                          <button className="flex-1 md:flex-none border-2 border-[#002045] text-[#002045] px-4 py-2 rounded-lg font-['Work_Sans'] font-bold text-[14px] hover:bg-[#002045]/5 transition-all">
                            Select
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              /* ── Standard layout: stacked policy cards ── */
              <div className="grid grid-cols-1 gap-[24px]">
                {(category.policies || []).map((policy, idx) => (
                  <>
                    <PolicyCard
                      key={policy.id}
                      policy={policy}
                      onCompare={handleCompare}
                      isSelected={!!selected.find((p) => p.id === policy.id)}
                      category={categorySlug}
                    />
                    {/* Promo banner after 2nd card (health only) */}
                    {categorySlug === 'health' && idx === 1 && (
                      <div key="promo" className="relative h-40 rounded-xl overflow-hidden group">
                        <img
                          src="https://lh3.googleusercontent.com/aida/ADBb0ug1gFDjUFaDRrMgfNIy5C-gyr3HWWt2mro_E8ujabsBrtNKv-qq7_mpJmMkReqmP_CaS2GwuJVYWmuNbkayZrG4ziFXdiW3R79nR1odyM4XhEwGllcfXNJwmApFxmXQNc_R5AtEZIwEba29pys_W30nYw0ec1OptQepHMyLsTJhOgfBJ_mrl_yDxCnmeJ8k3zLP-PzDfZ2xrXJH1ao-AgIhXbp0o3dl4Kasq4Z-Z8goGTlcMSiPAj9OiCuS0rmqau_sv2fBpN7bxUo"
                          alt=""
                          className="absolute inset-0 w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-[#002045]/60 flex items-center justify-between px-[48px]">
                          <div className="text-white max-w-md">
                            <h4 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold">Family Floater Discount</h4>
                            <p className="font-['Work_Sans'] text-[16px]">Get up to 15% off when you add more than 3 members to your health plan.</p>
                          </div>
                          <button className="bg-[#fea619] text-[#684000] px-8 py-3 rounded-full font-['Work_Sans'] font-bold hover:scale-105 transition-all">
                            Explore Plans
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                ))}
              </div>
            )}

            {/* Spacer for sticky bar */}
            <div className="h-32" />
          </section>
        </div>
      </main>

      {/* Sticky comparison bar */}
      <ComparisonBar
        selected={selected}
        onRemove={(id) => setSelected((p) => p.filter((x) => x.id !== id))}
        onClear={() => setSelected([])}
        onCompare={handleOpenDrawer}
      />

      {/* Step 1 — Review list drawer */}
      {showDrawer && (
        <CompareDrawer
          selected={selected}
          onRemove={(id) => setSelected((p) => p.filter((x) => x.id !== id))}
          onConfirm={handleDrawerConfirm}
          onCancel={handleDrawerCancel}
        />
      )}

      {/* Step 2 — Full comparison table */}
      {showModal && (
        <CompareModal
          policies={selected}
          onClose={handleModalClose}
          category={categorySlug}
        />
      )}

      {/* Floating chat FAB */}
      <div className="fixed bottom-24 right-8 z-[60]">
        <button
          onClick={() => navigate('/chatbot', { state: { chatContext, messages } })}
          className="bg-[#002045] text-white w-14 h-14 rounded-full shadow-xl flex items-center justify-center hover:bg-[#1a365d] transition-all group relative"
        >
          <span className="material-symbols-outlined text-[28px]" style={{ fontVariationSettings: "'FILL' 1" }}>chat_bubble</span>
          <div className="absolute right-16 bg-white text-[#002045] px-4 py-2 rounded-lg shadow-lg border border-[#c4c6cf] opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            <p className="font-['Work_Sans'] font-semibold text-[14px]">Need help choosing a plan?</p>
          </div>
          {/* Ping badge */}
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#855300] opacity-75" />
            <span className="relative inline-flex rounded-full h-4 w-4 bg-[#855300]" />
          </span>
        </button>
      </div>
    </div>
  );
}
