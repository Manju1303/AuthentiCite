'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { generatePaper, rebuildPaper, getDownloadUrl } from '@/lib/api';
import AcademicPaperViewer from '@/components/AcademicPaperViewer';


export default function GeneratePaperPage() {
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [journalTier, setJournalTier] = useState('q1_ieee');
  const [isGenerating, setIsGenerating] = useState(false);
  const [resultPaper, setResultPaper] = useState<any>(null);
  const [error, setError] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || isGenerating) return;

    setIsGenerating(true);
    setError('');
    setResultPaper(null);
    setDownloadUrl('');

    try {
      const res = await generatePaper(topic, journalTier, 'ieee');
      setResultPaper(res);

      // Rebuild paper to DOCX
      if (res.paper_id) {
        await rebuildPaper(res.paper_id, 'ieee');
        setDownloadUrl(getDownloadUrl(res.paper_id, 'docx'));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate research paper.');
    } finally {
      setIsGenerating(false);
    }
  };

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
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Back to Home
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-grow max-w-4xl w-full mx-auto px-6 py-12 space-y-8">
        <div className="text-center space-y-3">
          <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold uppercase tracking-widest font-mono">
            Q1–Q4 Journal Suite
          </span>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">AI Topic-to-Paper Generator</h1>
          <p className="text-xs text-slate-400 max-w-lg mx-auto">
            Input any research topic to synthesize a complete, publication-ready academic paper formatted to IEEE, Springer, Elsevier, or ACM standards.
          </p>
        </div>

        {/* Input Card */}
        <form onSubmit={handleGenerate} className="p-8 bg-slate-900/40 border border-slate-800 rounded-3xl space-y-6 shadow-2xl backdrop-blur-xl">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-200 uppercase tracking-wider block">Research Topic / Title Prompt</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Distributed Blockchain Consensus in Smart Grids with Zero-Knowledge Proofs"
              className="w-full px-4 py-3.5 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-sans"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-200 uppercase tracking-wider block">Target Journal Profile Tier</label>
            <select
              value={journalTier}
              onChange={(e) => setJournalTier(e.target.value)}
              className="w-full px-4 py-3.5 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
            >
               <option value="q1_ieee">Q1: IEEE Transactions (Two-Column, Numeric Citations)</option>
              <option value="q1_nature">Q1: Nature / Springer (Single Column, Author-Year Citations)</option>
              <option value="q2_elsevier">Q2: Elsevier ScienceDirect Journal Profile</option>
              <option value="q3_acm">Q3: ACM Computing Surveys Profile</option>
              <option value="q4_standard">Q4: International Standard Academic Profile</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isGenerating || !topic.trim()}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl tracking-wider uppercase transition-all shadow-xl shadow-indigo-600/25 flex items-center justify-center space-x-2"
          >
            {isGenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Synthesizing Multi-Section Q1 Paper...</span>
              </>
            ) : (
              <span>Generate Full Academic Paper</span>
            )}
          </button>
        </form>

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-300 rounded-2xl text-xs text-center font-semibold">
            {error}
          </div>
        )}

        {/* Generated Paper Result Preview */}
        {resultPaper && (
          <AcademicPaperViewer
            paper={{
              paper_id: resultPaper.paper_id,
              title: resultPaper.title,
              journal_tier: resultPaper.journal_tier,
              abstract: resultPaper.abstract || 'This paper presents a comprehensive research framework.',
              keywords: resultPaper.keywords || 'Artificial Intelligence, Machine Learning, Data Science',
              sections: resultPaper.sections || [],
              references: resultPaper.references || []
            }}
            onOpenWorkspace={(id) => router.push(`/dashboard?id=${id}`)}
          />
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-950/80 py-6 text-center text-[10px] text-slate-500 bg-slate-950/40">
        <p>© 2026 AuthentiCite. Q1-Q4 Journal Suite.</p>
      </footer>
    </div>
  );
}
