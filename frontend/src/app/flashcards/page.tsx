'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Flashcard } from '@/types';
import { motion } from 'framer-motion';
import { BookMarked, RotateCcw, ThumbsUp, ThumbsDown, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';

export default function FlashcardsPage() {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');

  useEffect(() => {
    loadCards();
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const data = await api.getSubjects();
      setSubjects(data);
    } catch {}
  };

  const loadCards = async () => {
    try {
      const data = await api.getDueFlashcards();
      setCards(data);
    } finally { setLoading(false); }
  };

  const generateCards = async () => {
    if (!selectedSubject) return;
    setGenerating(true);
    try {
      await api.generateFlashcards(selectedSubject, 10);
      await loadCards();
    } catch (err) {
      console.error('Failed to generate flashcards:', err);
    } finally {
      setGenerating(false);
    }
  };

  const review = async (quality: number) => {
    const card = cards[index];
    await api.reviewFlashcard(card.id, quality);
    if (index < cards.length - 1) {
      setIndex(index + 1);
      setFlipped(false);
    } else {
      loadCards();
      setIndex(0);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookMarked className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Flashcards</h1>
            <p className="text-sm text-white/40">Spaced repetition learning</p>
          </div>
        </div>
        <p className="text-sm text-white/50">{cards.length} cards due</p>
      </div>

      {cards.length === 0 ? (
        <div className="card text-center py-16">
          <BookMarked className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <p className="text-white/60 mb-2">No cards due for review</p>
          <p className="text-white/40 text-sm mb-6">Generate flashcards from your course material</p>
          <div className="max-w-xs mx-auto space-y-3">
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="input-glass w-full"
            >
              <option value="">Select a subject...</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            <button
              onClick={generateCards}
              disabled={!selectedSubject || generating}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              {generating ? 'Generating...' : 'Generate Flashcards'}
            </button>
          </div>
        </div>
      ) : (
        <div className="max-w-lg mx-auto">
          <p className="text-sm text-white/50 text-center mb-4">
            Card {index + 1} of {cards.length}
          </p>

          <motion.div
            key={index}
            initial={{ opacity: 0, rotateY: flipped ? 180 : 0 }}
            animate={{ opacity: 1, rotateY: flipped ? 180 : 0 }}
            className="card min-h-[300px] flex items-center justify-center cursor-pointer"
            onClick={() => setFlipped(!flipped)}
          >
            <div className="text-center">
              <p className="text-sm text-indigo-400 mb-4">
                {flipped ? 'Answer' : 'Question'}
              </p>
              <p className="text-lg text-white font-medium">
                {flipped ? cards[index].back : cards[index].front}
              </p>
              <p className="text-xs text-white/30 mt-6">Click to flip</p>
            </div>
          </motion.div>

          {flipped && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center gap-4 mt-6"
            >
              <button
                onClick={() => review(1)}
                className="btn-secondary flex items-center gap-2"
              >
                <ThumbsDown className="w-4 h-4 text-red-400" />
                Hard
              </button>
              <button
                onClick={() => review(3)}
                className="btn-secondary flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4 text-yellow-400" />
                Good
              </button>
              <button
                onClick={() => review(5)}
                className="btn-primary flex items-center gap-2"
              >
                <ThumbsUp className="w-4 h-4" />
                Easy
              </button>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}