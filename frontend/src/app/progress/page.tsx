'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { BarChart3, Clock, BookOpen, Brain, Target, Flame, CheckCircle2, AlertTriangle } from 'lucide-react';
import dynamic from 'next/dynamic';

const ProgressCharts = dynamic(() => import('@/components/ProgressCharts'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64 glass rounded-2xl">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

const POLL_INTERVAL = 15000;

export default function ProgressPage() {
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const data = await api.getProgressSummary();
      setSummary(data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load progress');
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_INTERVAL);
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => {
      clearInterval(timer);
      window.removeEventListener('focus', onFocus);
    };
  }, [load]);

  const overall = summary?.overall;
  const hours = summary?.hours;
  const quizzes = summary?.quizzes;
  const streak = summary?.streak || 0;

  const stats = [
    {
      icon: BookOpen,
      label: 'Topics Learned',
      value: overall ? `${overall.topics_learned}${overall.topics_total ? `/${overall.topics_total}` : ''}` : '—',
      sub: overall ? `${overall.completion}% complete` : '',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Clock,
      label: 'Total Hours',
      value: hours ? hours.total_hours.toFixed(1) : '—',
      sub: 'study + quizzes',
      color: 'from-amber-500 to-orange-500',
    },
    {
      icon: Target,
      label: 'Avg Quiz Score',
      value: quizzes?.count ? `${Math.round(quizzes.avg_score)}%` : '—',
      sub: quizzes?.count ? `${quizzes.passed}/${quizzes.count} passed` : 'no quizzes yet',
      color: 'from-emerald-500 to-green-500',
    },
    {
      icon: Brain,
      label: 'Mastery Level',
      value: overall ? `${Math.round(overall.mastery)}%` : '—',
      sub: 'avg confidence',
      color: 'from-purple-500 to-pink-500',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-2">
        <BarChart3 className="w-6 h-6 text-indigo-400" />
        <div>
          <h1 className="text-xl font-bold text-white">Progress</h1>
          <p className="text-sm text-white/40">Track your learning journey</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {streak > 0 && (
            <span className="flex items-center gap-1.5 text-sm text-orange-400 bg-orange-500/10 border border-orange-500/20 rounded-full px-3 py-1.5">
              <Flame className="w-4 h-4" />
              {streak}-day streak
            </span>
          )}
          <span className="text-xs text-white/30 bg-white/5 rounded-full px-3 py-1.5">
            live · updates every 15s
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
            <div className="min-w-0">
              <p className="text-2xl font-bold text-white">{stat.value}</p>
              <p className="text-xs text-white/50">{stat.label}</p>
              <p className="text-[11px] text-white/30 truncate">{stat.sub}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <ProgressCharts
        weekly={hours?.weekly || []}
        subjects={(summary?.subjects || []).map((s: any) => ({
          name: s.name,
          progress: Math.round(s.progress),
          color: s.color || undefined,
        }))}
        trend={quizzes?.trend || []}
      />

      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Recent Activity</h3>
        {quizzes?.trend?.length ? (
          <div className="space-y-3">
            {quizzes.trend.slice(-5).reverse().map((q: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                {q.score >= 70 ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />
                )}
                <span className="text-sm text-white/70 truncate">{q.title}</span>
                <span className="ml-auto text-sm font-medium text-white">{Math.round(q.score)}%</span>
                <span className="text-xs text-white/30 w-10 text-right">{q.date}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-white/30">No quizzes completed yet — head to Quizzes and take your first one</p>
        )}
      </div>
    </div>
  );
}
