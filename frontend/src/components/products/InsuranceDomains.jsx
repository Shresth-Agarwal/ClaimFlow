/**
 * InsuranceDomains
 * Bento-grid layout — updated structure from new HTML, original colour palette retained.
 * Each domain CTA navigates to /policy/:category with inherited state.
 */

import { useNavigate } from 'react-router-dom';

const HEALTH_PLANS = [
  { label: 'Family Floater',  desc: 'Single cover for the entire family with cashless benefits.' },
  { label: 'Critical Illness', desc: 'Lump sum payout for 30+ life-threatening conditions.' },
  { label: 'Senior Citizen',  desc: 'Specialised care and lower waiting periods for parents.' },
  { label: 'Individual Cover', desc: 'Personalised health security for single adults.' },
];

const MOTOR_PLANS = ['Private Car', 'Two Wheeler', 'Commercial Vehicle'];
const AGRI_PLANS  = ['PM Fasal Bima Yojana', 'Livestock Insurance', 'Tractor & Harvester'];
const PROPERTY_TAGS = ['Home Cover', 'Shop Owners', 'Warehouse', 'Office Package'];

export default function InsuranceDomains({ recommendation, chatContext, messages }) {
  const navigate = useNavigate();

  const goTo = (category) =>
    navigate(`/policy/${category}`, { state: { chatContext, messages, recommendation } });

  return (
    <section className="py-[80px] px-[24px] max-w-[1280px] mx-auto">

      {recommendation && (
        <div className="mb-[32px] inline-flex items-center gap-2 bg-[#ffddb8] text-[#653e00] px-[16px] py-[8px] rounded-full font-['Work_Sans'] font-semibold text-[14px]">
          <span className="material-symbols-outlined text-[18px]">recommend</span>
          Based on your claim, we recommend:{' '}
          <span className="font-bold">{recommendation}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-[24px]">

        {/* ── Health & Wellness (8 cols) ── */}
        <div className="md:col-span-8 bg-white p-[24px] rounded-xl border border-[#c4c6cf]/30 shadow-[0px_4px_20px_rgba(26,54,93,0.05)] group hover:border-[#fea619] transition-all">
          <div className="flex justify-between items-start mb-[24px]">
            <div>
              <span className="material-symbols-outlined text-[#855300] text-[32px]">health_and_safety</span>
              <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#191c1e] mt-[4px]">Health &amp; Wellness</h2>
            </div>
            <button onClick={() => goTo('health')} className="text-[#855300] font-['Work_Sans'] font-semibold text-[14px] flex items-center gap-[4px] hover:underline">
              View All <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-[12px]">
            {HEALTH_PLANS.map(({ label, desc }) => (
              <div key={label} onClick={() => goTo('health')}
                className="p-[12px] bg-[#f2f4f6] rounded-lg hover:bg-[#e6e8ea] transition-colors cursor-pointer">
                <h3 className="font-['Work_Sans'] font-bold text-[#002045] mb-[4px]">{label}</h3>
                <p className="font-['Work_Sans'] text-[12px] text-[#43474e]">{desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-[24px]">
            <button onClick={() => goTo('health')}
              className="bg-[#fea619] text-[#684000] px-[24px] py-[8px] rounded-lg font-['Work_Sans'] font-semibold text-[14px] w-full hover:opacity-90 transition-opacity">
              Get Health Quote
            </button>
          </div>
        </div>

        {/* ── Motor Insurance (4 cols) ── */}
        <div className="md:col-span-4 bg-[#1a365d] text-white p-[24px] rounded-xl shadow-[0px_4px_20px_rgba(26,54,93,0.05)] flex flex-col justify-between">
          <div>
            <span className="material-symbols-outlined text-[#fea619] text-[32px]">directions_car</span>
            <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold mt-[4px]">Motor Insurance</h2>
            <ul className="mt-[24px] space-y-[12px]">
              {MOTOR_PLANS.map((plan) => (
                <li key={plan} className="flex items-center gap-[12px] text-white/80">
                  <span className="material-symbols-outlined text-[#ffddb8]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  {plan}
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-[48px]">
            <button onClick={() => goTo('motor')}
              className="border border-[#ffddb8] text-[#ffddb8] px-[24px] py-[8px] rounded-lg font-['Work_Sans'] font-semibold text-[14px] w-full hover:bg-[#ffddb8]/10 transition-colors">
              View Motor Details
            </button>
          </div>
        </div>

        {/* ── Agri & Rural (4 cols) ── */}
        <div className="md:col-span-4 bg-white p-[24px] rounded-xl border border-[#c4c6cf]/30 shadow-[0px_4px_20px_rgba(26,54,93,0.05)] flex flex-col">
          <span className="material-symbols-outlined text-[#855300] text-[32px]">agriculture</span>
          <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#191c1e] mt-[4px]">Agri &amp; Rural</h2>
          <div className="mt-[24px] space-y-[8px] flex-grow">
            {AGRI_PLANS.map((plan) => (
              <div key={plan} onClick={() => goTo('agriculture')}
                className="p-[12px] bg-[#f2f4f6] rounded-lg cursor-pointer hover:bg-[#e6e8ea] transition-colors">
                <p className="font-['Work_Sans'] font-bold text-[#002045]">{plan}</p>
              </div>
            ))}
          </div>
          <button onClick={() => goTo('agriculture')}
            className="bg-[#002045] text-white px-[24px] py-[8px] rounded-lg font-['Work_Sans'] font-semibold text-[14px] mt-[24px] hover:bg-[#1a365d] transition-colors">
            View Agri Solutions
          </button>
        </div>

        {/* ── Property & Assets (8 cols) ── */}
        <div className="md:col-span-8 relative rounded-xl shadow-[0px_4px_20px_rgba(26,54,93,0.05)] overflow-hidden min-h-[300px]">
          <img
            src="https://lh3.googleusercontent.com/aida/ADBb0ug7O15aHW6zNvbG92bonIqx5312WYTISx_ljWR7ekE2-H9tzqDSP0uUtIyTdOyp-hVpYYHGEEoJXF6YyG8WgtO6aQeD6_Qlklzu1sb4yIidSN0Umq5wIAFIP_nqlNT1eZXKbO73UjoF0KtuK0BXD1h9cC4tQT8g2HZkAxRlq5AXg-9AIqT5dBNGt2JEecZzQG2KElMWd9tmtIao79ClsSUR3wOPBBP2pt0_h-GDJ_FP_qhe2dtPpn6k2IKVFZseGbKhEUiJNclOuQ"
            alt="Modern property" className="absolute inset-0 w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#1a365d]/95 to-[#1a365d]/60 p-[24px] flex flex-col justify-end text-white">
            <span className="material-symbols-outlined text-[#fea619] text-[32px]">domain</span>
            <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold mb-[8px]">Property &amp; Assets</h2>
            <div className="flex flex-wrap gap-[12px] mb-[24px]">
              {PROPERTY_TAGS.map((tag) => (
                <span key={tag} className="bg-white/10 backdrop-blur-md px-[12px] py-[4px] rounded-full font-['Work_Sans'] text-[12px]">{tag}</span>
              ))}
            </div>
            <button onClick={() => goTo('property')}
              className="bg-[#fea619] text-[#684000] px-[48px] py-[8px] rounded-lg font-['Work_Sans'] font-bold text-[14px] w-fit hover:opacity-90 transition-opacity">
              Get Asset Quote
            </button>
          </div>
        </div>

      </div>
    </section>
  );
}
