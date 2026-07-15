'use client';

import { useRouter } from 'next/navigation';
import { DocumentUpload } from '@/components/DocumentUpload';

export default function Home() {
  const router = useRouter();

  const handleUploadSuccess = (paperId: string) => {
    // Navigate to dashboard for analysis
    router.push(`/dashboard?id=${paperId}`);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Background radial glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] bg-gradient-radial from-indigo-500/10 via-transparent to-transparent pointer-events-none" />

      {/* Navigation Header */}
      <header className="border-b border-slate-900 bg-slate-950/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <span className="text-white font-extrabold text-lg">Ω</span>
            </div>
            <span className="text-lg font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
              ResearchAI
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="px-3.5 py-1.5 rounded-full bg-slate-900 text-xs font-semibold text-slate-400 border border-slate-800">
              v1.0 (Self-Hosted)
            </span>
          </div>
        </div>
      </header>

      {/* Main Hero and Upload Section */}
      <section className="flex-grow flex items-center justify-center px-6 py-12 relative">
        <div className="max-w-4xl w-full text-center space-y-10">
          <div className="space-y-4">
            <span className="px-4 py-1.5 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-bold uppercase tracking-wider border border-indigo-500/20 inline-block animate-pulse">
              Final Pipeline Version
            </span>
            <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-white max-w-3xl mx-auto leading-[1.1]">
              Rewrite & Analyze Research Papers
            </h1>
            <p className="text-base md:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Estimate plagiarism similarity, rewrite flagged sections with academic LLMs, and export in official journal layouts like IEEE and Springer.
            </p>
          </div>

          <div className="w-full">
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Feature Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left pt-6 max-w-3xl mx-auto">
            <div className="p-5 bg-slate-900/30 border border-slate-850 rounded-2xl space-y-2">
              <span className="text-indigo-400 font-bold text-lg">📄 Multi-Format Parser</span>
              <p className="text-xs text-slate-400 leading-relaxed">Extracts text, fonts, margins, tables, and images from DOCX and PDF with OCR fallback.</p>
            </div>
            <div className="p-5 bg-slate-900/30 border border-slate-850 rounded-2xl space-y-2">
              <span className="text-indigo-400 font-bold text-lg">📊 Similarity Analyzer</span>
              <p className="text-xs text-slate-400 leading-relaxed">Runs pure Python TF-IDF Cosine Similarity calculations to isolate plagiarized paragraphs.</p>
            </div>
            <div className="p-5 bg-slate-900/30 border border-slate-850 rounded-2xl space-y-2">
              <span className="text-indigo-400 font-bold text-lg">🎓 Layout Rebuilder</span>
              <p className="text-xs text-slate-400 leading-relaxed">Restores formatting or auto-compiles rewritten documents to standard IEEE/Springer journal templates.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-950 py-8 text-center text-xs text-slate-500 bg-slate-950/20">
        <p>© 2026 ResearchAI Inc. Run locally using open-source models.</p>
      </footer>
    </main>
  );
}
