import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';
import { ChatDrawer } from '@/components/layout/ChatDrawer';

export const metadata: Metadata = {
  title: 'Agentic CFO - SeedlingLabs',
  description: 'AI-powered financial operations dashboard',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0c10] text-white antialiased">
        <Sidebar />
        
        <main className="ml-16 md:ml-[220px] min-h-screen">
          <TopBar />
          <div className="p-6">
            {children}
          </div>
        </main>

        <ChatDrawer />
      </body>
    </html>
  );
}
