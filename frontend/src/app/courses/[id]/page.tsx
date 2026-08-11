'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Subject } from '@/types';
import { motion } from 'framer-motion';
import { BookOpen, ChevronDown, ChevronRight, Clock, BarChart3, Network, Map, ClipboardList, Sparkles, Loader2, CheckCircle2 } from 'lucide-react';

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [subject, setSubject] = useState<Subject | null>(null);
  const [units, setUnits] = useState<any[]>([]);
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(new Set());
  const [chapters, setChapters] = useState<Record<string, any[]>>({});
  const [openChapters, setOpenChapters] = useState<Set<string>>(new Set());
  const [topics, setTopics] = useState<Record<string, any[]>>({});
  const [loadingUnits, setLoadingUnits] = useState<Record<string, boolean>>({});
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [quizLoading, setQuizLoading] = useState<string | null>(null);

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

  const toggleUnit = async (unitId: string) => {
    const newExpanded = new Set(expandedUnits);
    if (newExpanded.has(unitId)) {
      newExpanded.delete(unitId);
      setExpandedUnits(newExpanded);
      return;
    }
    newExpanded.add(unitId);
    setExpandedUnits(newExpanded);

    let data = chapters[unitId];
    if (!data) {
      data = await api.getChapters(params.id as string, unitId);
      setChapters((prev) => ({ ...prev, [unitId]: data }));
    }

    const chapterIds = (data || []).map((ch: any) => ch.id);
    const toLoad = (data || []).filter((ch: any) => !topics[ch.id]);
    setLoadingUnits((l) => ({ ...l, [unitId]: toLoad.length > 0 }));
    const allTopics: Record<string, any[]> = {};
    await Promise.all(
      toLoad.map(async (ch: any) => {
        try {
          allTopics[ch.id] = await api.getTopics(params.id as string, unitId, ch.id);
        } catch {
          allTopics[ch.id] = [];
        }
      })
    );
    if (Object.keys(allTopics).length) setTopics((prev) => ({ ...prev, ...allTopics }));
    setLoadingUnits((l) => ({ ...l, [unitId]: false }));
    setOpenChapters((prev) => new Set([...prev, ...chapterIds]));
    setExpandedTopics((prev) => new Set([...prev, ...Object.values(allTopics).flat().map((t: any) => t.id)]));
  };

  const toggleChapter = (chapterId: string) => {
    const next = new Set(openChapters);
    if (next.has(chapterId)) next.delete(chapterId);
    else next.add(chapterId);
    setOpenChapters(next);
  };

  const toggleTopic = (topicId: string) => {
    const newExpanded = new Set(expandedTopics);
    if (newExpanded.has(topicId)) newExpanded.delete(topicId);
    else newExpanded.add(topicId);
    setExpandedTopics(newExpanded);
  };

  const startChapterAssessment = async (chapter: any) => {
    setQuizLoading(chapter.id);
    try {
      const chapterTopics = topics[chapter.id] || [];
      const res = await api.generateQuiz({
        subject_id: params.id,
        topic_id: chapterTopics[0]?.id || null,
        title: `${chapter.name} Assessment`,
        question_count: 5,
        difficulty: 'medium',
      });
      router.push(`/quizzes?quiz_id=${res.quiz_id}`);
    } catch {
      // ignore
    } finally {
      setQuizLoading(null);
    }
  };

  const startUnitAssessment = async (unit: any) => {
    setQuizLoading(unit.id);
    try {
      const res = await api.createUnitAssessment(unit.id);
      router.push(`/quizzes?quiz_id=${res.quiz_id}`);
    } catch {
      // ignore
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
                      <div key={chapter.id} className="rounded-lg bg-white/5">
                        <button
                          onClick={() => toggleChapter(chapter.id)}
                          className="w-full flex items-center gap-3 p-3 hover:bg-white/10 transition-colors cursor-pointer"
                        >
                          {openChapters.has(chapter.id) ? (
                            <ChevronDown className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-white/30 flex-shrink-0" />
                          )}
                          <div className="flex-1 min-w-0 text-left">
                            <p className="text-sm text-white/80">{chapter.name}</p>
                            <p className="text-xs text-white/30 mt-0.5">
                              {chapter.estimated_hours}h · {chapter.difficulty}/5 difficulty
                            </p>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <div className="w-20 h-1.5 rounded-full bg-white/10 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                                style={{ width: `${chapter.progress * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-white/40">{Math.round(chapter.progress * 100)}%</span>
                          </div>
                        </button>

                        {openChapters.has(chapter.id) && (
                          <div className="border-t border-white/5 p-4 space-y-3">
                            {loadingUnits[chapter.unit_id] ? (
                              <div className="flex items-center justify-center py-6">
                                <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                              </div>
                            ) : (topics[chapter.id] || []).length === 0 ? (
                              <p className="text-sm text-white/30 text-center py-4">No topics in this chapter yet</p>
                            ) : (
                              <div className="space-y-2">
                                {(topics[chapter.id] || []).map((topic: any) => (
                                  <div key={topic.id} className="rounded-lg bg-white/5 overflow-hidden">
                                    <button
                                      onClick={() => toggleTopic(topic.id)}
                                      className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-white/10 transition-colors"
                                    >
                                      {expandedTopics.has(topic.id) ? (
                                        <ChevronDown className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                                      ) : (
                                        <ChevronRight className="w-4 h-4 text-white/30 flex-shrink-0" />
                                      )}
                                      <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white/90">{topic.name}</p>
                                        {topic.summary && !expandedTopics.has(topic.id) && (
                                          <p className="text-xs text-white/40 mt-0.5 line-clamp-1">{topic.summary}</p>
                                        )}
                                      </div>
                                      {topic.difficulty && (
                                        <span className="text-[10px] text-white/30 flex-shrink-0">
                                          difficulty {topic.difficulty}/5
                                        </span>
                                      )}
                                    </button>
                                    {expandedTopics.has(topic.id) && (
                                      <div className="px-3 pb-3">
                                        {topic.content && (
                                          <div className="text-sm text-white/60 leading-relaxed">
                                            {topic.content.split('\n').map((line: string, i: number) =>
                                              line.trim() ? <p key={i} className="mb-2">{line}</p> : null
                                            )}
                                          </div>
                                        )}
                                        {topic.formula && (
                                          <div className="mt-2 rounded-lg bg-indigo-500/10 border border-indigo-400/20 p-3 font-mono text-xs text-indigo-200">
                                            {topic.formula}
                                          </div>
                                        )}
                                        {topic.code_example && (
                                          <pre className="mt-2 rounded-lg bg-black/40 border border-white/10 p-3 text-xs text-emerald-200 overflow-x-auto">
                                            {topic.code_example}
                                          </pre>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                            <div className="flex items-center gap-3 pt-1">
                              <button
                                onClick={() => startChapterAssessment(chapter)}
                                disabled={quizLoading === chapter.id}
                                className="flex items-center gap-2 text-xs px-4 py-2 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-300 font-medium transition-colors disabled:opacity-50"
                              >
                                {quizLoading === chapter.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                                Take Chapter Assessment
                              </button>
                              <span className="text-[11px] text-white/30 flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" /> Progress updates as you score
                              </span>
                            </div>
                          </div>
                        )}
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
