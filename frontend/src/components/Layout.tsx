'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import ErrorBoundary from '@/components/ErrorBoundary';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  // Landing page — full-screen, no sidebar
  if (pathname === '/') {
    return <ErrorBoundary>{children}</ErrorBoundary>;
  }

  return (
      <div className="min-h-screen bg-[#0f0f1a]">
        <div className="animated-bg" />
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
        <div
          className={`transition-all duration-300 ${
            collapsed ? 'ml-[72px]' : 'ml-[260px]'
          }`}
        >
          <Navbar />
          <main className="p-6"><ErrorBoundary>{children}</ErrorBoundary></main>
        </div>
      </div>
    );
}