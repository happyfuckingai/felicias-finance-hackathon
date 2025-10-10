import { AppProvider } from '@/components/app-provider';
import { Toaster } from '@/components/ui/sonner';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  // Mock app config for now
  const appConfig = {
    companyName: "Felicia's Finance",
    logo: '/logo.png',
    logoDark: '/logo-dark.png',
    pageTitle: "Felicia's Finance - AI-Powered Financial Management",
    pageDescription: "Manage your finances with AI assistance",
    accent: '#8b5cf6',
    accentDark: '#a855f7',
    supportsChatInput: true,
    supportsVideoInput: true,
    supportsScreenShare: true,
    isPreConnectBufferEnabled: true,
    startButtonText: 'Start Financial Assistant',
  };

  return (
    <AppProvider appConfig={appConfig}>
      {children}
      <Toaster />
    </AppProvider>
  );
}