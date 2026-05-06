import TopAppBar from '../components/dashboard/TopAppBar';
import HeroSection from '../components/dashboard/HeroSection';
import PartnerLogos from '../components/dashboard/PartnerLogos';
import CategoryGrid from '../components/dashboard/CategoryGrid';
import TrustIndicators from '../components/dashboard/TrustIndicators';
import ChatFAB from '../components/dashboard/ChatFAB';
import DashboardFooter from '../components/dashboard/DashboardFooter';

export default function DashboardPage() {
  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] min-h-screen flex flex-col">
      <TopAppBar />

      <main className="flex-grow flex flex-col pt-16">
        <HeroSection />
        <PartnerLogos />
        <CategoryGrid />
        <TrustIndicators />
      </main>

      <ChatFAB />
      <DashboardFooter />
    </div>
  );
}
