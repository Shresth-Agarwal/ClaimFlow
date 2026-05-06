/**
 * QuickQuoteCTA
 * AI-driven plan recommendation call-to-action section.
 * Accepts `recommendedPlan` prop to pre-populate the recommendation card
 * with data inherited from the Interactions (chatbot) dashboard.
 */

export default function QuickQuoteCTA({ recommendedPlan }) {
  const plan = recommendedPlan || { name: 'Elite Health Plus', premium: '₹1,250' };

  return (
    <section className="py-[80px] max-w-[1280px] mx-auto px-[24px]">
      <div className="bg-[#1a365d] rounded-3xl p-[48px] md:p-[80px] flex flex-col md:flex-row items-center gap-[80px]">
        <div className="flex-1">
          <h2 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-white mb-[24px]">
            Not sure which plan is right?
          </h2>
          <p className="font-['Work_Sans'] text-[18px] leading-[1.6] text-[#86a0cd] mb-[48px]">
            Answer 3 simple questions and our AI-driven engine will recommend the perfect coverage
            for your profile.
          </p>
          <button className="bg-[#fea619] text-[#684000] px-[48px] py-[24px] rounded-xl font-['Be_Vietnam_Pro'] text-[24px] font-bold shadow-lg hover:scale-105 transition-transform">
            Start Comparison
          </button>
        </div>

        {/* Recommendation card */}
        <div className="flex-1 flex justify-center">
          <div className="bg-white p-[48px] rounded-2xl shadow-2xl max-w-sm rotate-3">
            <div className="flex items-center gap-[24px] mb-[24px]">
              <div className="w-12 h-12 bg-[#ffddb8] rounded-full flex items-center justify-center">
                <span className="material-symbols-outlined text-[#855300]">recommend</span>
              </div>
              <div>
                <div className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045]">
                  Recommended
                </div>
                <div className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045]">
                  {plan.name}
                </div>
              </div>
            </div>

            <div className="space-y-[12px] mb-[48px]">
              <div className="h-2 bg-[#c4c6cf] w-full rounded-full" />
              <div className="h-2 bg-[#c4c6cf] w-3/4 rounded-full" />
            </div>

            <div className="flex justify-between items-center border-t border-[#c4c6cf] pt-[24px]">
              <span className="font-['Work_Sans'] text-[16px] text-[#43474e]">Monthly Premium</span>
              <span className="font-['Be_Vietnam_Pro'] text-[24px] font-bold text-[#002045]">
                {plan.premium}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
