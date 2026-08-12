'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import {
  BookOpen, ChevronDown, ChevronRight, Clock, ClipboardList, Sparkles,
  Loader2, Send, Bot, User, Lightbulb, GraduationCap, ArrowLeft, FileText
} from 'lucide-react';
import dynamic from 'next/dynamic';

const MarkdownRenderer = dynamic(() => import('@/components/MarkdownRenderer'), { ssr: false });

type ChatMessageT = { role: string; content: string };

const quickPrompts = [
  'Explain this unit in simple words',
  'Give me a worked example',
  'Quiz me on this unit',
  'What are the common mistakes?',
];

export default function UnitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const unitId = params.id as string;

  const [unit, setUnit] = useState<any>(null);
  const [subject, setSubject] = useState<any>(null);
  const [chapters, setChapters] = useState<any[]>([]);
  const [materials, setMaterials] = useState<Record<string, string>>({});
  const [loadingMaterials, setLoadingMaterials] = useState<Record<string, boolean>>({});
  const [unitMaterial, setUnitMaterial] = useState('');
  const [loadingUnitMaterial, setLoadingUnitMaterial] = useState(false);
  const [collapsedChapters, setCollapsedChapters] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const [messages, setMessages] = useState<ChatMessageT[]>([]);
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [quizLoading, setQuizLoading] = useState(false);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (params.id) loadData();
  }, [params.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadData = async () => {
    try {
      const unitsData = await api.getUnitDetail(unitId);
      setUnit(unitsData.unit);
      setSubject(unitsData.subject);
      const chaptersData = await api.getChapters(unitsData.subject.id, unitId);
      setChapters(chaptersData);
      loadUnitMaterial();
      chaptersData.forEach((ch: any) => loadChapterMaterial(ch.id));
    } finally {
      setLoading(false);
    }
  };

  const loadUnitMaterial = async () => {
    setLoadingUnitMaterial(true);
    try {
      const res = await api.exploreUnit(unitId);
      setUnitMaterial(res.content);
    } catch {
      // ignore
    } finally {
      setLoadingUnitMaterial(false);
    }
  };

  const loadChapterMaterial = async (chapterId: string) => {
    setLoadingMaterials((l) => ({ ...l, [chapterId]: true }));
    try {
      const res = await api.getChapterMaterial(chapterId);
      setMaterials((prev) => ({ ...prev, [chapterId]: res.content }));
    } catch {
      // ignore
    } finally {
      setLoadingMaterials((l) => ({ ...l, [chapterId]: false }));
    }
  };

  const toggleChapter = (chapterId: string) => {
    const next = new Set(collapsedChapters);
    if (next.has(chapterId)) next.delete(chapterId);
    else next.add(chapterId);
    setCollapsedChapters(next);
  };

  const sendMessage = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || chatLoading) return;
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setInput('');
    setChatLoading(true);
    try {
      const res = await api.chat({
        session_id: `unit-${unitId}-${Date.now().toString(36)}`,
        message: content,
        mode: 'tutor',
        subject_id: subject?.id,
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: res.message }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const startUnitAssessment = async () => {
    setAssessmentError(null);
    setQuizLoading(true);
    try {
      const res = await api.createUnitAssessment(unitId);
      router.push(`/quizzes?quiz_id=${res.quiz_id}`);
    } catch (err: any) {
      console.error('Failed to start unit assessment:', err);
      setAssessmentError(err.response?.data?.detail || err.message || 'Failed to start the unit assessment. Please try again.');
    } finally {
      setQuizLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!unit || !subject) return null;

  return (
    <div className="max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-white/10 mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push(`/courses/${subject.id}`)}
            className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> {subject.name}
          </button>
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
            <BookOpen className="w-6 h-6 text-indigo-400" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">{unit.name}</h1>
            {unit.description && <p className="text-sm text-white/50 mt-0.5">{unit.description}</p>}
          </div>
          <button
            onClick={startUnitAssessment}
            disabled={quizLoading}
            className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-300 transition-colors disabled:opacity-50"
          >
            {quizLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ClipboardList className="w-4 h-4" />}
            Unit Assessment
          </button>
        </div>
        {assessmentError && (
          <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {assessmentError}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Unit full material */}
          <div className="glass rounded-xl border border-white/10 overflow-hidden">
            <div className="p-4 border-b border-white/5 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" />
              <p className="font-medium text-white">{unit.name} — Full Study Material</p>
            </div>
            <div className="p-5">
              {loadingUnitMaterial ? (
                <div className="flex items-center justify-center py-10">
                  <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                  <span className="ml-2 text-sm text-white/40">Generating full unit material...</span>
                </div>
              ) : unitMaterial ? (
                <div className="prose prose-invert max-w-none text-sm text-white/70 leading-relaxed
                  [&_h1]:text-xl [&_h1]:font-bold [&_h1]:text-white [&_h1]:mt-6 [&_h1]:mb-3
                  [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_h2]:mt-5 [&_h2]:mb-2
                  [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-white [&_h3]:mt-4 [&_h3]:mb-2
                  [&_li]:mb-1 [&_p]:mb-3 [&_strong]:text-white
                  [&_code]:bg-black/40 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-emerald-200
                  [&_pre]:bg-black/40 [&_pre]:p-3 [&_pre]:rounded-lg [&_pre]:text-xs [&_pre]:overflow-x-auto [&_pre]:my-3">
                  <MarkdownRenderer content={unitMaterial} />
                </div>
              ) : (
                <button
                  onClick={loadUnitMaterial}
                  className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 transition-colors"
                >
                  <Sparkles className="w-4 h-4" /> Generate Full Unit Material
                </button>
              )}
            </div>
          </div>

          {/* Chapters with full material */}
          {chapters.length === 0 ? (
            <div className="glass rounded-xl border border-white/10 p-8 text-center text-white/40">
              No chapters in this unit yet
            </div>
          ) : (
            chapters.map((chapter: any) => (
              <div key={chapter.id} className="glass rounded-xl border border-white/10 overflow-hidden">
                <button
                  onClick={() => toggleChapter(chapter.id)}
                  className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors"
                >
                  {collapsedChapters.has(chapter.id) ? (
                    <ChevronRight className="w-5 h-5 text-white/30 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-indigo-400 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0 text-left">
                    <p className="font-medium text-white">{chapter.name}</p>
                    <p className="text-xs text-white/40 mt-0.5">
                      <Clock className="w-3 h-3 inline mr-1" />
                      {chapter.estimated_hours}h · {chapter.difficulty}/5 difficulty
                    </p>
                  </div>
                  {loadingMaterials[chapter.id] && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
                </button>

                {!collapsedChapters.has(chapter.id) && (
                  <div className="border-t border-white/5 p-5">
                    {loadingMaterials[chapter.id] ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                        <span className="ml-2 text-sm text-white/40">Generating full chapter material...</span>
                      </div>
                    ) : materials[chapter.id] ? (
                      <div className="prose prose-invert max-w-none text-sm text-white/70 leading-relaxed
                        [&_h1]:text-xl [&_h1]:font-bold [&_h1]:text-white [&_h1]:mt-6 [&_h1]:mb-3
                        [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_h2]:mt-5 [&_h2]:mb-2
                        [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-white [&_h3]:mt-4 [&_h3]:mb-2
                        [&_li]:mb-1 [&_p]:mb-3 [&_strong]:text-white
                        [&_code]:bg-black/40 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-emerald-200
                        [&_pre]:bg-black/40 [&_pre]:p-3 [&_pre]:rounded-lg [&_pre]:text-xs [&_pre]:overflow-x-auto [&_pre]:my-3">
                        <MarkdownRenderer content={materials[chapter.id]} />
                      </div>
                    ) : (
                      <button
                        onClick={() => loadChapterMaterial(chapter.id)}
                        className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 transition-colors"
                      >
                        <Sparkles className="w-4 h-4" /> Generate Full Chapter Material
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* AI Panel */}
        <div className="lg:col-span-1">
          <div className="glass rounded-2xl border border-white/10 flex flex-col h-[75vh] lg:sticky lg:top-24">
            <div className="p-4 border-b border-white/5 flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">AI Assistant</p>
                <p className="text-[10px] text-white/40">Helping you with {unit.name}</p>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 && (
                <div className="text-center pt-6 space-y-3">
                  <GraduationCap className="w-10 h-10 text-indigo-400/50 mx-auto" />
                  <p className="text-sm text-white/50">
                    Ask me anything about this unit — concepts, examples, formulas, or a quick quiz.
                  </p>
                  <div className="flex flex-col gap-2">
                    {quickPrompts.map((p) => (
                      <button
                        key={p}
                        onClick={() => sendMessage(p)}
                        className="text-left text-xs px-3 py-2 rounded-lg bg-white/5 hover:bg-indigo-500/20 text-white/70 transition-colors"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : ''}`}
                >
                  {m.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-3.5 h-3.5 text-indigo-400" />
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                      m.role === 'user'
                        ? 'bg-indigo-500/20 text-white/90'
                        : 'bg-white/5 text-white/70'
                    }`}
                  >
                    {m.content}
                  </div>
                  {m.role === 'user' && (
                    <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                      <User className="w-3.5 h-3.5 text-white/50" />
                    </div>
                  )}
                </motion.div>
              ))}
              {chatLoading && (
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                    <Bot className="w-3.5 h-3.5 text-indigo-400" />
                  </div>
                  <div className="rounded-xl bg-white/5 px-3 py-2 flex items-center gap-1">
                    <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                    <span className="text-xs text-white/40">Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-3 border-t border-white/5">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask about this unit..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-indigo-400/50"
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={!input.trim() || chatLoading}
                  className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center disabled:opacity-40 transition-opacity"
                >
                  <Send className="w-4 h-4 text-white" />
                </button>
              </div>
              <div className="flex items-center gap-2 mt-2 text-[10px] text-white/30">
                <Lightbulb className="w-3 h-3" /> Ask for examples, clarifications, or practice questions
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
