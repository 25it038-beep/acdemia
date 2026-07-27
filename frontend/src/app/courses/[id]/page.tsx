'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Subject, Unit, Chapter } from '@/types';
import { motion } from 'framer-motion';
import { BookOpen, ChevronDown, ChevronRight, Plus, Clock, BarChart3, Network, Map } from 'lucide-react';

export default function CourseDetailPage() {
  const params = useParams();
  const [subject, setSubject] = useState<Subject | null>(null);
  const [units, setUnits] = useState<any[]>([]);
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(new Set());
  const [chapters, setChapters] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(true);

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

  const loadChapters = async (unitId: string) => {
    if (chapters[unitId]) return;
    const data = await api.getChapters(params.id as string, unitId);
    setChapters((prev) => ({ ...prev, [unitId]: data }));
  };

  const toggleUnit = (unitId: string) => {
    const newExpanded = new Set(expandedUnits);
    if (newExpanded.has(unitId)) {
      newExpanded.delete(unitId);
    } else {
      newExpanded.add(unitId);
      loadChapters(unitId);
    }
    setExpandedUnits(newExpanded);
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
            <button className="btn-secondary flex items-center gap-2 text-sm">
              <Network className="w-4 h-4" /> Graph
            </button>
            <button className="btn-secondary flex items-center gap-2 text-sm">
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

      {/* Units */}
      <div className="space-y-3">
        {units.map((unit) => (
          <div key={unit.id} className="glass rounded-xl border border-white/10 overflow-hidden">
            <button
              onClick={() => toggleUnit(unit.id)}
              className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-3">
                {expandedUnits.has(unit.id) ? (
                  <ChevronDown className="w-5 h-5 text-indigo-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-white/30" />
                )}
                <div className="text-left">
                  <p className="font-medium text-white">{unit.name}</p>
                  {unit.description && (
                    <p className="text-xs text-white/40 mt-0.5">{unit.description}</p>
                  )}
                </div>
              </div>
              <span className="text-xs text-white/30">{unit.chapter_count} chapters</span>
            </button>

            {expandedUnits.has(unit.id) && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                className="border-t border-white/5"
              >
                {(chapters[unit.id] || []).length === 0 ? (
                  <p className="p-4 text-sm text-white/30 text-center">No chapters yet</p>
                ) : (
                  <div className="p-4 space-y-2">
                    {(chapters[unit.id] || []).map((chapter: any) => (
                      <div key={chapter.id} className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white/80">{chapter.name}</p>
                          <p className="text-xs text-white/30 mt-0.5">
                            {chapter.estimated_hours}h · {chapter.difficulty}/5 difficulty
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 rounded-full bg-white/10 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                              style={{ width: `${chapter.progress * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-white/40">{Math.round(chapter.progress * 100)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}