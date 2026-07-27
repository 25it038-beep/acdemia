import type { Metadata } from 'next'
import './globals.css'
import RootLayout from '@/components/Layout'

export const metadata: Metadata = {
  title: 'Academia AI - Learning Operating System',
  description: 'The world\'s most advanced AI Learning Operating System',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <RootLayout>{children}</RootLayout>
      </body>
    </html>
  )
}