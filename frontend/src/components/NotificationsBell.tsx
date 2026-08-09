'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, CheckCheck, Trophy, BookOpenCheck, Info, X } from 'lucide-react';
import { api } from '@/lib/api';
import { playNotificationSound } from '@/lib/sound';

const TYPE_ICONS: Record<string, any> = {
  quiz: Trophy,
  course: BookOpenCheck,
  info: Info,
};

function timeAgo(iso: string | null): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function NotificationsBell() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const prevUnread = useRef(0);
  const panelRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await api.getNotifications();
      setItems(data.notifications || []);
      setUnread(data.unread_count || 0);
      if (data.unread_count > prevUnread.current && prevUnread.current >= 0) {
        playNotificationSound();
      }
      prevUnread.current = data.unread_count || 0;
    } catch {
      // backend unreachable — keep previous state
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 15000);
    const onFocus = () => refresh();
    window.addEventListener('focus', onFocus);
    const onClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => {
      clearInterval(timer);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('mousedown', onClickOutside);
    };
  }, [refresh]);

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next && unread > 0) {
      try {
        await api.markAllNotificationsRead();
        setUnread(0);
        setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      } catch {
        // ignore
      }
    }
  };

  const openItem = (n: any) => {
    if (n.action_url) router.push(n.action_url);
    setOpen(false);
  };

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={toggle}
        className="relative w-10 h-10 rounded-xl glass glass-hover flex items-center justify-center"
        title="Notifications"
      >
        <Bell className="w-5 h-5 text-white/60" />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-indigo-500 rounded-full text-[10px] font-bold flex items-center justify-center text-white">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 glass border border-white/10 rounded-xl z-30 overflow-hidden animate-fade-in">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <p className="text-sm font-medium text-white">Notifications</p>
            <button
              onClick={() => {
                api.markAllNotificationsRead().then(() => {
                  setUnread(0);
                  setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
                }).catch(() => {});
              }}
              className="flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              Mark all read
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {items.length === 0 ? (
              <div className="px-4 py-10 text-center">
                <Bell className="w-8 h-8 text-white/15 mx-auto mb-2" />
                <p className="text-sm text-white/40">No notifications yet</p>
              </div>
            ) : (
              items.map((n) => {
                const Icon = TYPE_ICONS[n.notification_type] || Info;
                return (
                  <button
                    key={n.id}
                    onClick={() => openItem(n)}
                    className={`w-full text-left px-4 py-3 flex items-start gap-3 transition-colors hover:bg-white/5 ${
                      n.is_read ? 'opacity-50' : 'bg-indigo-500/5 border-l-2 border-indigo-500'
                    }`}
                  >
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center justify-center flex-shrink-0">
                      <Icon className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-white/85 leading-snug">{n.title}</p>
                      <p className="text-xs text-white/50 leading-snug mt-0.5">{n.message}</p>
                      <p className="text-[10px] text-white/30 mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
