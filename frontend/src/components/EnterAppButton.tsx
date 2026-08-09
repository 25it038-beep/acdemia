'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuth, SignInButton } from '@clerk/nextjs';

export default function EnterAppButton({
  className,
  children,
  redirectUrl = '/dashboard',
}: {
  className?: string;
  children: React.ReactNode;
  redirectUrl?: string;
}) {
  const { isSignedIn } = useAuth();
  const router = useRouter();

  if (isSignedIn) {
    return (
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => router.push(redirectUrl)}
        className={className}
      >
        {children}
      </motion.button>
    );
  }

  return (
    <SignInButton mode="modal" fallbackRedirectUrl={redirectUrl} signUpFallbackRedirectUrl={redirectUrl}>
      <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className={className}>
        {children}
      </motion.button>
    </SignInButton>
  );
}
