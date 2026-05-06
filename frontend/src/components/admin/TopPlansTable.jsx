const PLANS = [
  {
    name: 'Arogya Sanjeevani',
    type: 'Health Insurance',
    insurer: 'SBI General',
    initials: 'SB',
    initialsColor: 'bg-[#d6e3ff]/20 text-[#1a365d]',
    sales: '2,451',
    growth: '+15%',
    positive: true,
  },
  {
    name: 'Optima Restore',
    type: 'Comprehensive Health',
    insurer: 'HDFC ERGO',
    initials: 'HD',
    initialsColor: 'bg-[#d2e4ff]/20 text-[#003762]',
    sales: '1,890',
    growth: '+12%',
    positive: true,
  },
  {
    name: 'iSelect Smart360',
    type: 'Term Life',
    insurer: 'Canara HSBC',
    initials: 'CA',
    initialsColor: 'bg-[#ffddb8]/20 text-[#fea619]',
    sales: '1,204',
    growth: '+8%',
    positive: true,
  },
  {
    name: 'Motor Protect Plus',
    type: 'Comprehensive Auto',
    insurer: 'ICICI Lombard',
    initials: 'IC',
    initialsColor: 'bg-[#e0e3e5] text-[#43474e]',
    sales: '985',
    growth: '-3%',
    positive: false,
  },
];

export default function TopPlansTable() {
  return (
    <div className="bg-white rounded-xl shadow-ambient overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-[#e0e3e5] flex justify-between items-center bg-white">
        <h3 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#1a365d]">
          Top-Selling Plans
        </h3>
        <button className="font-['Work_Sans'] font-semibold text-[14px] text-[#fea619] hover:text-[#855300] transition-colors flex items-center gap-1">
          View All <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#f7f9fb] font-['Work_Sans'] font-semibold text-[14px] text-[#43474e] border-b border-[#e0e3e5]">
              {['Plan Name', 'Insurer', 'Sales', 'Growth', ''].map((col) => (
                <th key={col} className="p-4 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="font-['Work_Sans'] text-[16px] text-[#191c1e]">
            {PLANS.map((plan, i) => (
              <tr
                key={plan.name}
                className={`hover:bg-[#f7f9fb] transition-colors group ${
                  i < PLANS.length - 1 ? 'border-b border-[#e0e3e5]/50' : ''
                }`}
              >
                <td className="p-4">
                  <div className="font-semibold text-[#1a365d]">{plan.name}</div>
                  <div className="font-['Work_Sans'] text-[12px] text-[#74777f]">{plan.type}</div>
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-8 h-8 rounded flex items-center justify-center font-bold text-xs ${plan.initialsColor}`}
                    >
                      {plan.initials}
                    </div>
                    <span>{plan.insurer}</span>
                  </div>
                </td>
                <td className="p-4 font-semibold">{plan.sales}</td>
                <td className="p-4">
                  <span
                    className={`px-2 py-1 rounded text-sm font-semibold ${
                      plan.positive
                        ? 'text-emerald-600 bg-emerald-50'
                        : 'text-rose-600 bg-rose-50'
                    }`}
                  >
                    {plan.growth}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <button className="text-[#1a365d] hover:text-[#fea619] transition-colors opacity-0 group-hover:opacity-100 p-2">
                    <span className="material-symbols-outlined">more_vert</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
