import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { QueryProvider } from '@/providers/QueryProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';
import { ToastProvider } from '@/providers/ToastProvider';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'GraphGuard AI — Enterprise Compliance Knowledge Graph Synthesis',
  description:
    'Multi-modal enterprise compliance Knowledge Graph synthesis and GraphRAG platform.',
};

import { AuthProvider } from '@/context/auth-context';
import { AuthGuard } from '@/components/auth-guard';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`} suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <QueryProvider>
          <ThemeProvider>
            <AuthProvider>
              <AuthGuard>
                <ToastProvider>
                  <DashboardLayout>{children}</DashboardLayout>
                </ToastProvider>
              </AuthGuard>
            </AuthProvider>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
