'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getPaperDetails, rewriteAll, PaperAnalysis, Section } from '@/lib/api';
import { CompareView } from '@/components/CompareView';

function RewriteContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const paperId = searchParams.get('id');

  const [loading, setLoading] = useState(true);
  const [bulkRewriting, setBulkRewriting] = useState(false);
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const fetchDetails = async () => {
    if (!paperId) return;
    try {
      setLoading(true);
      const data = await getPaperDetails(paperId);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load paper details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [paperId]);

  const handleUpdateSection = (updatedSec: Section) => {
    if (!analysis) return;
    const newSections = analysis.sections.map((s) => (s.id === updatedSec.id ? updatedSec : s));
    setAnalysis({
      ...analysis,
      sections: newSections,
    });
  };

  const handleRewriteAll = async () => {
    if (!paperId) return;
    setBulkRewriting(true);
    setError('');
    setSuccessMsg('');
    try {
      await rewriteAll(paperId);
      setSuccessMsg('Bulk rewrite initiated. Fetching updates...');
      const interval = setInterval(async () => {
        const data = await getPaperDetails(paperId);
        setAnalysis(data);
        if (data.paper.status === 'ready' || data.paper.status === 'parsed') {
          clearInterval(interval);
          setBulkRewriting(false);
          setSuccessMsg('Bulk rewrite successfully completed!');
        }
      }, 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to rewrite all flagged sections.');
      setBulkRewriting(false);
    }
  };

  if (!paperId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
        <p className="text-sm text-slate-400">No paper selected for rewrite.</p>
        <button onClick={() => router.push('/')} className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold uppercase tracking-wider text-white transition-all">
          Go Upload File
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold text-slate-400">Loading rewriter workspace...</p>
      </div>
    );
  }

  const paper = analysis?.paper;
  const sections = analysis?.sections || [];
  const references = analysis?.references || [];
  const flaggedCount = sections.filter((s) => s.is_flagged).length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between relative bg-grid-mesh">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-950/40 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => router.push('/')}>
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-600/35">
              <span className="text-white font-extrabold text-sm">A</span>
            </div>
            <span className="text-md font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-355 font-mono">
              AuthentiCite
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-855 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Back to Home
            </button>
            <button
              onClick={() => {
                localStorage.removeItem('isAuthenticated');
                router.push('/login');
              }}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-855 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-8 space-y-6 animate-fade-in">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between p-5 bg-slate-900/20 border border-slate-900 rounded-2xl gap-4 backdrop-blur-md">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block">Active Workspace</span>
            <h2 className="text-base font-extrabold text-white font-mono truncate max-w-md">{paper?.filename}</h2>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
              {flaggedCount} similarity flags remaining
            </p>
          </div>
          <div className="flex gap-3">
            {flaggedCount > 0 && (
              <button
                onClick={handleRewriteAll}
                disabled={bulkRewriting}
                className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:bg-rose-800 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-rose-600/15"
              >
                {bulkRewriting ? 'Rewriting Flagged...' : 'Rewrite All Flagged'}
              </button>
            )}
            <button
              onClick={() => router.push(`/download?id=${paperId}`)}
              className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
            >
              Export & Download
            </button>
            <button
              onClick={() => router.push(`/dashboard?id=${paperId}`)}
              className="px-4 py-2.5 bg-slate-905 border border-slate-800 hover:bg-slate-800 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Back to Report
            </button>
          </div>
        </div>

        {/* Notifications */}
        {successMsg && (
          <div className="p-3 bg-emerald-500/5 border border-emerald-500/15 text-emerald-400 rounded-xl text-xs font-semibold text-center animate-pulse">
            {successMsg}
          </div>
        )}
        {error && (
          <div className="p-3 bg-rose-500/5 border border-rose-500/15 text-rose-400 rounded-xl text-xs font-semibold text-center">
            {error}
          </div>
        )}

        {/* Editor Blocks */}
        <div className="space-y-4">
          <div className="flex justify-between items-center pb-2">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Interactive Editor Blocks</h3>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
              Expand items below to compare
            </span>
          </div>

          <div className="space-y-4">
            {sections.map((sec) => {
              const isParagraph = sec.layout_metadata.type === 'paragraph';

              if (!isParagraph) {
                return (
                  <div key={sec.id} className="p-3 bg-slate-900/10 border border-slate-950 rounded-xl text-[10px] text-slate-550 italic uppercase tracking-wider text-center select-none">
                    [{sec.layout_metadata.type} block preserved in export]
                  </div>
                );
              }

              return (
                <CompareView
                  key={sec.id}
                  section={sec}
                  onUpdate={handleUpdateSection}
                />
              );
            })}
          </div>
        </div>

        {/* Preserved References */}
        {references.length > 0 && (
          <div className="p-5 bg-slate-900/15 border border-slate-900 rounded-2xl backdrop-blur-md space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-850 pb-2">
              Preserved References
            </h3>
            <ol className="list-decimal list-inside space-y-1.5 text-xs text-slate-400 font-sans">
              {references.map((ref) => (
                <li key={ref.id} className="leading-relaxed pl-2">
                  <span className="text-slate-300">{ref.raw_reference}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-950/80 py-6 text-center text-[10px] text-slate-500 bg-slate-950/40">
        <p>© 2026 AuthentiCite. Managed and processed locally.</p>
      </footer>
    </div>
  );
}

export default function Rewrite() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold text-slate-400">Loading rewriter workspace...</p>
      </div>
    }>
      <RewriteContent />
    </Suspense>
  );
}
