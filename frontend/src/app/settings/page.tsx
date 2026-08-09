'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/lib/api';
import { User } from '@/types';
import { User as UserIcon, Settings, Save, Check, GraduationCap, BadgeCheck, Compass } from 'lucide-react';

const themeOptions = [
  { id: 'beginner', label: 'Beginner' },
  { id: 'school', label: 'School' },
  { id: 'college', label: 'College' },
  { id: 'engineering', label: 'Engineering' },
  { id: 'research', label: 'Research' },
  { id: 'interview', label: 'Interview' },
  { id: 'exam', label: 'Exam' },
  { id: 'coding', label: 'Coding' },
  { id: 'visual', label: 'Visual' },
  { id: 'story', label: 'Story' },
  { id: 'revision', label: 'Revision' },
];

const educationOptions = [
  'High School',
  'Diploma',
  'Undergraduate (Bachelors)',
  'Postgraduate (Masters)',
  'PhD / Doctorate',
  'Professional Certification',
  'Self-Taught',
  'Other',
];

const designationOptions = [
  'Student',
  'Developer',
  'Engineer',
  'Researcher',
  'Data Scientist',
  'Designer',
  'Teacher',
  'Working Professional',
  'Other',
];

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setTheme] = useState('college');
  const [educationLevel, setEducationLevel] = useState('');
  const [occupation, setOccupation] = useState('');
  const [domain, setDomain] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getMe().then((u) => {
      setUser(u);
      setTheme(u.learning_mode || 'college');
      setEducationLevel(u.education_level || '');
      setOccupation(u.occupation || '');
      setDomain(u.domain || '');
    }).catch(() => {});
  }, []);

  const saveProfile = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const updated = await api.updateMe({
        learning_mode: theme,
        education_level: educationLevel,
        occupation,
        domain,
      });
      setUser(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setSaved(false);
    } finally {
      setSaving(false);
    }
  };

  const designation = occupation || 'Learner';
  const level = educationLevel || 'any level';
  const area = domain || 'your domain';

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Settings className="w-6 h-6 text-indigo-400" />
        <div>
          <h1 className="text-xl font-bold text-white">Settings</h1>
          <p className="text-sm text-white/40">Manage your preferences</p>
        </div>
      </div>

      {/* Profile */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Profile</h3>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <UserIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <p className="font-semibold text-white">{user?.full_name || 'Student'}</p>
            <p className="text-sm text-white/50">{user?.email}</p>
            <p className="text-xs text-white/30 mt-1">{user?.university || 'University'} · {user?.course || 'Computer Science'}</p>
          </div>
        </div>
      </div>

      {/* Learner Profile */}
      <motion.div
        className="card border border-indigo-500/20"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3 mb-1">
          <GraduationCap className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white/70">Learner Profile</h3>
        </div>
        <p className="text-xs text-white/40 mb-5">
          Tell the AI what you are and what you're studying, so it can address you by your
          designation and match every answer to your level and domain.
        </p>

        <div className="space-y-5">
          {/* Theme */}
          <div>
            <label className="text-xs font-medium text-white/60 mb-2 block">
              Theme (how the AI should teach you)
            </label>
            <div className="flex flex-wrap gap-2">
              {themeOptions.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTheme(t.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    theme === t.id
                      ? 'bg-indigo-500/20 border border-indigo-500/40 text-indigo-400'
                      : 'bg-white/5 border border-white/10 text-white/50 hover:text-white/70 hover:bg-white/10'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Education */}
          <div>
            <label className="text-xs font-medium text-white/60 mb-2 block">
              What education are you in?
            </label>
            <select
              value={educationLevel}
              onChange={(e) => setEducationLevel(e.target.value)}
              className="input-glass w-full"
            >
              <option value="">Select education level</option>
              {educationOptions.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>

          {/* What they are doing */}
          <div>
            <label className="text-xs font-medium text-white/60 mb-2 block">
              What are you doing? (your designation)
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {designationOptions.map((o) => (
                <button
                  key={o}
                  type="button"
                  onClick={() => setOccupation(o === 'Other' ? '' : o)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    occupation === o
                      ? 'bg-purple-500/20 border border-purple-500/40 text-purple-400'
                      : 'bg-white/5 border border-white/10 text-white/50 hover:text-white/70 hover:bg-white/10'
                  }`}
                >
                  {o}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              placeholder="e.g., Software Developer, Research Scholar..."
              className="input-glass w-full"
            />
          </div>

          {/* Domain */}
          <div>
            <label className="text-xs font-medium text-white/60 mb-2 block flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5" /> Which domain are you in?
            </label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="e.g., Computer Science, Data Science, Physics..."
              className="input-glass w-full"
            />
          </div>

          {/* Preview */}
          <div className="rounded-xl bg-indigo-500/10 border border-indigo-500/20 px-4 py-3 flex items-start gap-3">
            <BadgeCheck className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-white/60">
              The AI will address you as <span className="text-indigo-300 font-semibold">{designation}</span>{' '}
              at <span className="text-indigo-300 font-semibold">{level}</span> in{' '}
              <span className="text-indigo-300 font-semibold">{area}</span>, teaching in{' '}
              <span className="text-indigo-300 font-semibold">{theme} mode</span>.
            </p>
          </div>

          {/* Save */}
          <div className="flex items-center gap-3">
            <button
              onClick={saveProfile}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 disabled:bg-white/10 text-white text-sm font-medium transition-all"
            >
              {saving ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
            {saved && (
              <span className="inline-flex items-center gap-1.5 text-sm text-emerald-400">
                <Check className="w-4 h-4" /> Saved — AI now knows your level
              </span>
            )}
          </div>
        </div>
      </motion.div>

      {/* Notifications */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Notifications</h3>
        <div className="space-y-3">
          {['Study Reminders', 'Quiz Results', 'New Content Available', 'Progress Updates'].map((item) => (
            <div key={item} className="flex items-center justify-between">
              <span className="text-sm text-white/70">{item}</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:bg-indigo-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
