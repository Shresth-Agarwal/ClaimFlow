/**
 * Reusable metric card for the admin dashboard.
 * @param {{ label, value, icon, iconBg, iconColor, blobBg, trend, trendLabel }} props
 */
export default function MetricCard({ label, value, icon, iconBg, iconColor, blobBg, trend, trendLabel }) {
  const isPositive = trend?.startsWith('+');

  return (
    <div className="bg-white rounded-xl p-6 shadow-ambient hover:shadow-ambient-hover transition-shadow duration-300 border border-transparent hover:border-[#fea619]/30 relative overflow-hidden group">
      {/* Decorative blob */}
      <div
        className={`absolute -right-4 -top-4 w-24 h-24 ${blobBg} rounded-full group-hover:scale-110 transition-transform duration-500`}
      />

      <div className="flex justify-between items-start relative z-10">
        <div>
          <p className="font-['Work_Sans'] text-[12px] font-semibold text-[#74777f] mb-1 uppercase tracking-wider">
            {label}
          </p>
          <h2 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#1a365d]">
            {value}
          </h2>
        </div>
        <div className={`${iconBg} ${iconColor} p-2 rounded-lg`}>
          <span
            className="material-symbols-outlined"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            {icon}
          </span>
        </div>
      </div>

      {trend && (
        <div className="mt-4 flex items-center gap-2 font-['Work_Sans'] text-[12px] relative z-10">
          <span
            className={`px-1.5 py-0.5 rounded-md flex items-center gap-1 font-semibold ${
              isPositive ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">
              {isPositive ? 'trending_up' : 'trending_down'}
            </span>
            {trend}
          </span>
          <span className="text-[#74777f]">{trendLabel}</span>
        </div>
      )}
    </div>
  );
}
