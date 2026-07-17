'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getPaperDetails, analyzePaper, PaperAnalysis, Section } from '@/lib/api';
import { SimilarityGauge } from '@/components/SimilarityGauge';

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const paperId = searchParams.get('id');

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [error, setError] = useState('');

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

  const handleRunAnalysis = async () => {
    if (!paperId) return;
    setAnalyzing(true);
    setError('');
    try {
      await analyzePaper(paperId);
      await fetchDetails();
    } catch (err: any) {
      setError(err.message || 'Failed to run analysis.');
    } finally {
      setAnalyzing(false);
    }
  };

  if (!paperId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
        <p className="text-sm text-slate-400">No paper selected for analysis.</p>
        <button onClick={() => router.push('/')} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold uppercase tracking-wider text-white transition-all">
          Go Upload File
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold text-slate-400">Loading analysis workspace...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto mt-12 p-6 bg-rose-500/5 border border-rose-500/15 text-rose-450 rounded-2xl text-center space-y-4">
        <p className="text-xs font-semibold">{error}</p>
        <button onClick={fetchDetails} className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold tracking-wider uppercase transition-all">
          Retry
        </button>
      </div>
    );
  }

  const paper = analysis?.paper;
  const sections = analysis?.sections || [];
  const references = analysis?.references || [];

  const totalParagraphs = sections.filter(s => s.layout_metadata.type === 'paragraph').length;
  const flaggedParagraphs = sections.filter(s => s.is_flagged).length;
  const isAnalyzed = paper && paper.status !== 'uploaded' && paper.status !== 'parsed';

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
          <div className="flex items-center gap-4">
            <span className="px-3 py-1 rounded-full bg-slate-900/60 text-[10px] font-semibold text-slate-450 border border-slate-800/80">
              Analysis Space
            </span>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-8 space-y-8 animate-fade-in">
        {/* Top Info Card */}
        <div className="flex flex-col md:flex-row md:items-center justify-between p-5 bg-slate-900/20 border border-slate-900 rounded-2xl gap-5 backdrop-blur-md">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block">Document Info</span>
            <h2 className="text-base font-extrabold text-white font-mono truncate max-w-lg">{paper?.filename}</h2>
            <p className="text-[10px] text-slate-550 font-bold uppercase tracking-wider">
              Format: {paper?.original_format} &bull; Status: {paper?.status}
            </p>
          </div>
          <div className="flex gap-3">
            {!isAnalyzed ? (
              <button
                onClick={handleRunAnalysis}
                disabled={analyzing}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
              >
                {analyzing ? 'Analyzing Chunks...' : 'Run Similarity Analysis'}
              </button>
            ) : (
              <button
                onClick={() => router.push(`/rewrite?id=${paperId}`)}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
              >
                Proceed to Rewrite
              </button>
            )}
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Upload New
            </button>
          </div>
        </div>

        {isAnalyzed ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Gauge and Summary */}
            <div className="lg:col-span-1 space-y-6">
              <div className="p-6 bg-slate-900/15 border border-slate-900 rounded-2xl backdrop-blur-md">
                <SimilarityGauge score={paper?.overall_similarity || 0} />
              </div>
              
              <div className="p-5 bg-slate-900/15 border border-slate-900 rounded-2xl space-y-4 backdrop-blur-md">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-850 pb-2">
                  Similarity Summary
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400 font-medium">Total Paragraph Blocks</span>
                    <span className="text-white font-bold">{totalParagraphs}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400 font-medium">Flagged Chunks (&gt;20%)</span>
                    <span className="text-rose-450 font-bold">{flaggedParagraphs}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400 font-medium">Safe Blocks</span>
                    <span className="text-emerald-450 font-bold">{totalParagraphs - flaggedParagraphs}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Content Maps */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex justify-between items-center pb-2">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Paragraph Structure Map</h3>
                <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                  {sections.length} blocks parsed
                </span>
              </div>

              <div className="space-y-3.5 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                {sections.map((sec, idx) => {
                  const isParagraph = sec.layout_metadata.type === 'paragraph';
                  const hasMatch = sec.layout_metadata.similarity_source;

                  if (!isParagraph) {
                    return (
                      <div key={sec.id} className="p-3 bg-slate-900/10 border border-slate-950 rounded-xl text-[10px] text-slate-550 italic uppercase tracking-wider text-center select-none">
                        [{sec.layout_metadata.type} block preserved]
                      </div>
                    );
                  }

                  return (
                    <div
                      key={sec.id}
                      onClick={() => router.push(`/rewrite?id=${paperId}`)}
                      className={`p-4 rounded-2xl border cursor-pointer transition-all duration-300 ${
                        sec.is_flagged
                          ? 'bg-rose-500/[0.02] border-rose-500/15 hover:border-rose-500/30'
                          : 'bg-slate-900/10 border-slate-900 hover:border-slate-800'
                      }`}
                    >
                      <div className="flex justify-between items-center gap-4 mb-2">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest font-mono">
                          {sec.section_name || 'Block'} &bull; #{idx + 1}
                        </span>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${
                          sec.is_flagged ? 'text-rose-400' : 'text-slate-500'
                        }`}>
                          Similarity: {Math.round(sec.similarity_score * 100)}%
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed line-clamp-2 select-none">
                        {sec.original_text}
                      </p>

                      {hasMatch && (
                        <div className="mt-2.5 p-2.5 bg-rose-500/[0.03] border border-rose-500/10 rounded-xl text-[11px] text-rose-300">
                          <span className="font-bold text-[10px] uppercase tracking-wide">Match Detected:</span>
                          <p className="italic mt-0.5 text-slate-400">"{hasMatch.matching_text.substring(0, 80)}..."</p>
                          <p className="text-[9px] text-slate-500 mt-1 font-mono">Source: {hasMatch.filename}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 px-6 bg-slate-900/10 border border-slate-900 rounded-2xl text-center space-y-6 max-w-xl mx-auto backdrop-blur-md">
            <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-850 flex items-center justify-center text-indigo-400">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div className="space-y-2">
              <h3 className="text-base font-bold text-white">Document Processed</h3>
              <p className="text-xs text-slate-400 leading-relaxed max-w-sm mx-auto">
                Successfully extracted {sections.length} blocks and {references.length} reference units. Run similarity checking to compute index scores.
              </p>
            </div>
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="px-6 py-2.5 bg-indigo-650 hover:bg-indigo-500 disabled:bg-indigo-855 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
            >
              {analyzing ? 'Analyzing Chunks...' : 'Run Similarity Analysis'}
            </button>
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

export default function Dashboard() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold text-slate-400">Loading analysis workspace...</p>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
