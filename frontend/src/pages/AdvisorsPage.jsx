/**
 * AdvisorsPage  (/advisors)
 *
 * Expert Advisor Network — the step that follows the Products dashboard.
 *
 * Inherited state (via React Router location.state from ProductsPage):
 *   - chatContext     : { policyType, policyNumber, insuredAmount }
 *   - recommendation  : string | null  — AI-suggested plan from Products step
 *   - messages        : ChatMessage[]
 *
 * Features:
 *   - Live client-side search across name / specialty / badge
 *   - Paginated advisor grid (ADVISORS_PER_PAGE per page)
 *   - "Book Consultation" calls POST /advisors/book with isLoading + error states
 *   - Success modal on confirmed booking
 *   - Context banner when arriving from the Products flow
 */

import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import TopAppBar from '../components/dashboard/TopAppBar';
import AdvisorSearch from '../components/advisors/AdvisorSearch';
import AdvisorGrid from '../components/advisors/AdvisorGrid';
import AdvisorPagination from '../components/advisors/AdvisorPagination';
import BookingConfirmModal from '../components/advisors/BookingConfirmModal';

// ── Static advisor data (replace with GET /advisors when backend is ready) ───
const ALL_ADVISORS = [
  {
    id: 1,
    name: 'Dr. Aris Thorne',
    
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAEEcuL6L1-vgseD_4tOnIJrTODg9I7vhwrrHztXb9aik2x8SW1m3xGJI6VWeVou6XXdBq61IvNUIaZ0btX4Qu6LbDFy864l7zYjcJ-Stv0844OomcuygugzzVOGo5DslWxu6qUkf6x7Tb1m4zlCjgNiNxU5ZwV3lSFz2wA3xfM1pb6ETiLC1HIjbIyW6Y9uvC9rtnV-dtKTNxcPALXJnmGZ2IzpUlvMFah_bgDwHbr-tn9oElA3lA6ZijsffWYfaTRfBrwVuqotQh9',
  },
  {
    id: 2,
    name: 'Sarah Jenkins',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA9N36H-P16MKjDkIze1WT4lnM3wLAdTB8o1GvK05n8Xo9-38SrkHZA557kkINqCYv0SEx1SovQazsDVngi7zq14bIlIZqZyBwmg6sGo5k0Qu-O6aW2CcpQg2IrhDYDRuyESDG4qxJ4eioRpAttV4845bVu__YoxIjxORrFrQhsnvrxecqX-s1J6yZLR5_sEnmww3Qfyqb0MWlrH7ovCIY1SY8t-SSLkMCKMiMjxLtM-fDVyWBCjewh_3OQiww5_AGS1alc0hdZ-twp',
  },
  {
    id: 3,
    name: 'Marcus Holloway',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBJIrMs_qZKyNIv5T10FTbY0_fYQNd7rd13az_Hi6W57YHzHKCutQXUIIUkZ2kVDIb1gjq770ACjamuM7W8CashQjwk0hjvxVIL5PeRHd7mTuxBgf673LzGJj9eRtbnR7169lk4MySQviAO-1LAEHJ3VUtug18CdcTYRQOZkAKGC-VZMeFUHeRw-Db0Cc2jhMI19mmjd5ibrRH5htFVqRfWhx09SFzvPOxZSeCqAMZi879TeadarCILPr908eU_d51vUPPGQ2n7jT_W',
  },
  {
    id: 4,
    name: 'Elena Rodriguez',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAGVutk-JzZ2O6L9l01028TxYGw86v7aQY7n_72ZJR8Nn4LKHNuqPiRdYk5dA6OAoPaoU2QeZuRGwQ7R6Evy9FZZQNUlTKzg3H_SaEUipinBKxugyWi6katVRjdikxPE9tSAhET5LkXQu0J2LeWE6ooBZRp7CJLtJAQlDJfzqeCvckBf5Zm5WxUmG-lqIrbcCIL-x4AnkGQIZLh_B2JCHnl0CSRO5Lapm1l8nKu213QbGxstXfOFm5Y5_r8d13fDQik1OjeI7PnTuPs',
  },
  {
    id: 5,
    name: 'David Chen',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCxJ4DfjYoiSV_O7uP9uO86ZlcnW6OpgyggOkU-7SuIQvRQO2jS4cN_18UaxHh_wqia5vhNYb8umoPaaq9Abu4ixiovTCmY7axjWS_Fpv6WQNje-_c1hJBaPTOi8NgJA3m2B3DeQQWvkJCVb9C2_wbmVS9RtftPfDcEwNHQ0BB-jnRjfKvciCdMkzvtk9NCMVNpll40GejANQ-U-6GIvPar4RpPPQk5S2BVsklDskshLkEkRN98zyQJQuNaXAJvBDbhwi_b-F26GpqG',
  },
  {
    id: 6,
    name: 'Sophia Williams',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAFFybeibrXd_k96GMexZrbTM6dDCHZnB2HtJztfqM3B47eOgbip4a4vB5wBxc_i6ZxvWEWT1uutBLqkeGVTh-K4DapH2A2RpZFaGfBKCnKs-TUMxbKnHxcfV6u5_ngu6hqLn3PV6C4230S7QuP6FmgdB09oU8KUDMHwNS4OgTRTtv_tcfw7XzwRT6jfzVeB7mFHE3uT8R7IiZtjwZPJQkDMVACQBgGPfvU56Fm7JQPaAwrNcjdzSQnW6Lxk5LPpaBokHek7RS_7W6a',
  },
  {
    id: 7,
    name: 'Jameson Vance',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAmG1UUqCLFhuw8HY_WAHaBhsx4GxDahz1L-46MyEyWmoUi0fzNJ0SgrJHQMyoclfLAzkBC0x6ffGIUcXSJBqqJ_SEod5_CAVXo4hBNUCmabrAyxvmVqjlozH74p1WYwH6aMz3skyrPm7kH6tIB0E5i3LhcHE3xOXH17a6hFliYZVdi08xb29rbNKOQcE9EbSptxW4seAz2yetXF4WVQl7kes6NQXFcLkCS5H2IgpgS7UzmSQd-J8-QCGleDvkt0v-skdpYaX9WHFeV',
  },
  {
    id: 8,
    name: 'Dr. Linda Wu',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDs5oCXiRAdKHaXXt9oRfE3OXwMYO4Q6QIWP3oOyxqxAhXhTNS0Ay4AWQYe8PlJRl3_ioTErO1-_cyAQdPOjx-io97oiLWkzKXFJi78frzUuX2cQyCT0gez6CiKXDsJwLeGwusNTUdUGZbUTQ0Fn7hYh9Yv7puOAYgqNIdB8GD_nY0pqQTekOTO659kGZ1XiwwI3bMLzGZyzcaQFRGPKBU4ASBw343E5r4xjTShlFjoWYMPlonxLjthiRliiub3ydmyzuKhBYDU2K05',
  },
  {
    id: 9,
    name: 'Robert Green',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB50QOxmuLfi-r0Hpc-t8iMFQKVsjd88O5kEJlV-buzxWnMjVephqT97FpdcL_XG86iGRjqHTWqG0YesOejy9Ga8ZaZb0NftKd141oubFBOJtGHrtlzK3GSF_hm3bp2clbpXkNZdztDm_qXJFRwX_XecMdunxN2B3XBhIWjl4QVVjImUjcNc95qEqvDei6ST8TwrBD4--RTnioFHmdZT-a4arxJsyezIAzQ5WuEk_IYm910136yUv2854PW0BdaLX__CMXE46sQyF_n',
  },
  {
    id: 10,
    name: 'Monica Geller',
    photo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBWha_aEpgaoRNMKH4_BaHwwRxlBcnxQT8_n-YcD3jSY8ujEi9mucbpp-_jb2mP3KXKqM5qzhvjS228ymbrppfU64NmpYRQHpIMbPH29cBlujnWtrhtWgADac0sA1EdWZabi_CwAYb7ghZzPkTr9MDfPH_8r2PjD6et2kgLMJgUOn0C_atJzF5EmgTpwk9jWs4sy5mRB6pxex8fAolCgNWvuJoVLy3hrhk26sDuKbrDoebVVGDXzzGiL4PP383thN4xD4e1W32ASw02',
  },
];

