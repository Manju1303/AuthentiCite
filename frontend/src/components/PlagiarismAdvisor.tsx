'use client';

import React, { useEffect, useState } from 'react';
import { getPlagiarismAdvice, PlagiarismAdviceResponse } from '@/lib/api';

interface PlagiarismAdvisorProps {
  paperId: string;
  onRewriteSection?: (sectionId: string) => void;
  onRewriteAll?: () => void;
}

export const PlagiarismAdvisor: React.FC<PlagiarismAdvisorProps> = ({
  paperId,
  onRewriteSection,
  onRewriteAll,
}) => {
  const [advice, setAdvice] = useState<PlagiarismAdviceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadAdvice() {
      try {
        setLoading(true);
        const data = await getPlagiarismAdvice(paperId);
        setAdvice(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load plagiarism reduction advice.');
      } finally {
        setLoading(false);
      }
    }
    if (paperId) {
      loadAdvice();
    }
  }, [paperId]);

  if (loading) {
    return (
      <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl flex items-center justify-center space-x-3">
        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-slate-400 font-semibold">Generating Plagiarism Reduction Advice...</span>
      </div>
    );
  }

  if (error || !advice) {
    return (
      <div className="p-5 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-xs text-rose-300">
        {error || 'No reduction advice available for this document.'}
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-extrabold text-white font-mono">Plagiarism Reduction Advisor</h3>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">{advice.strategy_summary}</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="px-3.5 py-1.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-xs font-bold font-mono">
            Similarity: {advice.overall_similarity}%
          </div>
          {onRewriteAll && (
            <button
              onClick={onRewriteAll}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs rounded-xl tracking-wider uppercase transition-all shadow-lg shadow-indigo-600/20"
            >
              Auto-Rewrite High-Risk Blocks
            </button>
          )}
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Actionable Paragraph Fixes ({advice.flagged_count} Flagged)
        </h4>

        {advice.recommendations.length === 0 ? (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-300">
            Great news! No high-risk similarity blocks were detected in this document.
          </div>
        ) : (
          advice.recommendations.map((rec) => (
            <div
              key={rec.section_id}
              className="p-4 bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 rounded-xl space-y-3 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-indigo-400 font-mono">
                  {rec.section_name}
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  Similarity: {rec.similarity_score}%
                </span>
              </div>

              <p className="text-xs text-slate-300 italic border-l-2 border-slate-700 pl-3 py-1">
                "{rec.snippet}"
              </p>

              <div className="space-y-1.5">
                <div className="text-[11px] font-semibold text-slate-200 flex items-center space-x-1.5">
                  <span>Recommended Action:</span>
                  <span className="text-indigo-300 font-bold">{rec.recommended_action}</span>
                </div>
                <ul className="list-disc list-inside text-[11px] text-slate-400 space-y-0.5 pl-1">
                  {rec.tactics.map((tactic, idx) => (
                    <li key={idx}>{tactic}</li>
                  ))}
                </ul>
              </div>

              {onRewriteSection && (
                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => onRewriteSection(rec.section_id)}
                    className="px-3 py-1.5 bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-500/30 text-indigo-300 rounded-lg text-[11px] font-semibold transition-all"
                  >
                    Apply AI Paraphrase & Structural Shift
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
