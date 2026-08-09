'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Subject } from '@/types';
import { motion } from 'framer-motion';
import { BookOpen, Plus, Search, Upload, MoreVertical, Trash2, Map, Sparkles } from 'lucide-react';

export default function CoursesPage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const data = await api.getSubjects();
      setSubjects(data);
    } catch {
      // API unavailable — show offline state
    }
    finally { setLoading(false); }
  };

  const createSubject = async () => {
    if (!name.trim()) return;
    await api.createSubject({ name, description });
    setShowCreate(false);
    setName('');
    setDescription('');
    loadSubjects();
  };

  const deleteSubject = async (id: string) => {
    await api.deleteSubject(id);
    loadSubjects();
  };

  const [generating, setGenerating] = useState<Record<string, boolean>>({});

  const generateWorkflow = async (e: any, id: string) => {
    e.stopPropagation();
    setGenerating((g) => ({ ...g, [id]: true }));
    try {
      await api.generateSubjectWorkflow(id);
    } catch {
      // ignore
    } finally {
      setGenerating((g) => ({ ...g, [id]: false }));
      loadSubjects();
    }
  };

  const filteredSubjects = subjects.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Courses</h1>
          <p className="text-white/50 text-sm mt-1">
            {subjects.length} courses enrolled
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              placeholder="Search courses..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-glass pl-10 h-10 w-64 text-sm"
            />
          </div>
          <button className="btn-primary flex items-center gap-2 text-sm" onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4" />
            New Course
          </button>
        </div>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowCreate(false)} />
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="relative glass rounded-2xl p-6 border border-white/10 w-full max-w-md"
          >
            <h2 className="text-lg font-semibold text-white mb-4">Create New Course</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Course name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-glass"
              />
              <textarea
                placeholder="Description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="input-glass min-h-[100px] resize-none"
              />
              <div className="flex gap-3">
                <button onClick={() => setShowCreate(false)} className="btn-secondary flex-1 text-sm">
                  Cancel
                </button>
                <button onClick={createSubject} className="btn-primary flex-1 text-sm">
                  Create Course
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Course Grid */}
      {filteredSubjects.length === 0 ? (
        <div className="card text-center py-16">
          <BookOpen className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white/80 mb-2">No courses found</h3>
          <p className="text-white/40 text-sm mb-6">
            {search ? 'Try a different search term' : 'Create your first course to get started'}
          </p>
          {!search && (
            <button className="btn-primary" onClick={() => setShowCreate(true)}>
              Create Course
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSubjects.map((subject) => (
            <motion.div
              key={subject.id}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card group cursor-pointer relative"
              onClick={() => router.push(`/courses/${subject.id}`)}
            >
              <button
                onClick={(e) => { e.stopPropagation(); deleteSubject(subject.id); }}
                className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-white/5 hover:bg-red-500/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 className="w-4 h-4 text-red-400" />
              </button>

              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate">{subject.name}</p>
                  {subject.subject_code && (
                    <p className="text-xs text-white/40">{subject.subject_code}</p>
                  )}
                </div>
              </div>

              {subject.description && (
                <p className="text-sm text-white/50 mb-4 line-clamp-2">{subject.description}</p>
              )}

              <div className="flex items-center gap-4 text-xs text-white/40">
                <span className="flex items-center gap-1">
                  <BookOpen className="w-3.5 h-3.5" />
                  {subject.unit_count} units
                </span>
                <span className="flex items-center gap-1">
                  <Upload className="w-3.5 h-3.5" />
                  {subject.file_count} files
                </span>
              </div>

              <div className="mt-4">
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
                {subject.unit_count === 0 && (
                  <button
                    onClick={(e) => generateWorkflow(e, subject.id)}
                    disabled={generating[subject.id]}
                    className="mt-3 w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    {generating[subject.id] ? 'Generating workflow...' : 'Generate Workflow'}
                  </button>
                )}
                {subject.unit_count > 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/workflow?subject=${subject.id}`);
                    }}
                    className="mt-3 w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/70 text-xs font-medium transition-colors"
                  >
                    <Map className="w-3.5 h-3.5" />
                    View Workflow
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}