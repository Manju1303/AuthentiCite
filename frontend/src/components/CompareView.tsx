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
      const updated = await rewriteSection(section.id, editText);
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
    <div className="bg-slate-900/10 border border-slate-900 rounded-2xl p-5 space-y-5 transition-all duration-300">
      {/* Header Info */}
      <div className="flex items-center justify-between border-b border-slate-950 pb-3">
        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest font-mono">
          {section.section_name || 'Paragraph'} Block
        </span>
        <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold tracking-wider uppercase ${
          section.similarity_score >= 0.3 
            ? 'bg-rose-500/10 text-rose-450 border border-rose-500/10' 
            : section.similarity_score >= 0.15 
            ? 'bg-amber-500/10 text-amber-450 border border-amber-500/10' 
            : 'bg-emerald-500/10 text-emerald-450 border border-emerald-500/10'
        }`}>
          Similarity: {Math.round(section.similarity_score * 100)}%
        </span>
      </div>

      {/* Main Grid: Side by Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Original Paragraph */}
        <div className="space-y-2">
          <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500">Original Paragraph</span>
          <div className="p-3.5 bg-slate-950/20 border border-slate-950 rounded-xl text-slate-300 text-xs leading-relaxed min-h-[120px] select-all font-sans">
            {section.original_text}
          </div>
          {matchSource && (
            <div className="p-3 bg-rose-555/[0.02] border border-rose-500/10 rounded-xl text-[10px] text-rose-350 space-y-1">
              <span className="font-bold uppercase text-[9px]">Match Source:</span>
              <p className="italic">"{matchSource.matching_text.substring(0, 100)}..."</p>
              <p className="text-[9px] text-slate-500 font-mono">File: {matchSource.filename}</p>
            </div>
          )}
        </div>

        {/* Rewritten/Editable Paragraph */}
        <div className="space-y-2">
          <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500">AI Rewritten / Adjusted</span>
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="w-full p-3.5 bg-slate-950/40 border border-slate-900 rounded-xl text-slate-200 text-xs leading-relaxed min-h-[120px] focus:outline-none focus:border-indigo-650 transition-all font-sans resize-y"
            placeholder="AI Rewritten text will appear here. You can also edit it directly..."
          />
          {hasWarnings && (
            <div className="p-3 bg-amber-500/[0.02] border border-amber-500/10 rounded-xl text-[10px] text-amber-350 space-y-1">
              <span className="font-bold uppercase text-[9px]">⚠️ Quality Alerts:</span>
              <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                {section.layout_metadata.quality_warnings?.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Footer Controls */}
      <div className="flex items-center justify-between border-t border-slate-950 pt-3">
        <div className="max-w-[60%]">
          {error ? (
            <span className="text-[10px] font-semibold text-rose-450">{error}</span>
          ) : (
            <span className="text-[9px] text-slate-500 uppercase font-semibold tracking-wider">
              Citations & equations preserved
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRewrite}
            disabled={isRewriting || isSaving}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:opacity-50 text-white font-bold text-[10px] rounded-xl tracking-wide uppercase transition-all flex items-center gap-1.5 shadow-md shadow-indigo-600/10"
          >
            {isRewriting ? (
              <>
                <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                Rewriting...
              </>
            ) : 'AI Rewrite'}
          </button>
          <button
            onClick={handleSave}
            disabled={isRewriting || isSaving}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-950 border border-slate-850 text-slate-300 font-bold text-[10px] rounded-xl tracking-wide uppercase transition-all"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};
