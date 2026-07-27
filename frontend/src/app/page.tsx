'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  Sparkles, BookOpen, Brain, Network, FileText, Target,
  BarChart3, Mic, Upload, Map, ArrowRight, Play, ChevronDown,
  Star, Quote, GraduationCap, Bot, User, Zap
} from 'lucide-react';
import LoginModal from '@/components/LoginModal';

// ─── Particles ───────────────────────────────────────────
function Particles() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {Array.from({ length: 30 }).map((_, i) => (
        <div
          key={i}
          className="particle"
          style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 15}s`,
            animationDuration: `${15 + Math.random() * 20}s`,
            width: `${2 + Math.random() * 3}px`,
            height: `${2 + Math.random() * 3}px`,
          }}
        />
      ))}
    </div>
  );
}

// ─── Animated Counter ─────────────────────────────────────
function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;
    const duration = 2000;
    const steps = 60;
    const stepValue = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += stepValue;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [isInView, value]);

  return (
    <div ref={ref} className="stat-value">
      {count}{suffix}
    </div>
  );
}

// ─── Feature Card ────────────────────────────────────────
function FeatureCard({ icon: Icon, title, desc, delay }: { icon: any; title: string; desc: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className="feature-card group cursor-default"
    >
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
        <Icon className="w-6 h-6 text-indigo-400" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-white/50 leading-relaxed">{desc}</p>
    </motion.div>
  );
}

// ─── Testimonial Card ────────────────────────────────────
function TestimonialCard({ name, role, text, avatar, rating }: { name: string; role: string; text: string; avatar: string; rating: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="testimonial-card"
    >
      <div className="flex items-center gap-1 mb-4">
        {Array.from({ length: rating }).map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
        ))}
      </div>
      <Quote className="w-6 h-6 text-indigo-500/30 mb-2" />
      <p className="text-sm text-white/70 leading-relaxed mb-4">{text}</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
          {avatar}
        </div>
        <div>
          <p className="text-sm font-medium text-white">{name}</p>
          <p className="text-xs text-white/40">{role}</p>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Live Demo Chat ──────────────────────────────────────
function LiveDemoChat() {
  const [step, setStep] = useState(0);
  const messages = [
    { role: 'user', content: "I don't understand Binary Trees. Can you help?" },
    { role: 'ai', content: "Of course! Let's learn Binary Trees visually. Imagine a tree structure where each node has at most two children — left and right.", hasDiagram: true },
    { role: 'ai', content: "Here's a simple Binary Tree: The root is 10, with left child 5 and right child 15. Each child can also have its own children.", hasVisual: true },
    { role: 'user', content: "So how do I traverse it?" },
    { role: 'ai', content: "Great question! There are 3 main traversals:\n\n**In-order** (Left → Root → Right): 5, 10, 15\n**Pre-order** (Root → Left → Right): 10, 5, 15\n**Post-order** (Left → Right → Root): 5, 15, 10", hasCode: true },
    { role: 'ai', content: "I've generated a quiz on Binary Trees. Ready to test your understanding?", hasQuiz: true },
  ];

  useEffect(() => {
    if (step < messages.length) {
      const timer = setTimeout(() => setStep(step + 1), step === 0 ? 1000 : 2500);
      return () => clearTimeout(timer);
    }
  }, [step]);

  return (
    <div className="glass rounded-2xl border border-white/10 overflow-hidden max-w-2xl mx-auto">
      {/* Chat header */}
      <div className="px-5 py-4 border-b border-white/10 flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <Brain className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">AI Tutor</p>
          <p className="text-[10px] text-green-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
            Active • Binary Trees
          </p>
        </div>
        <div className="ml-auto flex gap-1">
          <span className="w-2 h-2 rounded-full bg-white/20" />
          <span className="w-2 h-2 rounded-full bg-white/20" />
          <span className="w-2 h-2 rounded-full bg-white/20" />
        </div>
      </div>

      {/* Messages */}
      <div className="p-5 space-y-4 min-h-[300px] max-h-[400px] overflow-y-auto">
        {messages.slice(0, step).map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'ai' && (
              <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
              </div>
            )}
            <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
              <p className="text-sm text-white/80 whitespace-pre-line">{msg.content}</p>
              {msg.hasDiagram && (
                <div className="mt-3 p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                  <div className="flex justify-center gap-4 text-xs">
                    <div className="text-center">
                      <div className="w-10 h-10 rounded-lg bg-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold mx-auto mb-1">10</div>
                      <span className="text-white/40">Root</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-0.5 bg-indigo-500/30" />
                    </div>
                    <div className="text-center">
                      <div className="w-10 h-10 rounded-lg bg-purple-500/30 flex items-center justify-center text-purple-300 font-bold mx-auto mb-1">5</div>
                      <span className="text-white/40">Left</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-0.5 bg-indigo-500/30" />
                    </div>
                    <div className="text-center">
                      <div className="w-10 h-10 rounded-lg bg-cyan-500/30 flex items-center justify-center text-cyan-300 font-bold mx-auto mb-1">15</div>
                      <span className="text-white/40">Right</span>
                    </div>
                  </div>
                </div>
              )}
              {msg.hasCode && (
                <div className="mt-2 p-3 bg-black/30 rounded-xl border border-white/5 font-mono text-xs text-green-400">
                  <p className="text-white/40 mb-1">// In-order traversal</p>
                  <p>function inOrder(node) {'{'}</p>
                  <p className="ml-4">if (node.left) inOrder(node.left);</p>
                  <p className="ml-4">console.log(node.value);</p>
                  <p className="ml-4">if (node.right) inOrder(node.right);</p>
                  <p>{'}'}</p>
                </div>
              )}
              {msg.hasQuiz && (
                <div className="mt-3 flex gap-2">
                  <button className="flex-1 px-3 py-2 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-medium hover:bg-indigo-500/30 transition-colors">
                    Start Quiz
                  </button>
                  <button className="flex-1 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white/60 text-xs hover:bg-white/10 transition-colors">
                    Review Notes
                  </button>
                </div>
              )}
              {msg.hasVisual && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 text-xs border border-indigo-500/20">Binary Tree</span>
                  <span className="px-2.5 py-1 rounded-lg bg-green-500/10 text-green-300 text-xs border border-green-500/20">O(log n)</span>
                  <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 text-xs border border-amber-500/20">Depth: 2</span>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-3.5 h-3.5 text-purple-400" />
              </div>
            )}
          </motion.div>
        ))}
        {step <= messages.length && step > 0 && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-white/5 border border-white/5">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-5 py-4 border-t border-white/10">
        <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 border border-white/5">
          <input
            type="text"
            placeholder="Ask anything about Binary Trees..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-white/80 placeholder:text-white/20"
            readOnly
          />
          <button className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
            <ArrowRight className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Landing Page ───────────────────────────────────
export default function LandingPage() {
  const [showLogin, setShowLogin] = useState(false);

  const features = [
    { icon: Brain, title: 'AI Tutor', desc: 'Get personalized explanations for every topic, just like a professor one-on-one session.' },
    { icon: Network, title: 'Knowledge Graph', desc: 'Visualize how concepts connect. See the bigger picture of your curriculum.' },
    { icon: FileText, title: 'Smart Notes', desc: 'AI generates concise, structured notes from your uploaded materials.' },
    { icon: Target, title: 'Quiz Generator', desc: 'Adaptive quizzes that identify weak areas and reinforce learning.' },
    { icon: BarChart3, title: 'Progress Analytics', desc: 'Track mastery with detailed analytics. Know exactly what to revise.' },
    { icon: Mic, title: 'Voice Learning', desc: 'Talk naturally with your AI tutor. Learn hands-free, anytime.' },
    { icon: Upload, title: 'Multi-file Upload', desc: 'Upload PDFs, PPTX, DOCX, images, videos, and ZIP files. AI processes everything.' },
    { icon: Map, title: 'Learning Roadmap', desc: 'Automatically generates a semester roadmap based on your syllabus.' },
  ];

  const stats = [
    { value: 100, suffix: 'K+', label: 'Lessons Generated' },
    { value: 10, suffix: 'M+', label: 'Questions Solved' },
    { value: 500, suffix: 'K+', label: 'Documents Processed' },
    { value: 95, suffix: '%', label: 'Student Satisfaction' },
  ];

  const testimonials = [
    { name: 'Priya Sharma', role: 'Computer Science, MIT', text: 'Academia AI completely transformed how I study. The knowledge graph helped me connect concepts I never realized were related.', avatar: 'PS', rating: 5 },
    { name: 'Rahul Verma', role: 'Mechanical Eng., IIT', text: 'The AI tutor explains complex engineering concepts better than most professors. My grades improved from C to A.', avatar: 'RV', rating: 5 },
    { name: 'Ananya Patel', role: 'Medicine, AIIMS', text: 'Uploaded 2000+ pages of medical textbooks. Academia AI organized everything and created a perfect study roadmap.', avatar: 'AP', rating: 5 },
  ];

  return (
    <div className="aurora min-h-screen">
      <Particles />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold gradient-text">Academia AI</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-white/50 hover:text-white/80 transition-colors">Features</a>
            <a href="#demo" className="text-sm text-white/50 hover:text-white/80 transition-colors">Demo</a>
            <a href="#stats" className="text-sm text-white/50 hover:text-white/80 transition-colors">Stats</a>
            <button onClick={() => setShowLogin(true)} className="btn-primary text-sm px-5 py-2.5">
              Get Started
            </button>
          </div>
          <button onClick={() => setShowLogin(true)} className="md:hidden btn-primary text-sm px-4 py-2">
            Sign In
          </button>
        </div>
      </nav>

      {/* ──────── Hero ──────── */}
      <section className="relative min-h-screen flex items-center justify-center pt-20 pb-16 px-6">
        <div className="aurora-glow" style={{ top: '10%', left: '5%', background: '#6366f1' }} />
        <div className="aurora-glow" style={{ top: '30%', right: '10%', background: '#8b5cf6' }} />
        <div className="aurora-glow" style={{ bottom: '20%', left: '40%', background: '#a78bfa' }} />

        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-8">
              <Zap className="w-4 h-4 text-indigo-400" />
              <span className="text-sm text-indigo-300">The future of learning is here</span>
            </div>

            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              Your Personal{' '}
              <span className="gradient-text">AI Learning</span>
              <br />
              Operating System
            </h1>

            <p className="text-lg md:text-xl text-white/50 max-w-3xl mx-auto mb-10 leading-relaxed">
              Upload your syllabus, books, notes, and previous papers. Academia AI builds your personalized learning roadmap,
              teaches every concept, answers doubts, generates quizzes, predicts weak areas, and helps you master your semester.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowLogin(true)}
                className="btn-primary text-lg px-8 py-4 flex items-center gap-3 glow-pulse"
              >
                <GraduationCap className="w-5 h-5" />
                Start Learning Free
                <ArrowRight className="w-5 h-5" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="btn-secondary text-lg px-8 py-4 flex items-center gap-3"
              >
                <Play className="w-5 h-5" />
                Watch Demo
              </motion.button>
              <a href="#features" className="btn-secondary text-lg px-8 py-4 flex items-center gap-3">
                Explore Features
              </a>
            </div>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
          >
            <ChevronDown className="w-6 h-6 text-white/30 animate-bounce" />
          </motion.div>
        </div>
      </section>

      {/* ──────── Features ──────── */}
      <section id="features" className="relative px-6 py-24">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-header"
          >
            <h2 className="section-title">
              Everything you need to{' '}
              <span className="gradient-text">master learning</span>
            </h2>
            <p className="section-subtitle">
              From uploading materials to AI-powered tutoring — Academia AI handles every aspect of your education.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((f, i) => (
              <FeatureCard key={f.title} {...f} delay={i * 0.05} />
            ))}
          </div>
        </div>
      </section>

      {/* ──────── Live Demo ──────── */}
      <section id="demo" className="relative px-6 py-24">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-header"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 mb-4">
              <span className="w-2 h-2 rounded-full bg-green-400" />
              <span className="text-xs text-green-300 font-medium">Live Demo</span>
            </div>
            <h2 className="section-title">
              See it in{' '}
              <span className="gradient-text">action</span>
            </h2>
            <p className="section-subtitle">
              Watch how Academia AI teaches complex topics interactively, with visuals, code, and quizzes.
            </p>
          </motion.div>

          <LiveDemoChat />
        </div>
      </section>

      {/* ──────── Stats ──────── */}
      <section id="stats" className="relative px-6 py-24">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-header"
          >
            <h2 className="section-title">
              Trusted by students{' '}
              <span className="gradient-text">worldwide</span>
            </h2>
            <p className="section-subtitle">Join the growing community of learners who transformed their education.</p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="stat-card glass rounded-2xl border border-white/5"
              >
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                <p className="stat-label">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ──────── Testimonials ──────── */}
      <section className="relative px-6 py-24">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-header"
          >
            <h2 className="section-title">
              What students{' '}
              <span className="gradient-text">say</span>
            </h2>
            <p className="section-subtitle">Thousands of students have transformed their learning experience.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <TestimonialCard key={t.name} {...t} />
            ))}
          </div>
        </div>
      </section>

      {/* ──────── CTA ──────── */}
      <section className="relative px-6 py-24">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass rounded-3xl border border-white/10 p-12 gradient-border"
          >
            <GraduationCap className="w-16 h-16 text-indigo-400 mx-auto mb-6" />
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to transform your learning?
            </h2>
            <p className="text-lg text-white/50 mb-8 max-w-xl mx-auto">
              Join thousands of students who use AI to learn faster, understand deeper, and score higher.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowLogin(true)}
              className="btn-primary text-lg px-10 py-4 flex items-center gap-3 mx-auto glow-pulse"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          </motion.div>
        </div>
      </section>

      {/* ──────── Footer ──────── */}
      <footer className="border-t border-white/5 px-6 py-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-white/30">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Academia AI — Learning Operating System
          </div>
          <div className="flex items-center gap-6 text-sm text-white/30">
            <span>© 2026 Academia AI</span>
            <a href="#" className="hover:text-white/50 transition-colors">Privacy</a>
            <a href="#" className="hover:text-white/50 transition-colors">Terms</a>
            <a href="#" className="hover:text-white/50 transition-colors">Contact</a>
          </div>
        </div>
      </footer>

      {/* ──────── Login Modal ──────── */}
      <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} />
    </div>
  );
}