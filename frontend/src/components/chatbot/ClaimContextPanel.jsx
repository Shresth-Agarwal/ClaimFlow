const DOCS = [
  { name: 'Policy_Schedule.pdf', icon: 'description', action: 'download' },
  { name: 'KYC_Verified.jpg', icon: 'verified', action: 'visibility' },
];

export default function ClaimContextPanel() {
  return (
    <aside className="w-72 bg-white border-l border-slate-100 p-6 hidden lg:block overflow-y-auto flex-shrink-0">
      <h4 className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045] mb-6 uppercase tracking-wider">
        Claim Context
      </h4>

      <div className="space-y-6">
        {/* Policy type */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="font-['Work_Sans'] text-[12px] text-[#74777f] uppercase tracking-wider">
            Policy Type
          </span>
          <p className="font-['Work_Sans'] font-bold text-[14px] text-[#002045] mt-1">
            Comprehensive Motor
          </p>
          <p className="font-['Work_Sans'] text-[12px] text-[#43474e] mt-0.5">
            Policy: #SRK-294022
          </p>
        </div>

        {/* Insured amount */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="font-['Work_Sans'] text-[12px] text-[#74777f] uppercase tracking-wider">
            Insured Amount
          </span>
          <p className="font-['Work_Sans'] font-bold text-[14px] text-[#002045] mt-1">
            ₹ 8,45,000
          </p>
          <div className="mt-2 w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div className="bg-[#fea619] h-full w-2/3" />
          </div>
          <p className="font-['Work_Sans'] text-[10px] text-[#74777f] mt-2">68% Cover remaining</p>
        </div>

        {/* Quick documents */}
        <div>
          <h5 className="font-['Work_Sans'] text-[12px] font-semibold text-[#74777f] mb-3 uppercase tracking-wider">
            Quick Documents
          </h5>
          <div className="space-y-2">
            {DOCS.map(({ name, icon, action }) => (
              <button
                key={name}
                className="w-full flex items-center justify-between p-2 hover:bg-slate-50 rounded-lg transition-colors border border-transparent hover:border-slate-200"
              >
                <span className="flex items-center gap-2 font-['Work_Sans'] text-[12px] font-medium">
                  <span className="material-symbols-outlined text-[#002045] text-[18px]">{icon}</span>
                  {name}
                </span>
                <span className="material-symbols-outlined text-[#74777f] text-[18px]">{action}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="pt-4">
          <button className="w-full py-2.5 font-['Work_Sans'] text-[12px] font-semibold border-2 border-[#002045] text-[#002045] rounded-lg hover:bg-[#002045] hover:text-white transition-all">
            View Full Policy Details
          </button>
        </div>
      </div>
    </aside>
  );
}
