/**
 * ProductsHero — uses the icon-only logo as a large decorative mark.
 */
import ClaimFlowLogo from '../ui/ClaimFlowLogo';

export default function ProductsHero() {
  return (
    <section className="relative bg-[#1a365d] text-white py-[80px] px-[24px] overflow-hidden">
      <div className="max-w-[1280px] mx-auto flex flex-col md:flex-row items-center gap-[48px] relative z-10">
        <div>
          <h1 className="font-['Be_Vietnam_Pro'] text-[48px] leading-[1.2] font-bold mb-[24px]">
            Comprehensive Protection for Every Stage of Life
          </h1>
          <p className="font-['Work_Sans'] text-[18px] leading-[1.6] text-[#86a0cd] mb-[48px]">
            Secure your future with systematic insurance solutions tailored for the Indian
            landscape. From family health to rural prosperity, ClaimFlow is your partner in
            resilience.
          </p>
          <div className="flex gap-[8px] flex-wrap">
            <button className="bg-[#fea619] text-[#684000] px-[48px] py-[12px] rounded-lg font-['Work_Sans'] font-bold text-[14px] shadow-lg hover:shadow-xl transition-all">
              Explore Categories
            </button>
            <button className="border-2 border-white text-white px-[48px] py-[12px] rounded-lg font-['Work_Sans'] font-bold text-[14px] hover:bg-white/10 transition-all">
              Watch Overview
            </button>
          </div>
        </div>
        {/* Right column — large decorative logo mark */}
        <div className="hidden md:flex flex-shrink-0 w-64 items-center justify-center opacity-20">
          <ClaimFlowLogo variant="icon" height={200} />
        </div>
      </div>
    </section>
  );
}
