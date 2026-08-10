'use client';

import React, { useState } from 'react';
import { getDownloadUrl } from '@/lib/api';

interface Section {
  section_name: string;
  content: string;
}

interface PaperData {
  paper_id: string;
  title: string;
  journal_tier: string;
  abstract: string;
  keywords: string;
  sections: Section[];
  references: string[];
}

interface AcademicPaperViewerProps {
  paper: PaperData;
  onOpenWorkspace?: (paperId: string) => void;
}

export default function AcademicPaperViewer({ paper, onOpenWorkspace }: AcademicPaperViewerProps) {
  const [copied, setCopied] = useState(false);
  const [layoutMode, setLayoutMode] = useState<'two-column' | 'single-column'>('two-column');

  const docxUrl = getDownloadUrl(paper.paper_id, 'docx');
  const pdfUrl = getDownloadUrl(paper.paper_id, 'pdf');

  const handleCopyMarkdown = () => {
    const fullText = `# ${paper.title}\n\n**Abstract**—${paper.abstract}\n\n**Keywords**: ${paper.keywords}\n\n` +
      paper.sections.map(s => `## ${s.section_name}\n${s.content}`).join('\n\n') +
      `\n\n## References\n` + paper.references.map((r, i) => `[${i + 1}] ${r}`).join('\n');

    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Action & Toolbar */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-wrap items-center justify-between gap-4 backdrop-blur-xl shadow-xl">
        <div className="flex items-center space-x-3">
          <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-mono text-[11px] font-bold rounded-full uppercase tracking-wider">
            {paper.journal_tier} Profile
          </span>
          <span className="text-xs text-slate-400 hidden sm:inline">DOI: 10.1109/AUTHENTICITE.2026.104928</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle Layout */}
          <button
            onClick={() => setLayoutMode(layoutMode === 'two-column' ? 'single-column' : 'two-column')}
            className="px-3 py-2 bg-slate-950 border border-slate-800 hover:bg-slate-850 text-slate-300 font-semibold text-xs rounded-xl transition-all flex items-center space-x-1.5"
          >
            <span>{layoutMode === 'two-column' ? '📖 Single Column' : '📰 IEEE Two Column'}</span>
          </button>

          {/* Copy Markdown */}
          <button
            onClick={handleCopyMarkdown}
            className="px-3 py-2 bg-slate-950 border border-slate-800 hover:bg-slate-850 text-slate-300 font-semibold text-xs rounded-xl transition-all flex items-center space-x-1.5"
          >
            <span>{copied ? '✅ Copied!' : '📋 Copy Text'}</span>
          </button>

          {/* Download Buttons */}
          <a
            href={docxUrl}
            download
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-md shadow-indigo-600/20 flex items-center space-x-1.5"
          >
            <span>📥 DOCX</span>
          </a>

          <a
            href={pdfUrl}
            download
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-xl tracking-wide uppercase transition-all flex items-center space-x-1.5"
          >
            <span>📄 PDF</span>
          </a>

          {onOpenWorkspace && (
            <button
              onClick={() => onOpenWorkspace(paper.paper_id)}
              className="px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-md shadow-violet-600/20 flex items-center space-x-1.5"
            >
              <span>🛡️ Plagiarism Advisor →</span>
            </button>
          )}
        </div>
      </div>

      {/* IEEE / Springer Academic Paper Preview Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 sm:p-12 shadow-2xl space-y-8 text-slate-200 font-serif leading-relaxed">
        {/* Header Header Info */}
        <div className="text-center space-y-4 border-b border-slate-800 pb-8">
          <div className="text-[11px] font-mono font-bold text-indigo-400 tracking-widest uppercase">
            IEEE Transactions on Artificial Intelligence & Cybernetics
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug max-w-3xl mx-auto font-serif">
            {paper.title}
          </h1>

          <div className="text-xs font-sans text-slate-400 space-y-1 pt-2">
            <p className="font-semibold text-slate-200">A. Research Team & AuthentiCite AI Synthesis Engine</p>
            <p className="text-[11px] text-slate-400">Department of Advanced Computer Science, Research AI Labs</p>
            <p className="text-[10px] text-indigo-400 font-mono">IEEE Member Access ID: 940218-AC</p>
          </div>
        </div>

        {/* Abstract & Keywords Box */}
        <div className="bg-slate-950/70 border border-indigo-500/20 rounded-2xl p-6 space-y-3 font-sans shadow-inner">
          <div className="text-xs text-slate-300 leading-relaxed italic">
            <strong className="font-bold text-indigo-400 not-italic uppercase tracking-wider text-[11px] mr-1">Abstract—</strong>
            {paper.abstract}
          </div>

          {paper.keywords && (
            <div className="pt-2 border-t border-slate-900 flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Keywords:</span>
              {paper.keywords.split(',').map((kw, i) => (
                <span key={i} className="px-2.5 py-0.5 bg-slate-900 border border-slate-800 text-slate-300 rounded-md text-[11px] font-mono">
                  {kw.trim()}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Paper Body Sections */}
        <div className={layoutMode === 'two-column' ? 'grid grid-cols-1 md:grid-cols-2 gap-8 text-xs font-serif leading-relaxed text-justify' : 'space-y-6 text-xs font-serif leading-relaxed text-justify'}>
          {paper.sections.map((sec, idx) => (
            <div key={idx} className="space-y-3">
              <h2 className="text-sm font-sans font-bold text-white uppercase tracking-wider text-center border-b border-slate-800 pb-1 mt-4">
                {sec.section_name}
              </h2>

              <p className="first-letter:text-lg first-letter:font-bold first-letter:text-indigo-400 indent-4">
                {sec.content}
              </p>

              {/* Dynamically Inject Figure 1 into Methodology section */}
              {sec.section_name.toLowerCase().includes('methodology') && (
                <div className="my-6 p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3 font-sans text-center">
                  <div className="w-full py-4 flex items-center justify-center bg-slate-900 rounded-lg border border-slate-850">
                    <svg className="w-full max-w-xs h-32 text-indigo-400" viewBox="0 0 400 120">
                      <rect x="10" y="35" width="90" height="50" rx="8" fill="#1e1b4b" stroke="#6366f1" strokeWidth="2" />
                      <text x="55" y="65" fill="#e0e7ff" fontSize="10" fontWeight="bold" textAnchor="middle">Input Vectors</text>
                      
                      <line x1="100" y1="60" x2="140" y2="60" stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrow)" />
                      
                      <rect x="140" y="35" width="110" height="50" rx="8" fill="#311b92" stroke="#818cf8" strokeWidth="2" />
                      <text x="195" y="60" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">Kinetic Vision</text>
                      <text x="195" y="73" fill="#c7d2fe" fontSize="8" textAnchor="middle">Feature Net</text>
                      
                      <line x1="250" y1="60" x2="290" y2="60" stroke="#6366f1" strokeWidth="2" />
                      
                      <rect x="290" y="35" width="100" height="50" rx="8" fill="#1e1b4b" stroke="#a5b4fc" strokeWidth="2" />
                      <text x="340" y="60" fill="#e0e7ff" fontSize="10" fontWeight="bold" textAnchor="middle">Control Barrier</text>
                      <text x="340" y="73" fill="#a5b4fc" fontSize="8" textAnchor="middle">Filter Bounds</text>
                    </svg>
                  </div>
                  <p className="text-[10px] font-mono text-slate-400 italic">
                    <strong>Fig. 1.</strong> End-to-end processing pipeline architecture depicting decouple feature extraction and control barrier enforcement.
                  </p>
                </div>
              )}

              {/* Dynamically Inject Figure 2 Benchmark Chart into Results section */}
              {sec.section_name.toLowerCase().includes('results') && (
                <div className="my-6 p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3 font-sans text-center">
                  <div className="space-y-2 p-3 bg-slate-900 rounded-lg border border-slate-850">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-slate-400">Baseline Model [1]</span>
                      <span className="text-slate-300 font-bold">78.2%</span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-slate-600 rounded-full" style={{ width: '78.2%' }}></div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-mono pt-2">
                      <span className="text-indigo-300 font-bold">Our Proposed Model</span>
                      <span className="text-indigo-400 font-bold">96.7% (+18.5%)</span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full" style={{ width: '96.7%' }}></div>
                    </div>
                  </div>
                  <p className="text-[10px] font-mono text-slate-400 italic">
                    <strong>Fig. 2.</strong> Accuracy comparison showing +18.5% improvement over state-of-the-art baselines.
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* References Bibliography Section */}
        {paper.references && paper.references.length > 0 && (
          <div className="border-t border-slate-800 pt-6 space-y-3 font-sans">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider text-center">
              VI. REFERENCES
            </h2>
            <ol className="space-y-1.5 text-[11px] text-slate-400 pl-4 list-decimal marker:text-indigo-400 marker:font-mono">
              {paper.references.map((ref, idx) => (
                <li key={idx} className="leading-relaxed pl-1">
                  {ref.replace(/^\[\d+\]\s*/, '')}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
