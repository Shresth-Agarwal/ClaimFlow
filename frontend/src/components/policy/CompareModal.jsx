/**
 * CompareModal
 * Full-screen side-by-side comparison table.
 * Colour palette: ClaimFlow standard.
 *   Header  : #002045 bg, #fea619 accent, white text
 *   Rows    : white / #f2f4f6 alternating
 *   Labels  : #1a365d sidebar
 *   Footer  : #1a365d bg, white text
 *   CTA     : #fea619 bg, #684000 text (Get Document)
 */

import { useState } from 'react';
import { generatePolicyPdf } from '../../utils/generatePolicyPdf';
import ClaimFlowLogo from '../ui/ClaimFlowLogo';

const COMPARE_ROWS = [
  { label: 'Annual Premium', key: (p) => p.price ?? p.premium ?? '—' },
  { label: 'Original Price', key: (p) => p.originalPrice ?? '—' },
  { label: 'Savings',        key: (p) => p.saving ?? '—' },
  { label: 'Rating',         key: (p) => p.rating ? `${p.rating} ★ (${p.reviews} reviews)` : '—' },
  { label: 'Key Features',   key: (p) => (p.features ?? []).join(', ') || '—' },
  { label: 'Not Covered',    key: (p) => (p.missingFeatures ?? []).join(', ') || 'None' },
  { label: 'Highlight',      key: (p) => p.highlight ?? '—' },
  { label: 'Note',           key: (p) => p.note ?? '—' },
];

