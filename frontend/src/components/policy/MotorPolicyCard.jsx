/**
 * MotorPolicyCard
 * Featured bento-style card for Motor Insurance results.
 * "Get Document" downloads a PDF policy quote generated in the browser.
 */

import { useState } from 'react';
import { generatePolicyPdf } from '../../utils/generatePolicyPdf';

export default function MotorPolicyCard({ policy }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const { logo, badge, badgeVariant, price, features } = policy;

  const handleGetDocument = () => {
    setIsGenerating(true);
    setTimeout(() => {
      generatePolicyPdf(policy, 'motor');
      setIsGenerating(false);
    }, 100);
  };

  return (
    <div className="relative group overflow-hidden rounded-2xl bg-white shadow-[0px_4px_20px_rgba(26,54,93,0.05)] hover:shadow-[0px_10px_30px_rgba(26,54,93,0.12)] transition-all duration-300 border border-transparent hover:border-[#855300]/20">
      {badge && (
        <div className={`absolute top-0 left-0 px-4 py-1 rounded-br-xl font-['Work_Sans'] text-[12px] font-bold z-10 ${
          badgeVariant === 'secondary' ? 'bg-[#855300] text-white' : 'bg-[#002045] text-white'
        }`}>
          {badge}
        </div>
      )}

      <div className="p-[24px] flex flex-col h-full">
        <div className="flex justify-between items-start mb-[24px]">
          <img src={logo} alt="" className="h-10 w-24 object-contain rounded" />
          <div className="text-right">
            <span className="font-['Work_Sans'] text-[12px] text-[#43474e] block">Annual Premium</span>
            <span className="font-['Be_Vietnam_Pro'] text-[24px] font-bold text-[#002045]">{price}</span>
          </div>
        </div>

        <div className="space-y-[12px] flex-1">
          {features.map((f) => (
            <div key={f} className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#003762]">verified</span>
              <span className="font-['Work_Sans'] text-[16px] text-[#43474e]">{f}</span>
            </div>
          ))}
        </div>

        <div className="mt-[24px] pt-[24px] border-t border-[#c4c6cf] flex items-center justify-between">
          <button className="font-['Work_Sans'] font-bold text-[14px] text-[#002045] hover:text-[#855300] flex items-center gap-1">
            View Details <span className="material-symbols-outlined text-sm">open_in_new</span>
          </button>
          <button
            onClick={handleGetDocument}
            disabled={isGenerating}
            className="flex items-center gap-2 bg-[#002045] text-white px-5 py-2 rounded-lg font-['Work_Sans'] font-bold text-[14px] hover:bg-[#1a365d] transition-all disabled:opacity-60"
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
                <span className="material-symbols-outlined text-[16px]">download</span>
                Get Document
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
