'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  BookOpen, GraduationCap, Brain, MessageSquare, FileText,
  LayoutDashboard, Network, Map, PenSquare, FolderOpen,
  Settings, LogOut, ChevronLeft, ChevronRight, Sparkles,
  Code2, Mic, BookMarked, Library, Target, BarChart3,
  Menu, X, Bell, User, Search
} from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
  { icon: BookOpen, label: 'Courses', href: '/courses' },
  { icon: FileText, label: 'Library', href: '/library' },
  { icon: Brain, label: 'AI Tutor', href: '/tutor' },
  { icon: Network, label: 'Knowledge Graph', href: '/knowledge-graph' },
  { icon: Map, label: 'Workflow Map', href: '/workflow' },
  { icon: PenSquare, label: 'Quizzes', href: '/quizzes' },
  { icon: Code2, label: 'Projects', href: '/projects' },
  { icon: BookMarked, label: 'Flashcards', href: '/flashcards' },
  { icon: Target, label: 'Study Plan', href: '/study-plan' },
  { icon: BarChart3, label: 'Progress', href: '/progress' },
  { icon: Mic, label: 'Voice Tutor', href: '/voice' },
  { icon: FolderOpen, label: 'Whiteboard', href: '/whiteboard' },
];

export default function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside
      className={`fixed left-0 top-0 h-screen z-40 transition-all duration-300 ease-in-out ${
        collapsed ? 'w-[72px]' : 'w-[260px]'
      }`}
    >
      <div className="h-full glass border-r border-white/10 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-white/10">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <h1 className="text-sm font-bold gradient-text truncate">Academia AI</h1>
                <p className="text-[10px] text-white/40 truncate">Learning OS</p>
              </div>
            )}
          </div>
          <button
            onClick={onToggle}
            className="ml-auto w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors flex-shrink-0"
          >
            {collapsed ? <ChevronRight className="w-4 h-4 text-white/50" /> : <ChevronLeft className="w-4 h-4 text-white/50" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <button
                key={item.href}
                onClick={() => router.push(item.href)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                  isActive
                    ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20'
                    : 'text-white/60 hover:text-white/80 hover:bg-white/5'
                } ${collapsed ? 'justify-center px-2' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-indigo-400' : ''}`} />
                {!collapsed && (
                  <span className="text-sm font-medium truncate">{item.label}</span>
                )}
                {isActive && !collapsed && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400" />
                )}
              </button>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-white/10 p-3">
          <button
            onClick={() => router.push('/settings')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/60 hover:text-white/80 hover:bg-white/5 transition-all ${
              collapsed ? 'justify-center' : ''
            }`}
          >
            <User className="w-5 h-5" />
            {!collapsed && <span className="text-sm truncate">Profile</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}