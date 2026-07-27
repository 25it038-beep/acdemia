'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { PenSquare, CheckCircle2, XCircle, AlertCircle, ArrowRight, Clock } from 'lucide-react';

export default function QuizzesPage() {
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeQuiz, setActiveQuiz] = useState<any>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<any[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const subjectsData = await api.getSubjects();
      setSubjects(subjectsData);
    } finally { setLoading(false); }
  };

  const generateQuiz = async () => {
    if (!selectedSubject) return;
    setLoading(true);
    try {
      const subjectsRes = await api.getSubjects();
      const subject = subjectsRes.find((s: any) => s.id === selectedSubject);
      const res = await api.generateQuiz({
        subject_id: selectedSubject,
        title: `Quiz - ${subject?.name || 'General'}`,
        quiz_type: 'mcq',
        difficulty: 'medium',
        question_count: 10,
      });
      const quizData = await api.getQuiz(res.quiz_id);
      setActiveQuiz(quizData);
      setCurrentQuestion(0);
      setAnswers([]);
      setSubmitted(false);
    } catch (err) {
      console.error('Failed to generate quiz:', err);
    } finally { setLoading(false); }
  };

  const answerQuestion = (answer: string) => {
    const question = activeQuiz.questions[currentQuestion];
    setAnswers([...answers, { question_id: question.id, answer }]);
    if (currentQuestion < activeQuiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitQuiz();
    }
  };

  const submitQuiz = async () => {
    try {
      const res = await api.submitQuiz(activeQuiz.id, answers);
      setScore(res.score);
      setSubmitted(true);
    } catch (err) {
      console.error('Failed to submit quiz:', err);
    }
  };

  // ... (rest of the quiz UI rendering)
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <PenSquare className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Quizzes</h1>
            <p className="text-sm text-white/40">Test your knowledge</p>
          </div>
        </div>
      </div>

      {!activeQuiz ? (
        <div className="card max-w-md mx-auto text-center py-12">
          <PenSquare className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white/80 mb-4">Generate a Quiz</h3>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="input-glass mb-4"
          >
            <option value="">Select a topic...</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button
            onClick={generateQuiz}
            disabled={!selectedSubject || loading}
            className="btn-primary w-full"
          >
            {loading ? 'Generating...' : 'Generate Quiz'}
          </button>
        </div>
      ) : submitted ? (
        <div className="card max-w-lg mx-auto text-center py-12">
          <div className={`w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center ${score >= 70 ? 'bg-green-500/20' : 'bg-yellow-500/20'}`}>
            {score >= 70 ? (
              <CheckCircle2 className="w-10 h-10 text-green-400" />
            ) : (
              <AlertCircle className="w-10 h-10 text-yellow-400" />
            )}
          </div>
          <h3 className="text-2xl font-bold text-white mb-2">{Math.round(score)}%</h3>
          <p className="text-white/60 mb-6">
            {score >= 70 ? 'Great job! You passed!' : 'Keep practicing!'}
          </p>
          <button
            onClick={() => setActiveQuiz(null)}
            className="btn-primary"
          >
            Try Another Quiz
          </button>
        </div>
      ) : (
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <p className="text-sm text-white/50">
              Question {currentQuestion + 1} of {activeQuiz.questions.length}
            </p>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-white/30" />
              <span className="text-sm text-white/50">{activeQuiz.time_limit_minutes || 'No'} min limit</span>
            </div>
          </div>

          <div className="h-1.5 bg-white/10 rounded-full mb-8 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
              style={{ width: `${((currentQuestion + 1) / activeQuiz.questions.length) * 100}%` }}
            />
          </div>

          {activeQuiz.questions[currentQuestion] && (
            <motion.div
              key={currentQuestion}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="card"
            >
              <h3 className="text-lg font-medium text-white mb-6">
                {activeQuiz.questions[currentQuestion].question_text}
              </h3>

              <div className="space-y-3">
                {(activeQuiz.questions[currentQuestion].options || []).map((option: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => answerQuestion(option)}
                    className="w-full text-left p-4 rounded-xl glass glass-hover border border-white/10 hover:border-indigo-500/30 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-sm font-medium text-indigo-400">
                        {String.fromCharCode(65 + i)}
                      </div>
                      <span className="text-sm text-white/80">{option}</span>
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}