'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Subject } from '@/types';
import { BookOpen, ChevronRight, Clock, BarChart3, Map, ClipboardList, Loader2 } from 'lucide-react';

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [subject, setSubject] = useState<Subject | null>(null);
  const [units, setUnits] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [quizLoading, setQuizLoading] = useState<string | null>(null);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);

  useEffect(() => {
    if (params.id) loadData();
  }, [params.id]);

  const loadData = async () => {
    try {
      const [subjectData, unitsData] = await Promise.all([
        api.getSubject(params.id as string),
        api.getUnits(params.id as string),
      ]);
      setSubject(subjectData);
      setUnits(unitsData);
    } finally { setLoading(false); }
  };

  const startUnitAssessment = async (unit: any) => {
    setAssessmentError(null);
    setQuizLoading(unit.id);
    try {
      const res = await api.createUnitAssessment(unit.id);
      router.push(`/quizzes?quiz_id=${res.quiz_id}`);
    } catch (err: any) {
      console.error('Failed to start unit assessment:', err);
      setAssessmentError(err.response?.data?.detail || err.message || 'Failed to start the unit assessment. Please try again.');
    } finally {
      setQuizLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!subject) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="glass rounded-2xl p-8 border border-white/10">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{subject.name}</h1>
              {subject.description && (
                <p className="text-white/50 mt-1">{subject.description}</p>
              )}
              <div className="flex items-center gap-4 mt-3 text-sm text-white/40">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" /> {subject.unit_count} units
                </span>
                <span className="flex items-center gap-1">
                  <BarChart3 className="w-4 h-4" /> {Math.round(subject.progress * 100)}% complete
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-secondary flex items-center gap-2 text-sm" onClick={() => router.push('/workflow')}>
              <Map className="w-4 h-4" /> Workflow
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6 h-2 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
            style={{ width: `${subject.progress * 100}%` }}
          />
        </div>
      </div>

      {assessmentError && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {assessmentError}
        </div>
      )}

      {/* Units */}
      <div className="space-y-3">
        {units.map((unit) => (
          <div
            key={unit.id}
            className="glass rounded-xl border border-white/10 overflow-hidden"
            onClick={() => router.push(`/units/${unit.id}`)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                router.push(`/units/${unit.id}`);
              }
            }}
            role="button"
            tabIndex={0}
          >
            <div className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors cursor-pointer">
              <div className="flex items-center gap-3">
                <ChevronRight className="w-5 h-5 text-indigo-400" />
                <div className="text-left">
                  <p className="font-medium text-white">{unit.name}</p>
                  {unit.description && (
                    <p className="text-xs text-white/40 mt-0.5">{unit.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    startUnitAssessment(unit);
                  }}
                  disabled={quizLoading === unit.id}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-300 transition-colors disabled:opacity-50"
                >
                  {quizLoading === unit.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <ClipboardList className="w-3 h-3" />}
                  Unit Assessment
                </button>
                <span className="text-xs text-white/30">{unit.chapter_count} chapters</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
