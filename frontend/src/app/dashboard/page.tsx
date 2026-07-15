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
        <p className="text-lg text-slate-400">No paper selected for analysis.</p>
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
        <p className="text-sm font-semibold text-slate-400">Loading paper analysis data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-3xl text-center space-y-4">
        <p className="font-semibold">{error}</p>
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
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
      {/* Top Header Card */}
      <div className="flex flex-col md:flex-row md:items-center justify-between p-6 bg-slate-900/40 border border-slate-850 rounded-3xl gap-6 backdrop-blur-xl">
        <div className="space-y-1.5">
          <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Document Status</span>
          <h2 className="text-2xl font-extrabold text-white font-mono truncate max-w-lg">{paper?.filename}</h2>
          <p className="text-xs text-slate-400 uppercase tracking-wider">Format: {paper?.original_format} • Status: {paper?.status}</p>
        </div>
        <div className="flex gap-4">
          {!isAnalyzed ? (
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
            >
              {analyzing ? 'Analyzing Chunks...' : 'Run Similarity Analysis'}
            </button>
          ) : (
            <button
              onClick={() => router.push(`/rewrite?id=${paperId}`)}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/10"
            >
              Proceed to Rewrite
            </button>
          )}
          <button
            onClick={() => router.push('/')}
            className="px-5 py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all"
          >
            Upload New
          </button>
        </div>
      </div>

      {isAnalyzed ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Similarity score meter */}
          <div className="lg:col-span-1 space-y-6">
            <SimilarityGauge score={paper?.overall_similarity || 0} />
            
            <div className="p-6 bg-slate-900/40 border border-slate-850 rounded-3xl space-y-4 backdrop-blur-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Similarity Report Details</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Total Paragraph Blocks</span>
                  <span className="text-white font-bold">{totalParagraphs}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Flagged Chunks (Similarity &gt; 20%)</span>
                  <span className="text-rose-400 font-bold">{flaggedParagraphs}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Safe Blocks</span>
                  <span className="text-emerald-400 font-bold">{totalParagraphs - flaggedParagraphs}</span>
                </div>
              </div>
            </div>
          </div>

          {/* List of Chunks/Paragraphs */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-white">Paragraph Structure Map</h3>
              <span className="text-xs text-slate-400">Click elements below to expand and edit in rewriter</span>
            </div>

            <div className="space-y-4 max-h-[700px] overflow-y-auto pr-2 custom-scrollbar">
              {sections.map((sec, idx) => {
                const isParagraph = sec.layout_metadata.type === 'paragraph';
                const hasMatch = sec.layout_metadata.similarity_source;

                if (!isParagraph) {
                  // Tables and images aren't similarity tested
                  return (
                    <div key={sec.id} className="p-4 bg-slate-900/20 border border-slate-900 rounded-2xl text-xs text-slate-500 italic">
                      [{sec.layout_metadata.type.toUpperCase()} block skipped in similarity checking]
                    </div>
                  );
                }

                return (
                  <div
                    key={sec.id}
                    className={`p-5 rounded-3xl border transition-all duration-300 ${
                      sec.is_flagged
                        ? 'bg-rose-500/5 border-rose-500/20 hover:border-rose-500/40'
                        : 'bg-slate-900/40 border-slate-850 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex justify-between items-start gap-4 mb-2">
                      <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                        {sec.section_name || 'Paragraph'}
                      </span>
                      <span className={`text-xs font-bold ${
                        sec.is_flagged ? 'text-rose-400 animate-pulse' : 'text-slate-500'
                      }`}>
                        Similarity: {Math.round(sec.similarity_score * 100)}%
                      </span>
                    </div>

                    <p className="text-sm text-slate-300 leading-relaxed font-sans line-clamp-3">
                      {sec.original_text}
                    </p>

                    {hasMatch && (
                      <div className="mt-3 p-3 bg-rose-500/5 border border-rose-500/10 rounded-2xl text-xs text-rose-300">
                        <span className="font-bold">Matching source text detected:</span>
                        <p className="italic mt-1">"{hasMatch.matching_text.substring(0, 100)}..."</p>
                        <p className="text-[10px] text-slate-400 mt-1">Source paper: {hasMatch.filename}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 bg-slate-900/40 border border-slate-850 rounded-3xl text-center space-y-6 max-w-2xl mx-auto backdrop-blur-xl">
          <div className="p-4 bg-indigo-500/10 rounded-full text-indigo-400">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10 animate-bounce">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-bold text-white">Document Parsed Successfully</h3>
            <p className="text-sm text-slate-400 leading-relaxed max-w-md">
              We have extracted {sections.length} blocks and {references.length} references. Click 'Run Similarity Analysis' to index paragraphs and locate duplicate regions.
            </p>
          </div>
          <button
            onClick={handleRunAnalysis}
            disabled={analyzing}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
          >
            {analyzing ? 'Analyzing Chunks...' : 'Run Similarity Analysis'}
          </button>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Loading paper details...</p>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