const ADVISORS_PER_PAGE = 10;

/** Simulates a booking — no backend call, resolves after a short delay. */
function mockBook() {
  return new Promise((resolve) => setTimeout(resolve, 900));
}

export default function AdvisorsPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // ── Inherited state from ProductsPage ─────────────────────────────────────
  const {
    chatContext = null,
    recommendation = null,
    messages = [],
  } = location.state || {};

  // ── Local state ───────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [bookingId, setBookingId] = useState(null);   // advisor.id currently being booked
  const [bookingError, setBookingError] = useState(null);
  const [confirmedAdvisor, setConfirmedAdvisor] = useState(null); // triggers success modal

  // ── Pagination logic ──────────────────────────────────────────────────────
  const filtered = ALL_ADVISORS.filter((a) => {
    const q = searchQuery.toLowerCase();
    return (
      a.name.toLowerCase().includes(q) ||
      a.specialty.toLowerCase().includes(q) ||
      a.badge.toLowerCase().includes(q)
    );
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / ADVISORS_PER_PAGE));
  const paginated = filtered.slice(
    (currentPage - 1) * ADVISORS_PER_PAGE,
    currentPage * ADVISORS_PER_PAGE
  );

  // Reset to page 1 when search changes
  const handleSearch = (q) => {
    setSearchQuery(q);
    setCurrentPage(1);
  };

  // ── Book consultation — pure mock, no backend ────────────────────────────
  const handleBook = async (advisor) => {
    setBookingId(advisor.id);
    setBookingError(null);
    try {
      await new Promise((resolve) => setTimeout(resolve, 900));
      setConfirmedAdvisor(advisor);
    } catch (err) {
      setBookingError(err.message);
    } finally {
      setBookingId(null);
    }
  };

  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] min-h-screen flex flex-col">
      {/* Same TopAppBar as user dashboard */}
      <TopAppBar activePage="Advisors" />

      {/* Context banner — shown when arriving from Products with claim data */}
      {chatContext && (
        <div className="fixed top-16 left-0 right-0 z-40 bg-[#ffddb8] border-b border-[#fea619]/40">
          <div className="max-w-[1280px] mx-auto px-[24px] py-[10px] flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-[12px]">
              <span
                className="material-symbols-outlined text-[#855300]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                info
              </span>
              <span className="font-['Work_Sans'] text-[14px] font-semibold text-[#653e00]">
                {recommendation
                  ? <>Recommended plan: <span className="font-bold">{recommendation}</span> · Find an advisor to get started</>
                  : <>Continuing from your claim — <span className="font-bold">{chatContext.policyType}</span> · {chatContext.policyNumber}</>
                }
              </span>
            </div>
            <button
              onClick={() => navigate('/products', { state: { chatContext, messages, recommendation } })}
              className="flex items-center gap-1 font-['Work_Sans'] text-[12px] font-semibold text-[#653e00] hover:underline"
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              Back to Products
            </button>
          </div>
        </div>
      )}

      <main className={`flex-grow flex flex-col ${chatContext ? 'pt-[104px]' : 'pt-16'}`}>
        <div className="px-4 md:px-10 flex flex-1 justify-center py-5">
          <div className="flex flex-col w-full max-w-[1280px]">

            {/* Headline */}
            <div className="flex flex-wrap justify-between gap-3 p-4 mt-8">
              <div className="flex min-w-72 flex-col gap-3">
                <p className="text-[#101419] text-4xl font-black leading-tight tracking-[-0.033em] font-['Be_Vietnam_Pro']">
                  Find an Expert Advisor
                </p>
                <p className="text-[#586e8d] text-base font-normal leading-normal font-['Work_Sans']">
                  Connect with top-rated professionals across various industries.
                </p>
              </div>
            </div>

            {/* Search */}
            <AdvisorSearch value={searchQuery} onChange={handleSearch} />

            {/* Booking error banner */}
            {bookingError && (
              <div className="mx-4 mb-2 flex items-center gap-2 text-[#ba1a1a] font-['Work_Sans'] text-[14px] bg-[#ffdad6] px-[16px] py-[10px] rounded-lg">
                <span className="material-symbols-outlined text-[18px]">error</span>
                Booking failed: {bookingError}
                <button
                  onClick={() => setBookingError(null)}
                  className="ml-auto text-[#ba1a1a] hover:opacity-70"
                  aria-label="Dismiss"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            )}

            {/* Advisor grid — passes paginated slice, search handled inside */}
            <AdvisorGrid
              advisors={paginated}
              searchQuery=""   /* filtering already done above */
              onBook={handleBook}
              bookingId={bookingId}
            />

            {/* Pagination */}
            {totalPages > 1 && (
              <AdvisorPagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
              />
            )}

          </div>
        </div>
      </main>

      {/* Booking success modal */}
      <BookingConfirmModal
        advisor={confirmedAdvisor}
        onClose={() => setConfirmedAdvisor(null)}
      />
    </div>
  );
}