export default function CompareModal({ policies, onClose, category }) {
  const [generatingId, setGeneratingId] = useState(null);

  if (!policies || policies.length === 0) return null;

  const handleGetDocument = (policy) => {
    setGeneratingId(policy.id);
    setTimeout(() => {
      generatePolicyPdf(policy, category ?? 'insurance');
      setGeneratingId(null);
    }, 100);
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[65] bg-[#002045]/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="fixed inset-4 md:inset-8 z-[70] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-[#c4c6cf]/30">

        {/* ── Dark header ── */}
        <div className="bg-[#002045] flex items-center justify-between px-6 py-4 flex-shrink-0">
          <div className="flex items-center gap-4">
            <ClaimFlowLogo variant="icon" height={32} />
            <div>
              <h2 className="font-['Be_Vietnam_Pro'] text-[20px] font-bold text-white">
                Policy Comparison
              </h2>
              <p className="font-['Work_Sans'] text-[12px] text-[#86a0cd] mt-0.5">
                Comparing {policies.length} {policies.length === 1 ? 'policy' : 'policies'} side-by-side
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white"
            aria-label="Close comparison"
          >
            <span className="material-symbols-outlined text-[22px]">close</span>
          </button>
        </div>

        {/* ── Scrollable table ── */}
        <div className="flex-1 overflow-auto bg-white">
          <table className="w-full border-collapse min-w-[600px]">

            {/* Sticky policy header row */}
            <thead className="sticky top-0 z-10">
              <tr className="bg-[#1a365d]">
                {/* Row-label column header */}
                <th className="w-44 p-4 text-left border-b border-[#002045] border-r border-r-white/10" />

                {/* One column per policy */}
                {policies.map((p) => (
                  <th key={p.id} className="p-4 border-b border-[#002045] border-r border-r-white/10 last:border-r-0 min-w-[200px]">
                    <div className="flex flex-col items-center gap-2">
                      {p.logo && (
                        <div className="bg-white rounded-lg p-1.5 border border-white/20">
                          <img
                            src={p.logo}
                            alt={p.name}
                            className="h-9 w-20 object-contain"
                          />
                        </div>
                      )}
                      <span className="font-['Be_Vietnam_Pro'] font-bold text-[14px] text-white text-center leading-tight">
                        {p.name}
                      </span>
                      {p.badge && (
                        <span className="bg-[#fea619] text-[#684000] px-2 py-0.5 rounded-full font-['Work_Sans'] text-[11px] font-bold">
                          {p.badge}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {COMPARE_ROWS.map(({ label, key }, rowIdx) => {
                const isEven = rowIdx % 2 === 0;
                return (
                  <tr key={label} className={isEven ? 'bg-white' : 'bg-[#f2f4f6]'}>

                    {/* Row label cell */}
                    <td className="p-4 font-['Work_Sans'] text-[12px] font-bold uppercase tracking-wider text-[#43474e] border-r border-[#eceef0] align-top bg-[#f7f9fb]">
                      {label}
                    </td>

                    {/* Value cells */}
                    {policies.map((p) => {
                      const val = key(p);
                      const isEmpty = val === '—' || val === 'None';
                      return (
                        <td
                          key={p.id}
                          className="p-4 font-['Work_Sans'] text-[14px] text-[#191c1e] align-top border-r border-[#eceef0] last:border-r-0"
                        >
                          {label === 'Key Features' ? (
                            <ul className="space-y-1.5">
                              {(p.features ?? []).map((f) => (
                                <li key={f} className="flex items-start gap-1.5">
                                  <span
                                    className="material-symbols-outlined text-[#fea619] text-[15px] mt-0.5 flex-shrink-0"
                                    style={{ fontVariationSettings: "'FILL' 1" }}
                                  >
                                    check_circle
                                  </span>
                                  <span className="text-[#191c1e]">{f}</span>
                                </li>
                              ))}
                            </ul>
                          ) : label === 'Not Covered' ? (
                            <span className={isEmpty ? 'text-[#c4c6cf]' : 'text-[#ba1a1a] line-through'}>
                              {val}
                            </span>
                          ) : label === 'Annual Premium' ? (
                            <span className="font-['Be_Vietnam_Pro'] text-[20px] font-bold text-[#002045]">
                              {val}
                            </span>
                          ) : label === 'Savings' && !isEmpty ? (
                            <span className="inline-block bg-[#ffddb8] text-[#653e00] px-2 py-0.5 rounded-full font-['Work_Sans'] font-bold text-[13px]">
                              {val}
                            </span>
                          ) : label === 'Rating' && !isEmpty ? (
                            <span className="text-[#855300] font-semibold">{val}</span>
                          ) : label === 'Highlight' && !isEmpty ? (
                            <span className="italic text-[#002045]">"{val}"</span>
                          ) : (
                            <span className={isEmpty ? 'text-[#c4c6cf]' : 'text-[#43474e]'}>{val}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}

              {/* ── Get Document row ── */}
              <tr className="bg-[#eceef0]">
                <td className="p-4 font-['Work_Sans'] text-[12px] font-bold uppercase tracking-wider text-[#43474e] border-r border-[#c4c6cf]/40 bg-[#f7f9fb]" />
                {policies.map((p) => (
                  <td key={p.id} className="p-4 border-r border-[#c4c6cf]/40 last:border-r-0">
                    <button
                      onClick={() => handleGetDocument(p)}
                      disabled={generatingId === p.id}
                      className="w-full flex items-center justify-center gap-2 bg-[#fea619] text-[#684000] py-2.5 rounded-lg font-['Work_Sans'] font-bold text-[14px] hover:opacity-90 active:scale-95 transition-all disabled:opacity-60 shadow-sm"
                    >
                      {generatingId === p.id ? (
                        <>
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                          Preparing…
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-[16px]">download</span>
                          Get Document
                        </>
                      )}
                    </button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* ── Dark footer ── */}
        <div className="bg-[#1a365d] px-6 py-3 flex items-center justify-between flex-shrink-0">
          <ClaimFlowLogo variant="compact" height={22} className="opacity-70" />
          <p className="font-['Work_Sans'] text-[12px] text-[#86a0cd]">
            Prices are indicative. Final premium subject to underwriting approval.
          </p>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg border border-white/20 text-white bg-white/10 font-['Work_Sans'] font-semibold text-[13px] hover:bg-white/20 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </>
  );
}
