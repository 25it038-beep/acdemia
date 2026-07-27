'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { Code2, Plus, ExternalLink, Clock, CheckCircle2, AlertCircle, Trash2, Github, Globe } from 'lucide-react';

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [technologies, setTechnologies] = useState('');
  const [difficulty, setDifficulty] = useState(1);
  const [deadline, setDeadline] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const createProject = async () => {
    try {
      await api.createProject({
        name,
        description,
        technologies: technologies.split(',').map((t: string) => t.trim()).filter(Boolean),
        difficulty,
        deadline: deadline ? new Date(deadline).toISOString() : undefined,
      });
      setShowCreate(false);
      setName('');
      setDescription('');
      setTechnologies('');
      setDifficulty(1);
      setDeadline('');
      loadProjects();
    } catch { /* ignore */ }
  };

  const deleteProject = async (id: string) => {
    if (!confirm('Delete this project?')) return;
    try {
      await api.deleteProject(id);
      loadProjects();
    } catch { /* ignore */ }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'in_progress': return <Clock className="w-4 h-4 text-indigo-400" />;
      default: return <AlertCircle className="w-4 h-4 text-yellow-400" />;
    }
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'in_progress': return 'In Progress';
      case 'archived': return 'Archived';
      default: return 'Pending';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Code2 className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Projects</h1>
            <p className="text-sm text-white/40">Hands-on learning through projects</p>
          </div>
        </div>
        <button className="btn-primary flex items-center gap-2 text-sm" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowCreate(false)} />
          <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} className="relative glass rounded-2xl p-6 border border-white/10 w-full max-w-md">
            <h2 className="text-lg font-semibold text-white mb-4">New Project</h2>
            <div className="space-y-4">
              <input type="text" placeholder="Project name" value={name} onChange={(e) => setName(e.target.value)} className="input-glass" />
              <textarea placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} className="input-glass min-h-[80px] resize-none" />
              <input type="text" placeholder="Technologies (comma separated)" value={technologies} onChange={(e) => setTechnologies(e.target.value)} className="input-glass" />
              <div className="flex gap-2 items-center">
                <label className="text-sm text-white/50">Difficulty:</label>
                {[1, 2, 3, 4, 5].map((d) => (
                  <button key={d} onClick={() => setDifficulty(d)} className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${d === difficulty ? 'bg-indigo-500 text-white' : 'bg-white/10 text-white/50'}`}>{d}</button>
                ))}
              </div>
              <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} className="input-glass" />
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowCreate(false)} className="btn-secondary flex-1">Cancel</button>
                <button onClick={createProject} className="btn-primary flex-1">Create</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* List */}
      {projects.length === 0 ? (
        <div className="card text-center py-16">
          <Code2 className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <p className="text-white/60 mb-2">No projects yet</p>
          <p className="text-white/40 text-sm">Create a project to start building with AI guidance</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <motion.div
              key={project.id}
              whileHover={{ y: -2 }}
              className="card cursor-pointer"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Code2 className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-semibold text-white">{project.name}</h3>
                </div>
                <button onClick={(e) => { e.stopPropagation(); deleteProject(project.id); }} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-red-500/10 text-white/30 hover:text-red-400">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              {project.description && (
                <p className="text-sm text-white/50 mb-3 line-clamp-2">{project.description}</p>
              )}
              <div className="flex items-center gap-2 mb-3">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${project.status === 'completed' ? 'border-green-500/20 text-green-300' : project.status === 'in_progress' ? 'border-indigo-500/20 text-indigo-300' : 'border-yellow-500/20 text-yellow-300'}`}>
                  {statusLabel(project.status)}
                </span>
                <span className="text-xs text-white/30">•</span>
                <span className="text-xs text-white/40">{project.difficulty}/5 difficulty</span>
              </div>
              {project.technologies?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {project.technologies.map((tech: string) => (
                    <span key={tech} className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 text-[10px] border border-indigo-500/20">{tech}</span>
                  ))}
                </div>
              )}
              {project.deadline && (
                <p className="text-xs text-white/30 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Due {new Date(project.deadline).toLocaleDateString()}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
