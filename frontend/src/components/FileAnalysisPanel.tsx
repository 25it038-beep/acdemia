'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { FileAnalysis, SimilarFile } from '@/types';
import {
  Brain,
  Loader2,
  Sparkles,
  BookOpen,
  Gauge,
  BarChart3,
  FileSearch,
  AlertCircle,
} from 'lucide-react';

const difficultyColors: Record<number, string> = {
  1: 'text-green-400 bg-green-500/10 border-green-500/20',
  2: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  3: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  4: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  5: 'text-red-400 bg-red-500/10 border-red-500/20',
};

export default function FileAnalysisPanel({ fileId }: { fileId: string }) {
  const [analysis, setAnalysis] = useState<FileAnalysis | null>(null);
  const [similar, setSimilar] = useState<SimilarFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    Promise.all([api.getFileAnalysis(fileId), api.getSimilarFiles(fileId)])
      .then(([a, s]) => {
        if (cancelled) return;
        setAnalysis(a);
        setSimilar(s);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.response?.data?.detail || 'ML analysis unavailable');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fileId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-indigo-400 py-2">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        Running ML analysis...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-xs text-yellow-400/80 py-2">
        <AlertCircle className="w-3.5 h-3.5" />
        {error}
      </div>
    );
  }

  if (!analysis?.status || analysis.status === 'empty') {
    return (
      <div className="flex items-center gap-2 text-xs text-white/40 py-2">
        <Brain className="w-3.5 h-3.5" />
        No text available for ML analysis
      </div>
    );
  }

  const difficulty = analysis.difficulty ?? ({} as NonNullable<FileAnalysis['difficulty']>);
  const readability = analysis.readability ?? ({} as NonNullable<FileAnalysis['readability']>);
  const stats = analysis.statistics ?? ({} as NonNullable<FileAnalysis['statistics']>);
  const maxMatches = Math.max(1, ...(analysis.subject_matches ?? []).map((m) => m.score));

  return (
    <div className="mt-3 space-y-3 text-xs">
      <div className="flex items-center gap-1.5 text-indigo-300 font-medium">
        <Brain className="w-3.5 h-3.5" />
        ML Analysis
      </div>

      {/* Difficulty */}
      {difficulty.difficulty && (
        <div className="flex items-center gap-2">
          <Gauge className="w-3.5 h-3.5 text-white/40" />
          <span className="text-white/50">Difficulty:</span>
          <span
            className={`px-2 py-0.5 rounded-full border capitalize ${
              difficultyColors[difficulty.difficulty] || difficultyColors[3]
            }`}
          >
            {difficulty.difficulty_label}
          </span>
          <span className="text-white/40">
            (grade {difficulty.readability_grade} readability)
          </span>
        </div>
      )}

      {/* Statistics */}
      {stats.word_count > 0 && (
        <div className="grid grid-cols-2 gap-1.5 text-white/60">
          <span className="flex items-center gap-1">
            <BarChart3 className="w-3 h-3 text-white/30" />
            {stats.word_count.toLocaleString()} words
          </span>
          <span>{stats.sentence_count} sentences</span>
          <span>{stats.unique_words.toLocaleString()} unique words</span>
          <span>~{stats.estimated_reading_minutes} min read</span>
          {readability.flesch_reading_ease !== undefined && (
            <span>Flesch: {readability.flesch_reading_ease}</span>
          )}
          {readability.flesch_kincaid_grade !== undefined && (
            <span>FK grade: {readability.flesch_kincaid_grade}</span>
          )}
        </div>
      )}

      {/* Keywords */}
      {analysis.keywords && analysis.keywords.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-white/50 mb-1.5">
            <Sparkles className="w-3 h-3" />
            Key concepts
          </div>
          <div className="flex flex-wrap gap-1.5">
            {analysis.keywords.map((k) => (
              <span
                key={k.keyword}
                className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300"
                title={`${k.frequency} occurrences`}
              >
                {k.keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Subject classification */}
      {analysis.subject_matches && analysis.subject_matches.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-white/50 mb-1.5">
            <BookOpen className="w-3 h-3" />
            Likely subjects
          </div>
          <div className="space-y-1.5">
            {analysis.subject_matches.map((m) => (
              <div key={m.subject} className="flex items-center gap-2">
                <span className="w-28 truncate text-white/60">{m.subject}</span>
                <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-400"
                    style={{ width: `${(m.score / maxMatches) * 100}%` }}
                  />
                </div>
                <span className="text-white/40 w-6 text-right">
                  {Math.round(m.score * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Similar files */}
      {similar.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-white/50 mb-1.5">
            <FileSearch className="w-3 h-3" />
            Similar documents
          </div>
          <div className="space-y-1">
            {similar.map((s) => (
              <div
                key={s.file_id}
                className="flex items-center justify-between gap-2 rounded-lg bg-white/5 px-2 py-1.5"
              >
                <span className="truncate text-white/60">{s.title}</span>
                <span className="text-indigo-300 shrink-0">
                  {Math.round(s.similarity * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
