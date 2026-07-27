'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Clock, BookOpen, Brain, Target, CheckCircle2, AlertTriangle } from 'lucide-react';
import dynamic from 'next/dynamic';

const ProgressCharts = dynamic(() => import('@/components/ProgressCharts'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64 glass rounded-2xl">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

export default function ProgressPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-2">
        <BarChart3 className="w-6 h-6 text-indigo-400" />
        <div>
          <h1 className="text-xl font-bold text-white">Progress</h1>
          <p className="text-sm text-white/40">Track your learning journey</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: BookOpen, label: 'Topics Learned', value: '142', color: 'from-blue-500 to-cyan-500' },
          { icon: Clock, label: 'Total Hours', value: '47.5', color: 'from-amber-500 to-orange-500' },
          { icon: Target, label: 'Avg Quiz Score', value: '78%', color: 'from-emerald-500 to-green-500' },
          { icon: Brain, label: 'Mastery Level', value: '65%', color: 'from-purple-500 to-pink-500' },
        ].map((stat, i) => (
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
              <p className="text-xs text-white/50">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <ProgressCharts />
    </div>
  );
}