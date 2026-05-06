const ACTIVE = [
  {
    id: 1,
    name: 'Rajesh Kumar',
    preview: 'Typing...',
    time: 'Now',
    online: true,
    avatar: 'https://lh3.googleusercontent.com/aida/ADBb0uioYvpV3fjcZMM0FqyuCh26zKbZQ-Hei1GOJgRgwZ_43NIkMm4BQmZCDDXzCAJ5QLcCJTq4nYAxsZ-NStovhp4bjPwylv_NQwxue1DYxVrWTqrSAYjIjDnuX3_emt9zOkzDy-CvQbr5LG84LIXBheVqKtFN5M5R41b7Ne5yEuGNaYw_XCryYNAnfYrx3FnLT1gD5v5_Fyi2ihP5Llpgp3afiYMyTfc8lnWEemui0cUV-SK-1UoSh44tIaXhGP4mBj3uNqaIs1FFW58',
    active: true,
  },
  {
    id: 2,
    name: 'Priya Sharma',
    preview: 'Claim #9821 approved...',
    time: '2h ago',
    online: false,
    avatar: 'https://lh3.googleusercontent.com/aida/ADBb0uiFiQdpoBLghCxd3O-J20BKJdHlm6oaDtjEizWCnDjEtjk8TxoBDw8aOgpetNsNDr0g--3m-RJd6wYY7-CGVYopdAVtHivyx47XgtNaPLZfEfLNdJarSgSUG3ImGJYRLbuG0Bb53WGfzTU49pN-zUgCIUt8RC-H9oJ0cbppxotTdkkaNfuOI2iI17MGr_qQwst7EU3pBTgigytyNEYeTHO2_j-GT12c2RcF34BLJJNpjhx9nrU7Lh-MWb4LWzPwCfHJhxPZt1DwfQ',
    active: false,
  },
];

const HISTORY = [
  { id: 3, name: 'Health Renewal', preview: 'Policy successfully renewed', time: 'Sep 12' },
];

export default function ChatSidebar() {
  return (
    <aside className="w-80 bg-slate-50 border-r border-slate-200 flex-col h-full hidden md:flex">
      <div className="p-6">
        <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045] mb-4">
          Support Hub
        </h2>
        <button className="w-full flex items-center justify-center gap-2 bg-[#fea619] text-[#684000] py-3 rounded-xl font-['Work_Sans'] font-semibold text-[14px] shadow-sm hover:brightness-105 transition-all">
          <span className="material-symbols-outlined">add_comment</span>
          New Conversation
        </button>
      </div>

      <div className="flex-grow overflow-y-auto px-4 space-y-2" style={{ scrollbarWidth: 'none' }}>
        <div className="px-2 pb-2 font-['Work_Sans'] text-[12px] font-semibold uppercase tracking-wider text-[#74777f]">
          Active Now
        </div>

        {ACTIVE.map((item) => (
          <div
            key={item.id}
            className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
              item.active
                ? 'bg-white shadow-sm border border-[#fea619]/30'
                : 'hover:bg-[#eceef0]'
            }`}
          >
            <div className="relative flex-shrink-0">
              <img
                src={item.avatar}
                alt={item.name}
                className="w-12 h-12 rounded-full object-cover"
              />
              <div
                className={`absolute bottom-0 right-0 w-3 h-3 border-2 border-white rounded-full ${
                  item.online ? 'bg-green-500' : 'bg-slate-300'
                }`}
              />
            </div>
            <div className="flex-grow min-w-0">
              <div className="flex justify-between items-center">
                <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045] truncate">
                  {item.name}
                </span>
                <span className="font-['Work_Sans'] text-[10px] text-[#74777f] ml-2 flex-shrink-0">
                  {item.time}
                </span>
              </div>
              <p className="font-['Work_Sans'] text-[12px] text-[#43474e] truncate">{item.preview}</p>
            </div>
          </div>
        ))}

        <div className="px-2 pt-6 pb-2 font-['Work_Sans'] text-[12px] font-semibold uppercase tracking-wider text-[#74777f]">
          History
        </div>

        {HISTORY.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-3 hover:bg-[#eceef0] rounded-xl cursor-pointer transition-colors"
          >
            <div className="w-12 h-12 rounded-full bg-[#e0e3e5] flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-[#74777f]">history</span>
            </div>
            <div className="flex-grow min-w-0">
              <div className="flex justify-between items-center">
                <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#191c1e] truncate">
                  {item.name}
                </span>
                <span className="font-['Work_Sans'] text-[10px] text-[#74777f] ml-2 flex-shrink-0">
                  {item.time}
                </span>
              </div>
              <p className="font-['Work_Sans'] text-[12px] text-[#74777f] truncate">{item.preview}</p>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
