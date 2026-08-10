'use client';

import { useRouter } from 'next/navigation';
import { DocumentUpload } from '@/components/DocumentUpload';

export default function Home() {
  const router = useRouter();

  const handleUploadSuccess = (paperId: string) => {
    router.push(`/dashboard?id=${paperId}`);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-600 selection:text-white relative bg-grid-mesh">
      {/* Background radial glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-gradient-to-b from-indigo-500/8 via-transparent to-transparent pointer-events-none" />

      {/* Navigation Header */}
      <header className="border-b border-slate-900 bg-slate-950/40 backdrop-blur-xl sticky top-0 z-50 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-600/35">
              <span className="text-white font-extrabold text-sm">A</span>
            </div>
            <span className="text-md font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-355 font-mono">
              AuthentiCite
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/generate')}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-1.5"
            >
              <span>📝 Paper Generator</span>
            </button>
            <span className="px-3 py-1 rounded-full bg-slate-900/60 text-[10px] font-semibold text-slate-400 border border-slate-800/80">
              v1.0.0
            </span>
          </div>
        </div>
      </header>

      {/* Main Hero and Upload Section */}
      <section className="flex-grow flex items-center justify-center px-6 py-16 relative">
        <div className="max-w-3xl w-full text-center space-y-8 animate-fade-in">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white max-w-2xl mx-auto leading-tight font-sans">
              Plagiarism Rewrite & Q1 Journal Paper Generator
            </h1>
            <p className="text-sm md:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
              Upload academic papers for similarity analysis & plagiarism reduction recommendations, or generate new Q1–Q4 papers directly from topic prompts.
            </p>
          </div>

          <div className="w-full pt-4">
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-950/80 py-6 text-center text-[10px] text-slate-500 bg-slate-950/40">
        <p>© 2026 AuthentiCite. Managed and processed locally.</p>
      </footer>
    </main>
  );
}
