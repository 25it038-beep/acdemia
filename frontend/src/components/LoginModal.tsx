'use client';

import { useState } from 'react';
import { SignIn, SignUp } from '@clerk/nextjs';
import { X } from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const [isLogin, setIsLogin] = useState(true);

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-backdrop fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="slide-over w-full max-w-md glass rounded-3xl border border-white/10 overflow-hidden shadow-2xl relative"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 w-8 h-8 rounded-xl flex items-center justify-center hover:bg-white/5 transition-colors"
          >
            <X className="w-4 h-4 text-white/50" />
          </button>

          <div className="px-8 py-8">
            {isLogin ? <SignIn /> : <SignUp />}

            <p className="text-center text-sm text-white/40 pt-4">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-indigo-400 hover:text-indigo-300 transition-colors font-medium"
              >
                {isLogin ? 'Create one' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
