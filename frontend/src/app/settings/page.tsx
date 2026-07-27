'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/lib/api';
import { User } from '@/types';
import { User as UserIcon, Settings, Bell, Shield, Palette, Moon, Sun } from 'lucide-react';

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Settings className="w-6 h-6 text-indigo-400" />
        <div>
          <h1 className="text-xl font-bold text-white">Settings</h1>
          <p className="text-sm text-white/40">Manage your preferences</p>
        </div>
      </div>

      {/* Profile */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Profile</h3>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <UserIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <p className="font-semibold text-white">{user?.full_name || 'Student'}</p>
            <p className="text-sm text-white/50">{user?.email}</p>
            <p className="text-xs text-white/30 mt-1">{user?.university || 'University'} · {user?.course || 'Computer Science'}</p>
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Learning Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/80">Learning Mode</p>
              <p className="text-xs text-white/40">Current: College Mode</p>
            </div>
            <select className="input-glass text-sm w-48">
              <option>Beginner</option>
              <option>School</option>
              <option selected>College</option>
              <option>Engineering</option>
              <option>Research</option>
              <option>Exam</option>
              <option>Coding</option>
            </select>
          </div>
          <hr className="border-white/10" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/80">Study Hours Per Day</p>
              <p className="text-xs text-white/40">Recommended: 2-4 hours</p>
            </div>
            <input type="range" min={1} max={8} defaultValue={3} className="w-48" />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Notifications</h3>
        <div className="space-y-3">
          {['Study Reminders', 'Quiz Results', 'New Content Available', 'Progress Updates'].map((item) => (
            <div key={item} className="flex items-center justify-between">
              <span className="text-sm text-white/70">{item}</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:bg-indigo-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}