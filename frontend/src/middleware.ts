import { clerkMiddleware } from '@clerk/nextjs/server'

export default clerkMiddleware(async (auth, req) => {
  const { pathname } = req.nextUrl
  const isPublic =
    pathname === '/' ||
    pathname.startsWith('/__clerk/') ||
    pathname.startsWith('/api/') ||
    pathname.startsWith('/trpc/')
  if (!isPublic) {
    await auth.protect()
  }
})

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/__clerk/:path*',
    '/(api|trpc)(.*)',
  ],
}
