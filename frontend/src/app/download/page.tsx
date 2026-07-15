'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getPaperDetails, rebuildPaper, getDownloadUrl, PaperAnalysis } from '@/lib/api';

const JOURNAL_CATEGORIES = [
  {
    id: 'general',
    name: 'General',
    journals: [
      { id: 'original', name: 'Original Style', icon: '📄', font: 'Preserved', columns: 'Preserved', spacing: 'Preserved', description: 'Restores the exact document margin, spacing, run alignments, and font sizes captured during parsing.' }
    ]
  },
  {
    id: 'engineering_cs',
    name: 'Engineering & CS',
    journals: [
      { id: 'ieee', name: 'IEEE Journal', icon: '🎓', font: 'Times New Roman 10pt', columns: '2 Columns', spacing: 'Single Space', description: 'Applies official IEEE rules: Times New Roman, centered titles, abstract block indents, and double-column body text.' },
      { id: 'springer', name: 'Springer LNCS', icon: '📚', font: 'Times New Roman 10pt', columns: '1 Column', spacing: 'Single Space', description: 'Formats to Springer Lecture Notes guidelines: single-column layout, custom margins, and decimal section numbers.' },
      { id: 'journal_of_the_acm', name: 'Journal of the ACM', icon: '💻', font: 'Times New Roman 10pt', columns: '1 Column', spacing: '1.15 Space', description: 'Official JACM single-column, single-spaced Times New Roman, justified layout with decimal section numbering.' },
      { id: 'nature_machine_intelligence', name: 'Nature Machine Intelligence', icon: '🤖', font: 'Arial 9pt', columns: '2 Columns', spacing: 'Single Space', description: 'Nature style double-column layout using Arial font, compact margins, and clean sans-serif headings.' }
    ]
  },
  {
    id: 'business_mgmt',
    name: 'Business & Management',
    journals: [
      { id: 'management_science', name: 'Management Science', icon: '📈', font: 'Times New Roman 11pt', columns: '1 Column', spacing: '1.5 Space', description: 'Formats to Management Science style: Times New Roman, 1.5 spacing, abstract indent, and decimal section numbering.' },
      { id: 'academy_of_management_journal', name: 'Academy of Management Journal (AMJ)', icon: '🏢', font: 'Times New Roman 12pt', columns: '1 Column', spacing: 'Double Space', description: 'AMJ style: Times New Roman 12pt, double-spaced (2.0), left aligned with centered bold Level 1 headings.' },
      { id: 'strategic_management_journal', name: 'Strategic Management Journal (SMJ)', icon: '🎯', font: 'Times New Roman 11pt', columns: '1 Column', spacing: 'Double Space', description: 'SMJ format: Times New Roman, double-spaced (2.0), left aligned with flush left italic subheadings.' },
      { id: 'harvard_business_review', name: 'Harvard Business Review (HBR)', icon: '💼', font: 'Calibri 11pt', columns: '1 Column', spacing: '1.15 Space', description: 'HBR executive style: Calibri, 1.15 spacing, left-aligned title/body, paragraph spacing, and bold sans-serif headers.' },
      { id: 'journal_of_operations_management', name: 'Journal of Operations Management (JOM)', icon: '⚙️', font: 'Times New Roman 11pt', columns: '1 Column', spacing: 'Double Space', description: 'JOM standard: Times New Roman 11pt, double-spaced (2.0), left aligned, academic standard margins.' },
      { id: 'mis_quarterly', name: 'MIS Quarterly (MISQ)', icon: '📊', font: 'Times New Roman 11pt', columns: '1 Column', spacing: '1.5 Space', description: 'MISQ layout: Times New Roman, 1.5 spacing, 1 inch margins, justified paragraphs, centered bold title.' },
      { id: 'information_management', name: 'Information & Management', icon: '💾', font: 'Times New Roman 11pt', columns: '1 Column', spacing: '1.15 Space', description: 'Elsevier Information & Management style: Times New Roman, 1.15 spacing, justified body, and decimal section numbering.' }
    ]
  },
  {
    id: 'sciences',
    name: 'General Sciences',
    journals: [
      { id: 'nature', name: 'Nature', icon: '🧬', font: 'Arial 9pt', columns: '2 Columns', spacing: 'Single Space', description: 'Nature format: double-column body text, Arial font, justified alignment, compact margins, and bold sans-serif headings.' },
      { id: 'science', name: 'Science', icon: '🧪', font: 'Times New Roman 9pt', columns: '2 Columns', spacing: 'Single Space', description: 'Science layout: double-column body text, Times New Roman, justified alignment, compact margins, and bold centered headers.' }
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

  // Search & Category states
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

  // Filter journals based on tab and search query
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
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between p-6 bg-slate-900/40 border border-slate-850 rounded-3xl gap-6 backdrop-blur-xl">
        <div className="space-y-1">
          <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Document Export</span>
          <h2 className="text-xl font-extrabold text-white font-mono truncate max-w-md">{paper?.filename}</h2>
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Configure Layout & Export</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => router.push(`/rewrite?id=${paperId}`)}
            className="px-5 py-3 bg-slate-850 hover:bg-slate-800 border border-slate-800 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all"
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

      {/* Controls & Filter Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-slate-900/20 p-4 border border-slate-850 rounded-3xl backdrop-blur-md">
        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          {['all', 'general', 'engineering_cs', 'business_mgmt', 'sciences'].map((tab) => {
            const label = tab === 'all' ? 'All' 
                        : tab === 'general' ? 'General'
                        : tab === 'engineering_cs' ? 'Engineering & CS'
                        : tab === 'business_mgmt' ? 'Business & Management'
                        : 'Sciences';
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === tab 
                    ? 'bg-indigo-650 text-white shadow-md shadow-indigo-600/15' 
                    : 'bg-slate-900/40 text-slate-400 border border-slate-850 hover:border-slate-750 hover:text-white'
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-72">
          <input
            type="text"
            placeholder="Search journal layouts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-850 rounded-xl text-xs font-medium text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
          />
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs select-none pointer-events-none">🔍</span>
        </div>
      </div>

      {/* Rebuild Setup Journals Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredJournals.map((journal) => {
          const isSelected = selectedFormat === journal.id;
          return (
            <div
              key={journal.id}
              onClick={() => setSelectedFormat(journal.id)}
              className={`p-5 border rounded-3xl cursor-pointer transition-all duration-300 backdrop-blur-xl relative overflow-hidden flex flex-col justify-between h-48 group ${
                isSelected
                  ? 'border-indigo-500 bg-indigo-500/5 shadow-lg shadow-indigo-550/5'
                  : 'border-slate-850 bg-slate-900/25 hover:border-slate-800 hover:bg-slate-900/35'
              }`}
            >
              {/* Category tag */}
              <span className="absolute top-4 right-4 px-2 py-0.5 bg-slate-950 text-[9px] font-bold text-slate-500 border border-slate-900 rounded-full group-hover:border-slate-850 transition-all">
                {journal.categoryName}
              </span>

              <div>
                <div className="flex items-center gap-3 mb-2.5">
                  <span className="text-2xl">{journal.icon}</span>
                  <h3 className="text-sm font-bold text-white leading-tight group-hover:text-indigo-400 transition-colors">
                    {journal.name}
                  </h3>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-3">
                  {journal.description}
                </p>
              </div>

              {/* Badges footer */}
              <div className="flex gap-2 pt-2 border-t border-slate-900/50 mt-auto">
                <span className="text-[9px] font-medium text-slate-500 bg-slate-950/40 px-1.5 py-0.5 rounded-md border border-slate-900">
                  {journal.font}
                </span>
                <span className="text-[9px] font-medium text-slate-500 bg-slate-950/40 px-1.5 py-0.5 rounded-md border border-slate-900">
                  {journal.columns}
                </span>
              </div>

              {/* Selection Checkmark */}
              {isSelected && (
                <div className="absolute bottom-4 right-4 bg-indigo-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px] font-bold">
                  ✓
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredJournals.length === 0 && (
        <div className="text-center p-12 bg-slate-900/20 border border-slate-850 rounded-3xl">
          <span className="text-3xl block mb-2">📂</span>
          <p className="text-slate-400 font-semibold text-sm">No journal layouts matched your search.</p>
        </div>
      )}

      {/* Selected Style Summary Card */}
      {selectedJournalInfo && (
        <div className="p-6 bg-indigo-950/15 border border-indigo-900/25 rounded-3xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 backdrop-blur-xl">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Active Configuration</span>
            <div className="flex items-center gap-2">
              <span className="text-lg">{selectedJournalInfo.icon}</span>
              <h4 className="text-base font-bold text-white">{selectedJournalInfo.name}</h4>
            </div>
            <p className="text-xs text-slate-400 max-w-2xl">{selectedJournalInfo.description}</p>
          </div>
          <div className="flex gap-3 text-center">
            <div className="px-3.5 py-2 bg-slate-950 border border-slate-900 rounded-xl space-y-0.5 min-w-[70px]">
              <span className="text-[8px] font-bold text-slate-500 uppercase tracking-wider block">Font</span>
              <span className="text-[10px] font-bold text-slate-350">{selectedJournalInfo.font.split(' ')[0]}</span>
            </div>
            <div className="px-3.5 py-2 bg-slate-950 border border-slate-900 rounded-xl space-y-0.5 min-w-[70px]">
              <span className="text-[8px] font-bold text-slate-500 uppercase tracking-wider block">Layout</span>
              <span className="text-[10px] font-bold text-slate-350">{selectedJournalInfo.columns}</span>
            </div>
            <div className="px-3.5 py-2 bg-slate-950 border border-slate-900 rounded-xl space-y-0.5 min-w-[70px]">
              <span className="text-[8px] font-bold text-slate-500 uppercase tracking-wider block">Spacing</span>
              <span className="text-[10px] font-bold text-slate-350">{selectedJournalInfo.spacing}</span>
            </div>
          </div>
        </div>
      )}

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
          className="px-6 py-3 bg-indigo-650 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-bold text-sm rounded-2xl tracking-wide uppercase transition-all shadow-lg shadow-indigo-650/15"
        >
          {compiling ? 'Compiling Document Layout...' : 'Compile & Rebuild Paper'}
        </button>
      </div>

      {/* Download Area */}
      {compiledInfo && (
        <div className="p-8 bg-slate-900/60 border border-slate-800 rounded-3xl backdrop-blur-xl shadow-2xl space-y-6 animate-fade-in">
          <div className="text-center space-y-1">
            <span className="p-3 bg-emerald-500/10 text-emerald-400 rounded-full inline-block mb-2 font-bold">✓</span>
            <h3 className="text-lg font-bold text-white">Document Rebuilt Successfully!</h3>
            <p className="text-xs text-slate-400 font-semibold">Target layout: {selectedFormat.toUpperCase()}</p>
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
              <p className="text-slate-400 font-semibold">
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
