'use client';

import { Search, User, Settings, LogOut } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useClerk, useUser } from '@clerk/nextjs';
import NotificationsBell from '@/components/NotificationsBell';

export default function Navbar() {
  const router = useRouter();
  const { signOut } = useClerk();
  const { user } = useUser();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    signOut({ redirectUrl: '/' });
  };

  const fullName = user?.fullName || user?.primaryEmailAddress?.emailAddress || 'Student';
  const avatarUrl = user?.imageUrl;

  return (
    <header className="h-16 glass border-b border-white/10 flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-4 flex-1 max-w-xl">
        <button onClick={() => router.push('/dashboard')} className="flex items-center gap-2 flex-shrink-0" title="Academia AI">
          <img src="/logo.web.png" alt="Academia AI" className="h-8 w-auto object-contain" />
        </button>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            placeholder="Search courses, topics, concepts..."
            className="input-glass pl-10 h-10 text-sm"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <NotificationsBell />

        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl glass glass-hover"
          >
            {avatarUrl ? (
              <img src={avatarUrl} alt="" className="w-8 h-8 rounded-lg object-cover" />
            ) : (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium text-white/80">{fullName}</p>
              <p className="text-[10px] text-white/40">{(user?.publicMetadata as any)?.domain || 'Learner'}</p>
            </div>
          </button>

          {showUserMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowUserMenu(false)} />
              <div className="absolute right-0 top-full mt-2 w-56 glass border border-white/10 rounded-xl p-2 z-20 animate-fade-in">
                <button
                  onClick={() => { setShowUserMenu(false); router.push('/settings'); }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-colors text-sm"
                >
                  <User className="w-4 h-4" />
                  Profile Settings
                </button>
                <button
                  onClick={() => { setShowUserMenu(false); router.push('/settings'); }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-colors text-sm"
                >
                  <Settings className="w-4 h-4" />
                  Preferences
                </button>
                <hr className="border-white/10 my-1" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors text-sm"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}