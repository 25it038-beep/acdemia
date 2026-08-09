'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { Target, Calendar, Clock, CheckCircle2, BookOpen, Plus } from 'lucide-react';

export default function StudyPlanPage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('');
  const [examDate, setExamDate] = useState('');
  const [dailyHours, setDailyHours] = useState(2);
  const [subjects, setSubjects] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [plansData, subjectsData] = await Promise.all([
        api.getStudyPlans(),
        api.getSubjects(),
      ]);
      setPlans(plansData);
      setSubjects(subjectsData);
    } finally { setLoading(false); }
  };

  const createPlan = async () => {
    await api.createStudyPlan({
      title,
      exam_date: examDate ? new Date(examDate).toISOString() : undefined,
      daily_hours: dailyHours,
    });
    setShowCreate(false);
    loadData();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Target className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Study Plan</h1>
            <p className="text-sm text-white/40">AI-generated study schedules</p>
          </div>
        </div>
        <button className="btn-primary flex items-center gap-2 text-sm" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" /> New Plan
        </button>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowCreate(false)} />
          <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} className="relative glass rounded-2xl p-6 border border-white/10 w-full max-w-md">
            <h2 className="text-lg font-semibold text-white mb-4">Create Study Plan</h2>
            <div className="space-y-4">
              <input type="text" placeholder="Plan title" value={title} onChange={(e) => setTitle(e.target.value)} className="input-glass" />
              <input type="date" value={examDate} onChange={(e) => setExamDate(e.target.value)} className="input-glass" />
              <input type="number" value={dailyHours} onChange={(e) => setDailyHours(Number(e.target.value))} min={1} max={12} className="input-glass" />
              <div className="flex gap-3">
                <button onClick={() => setShowCreate(false)} className="btn-secondary flex-1">Cancel</button>
                <button onClick={createPlan} className="btn-primary flex-1">Generate Plan</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {plans.length === 0 ? (
        <div className="card text-center py-16">
          <Target className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <p className="text-white/60 mb-2">No study plans yet</p>
          <p className="text-white/40 text-sm">Create a plan and let AI organize your study schedule</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {plans.map((plan) => (
            <div key={plan.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-white">{plan.title}</h3>
                  {plan.exam_date && (
                    <p className="text-sm text-white/40 flex items-center gap-1 mt-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(plan.exam_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-white/30" />
                  <span className="text-sm text-white/50">{plan.daily_hours}h/day</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500" style={{ width: `${plan.progress}%` }} />
                </div>
                <span className="text-xs text-white/40">{Math.round(plan.progress)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}