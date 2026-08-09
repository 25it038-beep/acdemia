import type { Metadata } from 'next'
import { ClerkProvider, Show, SignInButton, SignUpButton, UserButton } from '@clerk/nextjs'
import './globals.css'
import RootLayout from '@/components/Layout'
import AuthTokenBridge from '@/components/AuthTokenBridge'

export const metadata: Metadata = {
  title: 'Academia AI - Learning Operating System',
  description: 'The world\'s most advanced AI Learning Operating System',
  icons: {
    icon: '/logo.web.png',
  },
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <ClerkProvider>
          <AuthTokenBridge />
          <header>
            <Show when="signed-out">
              <SignInButton fallbackRedirectUrl="/onboarding" signUpFallbackRedirectUrl="/onboarding" />
              <SignUpButton />
            </Show>
            <Show when="signed-in">
              <UserButton />
            </Show>
          </header>
          <RootLayout>{children}</RootLayout>
          <footer className="w-full border-t border-white/10 py-4 text-center text-sm text-white/50">
            <a href="https://hs-ai-studio.onrender.com/#projects" target="_blank" rel="noopener noreferrer" className="hover:text-white/80 transition-colors">
              All Rights Reserved &copy; {new Date().getFullYear()} HS Solution
            </a>
          </footer>
        </ClerkProvider>
      </body>
    </html>
  )
}