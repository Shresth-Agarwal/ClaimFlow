/**
 * PolicyCard
 * Standard policy card — Health, Agriculture, Property results.
 * "Get Document" downloads a PDF policy quote generated in the browser.
 */

import { useState } from 'react';
import { generatePolicyPdf } from '../../utils/generatePolicyPdf';

export default function PolicyCard({ policy, onCompare, isSelected, category }) {
  const [isGenerating, setIsGenerating] = useState(false);

  const { name, logo, badge, rating, reviews, features, missingFeatures,
          highlight, highlightVariant, originalPrice, price, saving, note } = policy;

  const handleGetDocument = () => {
    setIsGenerating(true);
    // generatePolicyPdf is synchronous (opens print dialog) — reset state after brief delay
    setTimeout(() => {
      generatePolicyPdf(policy, category ?? 'insurance');
      setIsGenerating(false);
    }, 100);
  };

  return (
    <div
      className={`bg-white rounded-xl p-[24px] border transition-all relative overflow-hidden group
        shadow-[0px_4px_20px_rgba(26,54,93,0.05)] hover:shadow-[0px_10px_30px_rgba(26,54,93,0.12)]
        ${isSelected ? 'border-[#fea619]' : 'border-transparent hover:border-[#855300]'}`}
    >
      {/* Badge */}
      {badge && (
        <div className="absolute top-0 right-0 bg-[#855300] text-white px-4 py-1 rounded-bl-xl font-['Work_Sans'] font-bold text-[14px]">
          {badge}
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-[24px]">
        {/* Left — logo + name + rating */}
        <div className="md:w-1/4">
          <img src={logo} alt={name} className="w-32 h-auto mb-[12px] rounded-lg border border-[#c4c6cf] p-2" />
          <h3 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045]">{name}</h3>
          {rating && (
            <div className="flex items-center gap-1 text-[#855300] mt-1">
              <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
              <span className="font-['Work_Sans'] font-semibold text-[14px]">{rating} ({reviews} reviews)</span>
            </div>
          )}
        </div>

        {/* Middle — features + highlight */}
        <div className="md:w-2/4 flex flex-col gap-[12px]">
          <div className="grid grid-cols-2 gap-4">
            {(features || []).map((f) => (
              <div key={f} className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#58a2f0]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                <span className="font-['Work_Sans'] text-[16px]">{f}</span>
              </div>
            ))}
            {(missingFeatures || []).map((f) => (
              <div key={f} className="flex items-center gap-2 opacity-50">
                <span className="material-symbols-outlined text-[18px]">cancel</span>
                <span className="font-['Work_Sans'] text-[16px] line-through">{f}</span>
              </div>
            ))}
          </div>

          {highlight && (
            <div className={`mt-4 p-3 rounded-lg ${
              highlightVariant === 'premium'
                ? 'bg-[#003762]/10 border border-[#003762]/20'
                : 'bg-[#f2f4f6]'
            }`}>
              <p className={`font-['Work_Sans'] text-[12px] font-bold uppercase tracking-wider mb-1 ${
                highlightVariant === 'premium' ? 'text-[#58a2f0]' : 'text-[#43474e]'
              }`}>
                {highlightVariant === 'premium' ? 'Premium Service' : 'Highlight Feature'}
              </p>
              <p className="font-['Work_Sans'] text-[16px] text-[#002045] font-medium italic">"{highlight}"</p>
            </div>
          )}
        </div>

        {/* Right — price + actions */}
        <div className="md:w-1/4 flex flex-col items-end justify-between border-l border-[#c4c6cf] pl-[24px]">
          <div className="text-right">
            {originalPrice && (
              <p className="font-['Work_Sans'] text-[12px] text-[#43474e] line-through">{originalPrice}</p>
            )}
            <p className="font-['Be_Vietnam_Pro'] text-[32px] font-semibold text-[#002045]">
              {price} <span className="font-['Work_Sans'] text-[14px] font-normal">/yr</span>
            </p>
            {saving && <p className="font-['Work_Sans'] text-[12px] text-[#855300] font-bold">{saving}</p>}
            {note && <p className="font-['Work_Sans'] text-[12px] text-[#43474e]">{note}</p>}
          </div>

          <div className="flex flex-col gap-2 w-full mt-[48px]">
            {/* Get Document button */}
            <button
              onClick={handleGetDocument}
              disabled={isGenerating}
              className="w-full bg-[#002045] text-white py-3 rounded-lg font-['Work_Sans'] font-bold text-[14px] shadow-md hover:bg-[#1a365d] active:scale-95 transition-all disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Preparing…
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  Get Document
                </>
              )}
            </button>

            {/* Compare button */}
            <button
              onClick={() => onCompare(policy)}
              className={`w-full border-2 py-2 rounded-lg font-['Work_Sans'] font-bold text-[14px] transition-all ${
                isSelected
                  ? 'border-[#fea619] text-[#684000] bg-[#ffddb8]'
                  : 'border-[#002045] text-[#002045] hover:bg-[#e6e8ea]'
              }`}
            >
              {isSelected ? '✓ Added' : 'Compare'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
