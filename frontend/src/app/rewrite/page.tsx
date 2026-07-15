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
      setSuccessMsg('Bulk rewrite triggered in the background. Polling for updates...');
      // Start a simple interval to poll updates every 5 seconds until status becomes ready/parsed
      const interval = setInterval(async () => {
        const data = await getPaperDetails(paperId);
        setAnalysis(data);
        if (data.paper.status === 'ready' || data.paper.status === 'parsed') {
          clearInterval(interval);
          setBulkRewriting(false);
          setSuccessMsg('Bulk rewrite completed successfully! Refreshed layout.');
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
        <p className="text-lg text-slate-400">No paper selected for rewrite.</p>
        <button onClick={() => router.push('/')} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold uppercase tracking-wider text-white transition-all">
          Go Upload File
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Loading rewriter workspace...</p>
      </div>
    );
  }

  const paper = analysis?.paper;
  const sections = analysis?.sections || [];
  const references = analysis?.references || [];
  const flaggedCount = sections.filter((s) => s.is_flagged).length;

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
      {/* Top Workspace Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between p-6 bg-slate-900/40 border border-slate-850 rounded-3xl gap-6 backdrop-blur-xl sticky top-24 z-40">
        <div className="space-y-1">
          <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Rewriter Workspace</span>
          <h2 className="text-xl font-extrabold text-white font-mono truncate max-w-md">{paper?.filename}</h2>
          <p className="text-xs text-slate-400 uppercase tracking-wider">
            {flaggedCount} sections currently flagged for plagiarism / high similarity
          </p>
        </div>
        <div className="flex gap-4">
          {flaggedCount > 0 && (
            <button
              onClick={handleRewriteAll}
              disabled={bulkRewriting}
              className="px-6 py-3 bg-rose-600 hover:bg-rose-500 disabled:bg-rose-800 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-rose-600/15"
            >
              {bulkRewriting ? 'Rewriting Flagged...' : 'Rewrite All Flagged'}
            </button>
          )}
          <button
            onClick={() => router.push(`/download?id=${paperId}`)}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/10"
          >
            Export & Download
          </button>
          <button
            onClick={() => router.push(`/dashboard?id=${paperId}`)}
            className="px-5 py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all"
          >
            Back to Report
          </button>
        </div>
      </div>

      {/* Operation messages */}
      {successMsg && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-2xl text-sm font-semibold text-center animate-pulse">
          {successMsg}
        </div>
      )}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl text-sm font-semibold text-center">
          {error}
        </div>
      )}

      {/* Editor flow */}
      <div className="space-y-8">
        <h3 className="text-lg font-bold text-white tracking-tight">Interactive Editor Blocks</h3>
        <div className="space-y-6">
          {sections.map((sec) => {
            const isParagraph = sec.layout_metadata.type === 'paragraph';

            if (!isParagraph) {
              return (
                <div key={sec.id} className="p-5 bg-slate-900/10 border border-slate-900 rounded-3xl text-sm text-slate-500 italic select-none">
                  [{sec.layout_metadata.type.toUpperCase()} block is preserved in final formatting]
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

      {/* Bibliography References */}
      {references.length > 0 && (
        <div className="p-6 bg-slate-900/40 border border-slate-850 rounded-3xl backdrop-blur-xl space-y-4">
          <h3 className="text-base font-bold text-white uppercase tracking-wider border-b border-slate-850 pb-2">
            Preserved References list
          </h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-slate-400 font-sans">
            {references.map((ref) => (
              <li key={ref.id} className="leading-relaxed pl-2">
                <span className="text-slate-300">{ref.raw_reference}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

export default function Rewrite() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Loading rewriter workspace...</p>
      </div>
    }>
      <RewriteContent />
    </Suspense>
  );
}
