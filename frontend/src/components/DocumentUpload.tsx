import React, { useState, useRef } from 'react';

interface DocumentUploadProps {
  onUploadSuccess: (paperId: string) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const processFile = async (selectedFile: File) => {
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setStatus('error');
      setErrorMessage('Unsupported file format. Please upload a DOCX or PDF paper.');
      return;
    }
    
    if (selectedFile.size > 30 * 1024 * 1024) {
      setStatus('error');
      setErrorMessage('File size exceeds the 30 MB limit.');
      return;
    }

    setFile(selectedFile);
    setStatus('uploading');
    setErrorMessage('');

    try {
      const { uploadPaper } = await import('@/lib/api');
      const paper = await uploadPaper(selectedFile);
      setStatus('success');
      onUploadSuccess(paper.id);
    } catch (err: any) {
      setStatus('error');
      setErrorMessage(err.message || 'An error occurred during upload.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        className={`relative flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-3xl cursor-pointer transition-all duration-300 backdrop-blur-xl ${
          isDragActive 
            ? 'border-indigo-500 bg-indigo-500/5' 
            : 'border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".docx,.pdf"
          onChange={handleFileChange}
        />

        <div className="flex flex-col items-center text-center space-y-4">
          {/* Cloud Upload Icon */}
          <div className="p-4 bg-indigo-500/10 rounded-2xl text-indigo-400">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
          </div>

          <div className="space-y-1">
            <p className="text-lg font-bold text-white">Drag & drop your research paper</p>
            <p className="text-sm text-slate-400">DOCX or PDF up to 30 MB (approx. 30 pages)</p>
          </div>
        </div>

        {/* Upload Status Overlay */}
        {status === 'uploading' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 rounded-3xl backdrop-blur-sm space-y-4">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm font-semibold text-white">Parsing layout & extracting text...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 rounded-3xl backdrop-blur-sm space-y-3">
            <div className="p-3 bg-emerald-500/10 rounded-full text-emerald-400">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-8 h-8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <p className="text-sm font-bold text-white">Ready for analysis!</p>
            {file && <p className="text-xs text-slate-400 font-mono">{file.name}</p>}
          </div>
        )}
      </div>

      {status === 'error' && (
        <div className="mt-4 p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl text-sm font-semibold text-center">
          {errorMessage}
        </div>
      )}
    </div>
  );
};
