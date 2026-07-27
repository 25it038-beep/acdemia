'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Subject, User } from '@/types';
import { motion } from 'framer-motion';
import {
  BookOpen, Brain, FileText, Clock, TrendingUp, Trophy,
  Target, Sparkles, ArrowRight, Plus, GraduationCap,
  BarChart3, BookMarked, Network, Map, PenSquare, Mic
} from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [userData, subjectsData] = await Promise.all([
        api.getMe(),
        api.getSubjects(),
      ]);
      setUser(userData);
      setSubjects(subjectsData);
    } catch {
      // API unavailable — show offline state rather than redirect-loop
    } finally { setLoading(false); }
  };

  const stats = [
    { icon: BookOpen, label: 'Courses', value: subjects.length, color: 'from-blue-500 to-cyan-500' },
    { icon: Brain, label: 'Concepts Learned', value: '142', color: 'from-purple-500 to-pink-500' },
    { icon: Clock, label: 'Study Hours', value: '47h', color: 'from-amber-500 to-orange-500' },
    { icon: Trophy, label: 'Quizzes Passed', value: '23', color: 'from-emerald-500 to-green-500' },
  ];

  const quickActions = [
    { icon: Plus, label: 'New Course', href: '/courses', desc: 'Add a new subject' },
    { icon: FileText, label: 'Upload Material', href: '/library', desc: 'PDF, docs, videos' },
    { icon: Brain, label: 'AI Tutor', href: '/tutor', desc: 'Start learning' },
    { icon: Target, label: 'Practice Quiz', href: '/quizzes', desc: 'Test yourself' },
    { icon: Map, label: 'Workflow Map', href: '/workflow', desc: 'View progress' },
    { icon: Network, label: 'Knowledge Graph', href: '/knowledge-graph', desc: 'Explore connections' },
    { icon: BookMarked, label: 'Flashcards', href: '/flashcards', desc: 'Review concepts' },
    { icon: Mic, label: 'AI Tutor (Voice)', href: '/tutor', desc: 'Learn hands-free with voice' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome */}
      <div className="glass rounded-2xl p-8 border border-white/10">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Welcome back, {user?.full_name || 'Student'}
            </h1>
            <p className="text-white/50">
              Continue your learning journey. You have {subjects.length} active courses.
            </p>
          </div>
          <button className="btn-primary flex items-center gap-2 text-sm" onClick={() => router.push('/courses')}>
            <Plus className="w-4 h-4" />
            New Course
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="card flex items-center gap-4"
          >
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
              <stat.icon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
              <p className="text-sm text-white/50">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <motion.button
              key={action.label}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => router.push(action.href)}
              className="card text-left flex flex-col items-center text-center gap-2 py-6"
            >
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                <action.icon className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">{action.label}</p>
                <p className="text-xs text-white/40">{action.desc}</p>
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Recent Courses */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Courses</h2>
          <button onClick={() => router.push('/courses')} className="text-sm text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            View All <ArrowRight className="w-4 h-4" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subjects.length === 0 ? (
            <div className="col-span-full card text-center py-12">
              <GraduationCap className="w-12 h-12 text-white/20 mx-auto mb-4" />
              <p className="text-white/60 mb-2">No courses yet</p>
              <p className="text-white/40 text-sm mb-4">Upload your learning materials to get started</p>
              <button className="btn-primary text-sm" onClick={() => router.push('/courses')}>
                Create Your First Course
              </button>
            </div>
          ) : (
            subjects.slice(0, 6).map((subject) => (
              <motion.div
                key={subject.id}
                whileHover={{ y: -2 }}
                className="card cursor-pointer"
                onClick={() => router.push(`/courses/${subject.id}`)}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{subject.name}</p>
                    <p className="text-xs text-white/40">{subject.unit_count} units</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
                      style={{ width: `${subject.progress * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-white/40">
                    {Math.round(subject.progress * 100)}%
                  </span>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}