import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'PMOVES Console',
  description: 'Secure operator console for PMOVES ingestion workflows.',
};

export const dynamic = 'force-dynamic';
export const fetchCache = 'force-no-store';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-100 text-slate-900">{children}</body>
    </html>
  );
}
