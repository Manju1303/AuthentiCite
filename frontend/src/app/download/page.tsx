'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getPaperDetails, rebuildPaper, getDownloadUrl, PaperAnalysis } from '@/lib/api';

function DownloadContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const paperId = searchParams.get('id');

  const [loading, setLoading] = useState(true);
  const [compiling, setCompiling] = useState(false);
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [selectedFormat, setSelectedFormat] = useState('original'); // original, ieee, springer
  const [compiledInfo, setCompiledInfo] = useState<{ filename: string; format: string } | null>(null);
  const [error, setError] = useState('');
  const [pdfError, setPdfError] = useState(false);

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

  const handleCompile = async () => {
    if (!paperId) return;
    setCompiling(true);
    setError('');
    setCompiledInfo(null);
    setPdfError(false);
    try {
      const result = await rebuildPaper(paperId, selectedFormat);
      setCompiledInfo(result);
    } catch (err: any) {
      setError(err.message || 'Failed to compile and rebuild paper.');
    } finally {
      setCompiling(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!paperId) return;
    const url = getDownloadUrl(paperId, 'pdf');
    try {
      const response = await fetch(url, { method: 'HEAD' });
      if (!response.ok) {
        setPdfError(true);
      } else {
        window.open(url, '_blank');
      }
    } catch {
      setPdfError(true);
    }
  };

  if (!paperId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
        <p className="text-lg text-slate-400">No paper selected for export.</p>
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
        <p className="text-sm font-semibold text-slate-400">Loading export settings...</p>
      </div>
    );
  }

  const paper = analysis?.paper;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between p-6 bg-slate-900/40 border border-slate-850 rounded-3xl gap-6 backdrop-blur-xl">
        <div className="space-y-1">
          <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Document Export</span>
          <h2 className="text-xl font-extrabold text-white font-mono truncate max-w-md">{paper?.filename}</h2>
          <p className="text-xs text-slate-400 uppercase tracking-wider">Configure Layout & Export</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => router.push(`/rewrite?id=${paperId}`)}
            className="px-5 py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all"
          >
            Back to Editor
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl text-sm font-semibold text-center">
          {error}
        </div>
      )}

      {/* Rebuild Setup */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* original */}
        <div
          onClick={() => setSelectedFormat('original')}
          className={`p-6 border rounded-3xl cursor-pointer transition-all duration-300 backdrop-blur-xl ${
            selectedFormat === 'original'
              ? 'border-indigo-500 bg-indigo-500/5'
              : 'border-slate-850 bg-slate-900/30 hover:border-slate-800'
          }`}
        >
          <span className="text-2xl mb-3 block">📄</span>
          <h3 className="text-base font-bold text-white mb-2">Original Format</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Restores the exact document margin, spacing, run alignments, and font sizes captured during parsing.
          </p>
        </div>

        {/* IEEE */}
        <div
          onClick={() => setSelectedFormat('ieee')}
          className={`p-6 border rounded-3xl cursor-pointer transition-all duration-300 backdrop-blur-xl ${
            selectedFormat === 'ieee'
              ? 'border-indigo-500 bg-indigo-500/5'
              : 'border-slate-850 bg-slate-900/30 hover:border-slate-800'
          }`}
        >
          <span className="text-2xl mb-3 block">🎓</span>
          <h3 className="text-base font-bold text-white mb-2">IEEE Journal</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Applies official IEEE rules: Times New Roman, centered titles, abstract block indents, and double-column body text.
          </p>
        </div>

        {/* Springer */}
        <div
          onClick={() => setSelectedFormat('springer')}
          className={`p-6 border rounded-3xl cursor-pointer transition-all duration-300 backdrop-blur-xl ${
            selectedFormat === 'springer'
              ? 'border-indigo-500 bg-indigo-500/5'
              : 'border-slate-850 bg-slate-900/30 hover:border-slate-800'
          }`}
        >
          <span className="text-2xl mb-3 block">📚</span>
          <h3 className="text-base font-bold text-white mb-2">Springer LNCS</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Formats to Springer Lecture Notes guidelines: single-column layout, custom margins, and decimal section numbers.
          </p>
        </div>
      </div>

      {/* Compile button */}
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900/40 border border-slate-850 rounded-3xl text-center space-y-6 backdrop-blur-xl">
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-white">Generate Clean Copy</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Our Document Rebuilder will assemble the rewritten paragraphs while preserving all figures, equations, and tables intact.
          </p>
        </div>
        <button
          onClick={handleCompile}
          disabled={compiling}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-600/15"
        >
          {compiling ? 'Compiling Document Layout...' : 'Compile & Rebuild Paper'}
        </button>
      </div>

      {/* Download Area */}
      {compiledInfo && (
        <div className="p-8 bg-slate-900/60 border border-slate-800 rounded-3xl backdrop-blur-xl shadow-2xl space-y-6 animate-fade-in">
          <div className="text-center space-y-1">
            <span className="p-3 bg-emerald-500/10 text-emerald-400 rounded-full inline-block mb-2">✓</span>
            <h3 className="text-lg font-bold text-white">Document Rebuilt Successfully!</h3>
            <p className="text-xs text-slate-400">Target layout: {selectedFormat.toUpperCase()}</p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href={getDownloadUrl(paperId, 'docx')}
              download
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all flex items-center justify-center gap-2"
            >
              <span>📥</span> Download Word (DOCX)
            </a>
            <button
              onClick={handleDownloadPDF}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/15"
            >
              <span>📥</span> Download PDF
            </button>
          </div>

          {pdfError && (
            <div className="p-4 bg-amber-500/5 border border-amber-500/15 text-amber-300 rounded-2xl text-xs leading-relaxed max-w-lg mx-auto text-left space-y-1">
              <span className="font-bold">⚠️ PDF Render Engine Info:</span>
              <p>
                Headless PDF generation (converting Word to PDF) requires LibreOffice or MS Word to be installed on the host.
              </p>
              <p className="text-slate-400">
                You can download the compiled **Word (DOCX)** version above and save it as PDF directly from Microsoft Word.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Download() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Loading export settings...</p>
      </div>
    }>
      <DownloadContent />
    </Suspense>
  );
}
