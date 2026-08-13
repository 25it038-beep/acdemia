'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/lib/api';
import {
  Send, Bot, User, Brain, BookOpen, Code2, MessageSquare,
  Sparkles, StopCircle, Mic, Volume2, RefreshCw, BookMarked, Trash2
} from 'lucide-react';
import dynamic from 'next/dynamic';

const MarkdownRenderer = dynamic(() => import('@/components/MarkdownRenderer'), { ssr: false });

const modes = [
  { id: 'tutor', label: 'AI Tutor', icon: Brain, desc: 'Interactive teaching' },
  { id: 'mentor', label: 'Mentor', icon: User, desc: 'Guidance & advice' },
  { id: 'research', label: 'Research', icon: BookOpen, desc: 'Deep analysis' },
  { id: 'coding', label: 'Coding', icon: Code2, desc: 'Code assistance' },
  { id: 'exam', label: 'Exam Coach', icon: MessageSquare, desc: 'Exam prep' },
  { id: 'interview', label: 'Interview', icon: User, desc: 'Practice interviews' },
];

const SESSION_KEY = 'academia_chat_session';

type ChatMessageT = { role: string; content: string };

export default function TutorPage() {
  const [messages, setMessages] = useState<ChatMessageT[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('tutor');
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem(SESSION_KEY);
      if (saved) return saved;
    }
    return Math.random().toString(36).substring(7);
  });
  const [sessions, setSessions] = useState<Array<{ session_id: string; first_message: string; message_count: number; last_updated?: string }>>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [listenStatus, setListenStatus] = useState('');
  const [subjects, setSubjects] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  const refreshSessions = () => {
    api.getChatSessions().then(setSessions).catch(() => setSessions([]));
  };

  useEffect(() => {
    api.getSubjects().then((res) => setSubjects(res)).catch(() => setSubjects([]));
    refreshSessions();
  }, []);

  useEffect(() => {
    window.localStorage.setItem(SESSION_KEY, sessionId);
  }, [sessionId]);

  useEffect(() => {
    let cancelled = false;
    setHistoryLoading(true);
    setMessages([]);
    api.getChatHistory(sessionId)
      .then((msgs: Array<{ role: string; content: string }>) => {
        if (!cancelled) setMessages(msgs);
      })
      .catch(() => { if (!cancelled) setMessages([]); })
      .finally(() => { if (!cancelled) setHistoryLoading(false); });
    return () => { cancelled = true; };
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  const newChat = () => {
    setSessionId(Math.random().toString(36).substring(7));
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  const clearChat = () => {
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  const switchSession = (id: string) => {
    if (id === sessionId) return;
    setSessionId(id);
    setInput('');
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: ChatMessageT = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.chat({
        session_id: sessionId,
        message: input,
        mode,
        subject_id: selectedSubject || undefined,
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: res.message }]);
      refreshSessions();
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleVoice = () => {
    const SpeechRecognition =
      (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    if (!SpeechRecognition) {
      setListenStatus('Browser not supported');
      setTimeout(() => setListenStatus(''), 3000);
      return;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
      setIsListening(false);
      setListenStatus('');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setListenStatus('Speak now...');
    };

    recognition.onresult = (event: any) => {
      const result = event.results[event.results.length - 1];
      if (result.isFinal) {
        const text = result[0].transcript;
        setInput(text);
        setListenStatus('');
      }
    };

    recognition.onend = () => {
      recognitionRef.current = null;
      setIsListening(false);
      setListenStatus('');
    };

    recognition.onerror = (event: any) => {
      recognitionRef.current = null;
      setIsListening(false);
      setListenStatus('');
      if (event.error === 'not-allowed') {
        setListenStatus('Microphone blocked');
        setTimeout(() => setListenStatus(''), 3000);
      }
    };

    try {
      recognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      recognitionRef.current = null;
      setIsListening(false);
      setListenStatus('Mic error');
      setTimeout(() => setListenStatus(''), 3000);
    }
  };

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4 animate-fade-in">
      {/* Sidebar - Mode Selection */}
      <div className="w-64 space-y-2">
        <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-3 px-2">Learning Mode</h2>
        {modes.map((m) => {
          const Icon = m.icon;
          const isActive = mode === m.id;
          return (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-indigo-500/15 border border-indigo-500/20 text-indigo-400'
                  : 'text-white/50 hover:text-white/70 hover:bg-white/5'
              }`}
            >
              <Icon className="w-5 h-5" />
              <div className="text-left">
                <p className="text-sm font-medium">{m.label}</p>
                <p className="text-[10px] text-white/30">{m.desc}</p>
              </div>
            </button>
          );
        })}

        {sessions.length > 0 && (
          <>
            <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-2 px-2 pt-4">
              Recent Conversations
            </h2>
            <button
              onClick={newChat}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-white/50 hover:text-white/70 hover:bg-white/5 transition-all"
            >
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <div className="text-left">
                <p className="text-sm font-medium">New Chat</p>
                <p className="text-[10px] text-white/30">Start a fresh session</p>
              </div>
            </button>
            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {sessions.map((s) => {
                const isActive = s.session_id === sessionId;
                return (
                  <button
                    key={s.session_id}
                    onClick={() => switchSession(s.session_id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all ${
                      isActive
                        ? 'bg-indigo-500/15 border border-indigo-500/20 text-indigo-300'
                        : 'text-white/50 hover:text-white/70 hover:bg-white/5'
                    }`}
                    title={s.first_message}
                  >
                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs font-medium truncate">
                        {s.first_message || 'Untitled conversation'}
                      </p>
                      <p className="text-[10px] text-white/30">
                        {s.message_count} messages
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col glass rounded-2xl border border-white/10 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-white">AI {modes.find(m => m.id === mode)?.label}</h2>
            <p className="text-xs text-white/40">Interactive learning session</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="relative">
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="input-glass h-9 pr-8 text-sm appearance-none cursor-pointer"
                title="Select course material"
              >
                <option value="">All Courses</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <BookMarked className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 pointer-events-none" />
            </div>
            <button
              onClick={toggleVoice}
              className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                isListening ? 'bg-red-500/20 text-red-400' : 'glass glass-hover text-white/50'
              }`}
              title={isListening ? 'Stop listening' : 'Voice input'}
            >
              {isListening ? <StopCircle className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button
              onClick={newChat}
              className="w-9 h-9 rounded-lg glass glass-hover flex items-center justify-center"
              title="New chat"
            >
              <RefreshCw className="w-4 h-4 text-white/50" />
            </button>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="w-9 h-9 rounded-lg glass glass-hover flex items-center justify-center"
                title="Clear chat"
              >
                <Trash2 className="w-4 h-4 text-white/50" />
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && !historyLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Sparkles className="w-12 h-12 text-indigo-500/30 mb-4" />
              <h3 className="text-lg font-medium text-white/70 mb-2">Start Learning</h3>
              <p className="text-sm text-white/40 max-w-md">
                Ask me anything about your course material. I'll teach you step by step,
                check your understanding, and adapt to your level. Your conversations are
                saved and used as reference in future sessions.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-indigo-400" />
                </div>
              )}
              <div
                className={`max-w-[70%] rounded-2xl px-5 py-3 ${
                  msg.role === 'user'
                    ? 'bg-indigo-500/20 border border-indigo-500/20'
                    : 'glass border border-white/5'
                }`}
              >
                <div className="prose prose-sm prose-invert max-w-none">
                  <MarkdownRenderer content={msg.content} />
                </div>
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-4 h-4 text-purple-400" />
                </div>
              )}
            </motion.div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="glass rounded-2xl px-5 py-3">
                <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-white/10">
          {listenStatus && (
            <p className="text-xs text-indigo-400 mb-2 text-center">{listenStatus}</p>
          )}
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
            className="flex items-center gap-3"
          >
            <button
              type="button"
              onClick={toggleVoice}
              className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all ${
                isListening
                  ? 'bg-red-500/20 text-red-400 animate-glow'
                  : 'glass glass-hover text-white/40'
              }`}
              title={isListening ? 'Stop listening' : 'Voice input'}
            >
              {isListening ? <StopCircle className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isListening ? 'Listening...' : 'Ask anything... I\'ll teach you step by step'}
              className="input-glass flex-1 h-12"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="w-10 h-10 rounded-xl bg-indigo-500 hover:bg-indigo-600 disabled:bg-white/10 flex items-center justify-center flex-shrink-0 transition-all"
            >
              <Send className="w-5 h-5 text-white" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
