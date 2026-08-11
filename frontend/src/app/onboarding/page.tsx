'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';
import { GraduationCap, Loader2, ArrowRight, User, School, BookOpen, Hash, Layers, Briefcase, Compass, Target } from 'lucide-react';

const EDUCATION_LEVELS = ['High School', 'Undergraduate', 'Postgraduate', 'Graduate', 'Working Professional', 'Other'];

const LEARNING_MODES = [
  { value: 'school', label: 'School Student' },
  { value: 'college', label: 'College Student' },
  { value: 'engineering', label: 'Engineering / Technical' },
  { value: 'research', label: 'Research' },
  { value: 'interview', label: 'Interview Prep' },
  { value: 'exam', label: 'Competitive Exam' },
  { value: 'beginner', label: 'Self-study / Beginner' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isLoaded } = useUser();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    full_name: '',
    university: '',
    course: '',
    semester: '',
    education_level: 'Undergraduate',
    occupation: '',
    domain: '',
    learning_mode: 'college',
  });

  useEffect(() => {
    if (!isLoaded) return;
    if (!user) {
      router.replace('/');
      return;
    }
    if ((user.publicMetadata as any)?.onboarded) {
      router.replace('/dashboard');
      return;
    }
    setForm((f) => ({
      ...f,
      full_name: f.full_name || (user.firstName || user.lastName ? `${user.firstName ?? ''} ${user.lastName ?? ''}`.trim() : ''),
    }));
    api.getMe()
      .then((me) => {
        setForm({
          full_name: me.full_name || `${user.firstName ?? ''} ${user.lastName ?? ''}`.trim(),
          university: me.university || '',
          course: me.course || '',
          semester: me.semester ? String(me.semester) : '',
          education_level: me.education_level || 'Undergraduate',
          occupation: me.occupation || '',
          domain: me.domain || '',
          learning_mode: me.learning_mode || 'college',
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isLoaded, user, router]);

  const update = (key: keyof typeof form, value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async () => {
    if (!form.full_name.trim()) {
      toast.error('Please enter your name');
      return;
    }
    setSaving(true);
    try {
      const fullName = form.full_name.trim();
      const nameParts = fullName.split(/\s+/);
      const profile = await api.updateMe({
        full_name: fullName,
        university: form.university.trim() || null,
        course: form.course.trim() || null,
        semester: form.semester ? Number(form.semester) : null,
        education_level: form.education_level || null,
        occupation: form.occupation.trim() || null,
        domain: form.domain.trim() || null,
        learning_mode: form.learning_mode,
      });
      try {
        await user?.update({
          firstName: nameParts[0] || '',
          lastName: nameParts.slice(1).join(' ') || '',
          publicMetadata: {
            onboarded: true,
            onboarded_at: new Date().toISOString(),
            domain: form.domain.trim() || '',
          },
        } as any);
      } catch {
        await user?.update({
          publicMetadata: {
            onboarded: true,
            onboarded_at: new Date().toISOString(),
            domain: form.domain.trim() || '',
          },
        } as any).catch(() => {});
      }
      toast.success('Profile saved! Welcome to Academia AI');
      router.push('/dashboard');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = async () => {
    try {
      await user?.update({ publicMetadata: { onboarded: true, onboarded_at: new Date().toISOString() } } as any);
    } catch {}
    router.push('/dashboard');
  };

  if (loading) {
    return (
      <div className="aurora min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="aurora min-h-screen flex items-center justify-center p-6">
      <div className="aurora-glow" style={{ top: '15%', left: '10%', background: '#6366f1' }} />
      <div className="aurora-glow" style={{ bottom: '15%', right: '10%', background: '#8b5cf6' }} />

      <div className="relative z-10 w-full max-w-2xl">
        <div className="glass border border-white/10 rounded-3xl p-8 md:p-10">
          <div className="flex items-center gap-3 mb-2">
            <img src="/logo.web.png" alt="Academia AI" className="h-10 w-auto object-contain" />
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            Tell us <span className="gradient-text">about you</span>
          </h1>
          <p className="text-white/50 text-sm mb-8">
            This helps us personalize your AI tutor, courses, and study plans.
          </p>

          <div className="space-y-5">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                <User className="w-4 h-4 text-indigo-400" /> Full Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => update('full_name', e.target.value)}
                placeholder="e.g. Priya Sharma"
                className="input-glass w-full h-11 px-4 text-sm"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <School className="w-4 h-4 text-indigo-400" /> University / Institution
                </label>
                <input
                  type="text"
                  value={form.university}
                  onChange={(e) => update('university', e.target.value)}
                  placeholder="e.g. MIT"
                  className="input-glass w-full h-11 px-4 text-sm"
                />
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" /> Course / Major
                </label>
                <input
                  type="text"
                  value={form.course}
                  onChange={(e) => update('course', e.target.value)}
                  placeholder="e.g. Computer Science"
                  className="input-glass w-full h-11 px-4 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <Hash className="w-4 h-4 text-indigo-400" /> Semester / Year
                </label>
                <select
                  value={form.semester}
                  onChange={(e) => update('semester', e.target.value)}
                  className="input-glass w-full h-11 px-4 text-sm"
                >
                  <option value="">Not applicable</option>
                  {Array.from({ length: 8 }, (_, i) => i + 1).map((n) => (
                    <option key={n} value={n}>Semester {n}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <Layers className="w-4 h-4 text-indigo-400" /> Education Level
                </label>
                <select
                  value={form.education_level}
                  onChange={(e) => update('education_level', e.target.value)}
                  className="input-glass w-full h-11 px-4 text-sm"
                >
                  {EDUCATION_LEVELS.map((level) => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <Briefcase className="w-4 h-4 text-indigo-400" /> Occupation
                </label>
                <input
                  type="text"
                  value={form.occupation}
                  onChange={(e) => update('occupation', e.target.value)}
                  placeholder="e.g. Student, Engineer"
                  className="input-glass w-full h-11 px-4 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <Target className="w-4 h-4 text-indigo-400" /> Field / Domain
                </label>
                <input
                  type="text"
                  value={form.domain}
                  onChange={(e) => update('domain', e.target.value)}
                  placeholder="e.g. Artificial Intelligence"
                  className="input-glass w-full h-11 px-4 text-sm"
                />
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-white/70 mb-2">
                  <Compass className="w-4 h-4 text-indigo-400" /> Learning Mode
                </label>
                <select
                  value={form.learning_mode}
                  onChange={(e) => update('learning_mode', e.target.value)}
                  className="input-glass w-full h-11 px-4 text-sm"
                >
                  {LEARNING_MODES.map((mode) => (
                    <option key={mode.value} value={mode.value}>{mode.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 mt-8">
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="btn-primary w-full sm:flex-1 text-sm px-6 py-3 flex items-center justify-center gap-2"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <GraduationCap className="w-4 h-4" />}
              {saving ? 'Saving...' : 'Start Learning'}
              {!saving && <ArrowRight className="w-4 h-4" />}
            </button>
            <button
              onClick={handleSkip}
              disabled={saving}
              className="w-full sm:w-auto px-6 py-3 rounded-xl text-sm text-white/50 hover:text-white/80 hover:bg-white/5 transition-colors"
            >
              Skip for now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
