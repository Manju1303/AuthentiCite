'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getPaperDetails, rebuildPaper, getDownloadUrl, PaperAnalysis } from '@/lib/api';

const JOURNAL_CATEGORIES = [
  {
    id: 'general',
    name: 'General',
    journals: [
      { id: 'original', name: 'Original Style', icon: '', font: 'Preserved', columns: 'Preserved', spacing: 'Preserved', description: 'Restores the exact document margin, spacing, run alignments, and font sizes captured during parsing.' }
    ]
  },
  {
    id: 'engineering_cs',
    name: 'Engineering & CS',
    journals: [
      { id: 'ieee', name: 'IEEE Journal', icon: '', font: 'Times New Roman 10pt', columns: '2 Columns', spacing: 'Single Space', description: 'Applies official IEEE rules: Times New Roman, centered titles, abstract block indents, and double-column body text.' },
      { id: 'springer', name: 'Springer LNCS', icon: '', font: 'Times New Roman 10pt', columns: '1 Column', spacing: 'Single Space', description: 'Formats to Springer Lecture Notes guidelines: single-column layout, custom margins, and decimal section numbers.' },
      { id: 'journal_of_the_acm', name: 'Journal of the ACM', icon: '', font: 'Times New Roman 10pt', columns: '1 Column', spacing: '1.15 Space', description: 'Official JACM single-column, single-spaced Times New Roman, justified layout with decimal section numbering.' },
      { id: 'nature_machine_intelligence', name: 'Nature Machine Intelligence', icon: '', font: 'Arial 9pt', columns: '2 Columns', spacing: 'Single Space', description: 'Nature style double-column layout using Arial font, compact margins, and clean sans-serif headings.' }
    ]
  },
  {
    id: 'business_mgmt',
    name: 'Business & Management',
    journals: [
      { id: 'management_science', name: 'Management Science', icon: '', font: 'Times New Roman 11pt', columns: '1 Column', spacing: '1.5 Space', description: 'Formats to Management Science style: Times New Roman, 1.5 spacing, abstract indent, and decimal section numbering.' },
      { id: 'academy_of_management_journal', name: 'Academy of Management Journal (AMJ)', icon: '', font: 'Times New Roman 12pt', columns: '1 Column', spacing: 'Double Space', description: 'AMJ style: Times New Roman 12pt, double-spaced (2.0), left aligned with centered bold Level 1 headings.' },
      { id: 'strategic_management_journal', name: 'Strategic Management Journal (SMJ)', icon: '', font: 'Times New Roman 11pt', columns: '1 Column', spacing: 'Double Space', description: 'SMJ format: Times New Roman, double-spaced (2.0), left aligned with flush left italic subheadings.' },
      { id: 'harvard_business_review', name: 'Harvard Business Review (HBR)', icon: '', font: 'Calibri 11pt', columns: '1 Column', spacing: '1.15 Space', description: 'HBR executive style: Calibri, 1.15 spacing, left-aligned title/body, paragraph spacing, and bold sans-serif headers.' }
    ]
  },
  {
    id: 'sciences',
    name: 'General Sciences',
    journals: [
      { id: 'nature', name: 'Nature', icon: '', font: 'Arial 9pt', columns: '2 Columns', spacing: 'Single Space', description: 'Nature format: double-column body text, Arial font, justified alignment, compact margins, and bold sans-serif headings.' },
      { id: 'science', name: 'Science', icon: '', font: 'Times New Roman 9pt', columns: '2 Columns', spacing: 'Single Space', description: 'Science layout: double-column body text, Times New Roman, justified alignment, compact margins, and bold centered headers.' }
    ]
  }
];

function DownloadContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const paperId = searchParams.get('id');

  const [loading, setLoading] = useState(true);
  const [compiling, setCompiling] = useState(false);
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [selectedFormat, setSelectedFormat] = useState('original');
  const [compiledInfo, setCompiledInfo] = useState<{ filename: string; format: string } | null>(null);
  const [error, setError] = useState('');
  const [pdfError, setPdfError] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');

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
        <p className="text-sm text-slate-400">No paper selected for export.</p>
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
        <p className="text-xs font-semibold text-slate-400">Loading export settings...</p>
      </div>
    );
  }

  const paper = analysis?.paper;

  const getFilteredJournals = () => {
    let list: Array<{ id: string; name: string; icon: string; font: string; columns: string; spacing: string; description: string; categoryName: string }> = [];
    
    JOURNAL_CATEGORIES.forEach(cat => {
      if (activeTab === 'all' || activeTab === cat.id) {
        cat.journals.forEach(j => {
          list.push({ ...j, categoryName: cat.name });
        });
      }
    });

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      list = list.filter(j => 
        j.name.toLowerCase().includes(query) || 
        j.description.toLowerCase().includes(query) || 
        j.categoryName.toLowerCase().includes(query)
      );
    }

    return list;
  };

  const filteredJournals = getFilteredJournals();
  const selectedJournalInfo = JOURNAL_CATEGORIES.flatMap(c => c.journals).find(j => j.id === selectedFormat);

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
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-855 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Back to Home
            </button>
            <button
              onClick={() => {
                localStorage.removeItem('isAuthenticated');
                router.push('/login');
              }}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-855 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-8 space-y-6 animate-fade-in">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between p-5 bg-slate-900/20 border border-slate-900 rounded-2xl gap-4 backdrop-blur-md">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block">Document Export</span>
            <h2 className="text-base font-extrabold text-white font-mono truncate max-w-md">{paper?.filename}</h2>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
              Rebuild document using clean formatting
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push(`/rewrite?id=${paperId}`)}
              className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-bold text-xs rounded-xl tracking-wide uppercase transition-all"
            >
              Back to Editor
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/5 border border-rose-500/15 text-rose-455 rounded-xl text-xs font-semibold text-center">
            {error}
          </div>
        )}

        {/* Filters and tabs */}
        <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-slate-900/20 p-4 border border-slate-900 rounded-2xl backdrop-blur-md">
          {/* Category Tabs */}
          <div className="flex flex-wrap gap-1.5 w-full md:w-auto">
            {['all', 'general', 'engineering_cs', 'business_mgmt', 'sciences'].map((tab) => {
              const label = tab === 'all' ? 'All' 
                          : tab === 'general' ? 'General'
                          : tab === 'engineering_cs' ? 'CS & Engineering'
                          : tab === 'business_mgmt' ? 'Business'
                          : 'Sciences';
              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                    activeTab === tab 
                      ? 'bg-indigo-650 text-white shadow-md shadow-indigo-600/10' 
                      : 'bg-slate-950/40 text-slate-400 border border-slate-900 hover:border-slate-800 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {/* Search Bar */}
          <div className="relative w-full md:w-64">
            <input
              type="text"
              placeholder="Search layout templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-900 rounded-xl text-xs font-medium text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600 transition-all font-sans"
            />
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-[10px] select-none pointer-events-none">Search</span>
          </div>
        </div>

        {/* Journals Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredJournals.map((journal) => {
            const isSelected = selectedFormat === journal.id;
            return (
              <div
                key={journal.id}
                onClick={() => setSelectedFormat(journal.id)}
                className={`p-4 border rounded-2xl cursor-pointer transition-all duration-300 relative flex flex-col justify-between h-40 group ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-500/5 shadow-md shadow-indigo-500/5'
                    : 'border-slate-900 bg-slate-900/10 hover:border-slate-800 hover:bg-slate-900/20'
                }`}
              >
                <span className="absolute top-3.5 right-3.5 px-2 py-0.5 bg-slate-950 text-[8px] font-bold text-slate-500 border border-slate-900 rounded-full group-hover:border-slate-850 transition-all font-mono uppercase">
                  {journal.categoryName}
                </span>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{journal.icon}</span>
                    <h3 className="text-xs font-bold text-white leading-tight group-hover:text-indigo-400 transition-colors">
                      {journal.name}
                    </h3>
                  </div>
                  <p className="text-[10px] text-slate-450 leading-relaxed line-clamp-2 pr-4 font-sans">
                    {journal.description}
                  </p>
                </div>

                {/* Specs Badges */}
                <div className="flex gap-1.5 pt-2 border-t border-slate-950 mt-auto">
                  <span className="text-[8px] font-semibold text-slate-500 bg-slate-950/20 px-1.5 py-0.5 rounded-md border border-slate-900 font-mono uppercase">
                    {journal.font}
                  </span>
                  <span className="text-[8px] font-semibold text-slate-500 bg-slate-950/20 px-1.5 py-0.5 rounded-md border border-slate-900 font-mono uppercase">
                    {journal.columns}
                  </span>
                </div>

                {isSelected && (
                  <div className="absolute bottom-3 right-3 bg-indigo-500 text-white rounded-full w-4.5 h-4.5 flex items-center justify-center text-[9px] font-bold">
                    ✓
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {filteredJournals.length === 0 && (
          <div className="text-center py-12 bg-slate-900/10 border border-slate-900 rounded-2xl">
            <p className="text-slate-550 font-bold text-xs uppercase tracking-wider">No layout templates match search.</p>
          </div>
        )}

        {/* Selected style specifications info row */}
        {selectedJournalInfo && (
          <div className="p-4 bg-indigo-950/10 border border-indigo-900/20 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 backdrop-blur-md">
            <div className="space-y-1">
              <span className="text-[8px] font-bold text-indigo-400 uppercase tracking-widest block">Active Style Parameters</span>
              <div className="flex items-center gap-1.5">
                <span className="text-base">{selectedJournalInfo.icon}</span>
                <h4 className="text-xs font-bold text-white">{selectedJournalInfo.name}</h4>
              </div>
              <p className="text-[10px] text-slate-450 max-w-xl font-sans">{selectedJournalInfo.description}</p>
            </div>
            <div className="flex gap-2">
              <div className="px-3 py-1.5 bg-slate-950 border border-slate-900 rounded-xl space-y-0.5 min-w-[65px] text-center">
                <span className="text-[7px] font-bold text-slate-500 uppercase tracking-wider block">Font</span>
                <span className="text-[9px] font-bold text-slate-400 font-mono">{selectedJournalInfo.font.split(' ')[0]}</span>
              </div>
              <div className="px-3 py-1.5 bg-slate-950 border border-slate-900 rounded-xl space-y-0.5 min-w-[65px] text-center">
                <span className="text-[7px] font-bold text-slate-500 uppercase tracking-wider block">Layout</span>
                <span className="text-[9px] font-bold text-slate-400 font-mono">{selectedJournalInfo.columns}</span>
              </div>
              <div className="px-3 py-1.5 bg-slate-950 border border-slate-900 rounded-xl space-y-0.5 min-w-[65px] text-center">
                <span className="text-[7px] font-bold text-slate-500 uppercase tracking-wider block">Spacing</span>
                <span className="text-[9px] font-bold text-slate-400 font-mono">{selectedJournalInfo.spacing}</span>
              </div>
            </div>
          </div>
        )}

        {/* Compile Workspace */}
        <div className="flex flex-col items-center justify-center p-6 bg-slate-900/10 border border-slate-900 rounded-2xl text-center space-y-4 max-w-lg mx-auto backdrop-blur-md animate-fade-in">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Generate Clean Copy</h3>
            <p className="text-[10px] text-slate-400 max-w-xs mx-auto leading-relaxed">
              Compile your rewritten paragraphs back into a clean formatted copy, keeping diagrams, reference citations, and formulas correct.
            </p>
          </div>
          <button
            onClick={handleCompile}
            disabled={compiling}
            className="px-5 py-2.5 bg-indigo-650 hover:bg-indigo-500 disabled:bg-indigo-855 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-650/15"
          >
            {compiling ? 'Compiling Document...' : 'Compile & Rebuild Paper'}
          </button>
        </div>

        {/* Download Output */}
        {compiledInfo && (
          <div className="p-6 bg-slate-900/15 border border-slate-900 rounded-2xl backdrop-blur-md shadow-xl space-y-5 animate-fade-in max-w-xl mx-auto">
            <div className="text-center space-y-1">
              <span className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-1 text-sm font-bold">✓</span>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Document Rebuilt Successfully</h3>
              <p className="text-[9px] text-slate-500 font-mono">Format: {selectedFormat.toUpperCase()}</p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href={getDownloadUrl(paperId, 'docx')}
                download
                className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all flex items-center justify-center gap-1.5"
              >
                Word (DOCX)
              </a>
              <button
                onClick={handleDownloadPDF}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl tracking-wide uppercase transition-all flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/10"
              >
                PDF Document
              </button>
            </div>

            {pdfError && (
              <div className="p-3.5 bg-amber-500/[0.02] border border-amber-500/10 text-amber-300 rounded-xl text-[10px] leading-relaxed space-y-1">
                <span className="font-bold text-[9px] uppercase tracking-wide">PDF Rendering Support:</span>
                <p>
                  On-the-fly PDF conversion requires LibreOffice dependencies configured on your host server.
                </p>
                <p className="text-slate-450">
                  If the PDF download times out or fails, please download the Word (DOCX) copy and export to PDF directly from MS Word.
                </p>
              </div>
            )}
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

export default function Download() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold text-slate-400">Loading export settings...</p>
      </div>
    }>
      <DownloadContent />
    </Suspense>
  );
}
