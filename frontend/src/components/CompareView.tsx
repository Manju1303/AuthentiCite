import React, { useState } from 'react';
import { Section, rewriteSection } from '@/lib/api';

interface CompareViewProps {
  section: Section;
  onUpdate: (updatedSection: Section) => void;
}

export const CompareView: React.FC<CompareViewProps> = ({ section, onUpdate }) => {
  const [editText, setEditText] = useState(section.rewritten_text || section.original_text);
  const [isRewriting, setIsRewriting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  const handleRewrite = async () => {
    setIsRewriting(true);
    setError('');
    try {
      const updated = await rewriteSection(section.id, editText);
      setEditText(updated.rewritten_text || '');
      onUpdate(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to rewrite paragraph');
    } finally {
      setIsRewriting(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    try {
      // Direct save: send edited text back to server as rewrite
      const response = await fetch(`http://127.0.0.1:8000/api/v1/sections/${section.id}/rewrite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rewritten_text: editText }),
      });
      if (!response.ok) throw new Error('Failed to save edits');
      const updated = await response.json();
      onUpdate(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to save edits');
    } finally {
      setIsSaving(false);
    }
  };

  const hasWarnings = section.layout_metadata.quality_warnings && section.layout_metadata.quality_warnings.length > 0;
  const matchSource = section.layout_metadata.similarity_source;

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl shadow-xl space-y-6">
      {/* Header Info */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <span className="text-sm font-bold text-indigo-400 uppercase tracking-wide">
          {section.section_name || 'Paragraph'} Block
        </span>
        <div className="flex items-center gap-4">
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${
            section.similarity_score >= 0.3 
              ? 'bg-rose-500/10 text-rose-400' 
              : section.similarity_score >= 0.15 
              ? 'bg-amber-500/10 text-amber-400' 
              : 'bg-emerald-500/10 text-emerald-400'
          }`}>
            Similarity: {Math.round(section.similarity_score * 100)}%
          </span>
        </div>
      </div>

      {/* Main Grid: Side by Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Original Paragraph */}
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Original Paragraph</label>
          <div className="p-4 bg-slate-950/40 border border-slate-850 rounded-2xl text-slate-300 text-sm leading-relaxed min-h-[140px] select-all">
            {section.original_text}
          </div>
          {matchSource && (
            <div className="p-3.5 bg-rose-500/5 border border-rose-500/10 rounded-2xl text-xs text-rose-300 space-y-1">
              <span className="font-bold">Match Found in DB:</span>
              <p className="italic font-mono">"{matchSource.matching_text.substring(0, 120)}..."</p>
              <p className="text-[10px] text-slate-400">Source File: {matchSource.filename}</p>
            </div>
          )}
        </div>

        {/* Rewritten/Editable Paragraph */}
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">AI Rewritten / Adjusted</label>
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="w-full p-4 bg-slate-950 border border-slate-800 rounded-2xl text-white text-sm leading-relaxed min-h-[140px] focus:outline-none focus:border-indigo-500 transition-all font-sans resize-y"
            placeholder="AI Rewritten text will appear here. You can also edit it directly..."
          />
          {hasWarnings && (
            <div className="p-3 bg-amber-500/5 border border-amber-500/15 rounded-2xl text-xs text-amber-300 space-y-1">
              <span className="font-bold">⚠️ Quality Checker Alerts:</span>
              <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                {section.layout_metadata.quality_warnings?.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Footer Controls */}
      <div className="flex items-center justify-between border-t border-slate-850 pt-4">
        {error ? (
          <span className="text-xs font-semibold text-rose-400">{error}</span>
        ) : (
          <span className="text-xs text-slate-500">Citations and equations are auto-preserved</span>
        )}
        <div className="flex gap-3">
          <button
            onClick={handleRewrite}
            disabled={isRewriting || isSaving}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:opacity-50 text-white font-bold text-xs rounded-2xl tracking-wide uppercase transition-all flex items-center gap-2 shadow-lg shadow-indigo-600/10"
          >
            {isRewriting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Rewriting...
              </>
            ) : 'AI Rewrite'}
          </button>
          <button
            onClick={handleSave}
            disabled={isRewriting || isSaving}
            className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-900 text-white font-bold text-xs rounded-2xl tracking-wide uppercase transition-all"
          >
            {isSaving ? 'Saving...' : 'Save Edits'}
          </button>
        </div>
      </div>
    </div>
  );
};
