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
  authors?: string;
  affiliation?: string;
  conference_info?: string;
  doi?: string;
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
            {paper.conference_info || 'In Proceedings of the 3rd International Conference on Futuristic Technology (INCOFT 2025)'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug max-w-3xl mx-auto font-serif">
            {paper.title}
          </h1>

          <div className="text-xs font-sans text-slate-400 space-y-1 pt-2">
            <p className="font-bold text-slate-100 text-sm">
              {paper.authors || 'Divya B V, Anup Rao K, Ashish K Jacob, Vaishnav Pramod, Pattabi Ram'}
            </p>
            <p className="text-[11px] text-slate-400 max-w-xl mx-auto">
              {paper.affiliation || 'School of Electrical & Electronics Engineering, REVA University, Bangalore, India'}
            </p>
            <p className="text-[10px] text-indigo-400 font-mono pt-1">
              DOI: {paper.doi || '10.5220/0013734900004664'} | License: CC BY-NC-ND 4.0
            </p>
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

              {/* Drone Quadcopter Diagram for Construction Section */}
              {(sec.section_name.toLowerCase().includes('construction') || sec.section_name.toLowerCase().includes('quadcopter')) && (
                <div className="my-6 p-4 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3 font-sans text-center">
                  <div className="w-full py-4 flex items-center justify-center bg-slate-900 rounded-lg border border-slate-850">
                    <svg className="w-full max-w-xs h-36 text-indigo-400" viewBox="0 0 300 160">
                      {/* Frame Cross Arms */}
                      <line x1="50" y1="30" x2="250" y2="130" stroke="#4f46e5" strokeWidth="4" />
                      <line x1="250" y1="30" x2="50" y2="130" stroke="#4f46e5" strokeWidth="4" />
                      
                      {/* Central Body (Flight Controller KK2.1.5) */}
                      <rect x="110" y="55" width="80" height="50" rx="6" fill="#1e1b4b" stroke="#818cf8" strokeWidth="2" />
                      <text x="150" y="78" fill="#ffffff" fontSize="9" fontWeight="bold" textAnchor="middle">KK2.1.5 FC</text>
                      <text x="150" y="92" fill="#a5b4fc" fontSize="7" textAnchor="middle">Raspberry Pi Zero</text>

                      {/* 4 Motors (BLDC 1000 RPM/V) */}
                      <circle cx="50" cy="30" r="16" fill="#311b92" stroke="#6366f1" strokeWidth="2" />
                      <text x="50" y="33" fill="#fff" fontSize="7" textAnchor="middle">M1</text>

                      <circle cx="250" cy="30" r="16" fill="#311b92" stroke="#6366f1" strokeWidth="2" />
                      <text x="250" y="33" fill="#fff" fontSize="7" textAnchor="middle">M2</text>

                      <circle cx="50" cy="130" r="16" fill="#311b92" stroke="#6366f1" strokeWidth="2" />
                      <text x="50" y="133" fill="#fff" fontSize="7" textAnchor="middle">M3</text>

                      <circle cx="250" cy="130" r="16" fill="#311b92" stroke="#6366f1" strokeWidth="2" />
                      <text x="250" y="133" fill="#fff" fontSize="7" textAnchor="middle">M4</text>
                    </svg>
                  </div>
                  <p className="text-[10px] font-mono text-slate-400 italic">
                    <strong>Fig. 1.</strong> Experimental Quadcopter Configuration (F450 Frame, 1000 RPM/V BLDC Motors, KK2.1.5 Flight Controller).
                  </p>
                </div>
              )}

              {/* PWM Signal Processing Pipeline for Signal/Recreation Section */}
              {(sec.section_name.toLowerCase().includes('signal') || sec.section_name.toLowerCase().includes('result') || sec.section_name.toLowerCase().includes('recreation')) && (
                <div className="my-6 p-4 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3 font-sans text-center">
                  <div className="w-full py-4 flex flex-col items-center justify-center bg-slate-900 rounded-lg border border-slate-850 space-y-3 p-3">
                    <svg className="w-full max-w-sm h-28 text-indigo-400" viewBox="0 0 360 90">
                      {/* Transceiver */}
                      <rect x="10" y="20" width="80" height="45" rx="6" fill="#1e1b4b" stroke="#6366f1" strokeWidth="2" />
                      <text x="50" y="42" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle">Transceiver</text>
                      <text x="50" y="54" fill="#a5b4fc" fontSize="7" textAnchor="middle">Flysky RX</text>

                      <line x1="90" y1="42" x2="130" y2="42" stroke="#6366f1" strokeWidth="2" />

                      {/* Arduino UNO */}
                      <rect x="130" y="20" width="90" height="45" rx="6" fill="#311b92" stroke="#818cf8" strokeWidth="2" />
                      <text x="175" y="42" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle">Arduino UNO</text>
                      <text x="175" y="54" fill="#c7d2fe" fontSize="7" textAnchor="middle">PWM Pins 3,5,6,9.. (490Hz)</text>

                      <line x1="220" y1="42" x2="260" y2="42" stroke="#6366f1" strokeWidth="2" />

                      {/* RPi Zero */}
                      <rect x="260" y="20" width="90" height="45" rx="6" fill="#1e1b4b" stroke="#a5b4fc" strokeWidth="2" />
                      <text x="305" y="42" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle">Raspberry Pi Zero</text>
                      <text x="305" y="54" fill="#a5b4fc" fontSize="7" textAnchor="middle">Python PWM Mimic</text>
                    </svg>

                    {/* PWM Signal Waveform Simulation Graph */}
                    <div className="w-full bg-slate-950 p-2.5 rounded-md border border-slate-800 text-[10px] font-mono text-left space-y-1">
                      <div className="flex justify-between text-indigo-400 font-bold">
                        <span>Channel 2 (Throttle) Pulse Waveform</span>
                        <span>490 Hz</span>
                      </div>
                      <div className="h-6 flex items-center space-x-1 font-mono text-emerald-400 overflow-hidden">
                        <span>┌─┐_┌─┐_┌─┐_┌─┐ (1.5ms PWM Duty Cycle = 50% Hover)</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-[10px] font-mono text-slate-400 italic">
                    <strong>Fig. 2.</strong> Block Diagram of Transceiver Signal Acquisition & Microcontroller Emulation Pipeline.
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
